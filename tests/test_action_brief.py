from app.services.action_brief import build_action_brief


def test_learning_calculator_routes_an_individual_to_growth() -> None:
    brief = build_action_brief(
        source="skill_gap_scanner",
        calculator_result={"target_role": "Backend Engineer", "gap_count": 3},
        user_type="individual",
    )

    assert brief.metadata["product"] == "freelance-growth"
    assert brief.sections[2].body == "Continue in Growth SkillTree"
    assert brief.provenance.source_ids == ["calculator:skill_gap_scanner"]


def test_commercial_calculator_routes_to_dealflow() -> None:
    brief = build_action_brief(
        source="client_fit_score",
        calculator_result={"score": 72, "budget_confirmed": True},
        user_type="individual",
    )

    assert brief.metadata["product"] == "freelancer-dealflow"
    assert "DealFlow" in brief.sections[2].body


def test_action_brief_is_deterministic_and_inspectable() -> None:
    payload = {"score": 64, "risk": "medium", "nested": {"ignored": True}}
    first = build_action_brief(
        source="burnout_calculator",
        calculator_result=payload,
        user_type="individual",
    )
    second = build_action_brief(
        source="burnout_calculator",
        calculator_result=dict(reversed(list(payload.items()))),
        user_type="individual",
    )

    assert first.provenance.input_digest == second.provenance.input_digest
    assert [item.label for item in first.sections[0].evidence] == ["Risk", "Score"]
    assert len(first.sections[1].items) == 3
