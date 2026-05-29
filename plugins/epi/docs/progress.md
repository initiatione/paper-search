# EPI 插件进度说明

更新时间：2026-05-30。本文档记录当前源码树的开发状态、已完成能力、已知风险和下一步计划。它是面向继续开发和发布验收的进度页，不替代 `docs/epi-linkage.md` 的链路契约，也不替代 `docs/structure.md` 的结构说明。

## 当前定位

EPI 当前聚焦“高质量论文收集和整理 -> Obsidian/LLM Wiki 知识沉淀 -> 轻阅读负担报告”。它不是自动完成选题、实验、写作、投稿的科研工作台。复现思路可以出现，但只作为阅读报告中的 compact caveat 和验证线索，不占主要篇幅。

## 已完成能力

- Marketplace 包装：`plugin.json` 已声明 EPI 展示信息、GitHub marketplace 链接、技能目录和默认提示。
- 安装诊断：`doctor` 支持只读健康检查，区分插件结构错误和外部依赖 warning，并能给 `paper-search` 与 MinerU 配置链接。
- 配置引导：`config-status`、`init-config`、`propose-config-update`、`apply-config-update` 已形成配置生命周期；当前新增 `config-setup` skill，把首次配置和修改配置改成聊天式逐步引导。
- 论文发现：`dry-run` 支持候选标准化、过滤、ranking、报告、run index 和 research queue，且只写 `_runs`。
- 推进采集：`advance-ranked`、`advance-paper`、`advance-batch`、`ingest-one` 支持从候选论文进入 raw artifact、MinerU 解析、reader、critic 和 staging。
- Reader v2：已拆出三角色阅读输出、evidence map、证据地址校验和轻阅读报告所需摘要。
- Critic 质量门：`paper-quality-critic` 已从文件存在检查升级为工程论文可靠性检查，覆盖身份、claim support、benchmark integrity、复现信息 warning、scope overclaim 和 parse-vs-paper failure。
- Role critic quorum：Nature/Sci editor、peer reviewer、senior domain researcher 的角色审查已经进入 critic quorum 和后续 decision。
- Staging 和报告：通过 critic 后生成 suggested routes、`wiki-ingest-brief.json`、`promotion-plan.json` 和 `reports/<slug>-reading-report.md`。
- Agent-mediated wiki ingest：默认不由固定脚本写最终 wiki，而是生成 `wiki-ingest-handoff`，要求 agent 读取目标 vault contract 后再写入。
- Paper gate：`paper-gate` 提供 GitHub checks 风格只读质量门；`research-queue --actions` 以当前 gate 为准推荐下一步。
- Legacy promotion：`promote-to-wiki` 和 `rollback-promotion` 只保留旧 compiled-draft 路径，带路径安全限制和人工确认。
- Self-evolution：`propose-evolution`、`activate-evolution`、`evolution-query` 已采用 proposal-based、human approval、validation gate 和 metric comparison。
- 查询与维护：`runs-query`、`research-queue`、`wiki-query` 支持状态查询；redo/recritic 支持阶段性修复但不绕过 critic gate。

## 当前未提交工作

当前源码树本轮新增修复集中在完整链路实测暴露的问题：

- `plugins/epi/scripts/build/epi/paper_quality.py`
- `plugins/epi/scripts/build/epi/orchestrator.py`
- `plugins/epi/docs/epi-linkage.md`
- `plugins/epi/docs/progress.md`
- `plugins/epi/.codex-plugin/plugin.json`
- `tests/epi/test_paper_quality_critic_protocol.py`
- `tests/epi/test_redo_recritic.py`

这些改动的目标是：用仓库源插件 `D:\paper-search\plugins\epi` 跑通发现、下载、MinerU 解析、reader、critic、staging、paper-gate、wiki-ingest-handoff 的原链路。修复点包括：综述论文正文里的 `improve/better` 词汇不能在 reader 未写出性能断言时误触发 `benchmark_integrity` 阻断；`recritic`/`redo-read-recritic` 成功后必须同步论文自身 `run-state.json`，避免 dashboard 和 research queue 继续显示旧的 `critic_failed`。

## 最近验证

本轮已验证：

```powershell
python -m pytest tests\epi\test_paper_quality_critic_protocol.py -q --basetemp=.pytest_tmp_green_paper_quality
python -m pytest tests\epi\test_redo_recritic.py::test_recritic_cli_writes_routed_report_with_changed_artifacts tests\epi\test_paper_quality_critic_protocol.py -q --basetemp=.pytest_tmp_green_recritic_and_quality
python -m pytest tests\epi -q --basetemp=.pytest_tmp_full_chain_fix
python -m pytest tests\epi -q --basetemp=.pytest_tmp_release_full_chain_fix2
python -m coverage run -m pytest tests\epi -q --basetemp=.pytest_tmp_release_cov_full_chain_fix
python -m coverage xml -o plugins\epi\coverage\coverage.xml
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\epi
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\mineru-paper-parser
node C:\Users\liuchf\.codex\plugins\cache\openai-curated\plugin-eval\719ed655\scripts\plugin-eval.js analyze D:\paper-search\plugins\epi --format markdown
```

结果：目标回归测试通过；发布前全量 `tests\epi` 为 `202 passed in 23.51s`，coverage run 为 `202 passed in 25.00s`，`plugins\epi\coverage\coverage.xml` 已刷新。EPI 与 MinerU 两个 plugin validation 均 passed。Plugin Eval 结果为 `87/100`、`0 fail, 3 warn`、coverage `93.76%`；三个 warning 为已知 token budget 和 Windows 路径下 `py-tests-missing` 识别限制。

真实链路实测结果：

- 发现 run：`D:\paper-research-wiki\_runs\20260529T191647886910Z`，MCP 优先调用，MCP 返回 0 篇后记录 fallback，CLI fallback 找到 `A Survey on Robotics with Foundation Models: toward Embodied AI`。
- 论文 raw root：`D:\paper-research-wiki\_raw\papers\a-survey-on-robotics-with-foundation-models-toward-embodied-ai`。
- 修复前状态：`critic_failed`，阻断项为 `benchmark_integrity`。
- 修复后 `recritic`：`critic-quorum.json` 六个 reviewer 全部 pass，`paper-quality-critic` 记录 `benchmark_integrity: no explicit outperform/SOTA claim detected`。
- `advance-paper` 后状态：`staged`，`next_action=run-wiki-ingest-agent`。
- `paper-gate --json`：`status=waiting_for_human_gate`，`failure_checks=[]`，仅 `human-approval` action required。
- `wiki-ingest-handoff --json`：`ready_for_agent=true`，handoff artifacts 位于 `_staging\papers\<slug>`。

## 发布前必须重跑

```powershell
python -m pytest tests\epi -q --basetemp .pytest_tmp_epi_current
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\epi
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\mineru-paper-parser
python -m coverage run -m pytest tests\epi
python -m coverage xml -o plugins\epi\coverage\coverage.xml
node C:\Users\liuchf\.codex\plugins\cache\openai-curated\plugin-eval\719ed655\scripts\plugin-eval.js analyze D:\paper-search\plugins\epi --format markdown
```

验收标准：

- 源码测试通过。
- 两个插件 validation 通过。
- Plugin Eval 无 fail，分数不低于 `70/100`。
- coverage artifact 可被 Plugin Eval 识别。
- 若仍有 Windows `py-tests-missing` warning，需记录为评估器路径识别限制，而不是删除源码测试。

## 下一步计划

1. 发布本轮修复 commit，并从 GitHub/marketplace 重新安装 EPI，确认安装 cache 版本变为 `0.1.0+codex.20260530034504`。
2. 升级安装副本后，从新 Codex thread 用 `@epi` 运行 `doctor --json`、`config-status --json`、dry-run fixture smoke 和 `research-queue` 验证安装体验。
3. 对 `D:\paper-research-wiki` 补齐目标 vault contract 文件（例如 `AGENTS.md` 和 `_meta/*.md`），这样 wiki-ingest agent 能按本 vault 的最终规则落页，而不是只依赖 EPI suggested routes。
4. 记录 human approval 后，交给 wiki-ingest agent 消费 `_staging\papers\a-survey-on-robotics-with-foundation-models-toward-embodied-ai\wiki-ingest-brief.json` 和 reading report。

## 已知风险

- `docs/epi-linkage.md`、`docs/structure.md`、`docs/progress.md` 会增加 Plugin Eval 的 deferred token 估算，但这些文档是当前用户要求的维护材料，不应为了静态分数移出插件 docs。
- `paper-search` CLI、MinerU、Zotero 都是外部能力。缺失时应 warning 和引导，不应让只读诊断失败。
- `MINERU_TOKEN` 不得写入文档、日志、报告或配置预览，只能显示 set/missing。
- 当前安装 cache 不是开发源；源码提交并经 marketplace 升级后，安装副本才会变化。
- 最终 Obsidian/LLM Wiki 写入依赖目标 vault contract。EPI 只能提供 handoff 和 suggested routes，不能把固定脚本当成最终沉淀机制。
