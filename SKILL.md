---
name: testcase-design
description: "从需求设计软件功能测试用例，交付 XMind、Excel/CSV 或测试要点；也用于评审已有用例。用户要写测试用例、生成用例、设计用例、用例清单、完整可执行用例（前置+步骤+预期）、测试要点/测试点，把 PRD（含飞书 Wiki/云文档）转成用例，或评审/检查用例时使用；只说「写用例」「出个用例」且未提格式时也使用。不用于执行已有用例、写自动化脚本、探索性测试，以及生成-评审-修复闭环。"
---

# 软件功能测试用例设计

---

## 一、先勾选格式（未勾选禁止生成）

生成用例或测试要点之前，必须让用户勾选交付格式。**勾选完成前：不写文件、不输出用例/要点正文、不读 xmind/excel/testpoint 细则**（读完本节即停）。

**能唯一落到下面三项之一才跳过勾选**：

- 「XMind / 思维导图 / xmind格式」→ XMind 版
- 「Excel / CSV / 表格」「完整版 / 可执行 / 含前置·步骤·预期」→ Excel/CSV 完整可执行
- 「测试要点 / 测试点」→ 只要测试要点
- 同一次对话里已经勾选过，只是补条、改稿或按同一格式再出一版
- 评审 / 检查已有用例 → 不勾选，按第二节「评审已有用例」

「直接产出 / 不要再问 / 按默认」但没说出具体格式 → 仍要勾选，禁止擅自按 XMind 开写。

**如何勾选**：环境有结构化选项工具（如 AskQuestion）时，发起**单选**（不可多选），标题用「请选择用例交付格式」。没有该工具则在回复里列出下面三项并停步等待。

选项固定为下面三项（第一项可标「常用」）：

1. XMind 版
2. Excel/CSV 完整可执行（含前置、步骤、预期）
3. 只要测试要点（不写用例）

勾选之后，按第二节路由读对应文件并生成。

---

## 二、勾选后的产物路由

| 已定格式 | 必读规则 |
|----------|---------|
| XMind 版 | `references/functional-testcase-design.md` + `references/testcase-xmind-guideline.md` |
| Excel/CSV | `references/functional-testcase-design.md` + `references/testcase-excel-guideline.md` |
| 测试要点 | `references/testpoint-analysis-guideline.md`；飞书来源再读 functional 第一节 |

**评审已有用例**（不走第一节勾选）：先跑 `scripts/validate_testcase.py` 做结构校验，再按 `references/functional-testcase-design.md` 的 1.2、2.1、2.2、2.3、第三节与对应格式指南逐条人工核对，输出问题清单而非直接改稿。

---

## 三、执行约定

- 用户指定了输出目录时写到该目录，不必再镜像一份到 `testcases/`。
- 用户要 `.xmind` 时交 Markdown，说明用 XMind 按标题导入。要表格时直接交 CSV。不要为了转格式去装新依赖或编写转换器。
- 产物写完后，环境有 Python 时运行 `python scripts/validate_testcase.py <产物文件>`。有 FAIL 项先修好再交付。CSV 不带 BOM 时，Excel 打开会乱码，用 `python scripts/validate_testcase.py --fix-bom <csv>` 补齐。
