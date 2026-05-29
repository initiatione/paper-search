# EPI Attribution

Discovery wraps an external `paper-search` command and records command, source, query, and raw-response provenance in each run. MinerU parsing is optional and uses the local `skills\mineru-paper-parser\scripts\mineru_batch_to_md.py` entrypoint.

EPI keeps raw artifacts under `_raw` and evidence drafts under `_staging`. Final Obsidian/LLM Wiki pages are written by the wiki ingest agent according to the target vault contract; EPI's `references`, `concepts`, `synthesis`, and `reports` draft routes are suggestions, not final-page authority.
