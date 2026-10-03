from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SkillMatchGroup(BaseModel):
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    partial: List[str] = Field(default_factory=list)


class ExperienceMatch(BaseModel):
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    score_pct: float = 80.0  # 0 to 100


class EducationMatch(BaseModel):
    summary: str = ""
    matched: bool = True
    score_pct: float = 90.0  # 0 to 100


class KeywordMatchGroup(BaseModel):
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    score_pct: float = 75.0


class BiggestGap(BaseModel):
    skill: str = "Cloud & Deployment"
    priority: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"
    reason: str = "The JD specifically lists this as a key requirement, but your resume lacks direct evidence."
    how_to_fix: str = "Build a small demo project with real deployments, and document the architecture."
    course: Optional[Dict[str, str]] = None


class CourseRec(BaseModel):
    title: str
    url: str
    provider: str = "Verified Academy"
    reason: str = ""


class WeakBullet(BaseModel):
    original: str
    problem: str = "Too vague / lacks measurable impact"
    improved: str
    why_better: List[str] = Field(default_factory=lambda: [
        "Specific technology",
        "Shows what you actually did",
        "Clear measurable outcome"
    ])


class RecruiterPOV(BaseModel):
    first_impression: str = "Strong technical foundation."
    then: str = "Interesting relevant projects."
    concerns: str = "Could show more explicit measurable impact."
    takeaway: str = "Relevant experience, but needs clearer quantification of project outcomes."


class ReceiptItem(BaseModel):
    skill: str
    status: str  # "MATCHED", "MISSING", "PARTIAL"
    evidence: str
    source_location: str = "Resume Experience / Projects"
    confidence: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"


class SkillDNACategory(BaseModel):
    category: str
    candidate_pct: int
    jd_pct: int


class CapCheckItem(BaseModel):
    claim: str
    evidence_found: List[str] = Field(default_factory=list)
    gaps_found: List[str] = Field(default_factory=list)
    verdict: str = "🟡 A little ambitious 😭"
    suggestion: str


class ScoreBreakdown(BaseModel):
    required_skills_pct: float = 80.0  # Weight: 40%
    preferred_skills_pct: float = 70.0  # Weight: 25%
    experience_pct: float = 75.0        # Weight: 15%
    education_pct: float = 90.0         # Weight: 10%
    keywords_pct: float = 70.0          # Weight: 10%

    def calculate_final_score(self) -> float:
        score = (
            (self.required_skills_pct * 0.40) +
            (self.preferred_skills_pct * 0.25) +
            (self.experience_pct * 0.15) +
            (self.education_pct * 0.10) +
            (self.keywords_pct * 0.10)
        ) / 10.0
        return round(max(0.0, min(10.0, score)), 1)


class AnalysisResult(BaseModel):
    resume_id: int = 1
    resume_name: str = "Resume.pdf"
    score: float = 8.7
    verdict: str = "YOU'RE COOKING"
    verdict_emoji: str = "🔥"
    verdict_subtitle: str = "This resume is seriously aligned with the JD."
    
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    
    required_skills: SkillMatchGroup = Field(default_factory=SkillMatchGroup)
    preferred_skills: SkillMatchGroup = Field(default_factory=SkillMatchGroup)
    experience_match: ExperienceMatch = Field(default_factory=ExperienceMatch)
    education_match: EducationMatch = Field(default_factory=EducationMatch)
    keyword_match: KeywordMatchGroup = Field(default_factory=KeywordMatchGroup)
    
    what_now: str = "Your core skills are strong. Tackle your biggest gaps first before polishing minor bullets."
    application_ready: bool = True
    application_ready_text: str = "YES 🔥"
    application_ready_reason: str = "Your resume covers the core requirements well enough to move forward."
    
    biggest_gap: BiggestGap = Field(default_factory=BiggestGap)
    courses: List[CourseRec] = Field(default_factory=list)
    
    roast: Optional[WeakBullet] = None
    recruiter_pov: RecruiterPOV = Field(default_factory=RecruiterPOV)
    receipts: List[ReceiptItem] = Field(default_factory=list)
    weak_bullets: List[WeakBullet] = Field(default_factory=list)
    cap_checks: List[CapCheckItem] = Field(default_factory=list)
    skill_dna: List[SkillDNACategory] = Field(default_factory=list)


def compute_verdict(score: float) -> tuple[str, str, str]:
    if score >= 9.0:
        return "YOU'RE COOKING", "🔥", "This resume is seriously aligned with the JD."
    elif score >= 7.0:
        return "PRETTY SOLID", "👀", "You're close. A few gaps are holding you back."
    elif score >= 5.0:
        return "STILL COOKING...", "😭", "The potential is there. But we've got some serious gaps to fix."
    else:
        return "KINDA COOKED", "💀", "This JD and your resume aren't matching well yet. But the gaps are fixable."


def generate_progress_bar(pct: float, length: int = 15) -> str:
    filled = int(round((pct / 100.0) * length))
    filled = max(0, min(length, filled))
    empty = length - filled
    return "█" * filled + "░" * empty
