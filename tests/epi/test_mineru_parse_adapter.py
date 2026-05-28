import json
import sys

from epi.orchestrator import parse_paper_with_mineru
from epi.run_mineru_parse import run_mineru_command


def _seed_paper_root(tmp_path):
    paper_root = tmp_path / "vault" / "_raw" / "papers" / "paper"
    paper_root.mkdir(parents=True)
    (paper_root / "paper.pdf").write_bytes(b"%PDF-1.4\nfixture\n")
    return paper_root


def _write_success_command(tmp_path):
    script = tmp_path / "fake_mineru_success.py"
    script.write_text(
        """
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--project-root", required=True)
parser.add_argument("--input-dir", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--layout", default="document-dir")
args = parser.parse_args()

project_root = Path(args.project_root)
output_root = project_root / args.output_dir
document_dir = output_root / "paper"
images_dir = document_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)
(document_dir / "paper.md").write_text("# Parsed Paper\\n\\nEvidence from MinerU.\\n", encoding="utf-8")
(document_dir / "paper.tex").write_text("\\\\section{Parsed Paper}\\n", encoding="utf-8")
(images_dir / "figure-1.png").write_bytes(b"PNG")
manifest = {
    "batch_id": "fake-batch-001",
    "outputs": [
        {
            "file_name": "paper.pdf",
            "state": "done",
            "document_dir": "parsed/paper",
            "markdown_path": "parsed/paper/paper.md",
            "image_count": 1,
            "image_dir": "parsed/paper/images",
        }
    ],
}
(output_root / "mineru_batch_fake-batch-001.json").write_text(json.dumps(manifest), encoding="utf-8")
print("batch_id: fake-batch-001")
""".strip(),
        encoding="utf-8",
    )
    return script


def _write_failure_command(tmp_path):
    script = tmp_path / "fake_mineru_failure.py"
    script.write_text(
        """
import sys

print("simulated mineru failure", file=sys.stderr)
raise SystemExit(7)
""".strip(),
        encoding="utf-8",
    )
    return script


def test_mineru_command_imports_markdown_images_manifest_and_records_job(tmp_path):
    paper_root = _seed_paper_root(tmp_path)
    command = [sys.executable, str(_write_success_command(tmp_path))]

    record = run_mineru_command(paper_root, command=command)

    assert record["stage"] == "parse"
    assert record["mode"] == "mineru-command"
    assert record["status"] == "success"
    assert record["exit_code"] == 0
    assert record["exit_status"] == 0
    assert record["started_at"]
    assert record["finished_at"]
    assert record["batch_id"] == "fake-batch-001"
    assert record["input_artifact_hashes"]["paper.pdf"]
    assert record["output_artifact_hashes"]["paper.md"]
    assert record["output_artifact_hashes"]["paper.tex"]
    assert record["output_artifact_hashes"]["mineru-manifest.json"]
    assert record["markdown_path"] == str(paper_root / "mineru" / "paper.md")
    assert record["tex_path"] == str(paper_root / "mineru" / "paper.tex")
    assert record["image_count"] == 1
    assert (paper_root / "mineru" / "paper.md").read_text(encoding="utf-8").startswith("# Parsed Paper")
    assert (paper_root / "mineru" / "paper.tex").read_text(encoding="utf-8").startswith("\\section")
    assert (paper_root / "mineru" / "images" / "figure-1.png").read_bytes() == b"PNG"
    assert json.loads((paper_root / "mineru" / "mineru-manifest.json").read_text(encoding="utf-8"))["batch_id"] == (
        "fake-batch-001"
    )
    assert "batch_id: fake-batch-001" in (paper_root / "mineru-command" / "stdout.txt").read_text(encoding="utf-8")
    assert json.loads((paper_root / "parse-record.json").read_text(encoding="utf-8")) == record


def test_mineru_command_accepts_windows_command_string(tmp_path):
    paper_root = _seed_paper_root(tmp_path)
    command = f"{sys.executable} {_write_success_command(tmp_path)}"

    record = run_mineru_command(paper_root, command=command)

    assert record["status"] == "success"
    assert record["batch_id"] == "fake-batch-001"


def test_mineru_command_failure_records_error_without_fake_markdown(tmp_path):
    paper_root = _seed_paper_root(tmp_path)
    command = [sys.executable, str(_write_failure_command(tmp_path))]

    record = run_mineru_command(paper_root, command=command)

    assert record["stage"] == "parse"
    assert record["mode"] == "mineru-command"
    assert record["status"] == "failed"
    assert record["exit_code"] == 7
    assert record["exit_status"] == 1
    assert record["started_at"]
    assert record["finished_at"]
    assert record["input_artifact_hashes"]["paper.pdf"]
    assert "MinerU command failed" in record["error"]
    assert not (paper_root / "mineru" / "paper.md").exists()
    assert "simulated mineru failure" in (paper_root / "mineru-command" / "stderr.txt").read_text(encoding="utf-8")
    assert json.loads((paper_root / "parse-record.json").read_text(encoding="utf-8")) == record


def test_parse_paper_with_mineru_uses_vault_slug_boundary(tmp_path):
    vault = tmp_path / "vault"
    paper_root = vault / "_raw" / "papers" / "paper"
    paper_root.mkdir(parents=True)
    (paper_root / "paper.pdf").write_bytes(b"%PDF-1.4\nfixture\n")
    command = [sys.executable, str(_write_success_command(tmp_path))]

    record = parse_paper_with_mineru(vault, "paper", mineru_command=command)

    assert record["status"] == "success"
    assert record["batch_id"] == "fake-batch-001"
    assert (paper_root / "mineru" / "paper.md").is_file()
