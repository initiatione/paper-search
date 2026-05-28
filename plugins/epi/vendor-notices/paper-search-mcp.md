# paper-search-mcp Notice

Upstream project: `openags/paper-search-mcp`

Phase 1 uses this project as an external search dependency. The plugin does not vendor upstream source code by default.

Verified upstream boundary on 2026-05-27:

- PyPI package: `paper-search-mcp`
- Verified PyPI version: `0.1.3`
- PyPI `0.1.3` does not provide console-script executables.
- GitHub `main` declares `paper-search-mcp = paper_search_mcp.server:main` and `paper-search = paper_search_mcp.cli:main` for an unreleased `0.1.4` package line.
- MCP server entry from an installed package: `python -m paper_search_mcp.server`
- Live search CLI contract: `paper-search search "<query>" -n <max-results> -s <comma-separated-sources>`

Compatibility policy:

- Probe the configured `paper-search` CLI command before discovery.
- Record the discovered version or probe output in each run.
- Preserve upstream query, source names, source result counts, upstream errors, and raw JSON response path.
- Keep all upstream-specific response handling inside `scripts/epi/paper_search_adapter.py`.
- Add license text and a sync record before any future vendored copy is introduced.
