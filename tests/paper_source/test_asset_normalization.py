import json

from paper_source.asset_normalization import normalize_mineru_assets


def test_normalize_mineru_assets_updates_markdown_refs_and_subfigure_names(tmp_path):
    paper_root = tmp_path / "vault" / "_paper_source" / "raw" / "fixture-paper"
    mineru_dir = paper_root / "mineru"
    images_dir = mineru_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg").write_bytes(b"image-a")
    (images_dir / "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.jpg").write_bytes(b"image-b")
    markdown_path = mineru_dir / "fixture-paper.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# Abstract",
                "",
                "A parsed paper.   ",
                "",
                "![](images/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg)",
                "",
                "<details>",
                "<summary>line</summary>",
                "data",
                "</details>",
                "",
                "(a)",
                "",
                "![](images/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.jpg)",
                "",
                "<details>",
                "<summary>line</summary>",
                "data",
                "</details>",
                "",
                "(b)",
                "Fig. 1. Controller response: (a) position error and (b) velocity error.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    record = normalize_mineru_assets(paper_root, execute=True)

    text = markdown_path.read_text(encoding="utf-8")
    assert "images/fig-001a-controller-response-position-error-velocity.jpg" in text
    assert "images/fig-001b-controller-response-position-error-velocity.jpg" in text
    assert all(not line.endswith((" ", "\t")) for line in text.splitlines())
    assert not (images_dir / "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg").exists()
    assert not (images_dir / "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.jpg").exists()
    assert (images_dir / "fig-001a-controller-response-position-error-velocity.jpg").read_bytes() == b"image-a"
    assert (images_dir / "fig-001b-controller-response-position-error-velocity.jpg").read_bytes() == b"image-b"
    assert [item["figure_id"] for item in record["figure_index"]["figures"]] == ["fig-001a", "fig-001b"]
    assert len(record["needs_review"]) == 0
    assert json.loads((paper_root / "asset-normalization-record.json").read_text(encoding="utf-8"))["mode"] == "execute"

    second_record = normalize_mineru_assets(paper_root, execute=False)
    assert second_record["rename_plan"] == []


def test_normalize_mineru_assets_drops_formula_image_when_markdown_latex_exists(tmp_path):
    paper_root = tmp_path / "vault" / "_paper_source" / "raw" / "formula-paper"
    mineru_dir = paper_root / "mineru"
    images_dir = mineru_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "cccccccccccccccccccccccccccccccc.png").write_bytes(b"formula")
    markdown_path = mineru_dir / "formula-paper.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# Method",
                "",
                "Equation (1) defines the controller.",
                "",
                "$$",
                "u = Kx",
                "$$",
                "",
                "![](images/cccccccccccccccccccccccccccccccc.png)",
                "",
                "where K denotes the gain.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    record = normalize_mineru_assets(paper_root, execute=True)

    assert not (images_dir / "cccccccccccccccccccccccccccccccc.png").exists()
    assert "![](images/cccccccccccccccccccccccccccccccc.png)" not in markdown_path.read_text(encoding="utf-8")
    assert record["dropped_formula_images"][0]["status"] == "dropped"
    formula_index = json.loads((paper_root / "formula-index.json").read_text(encoding="utf-8"))
    assert formula_index["formulas"][0]["source"] == "mineru-markdown"
    assert "u = Kx" in formula_index["formulas"][0]["latex"]


def test_normalize_mineru_assets_keeps_image_when_only_global_tex_formula_exists(tmp_path):
    paper_root = tmp_path / "vault" / "_paper_source" / "raw" / "diagram-paper"
    mineru_dir = paper_root / "mineru"
    images_dir = mineru_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "dddddddddddddddddddddddddddddddd.png").write_bytes(b"diagram")
    (mineru_dir / "paper.tex").write_text(
        "\\begin{equation}\ny = mx + b\n\\end{equation}\n",
        encoding="utf-8",
    )
    markdown_path = mineru_dir / "diagram-paper.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# Method",
                "",
                "Eq. (2) is used elsewhere in the controller derivation.",
                "",
                "![](images/dddddddddddddddddddddddddddddddd.png)",
                "",
                "The block diagram above summarizes the control pipeline.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    record = normalize_mineru_assets(paper_root, execute=True)

    assert record["dropped_formula_images"] == []
    assert record["figure_index"]["figures"][0]["status"] == "unmapped"
    assert record["figure_index"]["figures"][0]["normalized_path"].startswith("images/unmapped-001-")
    assert (mineru_dir / record["figure_index"]["figures"][0]["normalized_path"]).exists()
    formula_index = json.loads((paper_root / "formula-index.json").read_text(encoding="utf-8"))
    assert formula_index["formulas"] == []


def test_normalize_mineru_assets_handles_caption_before_image_without_stealing_next_caption(tmp_path):
    paper_root = tmp_path / "vault" / "_paper_source" / "raw" / "caption-first-paper"
    mineru_dir = paper_root / "mineru"
    images_dir = mineru_dir / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.jpg").write_bytes(b"taxonomy")
    (images_dir / "ffffffffffffffffffffffffffffffff.jpg").write_bytes(b"prisma")
    markdown_path = mineru_dir / "caption-first-paper.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# 1.2 Related literature",
                "",
                "Fig. 1 Types of the control techniques used in AUV",
                "![](images/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.jpg)",
                "",
                "<details>",
                "<summary>flowchart</summary>",
                "graph TD",
                "</details>",
                "",
                "# 1.4 Motivation",
                "",
                "Fig. 2 Flowchart of PRISMA for AUV trajectory tracking after 2020",
                "![](images/ffffffffffffffffffffffffffffffff.jpg)",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    record = normalize_mineru_assets(paper_root, execute=True)

    figures = record["figure_index"]["figures"]
    assert [item["figure_id"] for item in figures] == ["fig-001", "fig-002"]
    assert figures[0]["original_label"] == "Fig. 1"
    assert figures[1]["original_label"] == "Fig. 2"
    assert figures[0]["normalized_path"].startswith("images/fig-001-")
    assert figures[1]["normalized_path"].startswith("images/fig-002-")
    text = markdown_path.read_text(encoding="utf-8")
    assert "images/fig-001-" in text
    assert "images/fig-002-" in text
    assert "-part-002" not in text
