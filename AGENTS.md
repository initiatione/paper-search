# PaperFlow Agent Instructions

This is the repo-level thin shell for agents working in `D:\paper-search`.

Before changing any plugin code, skill, workflow, docs, tests, manifest, generated contract, release script, or marketplace-visible behavior, read `docs/plugin-development.md` and follow it.

For Paper Source work, also read `plugins/paper-source/AGENTS.md` and `plugins/paper-source/skills/routing.yaml`.

For Paper Wiki work, also read `plugins/paper-wiki/AGENTS.md` and `plugins/paper-wiki/skills/routing.yaml`.

Local contracts and tests override external references. External projects are references only unless `docs/plugin-development.md` says otherwise.

PS/PW are allowed natural-language aliases and trigger phrases. Historical legacy names are not user entrypoints, route triggers, or new artifact contracts.

Do not treat source checkout validation as installed runtime validation. Report whether marketplace refresh, reinstall, or installed-cache verification is still needed.
