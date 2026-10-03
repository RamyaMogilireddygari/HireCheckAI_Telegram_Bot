import pytest
from app.services.local_analyzer import LocalAnalyzer
from app.services.formatter import TelegramFormatter
from app.handlers.callbacks import SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT


def test_formatter_html_safety():
    res = LocalAnalyzer.analyze(SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT, resume_name="Test <Resume>.pdf", resume_id=1)

    main_msg = TelegramFormatter.main_result(res)
    assert "&lt;Resume&gt;" in main_msg or "Test" in main_msg
    assert "RESUME MATCH" in main_msg
    assert "SKILLS MATCHING" in main_msg
    assert "SKILLS MISSING" in main_msg
    assert "WHAT NOW?" in main_msg
    assert "TOP 3 COURSES" in main_msg
    assert "APPLY FOR THIS ROLE?" in main_msg

    score_msg = TelegramFormatter.why_score(res)
    assert "SCORE BREAKDOWN" in score_msg
    assert "Required Skills" in score_msg
    assert "40% weight" in score_msg

    roast_msg = TelegramFormatter.roast_message(res)
    assert "RESUME ROAST" in roast_msg

    gap_msg = TelegramFormatter.biggest_gap_message(res)
    assert "BIGGEST GAP" in gap_msg

    pov_msg = TelegramFormatter.recruiter_pov_message(res)
    assert "RECRUITER POV" in pov_msg


@pytest.mark.asyncio
async def test_end_to_end_ai_service():
    from app.services.ai_service import AIService
    result = await AIService.analyze_resume(SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT, "Alex_Resume.pdf", 1)
    assert result.score > 0.0
    assert result.score <= 10.0
    assert len(result.courses) <= 3
    assert result.verdict != ""
    assert result.biggest_gap.skill != ""
