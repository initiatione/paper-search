# EPI Evaluation

This doc is the public contract for the plugin development quality loop.

## Runtime Checks

```powershell
python -m pytest tests\epi -q
python -m pytest plugins\epi -q
python -m coverage run -m pytest tests\epi
python -m coverage xml -o plugins\epi\coverage\coverage.xml
node <plugin-eval.js> analyze <plugin-root> --metric-pack plugins\epi\metric-packs\epi-quality-gates\manifest.json --format markdown
```

`tests\epi` is the source behavioral suite. `tests\epi\test_wrapper_entrypoints.py` covers marketplace-visible wrappers for `scripts\orchestrator.py`, `scripts\init_paper_wiki.py`, and the MinerU skill wrapper.

`scripts\release_check_epi.ps1` runs pytest and validators by default. If `PLUGIN_EVAL_SCRIPT` is set, it also runs Plugin Eval with the bundled `epi-quality-gates` metric pack; `EPI_METRIC_PACK_MANIFEST` can override the manifest path for local experiments.

## Development Quality Loop

The plugin-dev loop is:

1. Run Plugin Eval.
2. Run `epi-quality-gates`.
3. Capture a benchmark or comparison payload.
4. Compare before/after metrics.
5. Write an improvement brief.
6. Convert the brief into a `propose-evolution` input.

Use the local `evaluation-brief` command to generate the brief:

```powershell
python scripts\orchestrator.py evaluation-brief --target-asset templates\ranking.example.yaml --rationale "<text>" --proposed-change-json "<json>" --before-metrics-json "<json>" --after-metrics-json "<json>" --plugin-eval-json <path> --metric-pack-json <path> --benchmark-json <path> --out-dir .plugin-eval\improvement-briefs
```

The command writes both JSON and Markdown under `.plugin-eval\improvement-briefs\`. Those outputs are local development artifacts and stay out of commits.

Current Windows Plugin Eval builds absolute paths with backslashes, while its Python test-file heuristic matches only `/tests/` or `/test_*.py`, so `py-tests-missing` can appear even when `python -m pytest plugins\epi -q` passes. Treat that warning as an evaluator path-normalization limitation unless Plugin Eval starts reporting `py_test_file_count > 0`.

`deferred_cost_tokens-budget-high` is expected while `docs\epi-linkage.md` remains inside the plugin package as the required Chinese chain contract. Do not remove that document only to raise the static score. Valid budget cleanup is limited to deleting generated/redundant package files, trimming duplicated prose, and keeping `docs\workflow.md`, `docs\evaluation.md`, and `docs\config.md` as compact entrypoints.

Keep `.plugin-eval`, `.pytest_tmp*`, `.coverage`, and generated coverage artifacts out of commits. If the release coverage XML is intentionally refreshed, it must be force-added because `coverage/` is ignored.
