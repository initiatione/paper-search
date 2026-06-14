# Plugin Development Rules

本文档是 `D:\paper-search` 的插件开发门禁。适用于 `plugins/paper-source`、`plugins/paper-wiki` 以及后续新增的 Codex marketplace 插件。每次修改插件源码、skill、workflow、文档、测试或 marketplace 可见行为时，都必须按本规范收尾。

## 参考来源与遵循顺序

开发时必须明确区分“参考什么”和“遵循什么”。外部项目只提供设计参考或语法权威；本仓库的 manifest、routing、contract docs、tests 和 release checks 才决定 PaperFlow 插件当前行为。

参考来源：

- `https://github.com/WoJiSama/skill-based-architecture`：参考 skill-based architecture 的薄入口、任务路由、rules/workflows/references 分层和 footprint/route-health 思路；不要把上游单 skill 模板原样套到 PaperFlow。
- `https://github.com/kepano/obsidian-skills`：Obsidian syntax authority；frontmatter/properties、wikilinks、Markdown links、embeds、callouts、tags、math、bases/canvas 等格式规则以它为准。
- `Ar9av/obsidian-wiki` 和本机个性化 wiki skills：只作为 Paper Wiki 的 wiki-ingest、wiki-update、cross-link、tag/lint 模式参考；Paper Wiki 已内化这些模式，正常运行不把它们当必需 runtime stack。
- `$plugin-creator` / `$skill-creator`：创建或调整插件/skill 时的本地流程参考；使用前读取当前 skill 指令，不凭记忆套旧流程。
- `plugins/<plugin>/skills/routing.yaml` 的 `external_references`：记录当前插件承认的外部参考 URL、角色和 freshness policy；这里记录 URL，不冻结 commit 或本机 cache 路径。

必须遵循的本地 source of truth：

- `.codex-plugin/plugin.json`：插件 manifest source of truth；目录名、machine-facing name、版本和 marketplace 展示必须与它一致。
- `skills/routing.yaml`：插件级任务路由 source of truth；route id、trigger、skill/workflow/reference、always_read、task_closure 和允许的 overlap 都以它为准。
- `AGENTS.md`、`SKILL.md`、`workflows/*.md`、`references/*.md`、`rules/*.md`：agent 实际执行边界；入口保持薄，细节下沉到 workflow/reference/rule。
- Paper Source 合同：`plugins/paper-source/docs/paper-source-linkage.md`、`docs/structure.md`、`docs/workflow.md`、`skills/paper-ingest/references/source-first-reading.md`。
- Paper Wiki 合同：`plugins/paper-wiki/docs/workflow.md`、`docs/structure.md`、`docs/paper-source-integration.md`、`rules/wiki-writing-standard*.md`、`skills/paper-research-wiki/references/*.md`。
- Repo tests、`scripts/release_check_paper_source.ps1`、`scripts/release_check_paper_wiki.ps1`、`scripts/paperflow_audit.py`：开发完成的验证门禁；不能用“文档看起来合理”替代这些检查。

优先级规则：

- 本地合同和测试优先于外部参考；外部参考只能解释设计来源，不能覆盖当前 Paper Source / Paper Wiki 边界。
- 目标 vault 的 `AGENTS.md` 和 `_meta/*` 优先于样例 vault 或 upstream wiki repo；样例只能参考，不能当 hard schema。
- Obsidian 语法问题遵循 `kepano/obsidian-skills`；Paper evidence、source-first、formal graph、record readiness 遵循 PaperFlow 本地合同。
- 结构问题遵循 skill-based architecture 的原则，但必须适配 PaperFlow 的“两插件 + 多 skill + 中央 routing manifest”形态，不拆成上游单 skill 模板。
- 若外部参考、本地文档、测试或当前目标 vault 行为冲突，先保留 source-first、可点击 Obsidian PDF 链接、formal graph 边界和 Paper Source/Paper Wiki 职责边界；不能确定时先停下说明冲突，不要静默改合同。

## 版本同步

任何插件改动都必须同步版本信息，不能只改源码或 skill 后保持旧版本。

插件创建、结构调整、manifest 或 marketplace 相关改动必须同时遵守 `$plugin-creator`：

- 新建插件、补齐插件目录、修改 manifest/marketplace 或准备运行态刷新前，先按 `$plugin-creator` 的 `SKILL.md` 检查当前流程。
- 保持 `.codex-plugin/plugin.json` 是插件 manifest source of truth，插件外层目录名必须和 `plugin.json` 的 `name` 一致。
- manifest 里不能留下 `[TODO: ...]` placeholder，不能加入 validator 不支持的字段；`apps`、`mcpServers` 等字段只有在对应伴随文件真实存在时才写入。
- 修改 manifest 后必须运行 plugin validator；修改 marketplace 或安装可见状态时，按 `$plugin-creator` 的 cachebuster/reinstall 流程处理，不手改 installed cache 冒充发布完成。
- marketplace entry 必须保留 `policy.installation`、`policy.authentication`、`category`，不要无故改动现有 marketplace 的 `interface.displayName` 或插件排序。

每个被改动的插件都要更新：

- `plugins/<plugin>/.codex-plugin/plugin.json` 的 `version`。
- 同一文件里 `interface.shortDescription` 的版本前缀，例如 `v0.1.4 | ...`。
- 如果改动影响 marketplace 展示、默认入口、能力描述或插件列表，也要同步根 `marketplace.json` 和 `.agents/plugins/marketplace.json` 中对应插件的展示信息。
- 如果多个插件在同一次任务中都发生行为变化，逐个插件分别 bump，不用共享同一个版本号，除非这是有意的联合发布。

版本规则：

- patch bump：skill 文案、workflow 边界、测试、文档、兼容性修复、生成物 contract 小改。
- minor bump：新增用户可见能力、新 skill、新命令、新 artifact schema、新插件间职责边界。
- major bump：破坏旧 artifact、旧命令、旧 vault contract 或安装兼容性。

禁止事项：

- 禁止把安装 cache 当作开发源。开发改动只写 `D:\paper-search\plugins\...`。
- 禁止只改源码后宣称插件已更新到用户运行态。安装缓存只有在 marketplace/reinstall/refresh 后才代表 live runtime。
- 禁止为了绕过版本同步而把行为改动伪装成“仅文档”。如果文档改变了 agent 应该怎么做，就属于插件行为变化。

## 文档同步

开发完成后必须同步文档信息。按影响面更新：

- 仓库级说明：`README.md`，用于安装、结构、开发规范入口和发布边界。
- Paper Source 主链路：`plugins/paper-source/docs/paper-source-linkage.md`。
- Paper Source 结构：`plugins/paper-source/docs/structure.md`。
- Paper Source 工作流短入口：`plugins/paper-source/docs/workflow.md`。
- Paper Source 进度和验证：`plugins/paper-source/docs/progress.md`。
- Paper Wiki 结构/工作流/集成：`plugins/paper-wiki/docs/structure.md`、`plugins/paper-wiki/docs/workflow.md`、`plugins/paper-wiki/docs/paper-source-integration.md`。
- 对应 skill 的 `SKILL.md`、`workflows/*.md`、`references/*.md`、`skills/routing.yaml`。

文档必须写清楚：

- 改动后的职责边界。
- 新旧 artifact 或 skill 名称的兼容关系。
- 用户该从哪个插件/skill 入口继续。
- 需要运行的验证命令和结果。
- 是否仍需安装缓存刷新或 marketplace 发布。

## 命名边界

Current machine names:

PaperFlow 是 bundle/product 的 display name；当前 marketplace machine-facing name 是 `paperflow`。`paper-search` 只保留为仓库 URL、外部 `paper-search-mcp` / `paper-search` CLI 名称和历史安装缓存线索。

Paper Source 是 `plugins/paper-source` 的 display name；当前插件 machine-facing name 是 `paper-source`。旧别名不再作为用户入口、路由触发条件或新 artifact 合同。

Paper Wiki 是 `plugins/paper-wiki` 的 display name；当前插件 machine-facing name 是 `paper-wiki`。旧别名不再作为用户入口、路由触发条件或新 artifact 合同。

PS/PW 是允许的自然语言别名和触发短语；旧别名禁用不包括 PS/PW。不要新增 `$PS`、`$PW`、`ps`、`pw` 插件或 skill 入口。

当前命名已经硬切目录名、manifest `name`、marketplace `name` 和用户级 runtime 默认路径。不要再新增旧别名 shim；凡是处理历史 artifact、Python 包名、旧 vault 根或外部 `paper-search` MCP/CLI 的位置，必须明确标成内部迁移/历史数据处理，不能暴露为用户入口。

## Skill-Based Architecture

插件 skill 结构遵守 skill-based architecture：

- 创建或修改任何 skill 前，必须先按 `$skill-creator` 的原则检查：`SKILL.md` 只保留必要触发与执行指导，重资源放到 `scripts/`、`references/`、`assets/`，不要新增无关 `README.md`、安装指南或过程叙事。
- 结构和写法参考 `D:\paper-search\.codex_tmp_refs\skill-based-architecture`：入口薄、任务路由清晰、rules/workflows/references 分层、Common Tasks 只指向需要读取的文件。

- `SKILL.md` 是薄入口，保留触发、边界、路由和少量 always-read 信息。
- 步骤性 runbook 放到 `workflows/`。
- 长期规则放到 `rules/` 或插件级 docs。
- 背景、schema、gotchas、上游映射放到 `references/`。
- `skills/routing.yaml` 是插件级任务路由 source of truth；新增、删除或重命名 skill/workflow 时必须同步 routing。
- `agents/openai.yaml` 必须与 `SKILL.md` 的实际入口能力一致。

入口长度目标：常用 `SKILL.md` 正文保持 90 行以内。超过时先下沉重复说明或 workflow 细节，不把入口扩成完整 runbook。

## 插件职责边界

当前两个插件的边界是：

- Paper Source (`paper-source`)：论文发现、排序、PDF 获取、MinerU、source bundle、reader/critic、staging、approval/gate/record、`wiki-setup` vault bootstrap。
- Paper Wiki (`paper-wiki`)：正式论文 wiki 页面写入、检查、更新、redo/deep extraction、relink、语言 gate、tracking/QMD 兼容和 post-task check。
- `paper-source-paper-deposition`：Paper Source 历史 handoff 清理入口，不是用户级正式写页主入口。
- Paper Wiki 不初始化、修复、reset 或静默创建 vault 结构；缺 `_paper_source/`、`_meta/`、`.obsidian`、`.git` 或正式页面根目录时，指回 Paper Source `wiki-setup`。旧别名、旧 vault 根和旧 handoff 不再作为 Paper Wiki 输入合同。

任何跨插件改动都必须同时检查 Paper Source 生成 handoff、Paper Source routing、Paper Wiki routing、Paper Wiki workflow 和相关测试，防止职责漂移。

## 测试与验证

每次插件改动至少运行：

```powershell
python -m pytest tests\paper_research_wiki\test_plugin_contract.py tests\paper_source\test_skill_bundle_contract.py tests\test_marketplace_manifest.py -q
python -m json.tool plugins\paper-source\.codex-plugin\plugin.json > $null
python -m json.tool plugins\paper-wiki\.codex-plugin\plugin.json > $null
git diff --check
```

按改动类型追加：

- Paper Source handoff/schema 生成物：`tests\paper_source\test_wiki_deposition_task.py`、`tests\paper_source\test_one_paper_ingest.py`、`tests\paper_source\test_wiki_ingest_handoff.py`、`tests\paper_source\test_wiki_ingest_record.py`。
- Paper Source config/doctor/runtime：`tests\paper_source\test_runtime_config.py`、`tests\paper_source\test_doctor_cli.py`、`tests\paper_source\test_config_onboarding_docs.py`。
- Paper Wiki 页面写入/语言/链接规则：`tests\paper_research_wiki\test_plugin_contract.py`。
- Marketplace 或 manifest 改动：根 marketplace contract tests、`plugin.json` JSON 解析检查、必要时安装缓存验证；如果当前机器配置了 `PLUGIN_VALIDATE_SCRIPT`，再分别运行 `python $env:PLUGIN_VALIDATE_SCRIPT plugins\paper-source` 和 `python $env:PLUGIN_VALIDATE_SCRIPT plugins\paper-wiki`，不要引用不存在的固定 validator 路径。

如果运行了安装缓存或真实 vault 验证，必须明确报告路径，例如当前安装缓存 `C:\Users\liuchf\.codex\.tmp\marketplaces\paperflow\plugins\paper-source` / `C:\Users\liuchf\.codex\.tmp\marketplaces\paperflow\plugins\paper-wiki`，或真实 vault `D:\paper-research-wiki`。历史缓存线索不是当前运行态证明。不要把 source checkout 结果和 installed runtime 结果混为一谈。

## 发布与安装缓存

源码验证通过不等于用户运行态已更新。发布/刷新步骤单独执行，除非用户明确要求。

发布或安装刷新前必须确认：

- 版本已 bump。
- 文档、routing、tests、validator 已同步。
- `git diff --check` 无 whitespace error。
- 没有 secrets、token、runtime env、用户 vault 内容进入插件包。
- 安装缓存验证时使用 installed cache 路径，不读取源码路径冒充 live plugin。

## 收尾报告

每次插件开发收尾必须报告：

- 改了哪些插件。
- 版本从多少到多少；如果用户明确要求不 bump，要说明这只是源码临时改动，不能算发布完成。
- 同步了哪些文档。
- 跑了哪些测试和 validator，结果是什么。
- 是否仍需 marketplace 发布、reinstall 或 installed-cache 验证。
