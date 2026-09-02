"""Turn calculator output into a useful, inspectable next-action artifact."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from freelancer_core.artifacts import (
    Artifact,
    ArtifactKind,
    ArtifactSection,
    Evidence,
    Provenance,
)


GROWTH_SOURCES = {
    "burnout_calculator",
    "skill_gap_scanner",
    "portfolio_score",
    "freelance_vs_fulltime",
}

SOURCE_ACTIONS: dict[str, list[str]] = {
    "burnout_calculator": [
        "Remove or defer one low-value commitment this week.",
        "Set a hard stop for the next five working days.",
        "Review workload again after seven days using the same inputs.",
    ],
    "skill_gap_scanner": [
        "Choose one target capability rather than studying every gap.",
        "Create a small proof-of-work project for that capability.",
        "Reassess after publishing the proof of work.",
    ],
    "portfolio_score": [
        "Rewrite one case study around a measurable client outcome.",
        "Add evidence that supports the result, not only screenshots.",
        "Ask one past client for a specific testimonial.",
    ],
    "client_fit_score": [
        "Confirm budget, decision-maker, and timeline before proposing.",
        "Record one explicit disqualifier and enforce it.",
        "Create the qualified opportunity in DealFlow.",
    ],
    "scope_creep_calculator": [
        "List work outside the signed scope.",
        "Price the change before continuing delivery.",
        "Issue a written change request in DealFlow.",
    ],
    "hourly_rate_calculator": [
        "Convert the result into a minimum project price.",
        "Add a contingency for non-billable delivery time.",
        "Use the price as a proposal floor in DealFlow.",
    ],
    "proposal_win_rate": [
        "Segment wins by lead source and offer.",
        "Stop pursuing the weakest segment for one cycle.",
        "Test one proposal change and measure it separately.",
    ],
}

DEFAULT_ACTIONS = [
    "Save this baseline result.",
    "Choose the highest-impact recommendation.",
    "Repeat the calculation after taking action and compare the change.",
]


def _product_for(source: str, user_type: str) -> tuple[str, str]:
    if user_type == "individual" and source in GROWTH_SOURCES:
        return "freelance-growth", "Continue in Growth SkillTree"
    return "freelancer-dealflow", "Turn this result into a DealFlow action"


def _evidence_from(result: dict[str, Any]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for key, value in sorted(result.items()):
        if isinstance(value, (str, int, float, bool)) and len(evidence) < 12:
            label = key.replace("_", " ").strip().title()
            evidence.append(Evidence(label=label, value=str(value), source="calculator-input"))
    return evidence


def build_action_brief(
    *, source: str, calculator_result: dict[str, Any], user_type: str
) -> Artifact:
    """Build a deterministic brief; no model call or hidden scoring step."""
    canonical_input = json.dumps(calculator_result, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical_input.encode()).hexdigest()
    product_slug, product_action = _product_for(source, user_type)
    evidence = _evidence_from(calculator_result)

    return Artifact(
        kind=ArtifactKind.ACTION_BRIEF,
        title=f"Action brief: {source.replace('_', ' ')}",
        summary="A transparent handoff from calculator result to a concrete next action.",
        sections=[
            ArtifactSection(
                key="result",
                title="Result signals",
                body=(
                    "These values are copied from the submitted calculator result; "
                    "they are not independently verified."
                ),
                evidence=evidence,
            ),
            ArtifactSection(
                key="next_actions",
                title="Recommended next actions",
                items=SOURCE_ACTIONS.get(source, DEFAULT_ACTIONS),
            ),
            ArtifactSection(
                key="handoff",
                title="Product handoff",
                body=product_action,
            ),
        ],
        provenance=Provenance(
            producer="leadtools.action-brief",
            source_ids=[f"calculator:{source}"],
            input_digest=digest,
        ),
        metadata={"product": product_slug, "user_type": user_type},
    )
