---
name: mineru-paper-parser
description: "Use when parsing local PDFs in EPI with MinerU into Markdown, TeX, images, and a manifest."
---

# Mineru Precision Batch

Parse local PDFs with MinerU and save Markdown, LaTeX, images, and manifest outputs.

```powershell
python skills/mineru-paper-parser/scripts/mineru_batch_to_md.py --input-dir paper --output-dir parsed
```

Read tokens from `MINERU_TOKEN` or `.env/mineru.env`; never print or persist tokens. For API details and limits, read `references/mineru_api.md`.
