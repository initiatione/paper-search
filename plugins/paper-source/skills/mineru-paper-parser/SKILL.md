---
name: mineru-paper-parser
description: >
  Use when parsing papers with MinerU: "MinerU 解析", PDF 转 Markdown, parse-paper, TeX/images/manifest,
  figure/formula indexes, normalize-mineru-assets.
---

# MinerU Paper Parser

Parse local PDFs into reader-ready Paper Source artifacts: Markdown text, TeX/formulas, extracted images, and parse metadata.

## Contract

Final outputs live only under `_paper_source\\raw\\<slug>\mineru\`:

```text
_paper_source\\raw\\<slug>\mineru\
|-- <slug>.md
|-- paper.tex (optional native MinerU TeX)
|-- images\...
`-- mineru-manifest.json
_paper_source\\raw\\<slug>\
|-- figure-index.json
|-- formula-index.json
`-- asset-normalization-record.json
```

- `<slug>.md`: main reader surface. `paper.md` is accepted only as a legacy fallback from older vaults.
- `paper.tex`: optional native MinerU TeX when the parser returns a non-empty `.tex`; Paper Source does not generate a Markdown fallback by default.
- `images/`: extracted figure assets.
- `mineru-manifest.json`: `tex_source`, page/image counts, timing.
- `figure-index.json`: preserved figure/image mapping from original `Fig.` / `图` labels to normalized paths.
- `formula-index.json`: formula screenshot cleanup records plus Markdown/TeX formula locators.
- `asset-normalization-record.json`: dry-run or execute record for raw image renaming, Markdown rewrites, dropped formula screenshots, and review warnings.
- Successful parses keep only `mineru-command\stdout.txt` and `mineru-command\stderr.txt`; `mineru-command\paper` and `mineru-command\parsed` should not remain after success.

## Commands

Prefer Paper Source orchestrator:

```powershell
python scripts\orchestrator.py parse-paper --slug <slug> --vault <vault>
```

Use `--mineru-timeout <seconds>` for a one-off long or short run. If omitted, Paper Source reads `PAPER_SOURCE_MINERU_TIMEOUT`; invalid or non-positive values fall back to 7200 seconds. Legacy `EPI_MINERU_TIMEOUT` remains accepted for existing environments.

Repair existing raw bundles with a dry-run first:

```powershell
python scripts\orchestrator.py normalize-mineru-assets --slug <slug> --vault <vault> --json
python scripts\orchestrator.py normalize-mineru-assets --slug <slug> --vault <vault> --execute --json
```

`normalize-mineru-assets` may read `_paper_source/raw/<slug>` or legacy `_epi/raw/<slug>`. It only changes raw MinerU files: image names, Markdown image references, and the three index/record sidecars. It must not edit formal wiki pages.

Standalone batch path:

```powershell
python skills/mineru-paper-parser/scripts/mineru_batch_to_md.py --input-dir paper --output-dir parsed
```

## TeX And Failures

- Native TeX records `tex_source=mineru-native`.
- When MinerU returns only Markdown, Paper Source records `tex_source=paused-no-native-tex` and does not synthesize `paper.tex`; Markdown formulas must remain complete.
- New parse automatically normalizes image assets: figure-like images become stable `fig-###-*` names when a nearby `Fig.` / `Figure` / `图` label is found; ambiguous images stay reviewable as `unmapped-*`.
- Formula screenshots with Markdown/TeX LaTeX evidence are moved out of preserved figures and recorded in `formula-index.json`; Markdown and TeX formulas must remain complete.
- On failure, inspect `parse-record.json`, `mineru-command\stdout.txt`, then `mineru-command\stderr.txt`.
- `MinerU reported done but produced no Markdown output` means the upstream job finished but Paper Source could not locate usable Markdown for `mineru\<slug>.md`; keep work folders for diagnosis, then rerun `parse-paper` or repair with `redo-parse`.
- Token errors such as `A0202` or `A0211` usually mean authentication failed.

Read tokens from `MINERU_TOKEN` or `.env/mineru.env`. Never print or persist token values. MinerU API details live in `references/mineru_api.md`.
