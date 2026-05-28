---
name: mineru-paper-parser
description: "Use when parsing local PDFs inside the EPI plugin into organized Markdown, LaTeX, and image folders with MinerU's precise batch API. Defaults to token-authenticated precise batch API, relative project paths, VLM model, English language, and one folder per paper."
---

# Mineru Precision Batch

## Overview

Parse local PDF batches through MinerU's token-authenticated precise batch API and save each result as Markdown. Use this for research-paper workflows where the lightweight Agent API is too limited or where formula/table quality matters.

## Defaults

- Run the script from the workspace/project root where `.env/`, `paper/`, and `parsed/` should live.
- Use relative paths from the project root whenever possible.
- Read the API token from `MINERU_TOKEN` or `.env/mineru.env`.
- Do not print or persist tokens.
- Use `model_version=vlm`, `language=en`, formula extraction on, table extraction on, OCR off.
- Save each paper into its own directory by default: `<output>/<paper>/<paper>.md` plus `<output>/<paper>/images/`. A `mineru_batch_<batch_id>.json` manifest is written at the output root.

## Quick Start

The bundled script is the stable entrypoint. By default, it writes organized paper folders under `parsed/`:

```powershell
python skills/mineru-paper-parser/scripts/mineru_batch_to_md.py --input-dir paper --output-dir parsed
```

For a sibling workspace, still use a path relative to the project root:

```powershell
python skills/mineru-paper-parser/scripts/mineru_batch_to_md.py --input-dir ..\human_robot\paper --output-dir parsed
```

If a batch has already completed and only the local outputs need to be rebuilt, reuse the batch id without re-uploading:

```powershell
python skills/mineru-paper-parser/scripts/mineru_batch_to_md.py --batch-id <batch_id> --input-dir ..\human_robot\paper --output-dir parsed
```

Use `--layout flat` only when the user explicitly wants the legacy layout where all Markdown files share one output directory and one shared `images/` directory.

If the token is not already in the process environment, create a private env file from the publishable root example:

```powershell
Copy-Item .env_example .env\mineru.env
notepad .env\mineru.env
```

`.env/` is the local-only token directory and must stay ignored by git. `.env_example` is the only publishable example file.

## Workflow

1. Confirm the input directory and output directory, both relative to the project root when practical.
2. Confirm `MINERU_TOKEN` is available from the environment or `.env/mineru.env`.
3. Run the bundled script.
4. Watch state transitions such as `waiting-file`, `pending`, `running`, `done`, or `failed`.
5. Verify that each paper directory contains one `.md` file, its own `images/` directory when Markdown references images, and the manifest records the batch id, states, document directories, and image counts.

## API Notes

Read `references/mineru_api.md` only when you need endpoint details, request defaults, limits, or error-code handling.

The precise batch API flow is:

- `POST /api/v4/file-urls/batch`
- `PUT` each file to the signed upload URL
- `GET /api/v4/extract-results/batch/{batch_id}`
- Download `full_zip_url` and extract `full.md`
- Also extract `images/` from the same zip into the same directory as that paper's Markdown, because MinerU Markdown uses relative links like `![](images/<hash>.jpg)`.

If a file is more than 200 MB, more than 200 pages, or one batch contains more than 50 files, split the task before submission.
