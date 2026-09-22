---
name: testcase-design
description: "设计或编写软件功能测试用例时使用本 skill。适用于写测试用例、生成用例、设计用例、用例清单、XMind/Excel/CSV 用例、完整可执行用例（前置+步骤+预期）、测试要点/测试点、把需求或 PRD（含飞书 Wiki/云文档）转成用例、以及评审刚设计的用例结构。三种产物：XMind 精简版（按页面/功能点/字段分组，标题写条件+操作并下挂预期，无 TC/无维度节点/无前置步骤）、Excel/CSV 或 XMind 完整可执行、测试要点（输出后停步确认、不自动写用例）。未指定格式时必须先让用户勾选交付格式，确认后再生成，禁止未询问就默认开写。即使用户只说「写用例」「出个用例」「按这个需求测一下」且未提 XMind/Excel，也要使用。不要用于执行已有用例、写自动化脚本、探索性测试，也不要用于生成-评审-修复闭环（本 skill 只做单次设计/排版）。"
---

# 软件功能测试用例设计

从产品需求设计功能测试用例。按下方路由**只读当前任务需要的文件**，不要一次读完 `references/`。

质量、范围声明（有内容才写）、方法/维度/覆盖以 `references/functional-testcase-design.md` 为单一事实源。

---

## 一、先勾选格式（未勾选禁止生成）

生成用例或测试要点之前，必须让用户勾选交付格式。**勾选完成前：不写文件、不输出用例/要点正文、不读 xmind/excel/testpoint 细则**（读完本节即可停）。

**跳过勾选（仅下列情形）**：

- 本轮用户消息已明确指定其一：「XMind / 思维导图」「Excel / CSV / 表格」「完整版 / 可执行 / 含前置·步骤·预期」「精简版 / 只要标题 / 精简清单」「测试要点 / 测试点」。
- 同一次对话里已经勾选过，用户只是让补条、改稿或按同一格式再出一版。

「直接产出 / 不要再问 / 按默认」但**没说出具体格式** → 仍然要勾选，禁止擅自按 XMind 开写。

**如何勾选**：环境有结构化选项工具（如 AskQuestion）时，发起**单选**（不可多选），标题用「请选择用例交付格式」。没有该工具则在回复里列出同样四项并**停步等待**，不要在同一回合生成。

选项固定为下面四项（第一项可标「常用」）：

1. XMind 精简版（按页面/字段分组，标题即操作，下挂预期；无 TC、无前置/步骤）
2. Excel/CSV 完整可执行（含前置、步骤、预期）
3. XMind 完整可执行（含前置、步骤、预期）
4. 只要测试要点（不写用例）

用户勾选之后，再按第二节路由读对应文件并生成。

---

## 二、勾选后的产物路由

| 用户勾选 / 已明示 | 形态 | 必读规则 | 产物粒度 |
|------------------|------|---------|---------|
| XMind 精简版 | **精简版** | `references/functional-testcase-design.md` + `references/testcase-xmind-guideline.md` | 模块/功能点/字段分组 → 条件+操作标题 → `预期结果` + `-` |
| Excel/CSV | **完整版** | `references/functional-testcase-design.md` + `references/testcase-excel-guideline.md` | 11 列（含前置、步骤、预期） |
| XMind 完整可执行，或明示「完整版 / 可执行 / 含前置·步骤·预期」且选了 XMind | 完整版 | `references/functional-testcase-design.md` + `references/testcase-xmind-guideline.md`（完整形态） | 精简版层级 + 前置、步骤 |
| 精简 / 只要用例标题 / 用例清单 | 精简版 | 固定 XMind + `references/testcase-xmind-guideline.md` | 同上精简版（仍须有预期，不是纯标题清单） |
| 测试要点 / 测试点 | 测试要点 | `references/testpoint-analysis-guideline.md`（飞书取数见 functional 第二节） | 到 `-` |

勾选精简版时最常见失败：仍写 `#### 功能测试` / `TC1-001` / `（P0）`，或写出 `前置条件` / `测试步骤`，或漏写 `预期结果`（只剩标题），或把同一套精确匹配、空格、批量上限在每个字段和每个同类页签各写一遍。要点输出后停步，**不**自动写用例。**@ 显式引用**某 reference 时以该文件为准。

**评审已有用例**：用户让「评审 / 检查」已写好的用例时，先跑 `scripts/validate_testcase.py` 做结构校验，再按 `references/functional-testcase-design.md` 第六章「输出前核对」与对应格式指南逐条人工核对，输出问题清单而非直接改稿。

**不做闭环**：只做单次设计 / 排版 / 要点，不要自造多 Agent 评审修复循环。

---

## 三、飞书需求

须取全**正文 / 图片 / 画板 / 评论**，细则见 `references/functional-testcase-design.md` 第二节。环境中有飞书文档类 skill 或 MCP 时优先使用；拉不到或鉴权失败时把缺口写进范围声明，不得把鉴权失败说成「文档无评论/无画板」。

---

## 四、执行约定

- 禁止拿到需求直接写用例：先勾选格式，再按 functional 做需求拆解；不完整则提示补全。
- 范围声明（有内容才写）、覆盖：遵 `references/functional-testcase-design.md`。同一需求的用例写入**一份文件**，禁止因条数拆成多份。
- **生成文件**：用户指定了输出目录时写到该目录（不必再镜像一份到 `testcases/`）。用户要求 `.xmind` / `.csv` 且仓库里已有转换脚本时，环境允许则运行；确认无 traceback、输出存在且非空，并抽查根节点 / 列结构与源 Markdown 一致。没有脚本或无法跑时说明原因，完成结构与覆盖自检即可，不要为了转格式去装新依赖或编写转换器。
- **自检**：产物写完后，环境有 Python 时运行 `python scripts/validate_testcase.py <产物文件>` 做结构自检（XMind：层级不跳级 / 无维度节点 / 无 TC 与优先级 / 每条有预期明细；CSV 的 BOM / 11 列 / 优先级 / 实际结果列；要点的优先级标注与风险章节）。有 FAIL 项先修好再交付。注意：多数编辑器写出的 CSV **不带 BOM**，Excel 打开会乱码，用 `python scripts/validate_testcase.py --fix-bom <csv>` 补齐。
- **改转换脚本**：`python -m py_compile`，并用仓库内已有样例跑通主路径；新增第三方依赖须说明安装方式。

---

## 五、文件索引

| 文件 | 作用 | 何时读 |
|------|------|--------|
| `references/functional-testcase-design.md` | 核心规则（来源获取/方法/维度/覆盖） | 格式勾选之后写用例时；测试要点遇到飞书来源时读第二节 |
| `references/testcase-xmind-guideline.md` | XMind 日常脑图结构；精简版无 TC/维度节点/前置步骤、须有预期 | 用户勾选 XMind 后 |
| `references/testcase-excel-guideline.md` | Excel（CSV 11 列） | 用户勾选 Excel/CSV 后 |
| `references/testpoint-analysis-guideline.md` | 测试要点 | 用户勾选测试要点后 |
| `scripts/validate_testcase.py` | 产物结构自检；`--fix-bom` 给 CSV 补 BOM | 产物写完后、交付前 |
