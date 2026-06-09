# Context

This file is a glossary for the paperflow bundle and its plugin naming. It intentionally avoids implementation details.

## Terms

### PaperFlow

The user-facing bundle/product name for the coordinated academic paper workflow. PaperFlow contains two cooperating plugins: Paper Source and Paper Wiki.

### Paper Source

The user-facing name for the plugin that prepares traceable paper source evidence for Paper Wiki. Its responsibilities include paper discovery, acquisition, parsing, source bundle preparation, approval handoff, and completion recording.

Legacy alias: `epi`. It remains only for compatibility shims and existing artifacts; the current machine-facing plugin name is `paper-source`.

Alias: PS. PS is a conversational alias only, not a separate plugin name or explicit tool entrypoint.

### Paper Wiki

The user-facing name for the plugin that writes, queries, checks, repairs, and maintains the formal paper wiki graph from source evidence prepared by Paper Source or from an existing compatible vault.

Legacy alias: `prw`. It remains only for compatibility references and existing artifacts; the current machine-facing plugin name is `paper-wiki`.

Alias: PW. PW is a conversational alias only, not a separate plugin name or explicit tool entrypoint.

### Legacy Alias

A previous public or machine-facing name that remains recognized for compatibility during migration, but is no longer the preferred user-facing name.

### Display Name

The user-visible name shown in marketplace and product-facing copy. Current display names are PaperFlow, Paper Source, and Paper Wiki.

### Machine-Facing Name

A stable identifier used by manifests, plugin installation, artifacts, tests, or runtime compatibility. Current machine-facing names are `paperflow`, `paper-source`, and `paper-wiki`; legacy aliases remain compatibility-only.

### Capability Gap

A missing cooperating plugin or missing upstream artifact that prevents a later workflow step but does not invalidate earlier completed work.
