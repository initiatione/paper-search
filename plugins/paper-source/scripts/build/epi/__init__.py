"""Legacy compatibility package for the renamed paper_source runtime."""

from pathlib import Path

_paper_source_path = Path(__file__).resolve().parents[1] / "paper_source"
if _paper_source_path.is_dir():
    __path__.append(str(_paper_source_path))
