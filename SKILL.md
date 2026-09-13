---
name: testcase-design
description: "设计或编写软件功能测试用例时使用本 skill。适用于写测试用例、生成用例、设计用例、用例清单、XMind/Excel/CSV 用例、完整可执行用例（前置+步骤+预期）、测试要点/测试点、把需求或 PRD（含飞书 Wiki/云文档）转成用例、以及评审刚设计的用例结构。三种产物：未指定格式时默认 XMind 仅标题级清单；Excel/CSV 或用户要可执行时用完整版；只要测试要点则输出后停步确认、不自动写用例。即使用户只说「写用例」「出个用例」「按这个需求测一下」且未提 XMind/Excel，也要使用。不要用于执行已有用例、写自动化脚本、探索性测试，也不要用于生成-评审-修复闭环（本 skill 只做单次设计/排版）。"
---

# 软件功能测试用例设计

本 skill 指导从产品需求设计高质量功能测试用例，覆盖「需求拆解 → 用例设计 → 交付排版」全流程。详细规则按需读取 `references/` 下对应文件，**不要一次性全部读入**，按下方路由只读当前任务需要的文件。

---

## 一、第一步：判定产物形态（与交付格式联动）

| 用户要什么 / 交付格式 | 形态 | 必读规则 | 产物粒度 |
|----------------------|------|---------|---------|
| **XMind**（含未明确格式时的默认）且未要求完整可执行 | **仅标题级（XMind 默认）** | `references/functional-testcase-design.md`（方法/维度）+ `references/testcase-xmind-guideline.md` | 到 `#####` |
| **Excel/CSV** | **完整版（Excel 默认）** | `references/functional-testcase-design.md` + `references/testcase-excel-guideline.md` | 到 `######` |
| 明确要「完整版 / 可执行 / 含前置·步骤·预期」 | 完整版 | `references/functional-testcase-design.md` + 对应格式规则 | 到 `######` |
| 明确要「精简 / 只要用例标题 / 用例清单…」 | 仅标题级 | 固定 XMind + `references/testcase-xmind-guideline.md` | 到 `#####` |
| 明确要「测试要点 / 测试点」 | 测试要点 | `references/testpoint-analysis-guideline.md` | 到 `-` |

**判定信号**：
- 未指定格式 → 默认 **XMind** → 默认 **仅标题级**（读 xmind 指南，勿展开前置/步骤/预期）。
- 选 Excel → **完整版**。
- 「完整版 / 可执行用例 / 含前置·步骤·预期」→ 完整版。
- 「精简 / 只要用例标题 / 用例清单 / 不要前置·步骤·预期」→ 仅标题级 XMind。
- 「测试要点 / 测试点」→ 测试要点（输出后停步等确认，**不**自动接着写用例）。
- **@ 显式引用**本 skill 内某个 reference 文件 → 以被引用文件为准。
- 用户已说「直接产出 / 不要再问 / 按默认」或已指定格式 → **立即开写**，禁止再问一轮格式。
- 拿不准 → **XMind + 仅标题级**，不必反复追问。

未指定格式时最常见失败：把用例写成带 `前置条件` / `###### 测试步骤` / `###### 预期结果` 的完整 Markdown。那是 Excel 或用户明确要完整版时才允许的形态。


---

## 二、第二步：选交付格式

- 仅当用户既没指定格式、也没说「直接写 / 按默认」时，问**一次**选 **XMind** 还是 **Excel/CSV**。已指定或要求直接产出 → 不再问，按默认或已指定格式写。
  - 未明确 → 默认 **XMind**，仅标题级；遵 `references/testcase-xmind-guideline.md`
  - Excel → 完整版；遵 `references/testcase-excel-guideline.md`（CSV 11 列）
- **测试要点**：固定 XMind 兼容 Markdown（`testcases/{需求名}-测试要点.md`）。
- **不做闭环**：本 skill 只做单次设计 / 排版 / 测试要点。不要在这里自造多 Agent 评审修复循环。

---

## 三、设计方法与覆盖维度（所有形态共用）

→ `references/testcase-design-reference.md`

核心约束（需求拆解、范围声明、数量基准、好用例五标准、自检与禁止）见 `references/functional-testcase-design.md`。XMind 标题级的结构差异只在 `testcase-xmind-guideline.md`。

---

## 四、需求来源获取（飞书场景）

当需求来自飞书 Wiki / 云文档时，须取全**正文/图片/画板/评论**四类信息，详见参考手册第一章。环境中有飞书文档类 skill 或 MCP 时优先使用；拉不到或鉴权失败时，把缺口写进范围声明，不得把鉴权失败说成「文档无评论/无画板」。

---

## 五、执行约定

- **禁止拿到需求直接写用例**：先完成需求拆解；需求不完整时提示补全。
- **范围声明**：首个业务 `##` 前输出一次 `## 范围声明`。形态扫描只列适用项，需求明确排除的写一两项即可，不要把无关形态逐行列满 N/A。
- **分批**：超 50 条按功能点分批自检。
- **输出前**按对应规则自检清单核对再交付。
- **覆盖**：显式规则与 `【隐含规则】` 均有对应用例，或已在范围声明中标注缺口。
- **生成文件**：用户指定了输出目录时写到该目录（不必再镜像一份到 `testcases/`）。用户要求 `.xmind` / `.csv` 且仓库里已有转换脚本时，环境允许则运行；确认无 traceback、输出存在且非空，并抽查根节点 / 列结构与源 Markdown 一致。没有脚本或无法跑时说明原因，完成结构与覆盖自检即可，不要为了转格式去装新依赖或编写转换器。
- **改转换脚本**：`python -m py_compile`，并用仓库内已有样例跑通主路径；新增第三方依赖须说明安装方式。

---

## 六、文件索引

| 文件 | 作用 | 何时读 |
|------|------|--------|
| `references/functional-testcase-design.md` | 核心规则（方法/维度/数量/完整结构） | 写任何用例时（方法层）；写完整版时读第五章结构 |
| `references/testcase-xmind-guideline.md` | XMind 格式 + **默认仅标题级** | 交付 XMind 时（默认） |
| `references/testcase-excel-guideline.md` | Excel（CSV 11 列） | 交付 Excel 时 |
| `references/testpoint-analysis-guideline.md` | 测试要点 | 做测试要点时 |
| `references/testcase-design-reference.md` | 方法论/维度详解 | 需要细则时 |
