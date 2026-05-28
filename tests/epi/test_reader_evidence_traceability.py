import json

from epi.generate_reader import generate_reader_outputs


def test_generate_reader_outputs_emits_structured_evidence_addresses(tmp_path):
    paper_root = tmp_path / "paper"
    mineru_dir = paper_root / "mineru"
    images_dir = mineru_dir / "images"
    images_dir.mkdir(parents=True)

    (paper_root / "metadata.json").write_text(
        json.dumps(
            {
                "title": "Embodied Navigation Control for Mobile Robots",
                "venue": "IROS",
                "year": 2024,
                "doi": "10.1000/nav",
                "sources": ["fixture", "code"],
            }
        ),
        encoding="utf-8",
    )
    (mineru_dir / "paper.md").write_text(
        "# Abstract\n\n"
        "This paper presents embodied navigation control for mobile robots.\n\n"
        "## Method\n\n"
        "The controller combines perception, planning, and feedback control.\n",
        encoding="utf-8",
    )
    (images_dir / "figure-1.png").write_bytes(b"fake-image")

    reader_record = generate_reader_outputs(paper_root)

    reader_text = (paper_root / "reader" / "reader.md").read_text(encoding="utf-8")
    figures_text = (paper_root / "reader" / "figures.md").read_text(encoding="utf-8")
    reproducibility_text = (paper_root / "reader" / "reproducibility.md").read_text(encoding="utf-8")

    assert "Evidence: source=mineru/paper.md; heading=Abstract" in reader_text
    assert "Evidence: source=metadata.json; field=venue" in reader_text
    assert "Evidence: source=mineru/images; image=figure-1.png" in figures_text
    assert "Evidence: source=metadata.json; field=sources" in reproducibility_text

    assert reader_record["reader_dir"] == str(paper_root / "reader")
    assert reader_record["started_at"]
    assert reader_record["finished_at"]
    assert reader_record["exit_status"] == 0
    assert reader_record["input_artifact_hashes"]["metadata.json"]
    assert reader_record["input_artifact_hashes"]["mineru/paper.md"]
    assert reader_record["output_artifact_hashes"]["reader.md"]
    assert reader_record["output_artifact_hashes"]["figures.md"]
    assert reader_record["output_artifact_hashes"]["reproducibility.md"]
    assert reader_record["output_artifact_hashes"]["implementation-ideas.md"]
