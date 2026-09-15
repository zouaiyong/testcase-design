# -*- coding: utf-8 -*-
"""testcase-design 产物自检脚本。

用法：
    python scripts/validate_testcase.py <产物文件>          # 校验
    python scripts/validate_testcase.py --fix-bom <csv>     # 给 CSV 补 UTF-8 BOM

自动识别产物类型：
- .csv                → Excel 完整版合同（11 列 / BOM / 优先级 / 实际结果 / 标题字数 / 编号连续）
- .md 含 TC 编号      → XMind 用例（层级不跳级 / 维度标准名 / 标题 ≤21 汉字 / 编号连续；
                        含「测试步骤」或「前置条件」按完整版校验，否则按精简版校验）
- .md 不含 TC 编号    → 测试要点（要点行【高/中/低】/ 风险与回归提示 / 非步骤化）

校验全部通过退出码为 0，否则为 1 并逐条打印 FAIL 原因。
"""
import csv
import io
import os
import re
import sys

STD_DIMS = ["功能测试", "边界测试", "异常测试", "权限测试", "安全测试", "数据一致性测试",
            "并发测试", "集成测试", "性能测试", "兼容性测试", "用户体验测试"]
CSV_HEADER = ["用例编号", "功能模块", "功能测试点", "验证维度", "用例标题", "优先级",
              "前置条件", "测试步骤", "预期结果", "实际结果", "备注"]


def cjk_len(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


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


def validate_csv(path, results):
    raw = read_raw(path)
    results.append((raw.startswith(b"\xef\xbb\xbf"),
                    "UTF-8 BOM（缺失时可运行 --fix-bom 补齐）"))
    text = raw.decode("utf-8-sig", errors="replace")
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        results.append((False, "文件为空或无数据行"))
        return
    results.append((rows[0] == CSV_HEADER, f"表头为固定 11 列且顺序正确（实际：{rows[0]}）"))
    data = rows[1:]
    bad_len = [r[0] for r in data if len(r) != 11]
    results.append((not bad_len, f"每行 11 个字段（异常行：{bad_len[:3]}）"))
    ok11 = [r for r in data if len(r) == 11]
    bad_pri = [r[0] for r in ok11 if r[5].strip() not in ("高", "中", "低")]
    results.append((not bad_pri, f"优先级只有 高/中/低（异常：{bad_pri[:3]}）"))
    bad_act = [r[0] for r in ok11 if r[9].strip() not in ("—",)]
    results.append((not bad_act, f"实际结果列填 —（异常：{bad_act[:3]}）"))
    over = [f"{r[0]}:{r[4]}({cjk_len(r[4])}字)" for r in ok11 if cjk_len(r[4]) > 21]
    results.append((not over, f"用例标题 ≤21 个汉字（超长：{over[:3]}）"))
    empty = [r[0] for r in ok11 if not r[6].strip() or not r[7].strip() or not r[8].strip()]
    results.append((not empty, f"前置条件/测试步骤/预期结果均非空（异常：{empty[:3]}）"))
    bad_dim = sorted({r[3].strip() for r in ok11} - set(STD_DIMS))
    results.append((not bad_dim, f"验证维度均为 11 个标准名（异常：{bad_dim}）"))
    nums = [int(m.group(1)) for r in ok11
            for m in [re.match(r"TC(?:\d+-)?(\d+)$", r[0].strip())] if m]
    results.append((bool(nums) and nums == list(range(1, len(nums) + 1)),
                    f"用例编号连续不跳号（共 {len(nums)} 条）"))


def validate_xmind(text, results):
    lines = text.splitlines()
    headings = [(len(re.match(r"^(#+)", ln).group(1)), ln.strip())
                for ln in lines if re.match(r"^#+\s", ln)]
    prev, skip = 0, []
    for lv, t in headings:
        if prev and lv > prev + 1:
            skip.append(t[:40])
        prev = lv
    results.append((not skip, f"标题层级不跳级（跳级：{skip[:3]}）"))
    h4 = [t.lstrip("#").strip() for lv, t in headings if lv == 4]
    bad4 = [d for d in h4 if d not in STD_DIMS]
    results.append((not bad4, f"#### 均为 11 个标准维度名（异常：{bad4[:3]}）"))
    results.append(("功能测试" in h4, "功能测试维度存在"))
    h5 = [t for lv, t in headings if lv == 5]
    bad5 = [t for t in h5 if not re.match(r"^#####\s+TC\S*\d+\s+.+（P[012]）\s*$", t)]
    results.append((bool(h5) and not bad5, f"##### 均为 TC编号 标题（P优先级）（异常：{bad5[:3]}）"))
    over = []
    for t in h5:
        m = re.match(r"^#####\s+TC\S*\d+\s+(.+?)（P[012]）\s*$", t)
        if m and cjk_len(m.group(1)) > 21:
            over.append(f"{m.group(1)}({cjk_len(m.group(1))}字)")
    results.append((not over, f"标题 ≤21 个汉字（超长：{over[:3]}）"))
    nums = [int(m.group(2)) for t in h5
            for m in [re.match(r"^#####\s+TC(\d+)-(\d+)", t)] if m]
    if nums:
        results.append((nums == list(range(1, len(nums) + 1)), f"TC 编号连续不跳号（{len(nums)} 条）"))
    full = ("测试步骤" in text) or ("前置条件" in text)
    h6 = [t.lstrip("#").strip() for lv, t in headings if lv == 6]
    bad6 = [t for t in h6 if t not in ("预期结果", "测试步骤：")]
    results.append((not bad6, f"###### 只用于 测试步骤：/预期结果（异常：{bad6[:3]}）"))
    if full:
        results.append((True, "检测到前置/步骤：按完整版校验"))
    else:
        results.append(("前置条件" not in text and "测试步骤" not in text,
                        "精简版不含前置条件/测试步骤"))
    missing = []
    for i, (lv, t) in enumerate(headings):
        if lv == 5:
            nxt = headings[i + 1] if i + 1 < len(headings) else None
            if not (nxt and nxt[0] == 6 and "预期结果" in nxt[1]):
                missing.append(t[:40])
    results.append((not missing, f"每个 ##### 下都有 ###### 预期结果（缺失：{missing[:3]}）"))


def validate_testpoint(text, results):
    results.append((not re.search(r"TC\d", text), "要点不含 TC 编号"))
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
        if re.search(r"TC\d", text):
            validate_xmind(text, results)
        else:
            validate_testpoint(text, results)
    return report(results)


if __name__ == "__main__":
    sys.exit(main())
