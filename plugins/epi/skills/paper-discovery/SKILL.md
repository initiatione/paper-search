---
name: paper-discovery
description: "Use when running EPI paper search/ranking dry-runs, finding high-quality papers for a topic, excluding reviews/surveys on request, or starting the precise EPI steps 1-3 path: search, ranked selection, download, and MinerU parse without reader/critic/staging."
---

# Engineering Paper Discovery

Use for search/rank dry-runs and the narrow steps 1-3 path. The full EPI chain is documented in `docs\epi-linkage.md` and stays focused on high-quality paper collection, LLM Wiki deposition, and low-burden reading reports. If setup is unclear, run `doctor` or `config-status`. If config is missing, stop discovery and use `config-setup`; config onboarding lives in `docs\config.md` 的 `## 聊天式初始化脚本`，不要自由发挥成技术字段问卷，不要一次性输出完整默认配置.

```powershell
python scripts\orchestrator.py init-config --vault D:\paper-research-wiki --answers-json <answers.json>
python scripts\orchestrator.py dry-run --query "robotics embodied intelligence control" --max-results 20 --vault D:\paper-research-wiki
```

For "重新走 1-3", "下载论文并 MinerU 解析", or similar requests, avoid hand-writing candidate JSON. Run:

```powershell
python scripts\orchestrator.py doctor --plugin-root D:\paper-search\plugins\epi --vault D:\paper-research-wiki --json
python scripts\orchestrator.py dry-run --query "<topic>" --max-results 10 --sources arxiv,semantic,openalex --plugin-root D:\paper-search\plugins\epi --vault D:\paper-research-wiki
python scripts\orchestrator.py prepare-ranked --run-id <run-id> --max-papers 1 --vault D:\paper-research-wiki
```

`prepare-ranked` downloads selected ranked papers and parses them with MinerU, then stops after `_raw\papers\<slug>\mineru\...`. It must not generate reader, critic, staging, Zotero, or final wiki outputs. Verify evidence with `search-record.json`, `acquire-record.json`, `parse-record.json`, `paper.pdf`, `mineru\paper.md`, `mineru\paper.tex`, `mineru\images`, and `mineru\mineru-manifest.json`.

Safety: `dry-run` writes only `_runs/<run-id>/`. `prepare-ranked` writes raw paper artifacts only and stops after parse.

## Quality-first discovery output

When the user asks to "find papers", "找最新/高质量论文", "不要综述", or similar, do not stop at the raw dry-run report. Run the EPI discovery evidence first, then curate the chat answer for reading decisions.

Treat `paper_search_mcp` as a search transport, not as the definition of quality. The user usually wants papers that are worth reading, not just papers that one source happened to return. Borrow the discipline of multi-source academic search: explicit query construction, source routing, deduplication, citation/venue verification, and a visible evidence trail.

## Strong search protocol

Before running the first query, write a compact search plan for yourself:

1. Split the topic into concept blocks: domain object, method family, control task, environment/disturbance, validation mode, and exclusions. For example, AUV + reinforcement learning/deep RL/offline RL/adaptive control + trajectory tracking/path following/stabilization + ocean current/turbulent flow + sea trial/sim-to-real + `-review -survey`.
2. Build 3-5 query variants instead of one vague query. Include exact phrases, synonyms, acronym expansions, and task-specific terms. For non-review requests, every query variant should carry `-review -survey` and the filter stage should still enforce the exclusion.
3. Route sources by intent: use `paper_search_mcp` first with `arxiv,semantic,openalex` for robotics/AI/control; use live academic/web search to verify recent journal papers, DOI pages, citation counts, JCR/CiteScore-style metrics, code/PDF availability, and gaps that MCP missed. Do not let a single weak source define the final set.
4. Deduplicate across variants by DOI first, then normalized title. Prefer the best metadata record, but keep source evidence in the run notes.
5. Apply a quality gate before recommendation: a paper should usually have strong topic fit, a real method contribution, credible validation, DOI or stable arXiv ID, available PDF, and at least one quality signal such as reputable venue, citations, code/data, real AUV/field experiment, sim-to-real, safety guarantee, strong benchmark, or recent journal acceptance.
6. Separate quality tiers:
   - Tier A: journal/top robotics venue, DOI, PDF, high topic fit, strong validation such as sea trial, real AUV, sim-to-real, safety proof, or convincing benchmark.
   - Tier B: good journal/conference or arXiv with strong method fit and credible experiments, but missing one important signal such as code, citations, or field validation.
   - Tier C: relevant but weaker evidence, generic robotics/RL, low metadata confidence, old work, or preprint-only. Include only if it meaningfully broadens the map.
   - Reject: reviews/surveys when excluded, generic RL not tied to the domain/control task, no PDF, unclear bibliographic identity, or papers whose claims cannot be verified.
7. If the EPI `rank.json` misses obviously high-quality papers found by live verification, report that as a recall gap under `EPI 实测证据` and run a sharper query before finalizing when time allows.

1. Start with `doctor` or `config-status` only when setup status is unclear.
2. Run `dry-run` through the source plugin path. Prefer `paper_search_mcp`; report whether `search-record.json` says `source_mode=paper_search_mcp` or a fallback. For high-quality discovery, run multiple focused dry-runs when the first result set is generic, stale, or too review-heavy.
3. If the user asks for latest/current work, verify freshness with live academic/web search after the EPI run when EPI recall looks stale or generic.
4. If the user says "不要综述", "非综述", "not review", "research papers only", or similar, include `-review -survey` in the query and manually exclude titles/abstracts that are reviews, surveys, systematic reviews, or meta-analyses from the recommendation list.
5. Rank by topic fit first, then evidence quality: AUV/robot entity, RL/AI control method, venue/year, DOI/PDF, real experiment or credible simulation, code/data availability, citation count, journal impact factor/quartile when verified, and whether the result is journal/conference/arXiv.
6. For impact factor, JCR quartile, CiteScore, or similar quality metrics, verify with live search or a trusted metadata source before stating a number. If not verified in the current turn, write `影响因子/分区：未核实` rather than guessing.

In the chat, present the curated result in a scan-friendly format before technical logs. The section title can be `推荐优先看`, but the section should include every paper found and kept for this run, sorted by reading priority, not only the top few. Each item should have a numbered title line and a slightly richer Chinese note underneath. The note should be detailed enough to explain why the paper is worth reading, but short enough to remain a recommendation rather than a full abstract:

```markdown
**推荐优先看**

1. Paper Title
Venue Year，DOI `10.xxxx/...`。质量指标：引用数 `<n>`，影响因子/分区 `<verified IF/Q or 未核实>`，PDF/代码 `<available/missing/unknown>`。说明方法主线、任务场景和证据强度：例如 DRL + adaptive control + sim-to-real，用于 AUV 稳定/轨迹控制；如果有海试、真实 AUV、公开 PDF、代码、基准对比或强仿真证据，要点出来。最后用一句话说明优先级，例如“质量最高的一类”“适合作为工程落地参考”“偏前沿但需再验代码/会议版本”。

2. Paper Title
Venue Year，DOI `10.xxxx/...`。质量指标：引用数 `<n>`，影响因子/分区 `<verified IF/Q or 未核实>`，PDF/代码 `<available/missing/unknown>`。说明它解决的具体控制问题，如 path following、trajectory tracking、docking、obstacle avoidance、unknown currents、turbulent flows、fault/disturbance handling。再补一句和用户方向的关系：为什么它比泛机器人/RL论文更贴近本次主题。

**EPI 实测证据**
- run: `D:\paper-research-wiki\_runs\<run-id>`
- source_mode: `paper_search_mcp` or fallback
- accepted/rejected: `<n>/<n>`; mention review exclusions such as `excluded_terms:review,survey` when relevant
- query variants: `<short list>` and whether a sharper rerun was needed
- recall gaps: MCP misses or metadata mismatches found by live verification, if any
- MINERU_TOKEN: set/missing only if setup was checked
```

For each recommendation, aim for 2-3 compact Chinese sentences after the venue/DOI. Include these fields when known: citation count, impact factor/quartile or `未核实`, PDF/code availability, method family, control target, validation evidence, freshness/venue, and caveat. Do not include raw JSON, long abstracts, or secret values. Use links when verified.

If the kept list is long, still list all kept papers. Use shorter notes for lower-priority items rather than omitting them. Rejected review/survey papers should not appear in `推荐优先看` when the user asked to exclude them; summarize them under `EPI 实测证据` with rejection counts and representative `filter_reasons`.

After reporting, keep moving if the user's request implies continued work: run a sharper query when results are generic, run `prepare-ranked` when they ask for download/MinerU parse, or record the plugin gap when high-quality papers were found externally but EPI did not put them in `rank.json`.
