# -*- coding: utf-8 -*-
"""testcase-design 产物自检脚本。

用法：
    python scripts/validate_testcase.py <产物文件>          # 校验
    python scripts/validate_testcase.py --fix-bom <csv>     # 给 CSV 补 UTF-8 BOM

只接受 .csv / .md；.xlsx / .xmind 请先另存为 CSV / Markdown。自动识别产物类型：
- .csv                → Excel 完整版合同（10 列 / BOM / 优先级 / 实际结果 / 标题 ≤25 汉字且不含 TC·P0 与【高/中/低】 /
                        功能模块与功能测试点非空且测试点不是维度名 / 字段不以 = + - @ 开头 / 步骤每行带序号 /
                        排列：模块、功能点连续，块内维度按 2.2 顺序、同维度高优先级在前）
- .md 含「预期结果」标题 → XMind 用例（层级不跳级 / 无维度节点 / 无 TC 与（P0） / 标题行末【高/中/低】 /
                        标题 ≤25 汉字（不含优先级标记） / 标题无 ** 与反引号、行尾无空格 / 只有标题和 - 明细 /
                        - 明细只在「预期结果」「范围声明」下 / 范围声明至多一处、在模块前、只含 - 明细 /
                        用例下只挂一个「预期结果」且有明细 / 每个模块、功能点下至少一条用例 /
                        同一功能点不混用有分组和无分组；不得含「测试步骤」「前置条件」）
- .md 不含「预期结果」标题 → 测试要点（一个 # / 不跳级 / 层级到 #### / 要点行【高/中/低】 / 非步骤化 /
                        「风险与回归提示」为最后一节）

校验全部通过退出码为 0，否则为 1 并逐条打印 FAIL 原因；文件类型不支持退出码为 2。
"""
import csv
import io
import os
import re
import sys

STD_DIMS = ["功能测试", "边界测试", "异常测试", "权限测试", "安全测试", "数据一致性测试",
            "并发测试", "集成测试", "性能测试", "兼容性测试", "用户体验测试"]
CSV_HEADER = ["功能模块", "功能测试点", "验证维度", "用例标题", "优先级",
              "前置条件", "测试步骤", "预期结果", "实际结果", "备注"]
EXPECTED = "预期结果"
EXPECTED_LIKE = re.compile(r"^(预期|期望)(结果)?[：:]?$|^结果[：:]?$")
PRI_MARK = re.compile(r"【(高|中|低)】\s*$")
STEP_TITLES = {"测试步骤：", "测试步骤"}
FORMULA_WORDS = re.compile(r"等于|乘以|(?<![删排去剔扣免清解移拆消撤])除以")
FORMULA_MSG = "计算公式用数学符号（= × ÷ ≥ 等），不写「等于」「乘以」「除以」"
TITLE_MAX_CJK = 25
PRI_RANK = {"高": 0, "中": 1, "低": 2}
FORMULA_PREFIX = ("=", "+", "-", "@")
STEP_NUM = re.compile(r"^\s*\d+[.、．)）]")
SCOPE = "范围声明"
RISK = "风险与回归提示"


def cjk_len(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def title_body(s):
    return PRI_MARK.sub("", s).rstrip()


def read_raw(path):
    return open(path, "rb").read()


def report(results):
    failed = 0
    for ok, msg in results:
        print(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} 项通过")
    return 1 if failed else 0


def parse_headings(lines):
    out = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*?)\s*$", ln)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def next_heading_line(headings, idx, n_lines):
    if idx + 1 < len(headings):
        return headings[idx + 1][0]
    return n_lines


def direct_children(headings, idx):
    _, lv, _ = headings[idx]
    children = []
    for j in range(idx + 1, len(headings)):
        _, lv2, _ = headings[j]
        if lv2 <= lv:
            break
        if lv2 == lv + 1:
            children.append(j)
    return children


def list_items(lines, start, end):
    return [ln.strip() for ln in lines[start:end] if re.match(r"^\s*-\s+\S", ln)]


def span_end(headings, idx, n_lines):
    """标题 idx 的管辖范围终点：下一个级别 <= 它的标题所在行，或文件末尾。"""
    _, lv, _ = headings[idx]
    for j in range(idx + 1, len(headings)):
        if headings[j][1] <= lv:
            return headings[j][0]
    return n_lines


def level_skips(headings):
    prev, skip = 0, []
    for _, lv, t in headings:
        if prev and lv > prev + 1:
            skip.append(t[:40])
        prev = lv
    return skip


def validate_csv(path, results):
    raw = read_raw(path)
    results.append((raw.startswith(b"\xef\xbb\xbf"),
                    "UTF-8 BOM（缺失时可运行 --fix-bom 补齐）"))
    text = raw.decode("utf-8-sig", errors="replace")
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        results.append((False, "文件为空或无数据行"))
        return
    results.append((rows[0] == CSV_HEADER, f"表头为固定 10 列且顺序正确（实际：{rows[0]}）"))
    data = rows[1:]
    bad_len = [i for i, r in enumerate(data, start=2) if len(r) != 10]
    results.append((not bad_len, f"每行 10 个字段（异常行：{bad_len[:3]}）"))
    ok10 = [(i, r) for i, r in enumerate(data, start=2) if len(r) == 10]

    def label(i, r):
        return r[3].strip() or f"第{i}行"

    bad_pri = [label(i, r) for i, r in ok10 if r[4].strip() not in ("高", "中", "低")]
    results.append((not bad_pri, f"优先级只有 高/中/低（异常：{bad_pri[:3]}）"))
    bad_act = [label(i, r) for i, r in ok10 if r[8].strip() not in ("—",)]
    results.append((not bad_act, f"实际结果列填 —（异常：{bad_act[:3]}）"))
    empty_title = [f"第{i}行" for i, r in ok10 if not r[3].strip()]
    results.append((not empty_title, f"用例标题非空（异常：{empty_title[:3]}）"))
    titled_tc = [label(i, r) for i, r in ok10
                 if re.search(r"TC\d", r[3]) or re.search(r"（P[012]）", r[3])]
    results.append((not titled_tc, f"标题不含 TC 编号或（P0/P1/P2）（异常：{titled_tc[:3]}）"))
    over = [f"{label(i, r)}({cjk_len(r[3])}字)" for i, r in ok10 if cjk_len(r[3]) > TITLE_MAX_CJK]
    results.append((not over, f"用例标题 ≤{TITLE_MAX_CJK} 个汉字（超长：{over[:3]}）"))
    empty = [label(i, r) for i, r in ok10 if not r[5].strip() or not r[6].strip() or not r[7].strip()]
    results.append((not empty, f"前置条件/测试步骤/预期结果均非空（异常：{empty[:3]}）"))
    bad_dim = sorted({r[2].strip() for _, r in ok10} - set(STD_DIMS))
    results.append((not bad_dim, f"验证维度均为 11 个标准名（异常：{bad_dim}）"))
    wordy = [label(i, r) for i, r in ok10 if any(FORMULA_WORDS.search(c) for c in r)]
    results.append((not wordy, f"{FORMULA_MSG}（{len(wordy)} 行，例：{wordy[:3]}）"))

    empty_mod = [f"第{i}行" for i, r in ok10 if not r[0].strip() or not r[1].strip()]
    results.append((not empty_mod, f"功能模块/功能测试点非空（异常：{empty_mod[:3]}）"))
    dim_as_point = [label(i, r) for i, r in ok10 if r[1].strip() in STD_DIMS]
    results.append((not dim_as_point, f"功能测试点不填维度名（异常：{dim_as_point[:3]}）"))
    pri_in_title = [label(i, r) for i, r in ok10 if PRI_MARK.search(r[3])]
    results.append((not pri_in_title, f"标题列不带【高/中/低】，优先级只在第 5 列（异常：{pri_in_title[:3]}）"))
    bad_formula = [f"{label(i, r)}:第{k + 1}列" for i, r in ok10
                   for k, c in enumerate(r) if c.strip()[:1] in FORMULA_PREFIX]
    results.append((not bad_formula, f"字段不以 = + - @ 开头，Excel 会当公式（异常：{bad_formula[:3]}）"))
    bad_steps = [label(i, r) for i, r in ok10
                 if any(ln.strip() and not STEP_NUM.match(ln) for ln in r[6].splitlines())]
    results.append((not bad_steps, f"测试步骤每行带序号（异常：{bad_steps[:3]}）"))

    order_bad, seen_mod, seen_pt = [], set(), set()
    prev_mod = prev_key = None
    prev_rank = (-1, -1)
    for i, r in ok10:
        mod, pt, dim, pri = r[0].strip(), r[1].strip(), r[2].strip(), r[4].strip()
        key = (mod, pt)
        if mod != prev_mod:
            if mod in seen_mod:
                order_bad.append(f"第{i}行 模块「{mod}」不连续")
            seen_mod.add(mod)
        if key != prev_key:
            if key in seen_pt:
                order_bad.append(f"第{i}行 功能点「{pt}」不连续")
            seen_pt.add(key)
            prev_rank = (-1, -1)
        rank = (STD_DIMS.index(dim) if dim in STD_DIMS else 99, PRI_RANK.get(pri, 9))
        if rank < prev_rank:
            order_bad.append(f"第{i}行 「{r[3].strip()[:20]}」维度/优先级顺序")
        prev_rank, prev_mod, prev_key = rank, mod, key
    results.append((not order_bad, f"排列：模块、功能点连续，块内维度按 2.2 顺序、同维度高优先级在前（异常：{order_bad[:3]}）"))


def validate_xmind(text, results):
    lines = text.splitlines()
    headings = parse_headings(lines)
    n_lines = len(lines)

    h1 = [t for _, lv, t in headings if lv == 1]
    results.append((len(h1) == 1, f"全文恰好一个 # 中心主题（实际 {len(h1)} 个）"))

    skip = level_skips(headings)
    results.append((not skip, f"标题层级不跳级（跳级：{skip[:3]}）"))

    styled = [t[:40] for _, _, t in headings if re.search(r"[*`]", t)]
    results.append((not styled, f"标题不含 ** / * / 反引号（异常：{styled[:3]}）"))
    trailing = [t[:40] for i, _, t in headings if lines[i] != lines[i].rstrip()]
    results.append((not trailing, f"标题行尾无空格（异常：{trailing[:3]}）"))
    stray = [ln.strip()[:40] for ln in lines
             if ln.strip() and not re.match(r"^#+\s", ln) and not re.match(r"^\s*-\s+\S", ln)]
    results.append((not stray, f"全文只有标题和 - 明细，没有普通段落（异常：{stray[:3]}）"))

    dim_heads = [t for _, _, t in headings if t in STD_DIMS]
    results.append((not dim_heads, f"不把 11 个维度名写成标题节点（异常：{dim_heads[:3]}）"))

    modules = [t for _, lv, t in headings if lv == 2 and t != "范围声明"]
    results.append((bool(modules), "存在业务 ## 模块（范围声明不算）"))
    results.append((any(lv == 3 for _, lv, _ in headings), "存在 ### 功能点"))

    scope = [(k, lv) for k, (_, lv, t) in enumerate(headings) if t == "范围声明"]
    first_biz = next((k for k, (_, lv, t) in enumerate(headings) if lv == 2 and t != "范围声明"),
                     len(headings))
    scope_ok = len(scope) <= 1 and all(lv == 2 and k < first_biz for k, lv in scope)
    results.append((scope_ok, f"「范围声明」至多一处，为 ## 且在第一个业务模块之前（实际 {len(scope)} 处）"))

    cases = []
    expected_idx = []
    for i, (_, lv, t) in enumerate(headings):
        child_titles = [headings[j][2] for j in direct_children(headings, i)]
        if EXPECTED in child_titles:
            cases.append(i)
        if t.rstrip("：") == EXPECTED:
            expected_idx.append(i)

    results.append((bool(cases), f"至少有一条用例（标题下直接挂「{EXPECTED}」）（{len(cases)} 条）"))

    bad_case = []
    for i in cases:
        _, _, t = headings[i]
        if t.rstrip("：") == EXPECTED or t in STEP_TITLES or t == "范围声明" or t in STD_DIMS:
            bad_case.append(t[:40])
        elif re.search(r"TC\s*\d", t) or re.search(r"（P[012]）", t):
            bad_case.append(t[:40])
    results.append((not bad_case, f"用例标题不含 TC 编号、（P0）或维度名（异常：{bad_case[:3]}）"))

    missing_pri = [t[:40] for i in cases for _, _, t in [headings[i]] if not PRI_MARK.search(t)]
    results.append((not missing_pri, f"用例标题行末【高/中/低】（缺失：{missing_pri[:3]}）"))

    over = [f"{t}({cjk_len(title_body(t))}字)" for i in cases for _, _, t in [headings[i]]
            if cjk_len(title_body(t)) > TITLE_MAX_CJK]
    results.append((not over, f"用例标题 ≤{TITLE_MAX_CJK} 个汉字（不含优先级标记）（超长：{over[:3]}）"))

    h_expected = [t for _, _, t in headings if EXPECTED_LIKE.match(t)]
    bad_exp_name = [t for t in h_expected if t != EXPECTED]
    results.append((not bad_exp_name,
                    f"预期标题须恰好为「{EXPECTED}」（异常：{bad_exp_name[:3]}）"))

    missing_detail = []
    for i in expected_idx:
        start = headings[i][0] + 1
        end = next_heading_line(headings, i, n_lines)
        if not list_items(lines, start, end):
            parent = "?"
            for c in reversed(cases):
                if headings[c][0] < headings[i][0]:
                    parent = headings[c][2][:40]
                    break
            missing_detail.append(parent)
    results.append((not missing_detail, f"每个「{EXPECTED}」下至少一条 - 明细（缺失：{missing_detail[:3]}）"))

    extra = []
    for i in cases:
        kids = [headings[j][2] for j in direct_children(headings, i)]
        if kids != [EXPECTED] or list_items(lines, headings[i][0] + 1, next_heading_line(headings, i, n_lines)):
            extra.append(headings[i][2][:40])
    results.append((not extra, f"用例标题下只挂一个「{EXPECTED}」，没有别的子节点（异常：{extra[:3]}）"))

    case_set = set(cases)
    mixed = []
    for i, (_, lv, t) in enumerate(headings):
        if lv == 3 and len({j in case_set for j in direct_children(headings, i)}) > 1:
            mixed.append(t[:40])
    results.append((not mixed, f"同一功能点下不混用有分组和无分组写法（异常：{mixed[:3]}）"))

    h6 = [t for _, lv, t in headings if lv == 6]
    bad6 = [t for t in h6 if t != EXPECTED]
    results.append((not bad6, f"###### 只用于「{EXPECTED}」（异常：{bad6[:3]}）"))

    scope_spans = [(headings[k][0], span_end(headings, k, n_lines)) for k, _ in scope]

    def in_scope(line_no):
        return any(s < line_no < e for s, e in scope_spans)

    stray_items = []
    if headings and list_items(lines, 0, headings[0][0]):
        stray_items.append("文首")
    for k, (ln_i, _, t) in enumerate(headings):
        if t.rstrip("：") == EXPECTED or t == SCOPE or k in case_set or in_scope(ln_i):
            continue
        if list_items(lines, ln_i + 1, next_heading_line(headings, k, n_lines)):
            stray_items.append(t[:40])
    results.append((not stray_items, f"- 明细只出现在「{EXPECTED}」和「{SCOPE}」下（异常：{stray_items[:3]}）"))

    for k, _ in scope:
        ln_i = headings[k][0]
        kids = direct_children(headings, k)
        items = list_items(lines, ln_i + 1, next_heading_line(headings, k, n_lines))
        results.append((not kids and bool(items), f"「{SCOPE}」下只有 - 明细：无子标题且至少一条"))

    empty_nodes = []
    for k, (ln_i, lv, t) in enumerate(headings):
        if lv in (2, 3) and t != SCOPE and not in_scope(ln_i):
            end = span_end(headings, k, n_lines)
            if not any(ln_i < headings[c][0] < end for c in cases):
                empty_nodes.append(t[:40])
    results.append((not empty_nodes, f"每个模块 / 功能点下至少一条用例（空节点：{empty_nodes[:3]}）"))

    results.append(("前置条件" not in text and "测试步骤" not in text,
                    "XMind 用例不含前置条件/测试步骤（要前置/步骤走 Excel）"))

    wordy = [ln.strip()[:40] for ln in lines if FORMULA_WORDS.search(ln)]
    results.append((not wordy, f"{FORMULA_MSG}（{len(wordy)} 处，例：{wordy[:3]}）"))


def validate_testpoint(text, results):
    lines = text.splitlines()
    headings = parse_headings(lines)
    h1 = [t for _, lv, t in headings if lv == 1]
    results.append((len(h1) == 1, f"全文恰好一个 # 标题（实际 {len(h1)} 个）"))
    skip = level_skips(headings)
    results.append((not skip, f"标题层级不跳级（跳级：{skip[:3]}）"))
    deep = [t[:40] for _, lv, t in headings if lv >= 5]
    results.append((not deep, f"要点层级到 #### 为止，#### 下直接写 -（异常：{deep[:3]}）"))
    results.append((not re.search(r"^#+\s*预期结果\s*$", text, re.M), "要点不含「预期结果」标题"))
    results.append(("测试步骤" not in text, "要点不含测试步骤"))
    main_part = re.split(r"^##\s*" + RISK, text, flags=re.M)[0]
    pts = [ln for ln in main_part.splitlines() if re.match(r"^\s*-\s+", ln)]
    with_pri = [ln for ln in pts if re.search(r"【(高|中|低)】", ln)]
    results.append((bool(pts) and len(with_pri) == len(pts),
                    f"要点行末均带【高/中/低】（{len(with_pri)}/{len(pts)}）"))
    step_like = [ln.strip()[:30] for ln in pts if re.match(r"^\s*-\s*(点击|输入|打开|进入页面)", ln)]
    results.append((not step_like, f"要点非步骤化（步骤化：{step_like[:3]}）"))
    h2 = [t for _, lv, t in headings if lv == 2]
    results.append((bool(h2) and h2[-1].startswith(RISK), f"「{RISK}」是最后一个 ## 节"))


def main():
    args = [a for a in sys.argv[1:]]
    fix_bom = "--fix-bom" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    path = paths[0]
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".csv", ".md", ".markdown"):
        print(f"FAIL 不支持的文件类型「{ext or '无扩展名'}」：只校验 .csv / .md；.xlsx / .xmind 请先另存为 CSV / Markdown")
        return 2
    if fix_bom:
        raw = read_raw(path)
        if raw.startswith(b"\xef\xbb\xbf"):
            print("已带 BOM，无需处理")
            return 0
        open(path, "wb").write(b"\xef\xbb\xbf" + raw)
        print("已补齐 UTF-8 BOM")
        return 0

    results = []
    if path.lower().endswith(".csv"):
        validate_csv(path, results)
    else:
        text = read_raw(path).decode("utf-8-sig", errors="replace")
        if re.search(r"^#+\s*预期结果\s*：?\s*$", text, re.M):
            validate_xmind(text, results)
        else:
            validate_testpoint(text, results)
    return report(results)


if __name__ == "__main__":
    sys.exit(main())
