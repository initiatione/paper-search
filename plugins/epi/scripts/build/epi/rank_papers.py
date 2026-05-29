from __future__ import annotations

from math import log10


REPRODUCIBILITY_TERMS = (
    "reproducible",
    "benchmark",
    "ablation",
    "code",
    "dataset",
    "open-source",
    "open source",
    "simulator",
    "implementation",
)
BENCHMARK_TERMS = (
    "benchmark",
    "baseline",
    "ablation",
    "comparison",
    "evaluated",
    "experiment",
    "metric",
)


def _text(candidate: dict) -> str:
    return f"{candidate.get('title', '')} {candidate.get('abstract', '')}".lower()


def _term_score(text: str, terms: tuple[str, ...]) -> float:
    hits = sum(1 for term in terms if term in text)
    return min(1.0, hits / 3)


def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _ranking_protocol(
    *,
    matched_keywords: list[str],
    matched_negative_keywords: list[str],
    signals: dict[str, float],
    code_available: bool,
) -> dict:
    reasons: list[str] = []
    cautions: list[str] = []
    if matched_keywords:
        reasons.append("matched keywords: " + ", ".join(matched_keywords))
    if matched_negative_keywords:
        cautions.append("negative_keyword_overlap: " + ", ".join(matched_negative_keywords))
    if code_available:
        reasons.append("code availability signal present")
    else:
        cautions.append("weak_reproducibility_signal")
    if signals["benchmark_score"] < 0.34:
        cautions.append("weak_benchmark_signal")
    if signals["venue_score"] < 0.5:
        cautions.append("weak_venue_signal")

    decision = (
        "advance-candidate"
        if (
            signals["score"] >= 0.75
            and signals["reproducibility_score"] >= 0.35
            and signals["negative_keyword_penalty"] < 0.34
        )
        else "review-candidate"
    )
    return {
        "schema_version": "epi-ranking-protocol-v1",
        "decision": decision,
        "matched_positive_keywords": matched_keywords,
        "matched_negative_keywords": matched_negative_keywords,
        "reasons": reasons,
        "cautions": cautions,
        "lenses": {
            "editorial": {
                "score": signals["editorial_score"],
                "signals": ["venue_tier", "freshness", "topic_relevance"],
            },
            "peer_review": {
                "score": signals["peer_review_score"],
                "signals": ["citation_signal", "benchmark_signal", "pdf_available"],
            },
            "domain_fit": {
                "score": signals["domain_fit_score"],
                "signals": ["positive_keyword_overlap", "negative_keyword_penalty"],
            },
            "reproducibility": {
                "score": signals["reproducibility_score"],
                "signals": ["code_available", "reproducibility_terms"],
            },
        },
    }


def _score_take(score: float, *, strong: str, weak: str) -> str:
    return strong if score >= 0.7 else weak


def _ranking_rationale(
    *,
    decision: str,
    matched_keywords: list[str],
    matched_negative_keywords: list[str],
    protocol: dict,
    signals: dict[str, float],
) -> dict:
    review_before_ingest = list(protocol.get("cautions") or [])
    if decision == "advance-candidate":
        one_sentence = (
            "Advance for low-burden reading report and LLM Wiki deposition: "
            "the paper matches the user profile and has enough evidence signals to inspect."
        )
    else:
        one_sentence = (
            "review before ingest: the paper may match the topic, but ranking checks found signals "
            "that need human or critic attention first."
        )
    if matched_negative_keywords:
        review_before_ingest.append("negative_keyword_overlap")

    return {
        "schema_version": "epi-ranking-rationale-v1",
        "recommendation": decision,
        "one_sentence": one_sentence,
        "user_interest_match": {
            "positive_keywords": matched_keywords,
            "negative_keywords": matched_negative_keywords,
        },
        "role_views": {
            "nature_sci_editor": {
                "lens": "editorial significance",
                "take": _score_take(
                    signals["editorial_score"],
                    strong="Strong topic, venue, or freshness signal for a concise editorial summary.",
                    weak="Editorial value is plausible but not yet strong enough to prioritize without review.",
                ),
            },
            "peer_reviewer": {
                "lens": "method and evidence",
                "take": _score_take(
                    signals["peer_review_score"],
                    strong="Benchmark, citation, or PDF evidence is inspectable for method review.",
                    weak="Method evidence looks thin; check baselines, metrics, and experimental setup before ingest.",
                ),
            },
            "senior_domain_researcher": {
                "lens": "theory and experiment transfer",
                "take": _score_take(
                    signals["domain_fit_score"],
                    strong="Good fit for theory notes, experiment ideas, and domain synthesis.",
                    weak="Domain fit is partial; keep it in review unless it fills a specific wiki gap.",
                ),
            },
        },
        "wiki_deposition": {
            "value": "If advanced, distill into reference, concept, synthesis, and low-burden reading report pages.",
            "suggested_pages": ["references", "concepts", "synthesis", "reports"],
        },
        "review_before_ingest": review_before_ingest,
    }


def rank_candidates(
    candidates: list[dict],
    positive_keywords: list[str],
    venue_tiers: dict[str, float],
    negative_keywords: list[str] | None = None,
) -> list[dict]:
    ranked: list[dict] = []
    keywords = [keyword.lower() for keyword in positive_keywords]
    negative_terms = [keyword.lower() for keyword in (negative_keywords or [])]
    for candidate in candidates:
        text = _text(candidate)
        matched_keywords = _matched_keywords(text, keywords)
        matched_negative_keywords = _matched_keywords(text, negative_terms)
        keyword_hits = len(matched_keywords)
        topic_score = min(1.0, keyword_hits / max(1, len(keywords)))
        negative_keyword_penalty = min(1.0, len(matched_negative_keywords) / max(1, len(negative_terms)))
        profile_fit_score = max(0.0, topic_score - negative_keyword_penalty)
        venue_score = venue_tiers.get(str(candidate.get("venue") or "").lower(), 0.45)
        citation_score = min(1.0, log10(int(candidate.get("citation_count") or 0) + 1) / 3)
        freshness_score = 1.0 if int(candidate.get("year") or 0) >= 2024 else 0.7
        pdf_score = 1.0 if candidate.get("pdf_url") else 0.0
        code_score = 1.0 if candidate.get("code_url") else 0.0
        reproducibility_terms_score = _term_score(text, REPRODUCIBILITY_TERMS)
        benchmark_score = _term_score(text, BENCHMARK_TERMS)
        editorial_score = round(topic_score * 0.5 + venue_score * 0.3 + freshness_score * 0.2, 4)
        peer_review_score = round(citation_score * 0.35 + benchmark_score * 0.4 + pdf_score * 0.25, 4)
        domain_fit_score = round(profile_fit_score, 4)
        reproducibility_score = round(code_score * 0.6 + reproducibility_terms_score * 0.4, 4)
        base_score = (
            topic_score * 0.35
            + venue_score * 0.18
            + citation_score * 0.15
            + freshness_score * 0.10
            + pdf_score * 0.08
            + code_score * 0.08
            + 0.06
        )
        score = round(max(0.0, base_score - negative_keyword_penalty * 0.25), 4)
        ranked_candidate = dict(candidate)
        ranked_candidate["score"] = score
        ranked_candidate["ranking_signals"] = {
            "topic_score": round(topic_score, 4),
            "venue_score": round(venue_score, 4),
            "citation_score": round(citation_score, 4),
            "freshness_score": freshness_score,
            "pdf_score": pdf_score,
            "code_score": code_score,
            "benchmark_score": round(benchmark_score, 4),
            "reproducibility_terms_score": round(reproducibility_terms_score, 4),
            "negative_keyword_penalty": round(negative_keyword_penalty, 4),
            "editorial_score": editorial_score,
            "peer_review_score": peer_review_score,
            "domain_fit_score": domain_fit_score,
            "reproducibility_score": reproducibility_score,
        }
        protocol = _ranking_protocol(
            matched_keywords=matched_keywords,
            matched_negative_keywords=matched_negative_keywords,
            signals={
                **ranked_candidate["ranking_signals"],
                "score": score,
            },
            code_available=bool(candidate.get("code_url")),
        )
        ranked_candidate["ranking_protocol"] = protocol
        ranked_candidate["ranking_rationale"] = _ranking_rationale(
            decision=protocol["decision"],
            matched_keywords=matched_keywords,
            matched_negative_keywords=matched_negative_keywords,
            protocol=protocol,
            signals=ranked_candidate["ranking_signals"],
        )
        ranked.append(ranked_candidate)
    return sorted(ranked, key=lambda item: item["score"], reverse=True)
