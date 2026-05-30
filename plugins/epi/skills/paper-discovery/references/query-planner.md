# Query Planner

Use the query planner before the first search whenever the user asks for high-quality, latest, non-review, or domain-specific papers. It turns a vague topic into a small, inspectable search plan.

## Required Plan Fields

| Field | Meaning |
| --- | --- |
| `domain` | Best matching domain pack, such as `auv-control`, `embodied-ai`, `robot-learning`, or `general-robotics` |
| `concept_blocks` | Platform/domain object, method family, task, environment/disturbance, validation mode, and exclusions |
| `query_variants` | 5-8 query variants, with exact phrases and synonym expansion |
| `source_route` | T1/T2/T3 sources to search and what each source is expected to contribute |
| `recall_gap_checks` | Venue families, citation graph checks, and missing-source checks to run if first results look weak |
| `quality_signals` | Evidence terms that should raise ranking priority |

## Helper

The bundled helper is deterministic and network-free:

```powershell
python skills\paper-discovery\scripts\query-planner.py --topic "<topic>" --domain auto --non-review --max-queries 8
```

Use it when the user gives a compact request such as `最新 AUV RL control 论文，不要综述`. The helper output is a starting point; agent judgment still decides whether to add task-specific terms.

## Planning Rules

1. Prefer domain-specific synonyms over generic AI terms.
2. Generate both broad and narrow queries: broad queries catch recall, narrow queries catch precision.
3. Include evidence terms such as `field trial`, `sea trial`, `real robot`, `sim-to-real`, `safety`, `benchmark`, or `code` when the user asks for high quality.
4. For non-review requests, append `-review -survey` to every query and still enforce review exclusion in filtering.
5. If the plan produces fewer than 5 strong variants, broaden platform or method terms before broadening the whole topic.

## AUV Example

For `AUV reinforcement learning control, not review`, a good plan should include all of:

- `autonomous underwater vehicle` and `AUV`
- `reinforcement learning`, `deep reinforcement learning`, `offline reinforcement learning`, and `model-based reinforcement learning`
- `trajectory tracking`, `path following`, `stabilization`, and `station keeping`
- `ocean current`, `current disturbance`, `turbulence`, or `underwater disturbance`
- `sea trial`, `real AUV`, `sim-to-real`, `safety`, or `benchmark`

Do not rely on `AUV AI control` alone; it is too broad and often returns survey or generic navigation papers.
