from __future__ import annotations

import argparse
import json
from typing import Any

from epi.filter_candidates import default_discovery_exclusion_terms


DOMAIN_PACKS: dict[str, dict[str, Any]] = {
    "auv-control": {
        "detect": ["auv", "underwater", "marine", "ocean"],
        "platform": [
            "AUV",
            "autonomous underwater vehicle",
            "unmanned underwater vehicle",
            "underwater robot",
        ],
        "methods": [
            "reinforcement learning",
            "deep reinforcement learning",
            "offline reinforcement learning",
            "model-based reinforcement learning",
            "adaptive control",
            "safety-critical control",
        ],
        "tasks": [
            "trajectory tracking",
            "path following",
            "tracking control",
            "stabilization",
            "station keeping",
        ],
        "environment": [
            "ocean current",
            "current disturbance",
            "underwater disturbance",
            "turbulence",
        ],
        "evidence": [
            "sea trial",
            "field trial",
            "real AUV",
            "sim-to-real",
            "safety",
            "benchmark",
        ],
        "exclude": [
            "review",
            "survey",
            "literature review",
            "acoustic communication",
            "underwater sensor network",
        ],
        "venues": [
            "Ocean Engineering",
            "IEEE Journal of Oceanic Engineering",
            "Applied Ocean Research",
            "Control Engineering Practice",
            "OCEANS",
            "ICRA",
            "IROS",
        ],
    },
    "embodied-ai": {
        "detect": ["embodied", "vla", "world model", "foundation model", "diffusion policy"],
        "platform": ["embodied agent", "robot system", "manipulator", "mobile robot"],
        "methods": [
            "world model",
            "foundation model",
            "vision language action",
            "diffusion policy",
            "imitation learning",
            "reinforcement learning",
        ],
        "tasks": ["manipulation", "navigation", "planning", "long-horizon task"],
        "environment": ["sim-to-real", "real robot", "benchmark"],
        "evidence": ["real robot", "open-source code", "dataset", "ablation", "benchmark"],
        "exclude": ["review", "survey", "position paper", "pure LLM benchmark"],
        "venues": ["CoRL", "RSS", "ICRA", "IROS", "NeurIPS", "ICML", "ICLR", "RA-L"],
    },
    "general-robotics": {
        "detect": [],
        "platform": ["robot", "robotic system", "autonomous system"],
        "methods": [
            "model predictive control",
            "adaptive control",
            "robust control",
            "learning-based control",
            "control barrier function",
        ],
        "tasks": ["trajectory tracking", "path planning", "motion planning", "navigation"],
        "environment": ["disturbance", "uncertainty", "real-world"],
        "evidence": ["real-world experiment", "hardware experiment", "benchmark", "safety guarantee"],
        "exclude": ["review", "survey", "tutorial", "editorial"],
        "venues": ["TRO", "IJRR", "RA-L", "ICRA", "IROS", "RSS", "CoRL"],
    },
}


def choose_domain(topic: str, requested: str) -> str:
    if requested != "auto":
        if requested not in DOMAIN_PACKS:
            raise ValueError(f"unknown domain: {requested}")
        return requested

    lowered = topic.lower()
    for name, pack in DOMAIN_PACKS.items():
        if name == "general-robotics":
            continue
        if any(marker in lowered for marker in pack["detect"]):
            return name
    return "general-robotics"


def quote(term: str) -> str:
    if " " in term and not term.startswith('"'):
        return f'"{term}"'
    return term


def with_exclusion(query: str, non_review: bool) -> str:
    return f"{query} -review -survey" if non_review else query


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    kept: list[str] = []
    for item in items:
        normalized = " ".join(item.lower().split())
        if normalized in seen:
            continue
        seen.add(normalized)
        kept.append(item)
    return kept


def build_queries(pack: dict[str, Any], topic: str, non_review: bool, max_queries: int) -> list[str]:
    platform = pack["platform"]
    methods = pack["methods"]
    tasks = pack["tasks"]
    environment = pack["environment"]
    evidence = pack["evidence"]

    raw = [
        f"{quote(platform[1] if len(platform) > 1 else platform[0])} {quote(methods[0])} {quote(tasks[0])}",
        f"{quote(platform[0])} {quote(methods[1] if len(methods) > 1 else methods[0])} "
        f"{quote(tasks[1] if len(tasks) > 1 else tasks[0])}",
        f"{quote(platform[0])} {quote(methods[2] if len(methods) > 2 else methods[0])} "
        f"{quote(environment[0])}",
        f"{quote(platform[1] if len(platform) > 1 else platform[0])} "
        f"{quote(methods[3] if len(methods) > 3 else methods[0])} {quote(evidence[0])}",
        f"{quote(platform[-1])} {quote(methods[0])} {quote(tasks[-1])} "
        f"{quote(environment[1] if len(environment) > 1 else environment[0])}",
        f"{quote(platform[0])} {quote(tasks[2] if len(tasks) > 2 else tasks[0])} "
        f"{quote(evidence[1] if len(evidence) > 1 else evidence[0])}",
        f"{quote(platform[0])} {quote(methods[-1])} "
        f"{quote(evidence[-2] if len(evidence) > 1 else evidence[0])}",
        f"{topic} {quote(evidence[-1])}",
    ]
    return unique([with_exclusion(query, non_review) for query in raw])[:max_queries]


def build_query_plan(
    topic: str,
    domain: str = "auto",
    non_review: bool | None = None,
    max_queries: int = 8,
) -> dict[str, Any]:
    chosen = choose_domain(topic, domain)
    pack = DOMAIN_PACKS[chosen]
    exclude_reviews = bool(default_discovery_exclusion_terms(topic)) if non_review is None else non_review
    exclusions = list(pack["exclude"])
    if exclude_reviews:
        exclusions = unique(exclusions + ["review", "survey"])

    return {
        "workflow": "epi-query-plan",
        "topic": topic,
        "domain": chosen,
        "concept_blocks": {
            "platform": pack["platform"],
            "method_family": pack["methods"],
            "task": pack["tasks"],
            "environment_or_disturbance": pack["environment"],
            "validation_mode": pack["evidence"],
            "exclusions": exclusions,
        },
        "query_variants": build_queries(pack, topic, exclude_reviews, max(1, max_queries)),
        "source_route": {
            "t1": ["paper_search_mcp", "arxiv", "semantic", "openalex", "crossref"],
            "t2": ["official venue pages", "publisher DOI pages", "IEEE/ACM/Springer/ScienceDirect"],
            "t3": ["Google Scholar", "lab/project pages", "RoboWiki", "community hints"],
        },
        "recall_gap_checks": {
            "venue_families": pack["venues"],
            "citation_graph": ["journal version", "recent cited-by", "references", "related papers"],
            "library_dedup": ["DOI", "arXiv ID", "normalized title", "title+first-author+year"],
        },
        "quality_signals": pack["evidence"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic EPI paper discovery query plan.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--domain", default="auto", choices=["auto", *DOMAIN_PACKS.keys()])
    review_mode = parser.add_mutually_exclusive_group()
    review_mode.add_argument("--non-review", dest="non_review", action="store_true")
    review_mode.add_argument("--include-reviews", dest="non_review", action="store_false")
    parser.set_defaults(non_review=None)
    parser.add_argument("--max-queries", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    plan = build_query_plan(
        topic=args.topic,
        domain=args.domain,
        non_review=args.non_review,
        max_queries=args.max_queries,
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
