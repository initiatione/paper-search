import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_paper_source_runtime_config(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPER_SOURCE_RUNTIME_CONFIG", str(tmp_path / "missing-paper-source-runtime.json"))
    monkeypatch.delenv("EPI_RUNTIME_CONFIG", raising=False)
