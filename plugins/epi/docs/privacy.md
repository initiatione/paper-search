# Privacy

EPI is a local Codex plugin for engineering paper discovery and dry-run workflow preparation.

Phase 1 reads local templates and optional fixture files, probes the configured external paper-search MCP command, and writes run artifacts under the configured paper research wiki. It does not upload PDFs, call MinerU, write Zotero, or write compiled wiki pages.

Later phases may call configured external services such as paper-search MCP, MinerU, or Zotero only when the corresponding stage is enabled by the user.
