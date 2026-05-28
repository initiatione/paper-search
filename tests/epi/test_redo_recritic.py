import json
import sys

from epi.artifacts import file_sha256
from epi.orchestrator import main, run_one_paper_ingest
from epi.redo import redo_acquire, redo_parse, redo_read, recritic


def _write_phase2_fixture(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\noriginal paper\n")
    mineru_md = tmp_path / "paper.md"
    mineru_md.write_text(
        "# Abstract\n\nThis paper presents embodied navigation control for mobile robots.\n\n"
        "# Method\n\nThe controller combines perception, planning, and feedback control.\n",
        encoding="utf-8",
    )
    mineru_tex = tmp_path / "paper.tex"
    mineru_tex.write_text("\\section{Abstract} Fixture paper.\n", encoding="utf-8")
    candidate = {
        "id": "doi:10.1000/nav",
        "slug": "embodied-navigation-control-for-mobile-robots",
        "title": "Embodied Navigation Control for Mobile Robots",
        "authors": ["B. Engineer"],
        "year": 2024,
        "venue": "IROS",
        "abstract": "Robotics navigation and control with code.",
        "doi": "10.1000/nav",
        "pdf_url": "file://fixture-paper.pdf",
        "citation_count": 9,
        "score": 0.82,
        "sources": ["fixture"],
    }
    return candidate, pdf, mineru_md, mineru_tex


def _ingest_fixture(tmp_path):
    candidate, pdf, mineru_md, mineru_tex = _write_phase2_fixture(tmp_path)
    result = run_one_paper_ingest(
        vault_path=tmp_path / "vault",
        candidate=candidate,
        pdf_path=pdf,
        mineru_markdown_path=mineru_md,
        mineru_tex_path=mineru_tex,
    )
    return tmp_path / "vault", candidate["slug"], result["paper_root"]


def _redo_events(paper_root):
    return [
        json.loads(line)
        for line in (paper_root / "redo-records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_orchestrator_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["epi.orchestrator", *args])
    return main()


def _single_run_dir(vault):
    run_dirs = [path for path in (vault / "_runs").iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    return run_dirs[0]


def _assert_repair_run_state_contract(
    run_dir,
    *,
    workflow_type,
    expected_state,
    slug,
    vault,
    required_input_hash_keys,
    required_output_hash_keys,
):
    run_state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))

    assert run_state["stage"] == workflow_type
    assert run_state["run_id"] == run_dir.name
    assert run_state["workflow_type"] == workflow_type
    assert run_state["state"] == expected_state
    assert run_state["status"] == "success"
    assert run_state["paper_slug"] == slug
    assert run_state["vault_path"] == str(vault.resolve())
    assert run_state["compiled_wiki_write"] is False
    assert run_state["started_at"]
    assert run_state["finished_at"]
    assert run_state["exit_status"] == 0
    assert "orchestrator" in run_state["tool_versions"]
    assert run_state["input_artifact_hashes"]
    assert run_state["output_artifact_hashes"]
    for key in required_input_hash_keys:
        assert key in run_state["input_artifact_hashes"]
        assert run_state["input_artifact_hashes"][key]
    for key in required_output_hash_keys:
        assert key in run_state["output_artifact_hashes"]
        assert run_state["output_artifact_hashes"][key]


def test_redo_acquire_replaces_pdf_and_records_event_without_compiled_write(tmp_path):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    replacement_pdf = tmp_path / "replacement.pdf"
    replacement_pdf.write_bytes(b"%PDF-1.4\nreplacement paper\n")

    record = redo_acquire(vault, slug, replacement_pdf, reason="better source")

    assert record["stage"] == "redo-acquire"
    assert record["status"] == "success"
    assert record["reason"] == "better source"
    assert (paper_root / "paper.pdf").read_bytes() == replacement_pdf.read_bytes()
    assert _redo_events(paper_root)[-1]["stage"] == "redo-acquire"
    assert not (vault / "references" / f"{slug}.md").exists()


def test_redo_parse_and_redo_read_refresh_outputs_and_record_events(tmp_path):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    revised_md = tmp_path / "revised.md"
    revised_md.write_text(
        "# Abstract\n\nRevised embodied control summary.\n\n# Results\n\nNew parse evidence.\n",
        encoding="utf-8",
    )

    parse_record = redo_parse(vault, slug, revised_md, reason="parse critic requested redo")
    read_record = redo_read(vault, slug, reason="reader stale after parse redo")

    assert parse_record["stage"] == "redo-parse"
    assert read_record["stage"] == "redo-read"
    assert "Revised embodied control summary" in (paper_root / "mineru" / "paper.md").read_text(encoding="utf-8")
    assert "Revised embodied control summary" in (paper_root / "reader" / "reader.md").read_text(encoding="utf-8")
    assert [event["stage"] for event in _redo_events(paper_root)[-2:]] == ["redo-parse", "redo-read"]
    assert not (vault / "references" / f"{slug}.md").exists()


def test_recritic_refreshes_critic_report_and_records_event(tmp_path):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    (paper_root / "reader" / "reader.md").write_text(
        "# Reader\n\n- Claim 1: repaired reader.\n  Evidence: source=mineru/paper.md; heading=Abstract\n",
        encoding="utf-8",
    )

    record = recritic(vault, slug, reason="reader revised")
    critic_report = json.loads((paper_root / "critic" / "critic-report.json").read_text(encoding="utf-8"))

    assert record["stage"] == "recritic"
    assert record["status"] == "success"
    assert record["critic_outcome"] == "pass"
    assert critic_report["outcome"] == "pass"
    assert _redo_events(paper_root)[-1]["stage"] == "recritic"
    assert not (vault / "references" / f"{slug}.md").exists()


def test_redo_acquire_cli_writes_routed_report_with_changed_artifacts(tmp_path, monkeypatch):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    replacement_pdf = tmp_path / "replacement.pdf"
    replacement_pdf.write_bytes(b"%PDF-1.4\nreplacement paper\n")
    expected_replacement_hash = file_sha256(replacement_pdf)

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "redo-acquire",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--pdf",
        str(replacement_pdf),
        "--reason",
        "better source",
    )

    assert exit_code == 0
    run_dir = _single_run_dir(vault)
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    index_payload = json.loads((vault / "_runs" / "index.json").read_text(encoding="utf-8"))
    dashboard_text = (vault / "_runs" / "dashboard.md").read_text(encoding="utf-8")

    assert report_json["workflow_type"] == "redo-acquire"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "reacquired", "next_action": "redo-parse"}
    ]
    assert report_json["changed_artifacts"] == ["paper.pdf"]
    assert report_json["next_actions"] == ["redo-parse the reacquired PDF"]
    assert report_json["wiki_pages_written"] == []
    assert "paper.pdf" in report_md
    _assert_repair_run_state_contract(
        run_dir,
        workflow_type="redo-acquire",
        expected_state="reacquired",
        slug=slug,
        vault=vault,
        required_input_hash_keys=["input_pdf"],
        required_output_hash_keys=["paper.pdf", "redo-records.jsonl"],
    )
    run_state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
    assert run_state["input_artifact_hashes"]["input_pdf"] == expected_replacement_hash
    assert _redo_events(paper_root)[-1]["stage"] == "redo-acquire"
    assert index_payload["runs"][0]["run_id"] == run_dir.name
    assert index_payload["runs"][0]["workflow_type"] == "redo-acquire"
    assert run_dir.name in dashboard_text


def test_redo_parse_cli_writes_routed_report_with_changed_artifacts(tmp_path, monkeypatch):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    revised_md = tmp_path / "revised.md"
    revised_md.write_text(
        "# Abstract\n\nRevised embodied control summary.\n\n# Results\n\nNew parse evidence.\n",
        encoding="utf-8",
    )
    expected_markdown_hash = file_sha256(revised_md)

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "redo-parse",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--mineru-md",
        str(revised_md),
        "--reason",
        "parse critic requested redo",
    )

    assert exit_code == 0
    run_dir = _single_run_dir(vault)
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")

    assert report_json["workflow_type"] == "redo-parse"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "reparsed", "next_action": "redo-read"}
    ]
    assert report_json["changed_artifacts"] == ["mineru/paper.md", "mineru/paper.tex"]
    assert report_json["next_actions"] == ["redo-read the reparsed paper"]
    assert report_json["wiki_pages_written"] == []
    assert "mineru/paper.tex" in report_md
    _assert_repair_run_state_contract(
        run_dir,
        workflow_type="redo-parse",
        expected_state="reparsed",
        slug=slug,
        vault=vault,
        required_input_hash_keys=["input_markdown"],
        required_output_hash_keys=["mineru/paper.md", "mineru/paper.tex", "redo-records.jsonl"],
    )
    run_state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
    assert run_state["input_artifact_hashes"]["input_markdown"] == expected_markdown_hash
    assert _redo_events(paper_root)[-1]["stage"] == "redo-parse"


def test_redo_read_cli_writes_routed_report_with_changed_artifacts(tmp_path, monkeypatch):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    revised_md = tmp_path / "revised.md"
    revised_md.write_text(
        "# Abstract\n\nRevised embodied control summary.\n\n# Results\n\nNew parse evidence.\n",
        encoding="utf-8",
    )
    redo_parse(vault, slug, revised_md, reason="prepare for reader refresh")

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "redo-read",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--reason",
        "reader stale after parse redo",
    )

    assert exit_code == 0
    run_dir = _single_run_dir(vault)
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")

    assert report_json["workflow_type"] == "redo-read"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "reader_regenerated", "next_action": "recritic"}
    ]
    assert report_json["changed_artifacts"] == [
        "reader/reader.md",
        "reader/figures.md",
        "reader/reproducibility.md",
        "reader/implementation-ideas.md",
    ]
    assert report_json["next_actions"] == ["recritic the regenerated reader outputs"]
    assert report_json["wiki_pages_written"] == []
    assert "reader/implementation-ideas.md" in report_md
    _assert_repair_run_state_contract(
        run_dir,
        workflow_type="redo-read",
        expected_state="reader_regenerated",
        slug=slug,
        vault=vault,
        required_input_hash_keys=["mineru/paper.md"],
        required_output_hash_keys=[
            "reader/reader.md",
            "reader/figures.md",
            "reader/reproducibility.md",
            "reader/implementation-ideas.md",
            "redo-records.jsonl",
        ],
    )
    assert _redo_events(paper_root)[-1]["stage"] == "redo-read"


def test_recritic_cli_writes_routed_report_with_changed_artifacts(tmp_path, monkeypatch):
    vault, slug, paper_root = _ingest_fixture(tmp_path)
    (paper_root / "reader" / "reader.md").write_text(
        "# Reader\n\n- Claim 1: repaired reader.\n  Evidence: source=mineru/paper.md; heading=Abstract\n",
        encoding="utf-8",
    )
    expected_reader_hash = file_sha256(paper_root / "reader" / "reader.md")

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "recritic",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--reason",
        "reader revised",
    )

    assert exit_code == 0
    run_dir = _single_run_dir(vault)
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")

    assert report_json["workflow_type"] == "recritic"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "critic_passed", "next_action": "stage"}
    ]
    assert report_json["changed_artifacts"] == ["critic/critic-report.json"]
    assert report_json["next_actions"] == ["stage the paper for promotion review"]
    assert report_json["wiki_pages_written"] == []
    assert "critic/critic-report.json" in report_md
    _assert_repair_run_state_contract(
        run_dir,
        workflow_type="recritic",
        expected_state="critic_passed",
        slug=slug,
        vault=vault,
        required_input_hash_keys=["reader/reader.md"],
        required_output_hash_keys=["critic/critic-report.json", "redo-records.jsonl"],
    )
    run_state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
    assert run_state["input_artifact_hashes"]["reader/reader.md"] == expected_reader_hash
    assert _redo_events(paper_root)[-1]["stage"] == "recritic"
