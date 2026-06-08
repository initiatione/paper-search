from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_manifests_expose_paperflow_bundle_with_epi_and_prw_machine_names():
    for rel in [".agents/plugins/marketplace.json", "marketplace.json"]:
        payload = _load(ROOT / rel)
        plugin_names = [plugin["name"] for plugin in payload["plugins"]]

        assert payload["name"] == "paper-search"
        assert payload["interface"]["displayName"] == "PaperFlow"
        assert plugin_names == ["epi", "prw"]
        assert "mineru-paper-parser" not in plugin_names


def test_stage1_naming_preserves_machine_facing_plugin_names_and_paths():
    root_marketplace = _load(ROOT / "marketplace.json")
    agent_marketplace = _load(ROOT / ".agents" / "plugins" / "marketplace.json")

    for payload in [root_marketplace, agent_marketplace]:
        assert payload["name"] == "paper-search"
        assert payload["interface"]["displayName"] == "PaperFlow"
        entries = {plugin["name"]: plugin for plugin in payload["plugins"]}
        assert set(entries) == {"epi", "prw"}
        assert entries["epi"]["source"]["path"] == "./plugins/epi"
        assert entries["prw"]["source"]["path"] == "./plugins/PRW"
        assert "paper-source" not in entries
        assert "paper-wiki" not in entries
        assert "ps" not in entries
        assert "pw" not in entries


def test_readme_frames_mineru_as_internal_helper():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "not as a separate marketplace plugin" in text
