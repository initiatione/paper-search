import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from epi.acquire_papers import acquire_paper_from_url
from epi.orchestrator import acquire_paper_from_candidate


def _candidate(url, slug="downloaded-paper"):
    return {
        "slug": slug,
        "title": "Downloaded Paper",
        "authors": ["A. Researcher"],
        "year": 2026,
        "venue": "ICRA",
        "doi": "10.1000/downloaded",
        "pdf_url": url,
        "score": 0.7,
        "sources": ["local-http"],
    }


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


class _LocalServer:
    def __init__(self, root):
        self.root = root
        self.server = None
        self.thread = None
        self.previous_cwd = None

    def __enter__(self):
        self.previous_cwd = os.getcwd()
        os.chdir(self.root)
        handler = partial(_QuietHandler, directory=str(self.root))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        os.chdir(self.previous_cwd)


def test_acquire_paper_from_url_downloads_pdf_and_records_metadata(tmp_path):
    server_root = tmp_path / "server"
    server_root.mkdir()
    source_pdf = server_root / "paper.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\nurl fixture\n")
    paper_root = tmp_path / "vault" / "_raw" / "papers" / "downloaded-paper"

    with _LocalServer(server_root) as base_url:
        record = acquire_paper_from_url(_candidate(f"{base_url}/paper.pdf"), paper_root)

    assert record["stage"] == "acquire"
    assert record["mode"] == "url"
    assert record["status"] == "success"
    assert record["exit_status"] == 0
    assert record["started_at"]
    assert record["finished_at"]
    assert record["http_status"] == 200
    assert record["pdf_url"].endswith("/paper.pdf")
    assert record["output_path"] == str(paper_root / "paper.pdf")
    assert record["size_bytes"] == len(b"%PDF-1.4\nurl fixture\n")
    assert record["input_artifact_hashes"]["candidate_metadata"]
    assert record["output_artifact_hashes"]["paper.pdf"]
    assert record["output_artifact_hashes"]["metadata.json"]
    assert (paper_root / "paper.pdf").read_bytes() == source_pdf.read_bytes()
    metadata = json.loads((paper_root / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["slug"] == "downloaded-paper"
    assert metadata["pdf_url"] == record["pdf_url"]
    assert json.loads((paper_root / "acquire-record.json").read_text(encoding="utf-8")) == record


def test_acquire_paper_from_url_records_http_failure_without_pdf(tmp_path):
    server_root = tmp_path / "server"
    server_root.mkdir()
    paper_root = tmp_path / "vault" / "_raw" / "papers" / "missing-paper"

    with _LocalServer(server_root) as base_url:
        record = acquire_paper_from_url(_candidate(f"{base_url}/missing.pdf", slug="missing-paper"), paper_root)

    assert record["status"] == "failed"
    assert record["mode"] == "url"
    assert record["exit_status"] == 1
    assert record["started_at"]
    assert record["finished_at"]
    assert record["http_status"] == 404
    assert "HTTP 404" in record["error"]
    assert record["input_artifact_hashes"]["candidate_metadata"]
    assert record["output_artifact_hashes"]["metadata.json"]
    assert not (paper_root / "paper.pdf").exists()
    assert json.loads((paper_root / "acquire-record.json").read_text(encoding="utf-8")) == record


def test_acquire_paper_from_candidate_uses_vault_slug_boundary(tmp_path):
    server_root = tmp_path / "server"
    server_root.mkdir()
    (server_root / "paper.pdf").write_bytes(b"%PDF-1.4\norchestrator fixture\n")
    vault = tmp_path / "vault"

    with _LocalServer(server_root) as base_url:
        record = acquire_paper_from_candidate(vault, _candidate(f"{base_url}/paper.pdf"))

    paper_root = vault / "_raw" / "papers" / "downloaded-paper"
    assert record["status"] == "success"
    assert record["output_path"] == str(paper_root / "paper.pdf")
    assert (paper_root / "paper.pdf").is_file()
