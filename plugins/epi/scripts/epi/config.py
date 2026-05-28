from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PipelineConfig:
    plugin_root: Path
    vault_path: Path
    runs_dir: Path
    max_results: int
    profile: str
    domains: list[str]


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                data[current_key] = value.strip("'\"")
            else:
                data[current_key] = [] if current_key in {"domains"} else {}
            continue
        if current_key == "domains" and line.strip().startswith("- "):
            data.setdefault("domains", []).append(line.strip()[2:].strip("'\""))
        if current_key == "budget" and ":" in line:
            key, value = line.strip().split(":", 1)
            data.setdefault("budget", {})[key.strip()] = int(value.strip())
    return data


def load_config(plugin_root: Path, vault_path: Path, max_results: int | None) -> PipelineConfig:
    plugin_root = plugin_root.resolve()
    vault_path = vault_path.resolve()
    interests_path = plugin_root / "templates" / "interests.example.yaml"
    interests = _parse_simple_yaml(interests_path)
    budget = interests.get("budget", {})
    configured_max = int(budget.get("max_results", 20))
    return PipelineConfig(
        plugin_root=plugin_root,
        vault_path=vault_path,
        runs_dir=vault_path / "_runs",
        max_results=max_results or configured_max,
        profile=str(interests.get("profile", "robotics_ai_control")),
        domains=list(interests.get("domains", ["robotics", "ai", "embodied intelligence", "control"])),
    )
