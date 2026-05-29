---
name: paper-discovery
description: "Use when running EPI paper search/ranking dry-runs without acquisition, parsing, promotion, or Zotero."
---

# Engineering Paper Discovery

Use only for search/rank dry-runs. The full EPI chain is documented in `docs\epi-linkage.md` and stays focused on high-quality paper collection, LLM Wiki deposition, and low-burden reading reports. If setup is unclear, run `doctor` or `config-status`. If config is missing, stop discovery and use `config-setup`; config onboarding lives in `docs\config.md` 的 `## 聊天式初始化脚本`，不要自由发挥成技术字段问卷，不要一次性输出完整默认配置.

```powershell
python scripts\orchestrator.py init-config --vault D:\paper-research-wiki --answers-json <answers.json>
python scripts\orchestrator.py dry-run --query "robotics embodied intelligence control" --max-results 20 --vault D:\paper-research-wiki
```

Safety: dry-run writes only `_runs/<run-id>/`; it does not acquire PDFs, parse papers, promote wiki pages, or sync Zotero.
