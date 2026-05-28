---
name: skill-aware-evolve
description: "Use when EPI run evidence, feedback, Plugin Eval reports, or benchmark findings suggest changing controlled assets such as profiles, filters, ranking weights, critic checklists, reader templates, or routing rules."
---

# Skill-Aware Evolve

Evolution is staged and reversible. It must not directly edit plugin code.

Create a proposal:

```powershell
python scripts\orchestrator.py propose-evolution --reflection-type OPTIMIZATION --target-asset templates\ranking.example.yaml --rationale "Boost reproducibility after user feedback" --proposed-change-json "{\"weights\":{\"reproducibility_signal\":0.12}}" --evidence "_runs\feedback.jsonl#1"
```

Activate only after human approval:

```powershell
python scripts\orchestrator.py activate-evolution --proposal-id <proposal-id> --approved
```

Proposals live under `_evolution/proposals`; active records live under `_evolution/active`.
