# -*- coding: utf-8 -*-
"""testcase-design 产物自检脚本。

用法：
    python scripts/validate_testcase.py <产物文件>          # 校验
    python scripts/validate_testcase.py --fix-bom <csv>     # 给 CSV 补 UTF-8 BOM

自动识别产物类型：
- .csv                → Excel 完整版合同（10 列 / BOM / 优先级 / 实际结果 / 标题 ≤25 汉字且不含 TC·P0）
- .md 含「预期结果」标题 → XMind 用例（层级不跳级 / 无维度节点 / 无 TC 与（P0） / 标题行末【高/中/低】 /
                        标题 ≤25 汉字（不含优先级标记） / 每条用例下有预期明细；不得含「测试步骤」「前置条件」）
- .md 不含「预期结果」标题 → 测试要点（要点行【高/中/低】/ 风险与回归提示 / 非步骤化）

校验全部通过退出码为 0，否则为 1 并逐条打印 FAIL 原因。
"""
import csv
import io
import re
import sys

STD_DIMS = ["功能测试", "边界测试", "异常测试", "权限测试", "安全测试", "数据一致性测试",
            "并发测试", "集成测试", "性能测试", "兼容性测试", "用户体验测试"]
CSV_HEADER = ["功能模块", "功能测试点", "验证维度", "用例标题", "优先级",
              "前置条件", "测试步骤", "预期结果", "实际结果", "备注"]
EXPECTED = "预期结果"
PRI_MARK = re.compile(r"【(高|中|低)】\s*$")
STEP_TITLES = {"测试步骤：", "测试步骤"}
TITLE_MAX_CJK = 25


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


def validate_xmind(text, results):
    lines = text.splitlines()
    headings = parse_headings(lines)
    n_lines = len(lines)

    h1 = [t for _, lv, t in headings if lv == 1]
    results.append((len(h1) == 1, f"全文恰好一个 # 中心主题（实际 {len(h1)} 个）"))

    prev, skip = 0, []
    for _, lv, t in headings:
        if prev and lv > prev + 1:
            skip.append(t[:40])
        prev = lv
    results.append((not skip, f"标题层级不跳级（跳级：{skip[:3]}）"))

    dim_heads = [t for _, _, t in headings if t in STD_DIMS]
    results.append((not dim_heads, f"不把 11 个维度名写成标题节点（异常：{dim_heads[:3]}）"))

    modules = [t for _, lv, t in headings if lv == 2 and t != "范围声明"]
    results.append((bool(modules), "存在业务 ## 模块（范围声明不算）"))
    results.append((any(lv == 3 for _, lv, _ in headings), "存在 ### 功能点"))

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

    h_expected = [t for _, _, t in headings if t.rstrip("：") == EXPECTED]
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

    case_without_expected = []
    for i in cases:
        child_titles = [headings[j][2] for j in direct_children(headings, i)]
        if EXPECTED not in child_titles:
            case_without_expected.append(headings[i][2][:40])
    results.append((not case_without_expected, f"用例标题的直接子标题是「{EXPECTED}」"))

    h6 = [t for _, lv, t in headings if lv == 6]
    bad6 = [t for t in h6 if t != EXPECTED]
    results.append((not bad6, f"###### 只用于「{EXPECTED}」（异常：{bad6[:3]}）"))

    results.append(("前置条件" not in text and "测试步骤" not in text,
                    "XMind 用例不含前置条件/测试步骤（要前置/步骤走 Excel）"))


def validate_testpoint(text, results):
    results.append((not re.search(r"^#+\s*预期结果\s*$", text, re.M), "要点不含「预期结果」标题"))
    results.append(("测试步骤" not in text, "要点不含测试步骤"))
    main_part = re.split(r"^##\s*风险与回归提示", text, flags=re.M)[0]
    pts = [ln for ln in main_part.splitlines() if re.match(r"^\s*-\s+", ln)]
    with_pri = [ln for ln in pts if re.search(r"【(高|中|低)】", ln)]
    results.append((bool(pts) and len(with_pri) == len(pts),
                    f"要点行末均带【高/中/低】（{len(with_pri)}/{len(pts)}）"))
    step_like = [ln.strip()[:30] for ln in pts if re.match(r"^\s*-\s*(点击|输入|打开|进入页面)", ln)]
    results.append((not step_like, f"要点非步骤化（步骤化：{step_like[:3]}）"))
    results.append(("风险与回归提示" in text, "文末有「风险与回归提示」"))


def main():
    args = [a for a in sys.argv[1:]]
    fix_bom = "--fix-bom" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    path = paths[0]
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
