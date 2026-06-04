# Paper Research Wiki Workflow

The plugin exposes one user-facing assistant for direct EPI paper deposition, redo/deep extraction, wiki checks, wiki updates, and relink maintenance.

The ordinary path is: preflight EPI handoffs, identify ready papers, deposit them into staged or formal pages under the target vault contract, preserve provenance, write `final-source-review.json`, and return recording to EPI `record-wiki-ingest`.

Redo requests such as `重做`, `重新提取`, `更详细提取`, or batch redo re-read the original EPI source bundle, compare existing formal pages, and write direct updates or staged patches according to risk.

EPI prepares source bundles and handoff artifacts. Paper Research Wiki reads them and performs the formal wiki-side work without taking over EPI discovery, MinerU parsing, paper-gate, human approval, or record-only completion.
