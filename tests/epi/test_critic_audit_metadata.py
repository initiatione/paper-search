import json

import pytest

from epi.artifacts import file_sha256
from epi.run_critic import run_critics
from epi.stage_wiki import stage_paper


EXPECTED_TOOL_VERSIONS = {
    "critic_pipeline": "epi-local-static-v1",
}


def _write_critic_fixture(tmp_path, *, reader_text: str) -> tuple:
    paper_root = tmp_path / "_raw" / "papers" / "paper"
    critic_dir = paper_root / "critic"
    mineru_dir = paper_root / "mineru"
    reader_dir = paper_root / "reader"
    critic_dir.mkdir(parents=True)
    mineru_dir.mkdir(parents=True)
    reader_dir.mkdir(parents=True)
    (paper_root / "paper.pdf").write_bytes(b"%PDF-1.4\nfixture paper\n")
    (paper_root / "metadata.json").write_text(json.dumps({"slug": "paper", "title": "Fixture Paper"}), encoding="utf-8")
    (mineru_dir / "paper.md").write_text("# Paper\n\nParsed claim.\n", encoding="utf-8")
    (reader_dir / "reader.md").write_text(reader_text, encoding="utf-8")
    return paper_root, critic_dir


def test_run_critics_writes_audit_metadata_for_pass(tmp_path):
    paper_root, critic_dir = _write_critic_fixture(
        tmp_path,
        reader_text="# Reader\n\n- Claim 1: Parsed claim.\n  Evidence: source=mineru/paper.md; heading=Paper\n",
    )

    report = run_critics(paper_root)
    quorum = json.loads((critic_dir / "critic-quorum.json").read_text(encoding="utf-8"))

    assert report["outcome"] == "pass"
    assert report["started_at"]
    assert report["finished_at"]
    assert report["exit_status"] == 0
    assert report["tool_versions"] == EXPECTED_TOOL_VERSIONS
    assert report["input_artifact_hashes"] == {
        "paper.pdf": file_sha256(paper_root / "paper.pdf"),
        "metadata.json": file_sha256(paper_root / "metadata.json"),
        "mineru/paper.md": file_sha256(paper_root / "mineru" / "paper.md"),
        "reader/reader.md": file_sha256(paper_root / "reader" / "reader.md"),
    }
    assert report["output_artifact_hashes"]["critic-quorum.json"] == file_sha256(critic_dir / "critic-quorum.json")
    assert report["output_artifact_hashes"]["paper-quality-critic.md"] == file_sha256(
        critic_dir / "paper-quality-critic.md"
    )
    assert report["output_artifact_hashes"]["parse-quality-critic.md"] == file_sha256(
        critic_dir / "parse-quality-critic.md"
    )
    assert report["output_artifact_hashes"]["reader-quality-critic.md"] == file_sha256(
        critic_dir / "reader-quality-critic.md"
    )

    assert quorum["final_outcome"] == "pass"
    assert quorum["started_at"]
    assert quorum["finished_at"]
    assert quorum["exit_status"] == 0
    assert quorum["tool_versions"] == EXPECTED_TOOL_VERSIONS
    assert quorum["input_artifact_hashes"] == report["input_artifact_hashes"]
    assert quorum["output_artifact_hashes"]["paper-quality-critic.md"] == file_sha256(
        critic_dir / "paper-quality-critic.md"
    )
    assert quorum["output_artifact_hashes"]["parse-quality-critic.md"] == file_sha256(
        critic_dir / "parse-quality-critic.md"
    )
    assert quorum["output_artifact_hashes"]["reader-quality-critic.md"] == file_sha256(
        critic_dir / "reader-quality-critic.md"
    )


def test_run_critics_writes_audit_metadata_for_revise_reader(tmp_path):
    paper_root, critic_dir = _write_critic_fixture(
        tmp_path,
        reader_text="# Reader\n\n- Claim 1: Parsed claim without evidence marker.\n",
    )

    report = run_critics(paper_root)
    quorum = json.loads((critic_dir / "critic-quorum.json").read_text(encoding="utf-8"))

    assert report["outcome"] == "revise-reader"
    assert report["started_at"]
    assert report["finished_at"]
    # Non-pass is a completed review verdict, not a runtime crash.
    assert report["exit_status"] == 1
    assert report["next_action"] == "revise-reader"
    assert report["tool_versions"] == EXPECTED_TOOL_VERSIONS
    assert report["input_artifact_hashes"] == {
        "paper.pdf": file_sha256(paper_root / "paper.pdf"),
        "metadata.json": file_sha256(paper_root / "metadata.json"),
        "mineru/paper.md": file_sha256(paper_root / "mineru" / "paper.md"),
        "reader/reader.md": file_sha256(paper_root / "reader" / "reader.md"),
    }
    assert report["output_artifact_hashes"]["critic-quorum.json"] == file_sha256(critic_dir / "critic-quorum.json")
    assert report["output_artifact_hashes"]["paper-quality-critic.md"] == file_sha256(
        critic_dir / "paper-quality-critic.md"
    )
    assert report["output_artifact_hashes"]["parse-quality-critic.md"] == file_sha256(
        critic_dir / "parse-quality-critic.md"
    )
    assert report["output_artifact_hashes"]["reader-quality-critic.md"] == file_sha256(
        critic_dir / "reader-quality-critic.md"
    )

    assert quorum["final_outcome"] == "revise-reader"
    assert quorum["started_at"]
    assert quorum["finished_at"]
    # Quorum completed and produced a non-promotable decision.
    assert quorum["exit_status"] == 1
    assert quorum["tool_versions"] == EXPECTED_TOOL_VERSIONS
    assert quorum["input_artifact_hashes"] == report["input_artifact_hashes"]
    assert quorum["output_artifact_hashes"]["paper-quality-critic.md"] == file_sha256(
        critic_dir / "paper-quality-critic.md"
    )
    assert quorum["output_artifact_hashes"]["parse-quality-critic.md"] == file_sha256(
        critic_dir / "parse-quality-critic.md"
    )
    assert quorum["output_artifact_hashes"]["reader-quality-critic.md"] == file_sha256(
        critic_dir / "reader-quality-critic.md"
    )


def test_run_critics_nonpass_result_is_not_promotable(tmp_path):
    vault = tmp_path / "vault"
    paper_root, _critic_dir = _write_critic_fixture(
        vault,
        reader_text="# Reader\n\n- Claim 1: Parsed claim without evidence marker.\n",
    )

    report = run_critics(paper_root)

    assert report["outcome"] == "revise-reader"
    assert report["exit_status"] == 1
    assert report["next_action"] == "revise-reader"

    with pytest.raises(ValueError, match="critic outcome"):
        stage_paper(vault, "paper", paper_root)

    assert not (vault / "_staging" / "papers" / "paper").exists()
