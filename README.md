# Paper Search Codex Plugins

This repository publishes a Codex plugin marketplace for paper-search workflows.

## Add The Marketplace In Codex

In Codex, open **Plugin Marketplaces** and choose **Add marketplace**.

Use these values:

- Source: `https://github.com/initiatione/paper-search`
- Git ref: `main`
- Sparse path: leave empty

After the marketplace is added, select **Paper Search** from the marketplace dropdown and install `EPI`.

## Plugins

- `epi`: Engineering Paper Intelligence. Searches, ranks, preserves, parses, reviews, and promotes engineering papers into a dedicated paper research wiki.
- `mineru-paper-parser`: Local MinerU precise-batch paper parser used as a lower-level parsing capability.

## Local Development

The canonical marketplace manifest for Codex is:

```text
.agents/plugins/marketplace.json
```

The root `marketplace.json` mirrors the same entries for local inspection and compatibility with older local workflows.
