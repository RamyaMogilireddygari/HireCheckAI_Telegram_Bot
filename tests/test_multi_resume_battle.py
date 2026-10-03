import pytest
from app.services.local_analyzer import LocalAnalyzer
from app.services.formatter import TelegramFormatter

RESUME_STRONG = """
Candidate: Sarah (Senior Cloud ML Engineer)
Skills: Python, Machine Learning, Deep Learning, SQL, AWS, Docker, Kubernetes, FastAPI, React
Experience: 4 years as ML Engineer building and deploying production models on AWS ECS and Kubernetes.
Education: B.S. in Computer Science
"""

RESUME_MID = """
Candidate: Alex (Junior ML Developer)
Skills: Python, Machine Learning, SQL, Pandas, Scikit-learn, React
Experience: 1 year intern building ML models.
Education: B.Tech Computer Science
"""

RESUME_WEAK = """
Candidate: John (Marketing Specialist)
Skills: Social Media, Copywriting, Marketing, Excel, SEO
Experience: 3 years in digital marketing campaigns.
Education: B.A. in Communications
"""

JD_AI_ML = """
Role: AI/ML Platform Engineer
Required: Python, Machine Learning, SQL, AWS, Docker
Preferred: Kubernetes, FastAPI, React
"""


def test_resume_battle_ranking():
    res1 = LocalAnalyzer.analyze(RESUME_STRONG, JD_AI_ML, resume_name="Sarah_Senior.pdf", resume_id=1)
    res2 = LocalAnalyzer.analyze(RESUME_MID, JD_AI_ML, resume_name="Alex_Junior.pdf", resume_id=2)
    res3 = LocalAnalyzer.analyze(RESUME_WEAK, JD_AI_ML, resume_name="John_Marketing.pdf", resume_id=3)

    results = [res1, res2, res3]
    # Sarah should have the highest score, Alex in middle, John lowest
    assert res1.score > res2.score
    assert res2.score > res3.score

    battle_text = TelegramFormatter.resume_battle(results)
    assert "RESUME BATTLE" in battle_text
    assert "Sarah_Senior.pdf" in battle_text
    assert "Alex_Junior.pdf" in battle_text
    assert "John_Marketing.pdf" in battle_text
    assert "🏆 <b>Sarah_Senior.pdf</b>" in battle_text
