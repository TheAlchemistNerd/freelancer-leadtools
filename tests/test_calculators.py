"""Tests for Freelancer LeadTools Calculators."""
import pytest
from app.services.calculators import (
    calculate_burnout_risk,
    calculate_skill_gap,
    calculate_portfolio_score,
    calculate_client_fit,
    calculate_scope_creep,
)


class TestBurnoutCalculator:
    """Tests for burnout risk calculator."""

    def test_low_risk(self):
        """Test low burnout risk scenario."""
        result = calculate_burnout_risk(
            weekly_hours=35,
            context_switches=5,
            avg_sleep_hours=8,
        )
        assert result["score"] < 40
        assert result["level"] == "low"

    def test_high_risk(self):
        """Test high burnout risk scenario."""
        result = calculate_burnout_risk(
            weekly_hours=60,
            context_switches=20,
            avg_sleep_hours=5,
        )
        assert result["score"] >= 70
        assert result["level"] == "high"
        assert len(result["recovery_plan"]) == 7

    def test_score_bounds(self):
        """Test score is within bounds."""
        result = calculate_burnout_risk(
            weekly_hours=100,
            context_switches=50,
            avg_sleep_hours=0,
        )
        assert 0 <= result["score"] <= 100


class TestSkillGapCalculator:
    """Tests for skill gap scanner."""

    def test_backend_role(self):
        """Test backend role skill gaps."""
        result = calculate_skill_gap(
            target_role="Backend Developer",
            current_skills=["python", "sql"],
            experience_level="mid",
        )
        assert "apis" in result["gaps"] or "docker" in result["gaps"]
        assert len(result["roadmap"]) == 3

    def test_empty_skills(self):
        """Test with no current skills."""
        result = calculate_skill_gap(
            target_role="Full Stack Developer",
            current_skills=[],
            experience_level="junior",
        )
        assert len(result["gaps"]) > 0


class TestPortfolioScore:
    """Tests for portfolio score calculator."""

    def test_complete_portfolio(self):
        """Test portfolio with all elements."""
        result = calculate_portfolio_score(
            github_url="https://github.com/user",
            profile_url="https://example.com",
            project_links=["a", "b", "c", "d", "e"],
        )
        assert result["score"] >= 80

    def test_empty_portfolio(self):
        """Test empty portfolio."""
        result = calculate_portfolio_score(
            github_url=None,
            profile_url=None,
            project_links=[],
        )
        assert result["score"] < 50
        assert len(result["missing"]) > 0


class TestClientFit:
    """Tests for client fit calculator."""

    def test_good_client(self):
        """Test good client fit."""
        result = calculate_client_fit(
            offered_budget=10000,
            timeline_days=30,
            scope_clarity=5,
            communication=5,
            payment_reliability=5,
        )
        assert result["level"] == "good"
        assert len(result["red_flags"]) == 0

    def test_bad_client(self):
        """Test bad client fit."""
        result = calculate_client_fit(
            offered_budget=500,
            timeline_days=3,
            scope_clarity=1,
            communication=1,
            payment_reliability=1,
        )
        assert result["level"] == "poor"
        assert len(result["red_flags"]) > 0


class TestScopeCreep:
    """Tests for scope creep calculator."""

    def test_scope_creep_cost(self):
        """Test scope creep cost calculation."""
        result = calculate_scope_creep(
            extra_requests=5,
            hours_per_request=2,
            hourly_rate=100,
            delay_days=10,
        )
        assert result["direct_cost"] == 1000
        assert result["total_cost"] > result["direct_cost"]
        assert "Change Order" in result["boundary_message"]
