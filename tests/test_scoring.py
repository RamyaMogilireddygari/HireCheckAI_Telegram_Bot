from app.services.scoring import (
    ScoreBreakdown,
    compute_verdict,
    generate_progress_bar
)


def test_scoring_weights_calculation():
    # 40% Required, 25% Preferred, 15% Experience, 10% Education, 10% Keywords
    breakdown = ScoreBreakdown(
        required_skills_pct=100.0,
        preferred_skills_pct=100.0,
        experience_pct=100.0,
        education_pct=100.0,
        keywords_pct=100.0
    )
    assert breakdown.calculate_final_score() == 10.0

    breakdown_mixed = ScoreBreakdown(
        required_skills_pct=80.0,  # 80 * 0.40 = 32.0
        preferred_skills_pct=60.0,  # 60 * 0.25 = 15.0
        experience_pct=70.0,        # 70 * 0.15 = 10.5
        education_pct=90.0,         # 90 * 0.10 = 9.0
        keywords_pct=80.0          # 80 * 0.10 = 8.0
        # Total = 74.5 -> / 10 = 7.5
    )
    assert breakdown_mixed.calculate_final_score() == 7.5


def test_verdicts():
    v1, e1, _ = compute_verdict(9.5)
    assert "COOKING" in v1
    assert e1 == "🔥"

    v2, e2, _ = compute_verdict(8.0)
    assert "SOLID" in v2
    assert e2 == "👀"

    v3, e3, _ = compute_verdict(6.0)
    assert "STILL COOKING" in v3
    assert e3 == "😭"

    v4, e4, _ = compute_verdict(3.5)
    assert "COOKED" in v4
    assert e4 == "💀"


def test_progress_bar():
    bar_full = generate_progress_bar(100.0, length=10)
    assert bar_full == "██████████"

    bar_half = generate_progress_bar(50.0, length=10)
    assert bar_half == "█████░░░░░"

    bar_zero = generate_progress_bar(0.0, length=10)
    assert bar_zero == "░░░░░░░░░░"
