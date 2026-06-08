# Context

This file is a glossary for the paperflow bundle and its plugin naming. It intentionally avoids implementation details.

## Terms

### PaperFlow

The user-facing bundle/product name for the coordinated academic paper workflow. PaperFlow contains two cooperating plugins: Paper Source and Paper Wiki.

### Paper Source

The user-facing name for the plugin that prepares traceable paper source evidence for Paper Wiki. Its responsibilities include paper discovery, acquisition, parsing, source bundle preparation, approval handoff, and completion recording.

Legacy name: EPI. During the transition, the machine-facing plugin name may remain `epi` while user-facing copy uses Paper Source.

Alias: PS. PS is a conversational alias only, not a separate plugin name or explicit tool entrypoint.

### Paper Wiki

The user-facing name for the plugin that writes, queries, checks, repairs, and maintains the formal paper wiki graph from source evidence prepared by Paper Source or from an existing compatible vault.

Legacy name: PRW. During the transition, the machine-facing plugin name may remain `prw` while user-facing copy uses Paper Wiki.

Alias: PW. PW is a conversational alias only, not a separate plugin name or explicit tool entrypoint.

### Legacy Alias

A previous public or machine-facing name that remains recognized for compatibility during migration, but is no longer the preferred user-facing name.

### Display Name

The user-visible name shown in marketplace and product-facing copy. During the first naming transition, display names use PaperFlow, Paper Source, and Paper Wiki while existing machine-facing names may remain unchanged.

### Machine-Facing Name

A stable identifier used by manifests, plugin installation, artifacts, tests, or runtime compatibility. Machine-facing names may lag behind display names during a staged migration.

### Capability Gap

A missing cooperating plugin or missing upstream artifact that prevents a later workflow step but does not invalidate earlier completed work.
