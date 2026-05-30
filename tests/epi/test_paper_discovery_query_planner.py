import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLANNER = ROOT / "plugins" / "epi" / "skills" / "paper-discovery" / "scripts" / "query-planner.py"


def test_query_planner_generates_auv_non_review_plan():
    result = subprocess.run(
        [
            sys.executable,
            str(PLANNER),
            "--topic",
            "latest high quality AUV reinforcement learning control papers",
            "--domain",
            "auv-control",
            "--non-review",
            "--max-queries",
            "8",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    plan = json.loads(result.stdout)

    assert plan["workflow"] == "epi-query-plan"
    assert plan["domain"] == "auv-control"
    assert "autonomous underwater vehicle" in plan["concept_blocks"]["platform"]
    assert "offline reinforcement learning" in plan["concept_blocks"]["method_family"]
    assert "path following" in plan["concept_blocks"]["task"]
    assert "current disturbance" in plan["concept_blocks"]["environment_or_disturbance"]
    assert "real AUV" in plan["concept_blocks"]["validation_mode"]
    assert "review" in plan["concept_blocks"]["exclusions"]
    assert len(plan["query_variants"]) >= 5
    assert all("-review -survey" in query for query in plan["query_variants"])
    assert "paper_search_mcp" in plan["source_route"]["t1"]
    assert "Ocean Engineering" in plan["recall_gap_checks"]["venue_families"]
    assert "recent cited-by" in plan["recall_gap_checks"]["citation_graph"]


def test_query_planner_auto_detects_embodied_ai_domain():
    result = subprocess.run(
        [
            sys.executable,
            str(PLANNER),
            "--topic",
            "embodied AI world model robot learning manipulation papers",
            "--domain",
            "auto",
            "--max-queries",
            "6",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    plan = json.loads(result.stdout)

    assert plan["domain"] == "embodied-ai"
    assert "world model" in plan["concept_blocks"]["method_family"]
    assert "CoRL" in plan["recall_gap_checks"]["venue_families"]
