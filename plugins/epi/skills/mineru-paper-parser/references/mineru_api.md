# MinerU Precise Batch API Notes

Use the standard precise API for local batches:

- Request upload URLs: `POST https://mineru.net/api/v4/file-urls/batch`
- Upload each local file with `PUT` to its signed URL. Do not set `Content-Type` on the upload request.
- Poll batch results: `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}`
- Completed results expose `full_zip_url`; extract the `full.md` member and the `images/` members from the zip. The Markdown uses relative links such as `![](images/<hash>.jpg)`, so save `full.md` as `<paper>.md` beside that paper's own `images/` directory.

Important request defaults for engineering papers:

- `model_version`: `vlm` unless the user asks for faster/lower-cost `pipeline`
- `language`: `en` for English papers
- `enable_formula`: `true`
- `enable_table`: `true`
- `is_ocr`: `false` unless the input is scanned or image-heavy

Limits from the API docs:

- One upload URL request accepts at most 50 files.
- Each file must be at most 200 MB and 200 pages.
- `Authorization` must be `Bearer <token>`.
- Common token failures: `A0202` token error, `A0211` token expired.
