# Search Protocol

Treat `paper_search_mcp` as a search transport, not as the definition of quality. The user usually wants papers that are worth reading, not just papers that one source happened to return. Borrow the discipline of multi-source academic search: explicit query construction, source routing, deduplication, citation/venue verification, and a visible evidence trail.

Before running the first query:

1. Build a query plan using `query-planner.md` and the optional `scripts/query-planner.py` helper.
2. Split the topic into concept blocks: domain object, method family, control task, environment/disturbance, validation mode, and exclusions.
3. Build 5-8 query variants instead of one vague query. Include exact phrases, synonyms, acronym expansions, and task-specific terms from `domain-ontology.md`.
4. Default discovery is non-review: every query variant should carry `-review -survey` and the filter stage should still enforce the exclusion. Skip this only when the user explicitly asks for review or survey papers.
5. Route sources by intent: use `paper_search_mcp` first with `arxiv,semantic,openalex` for robotics/AI/control; use live academic/web search to verify recent journal papers, DOI pages, citation counts, JCR/CiteScore-style metrics, code/PDF availability, and gaps that MCP missed.
6. Apply `two-stage-retrieval.md`: first form a high-recall candidate pool, then deduplicate, verify, and precision-rank.
7. Apply `venue-prior.md` as a recall/ranking prior. For robotics/control, check whether flagship robotics, robot learning, AI/ML, and domain venues are missing. For AUV work, include marine engineering/ocean robotics venues.
8. Deduplicate across variants by DOI first, then normalized title.
9. Deduplicate against the downloaded wiki library under `_raw\papers`. A paper already present in `_raw\papers\<slug>\metadata.json` must be rejected with `already_in_library:<slug>` and should not be recommended again unless the user explicitly asks to repair or reprocess that existing paper.
10. For strong seed papers, use `citation-graph.md` to check journal versions, related papers, references, and recent cited-by papers.

If the first result set is generic, stale, or too review-heavy, run a sharper rerun rather than stopping early.
