import json
import logging
import re
from typing import Optional, Dict, Any, List
from app.config import config
from app.services.scoring import (
    AnalysisResult,
    ScoreBreakdown,
    SkillMatchGroup,
    ExperienceMatch,
    EducationMatch,
    KeywordMatchGroup,
    BiggestGap,
    CourseRec,
    WeakBullet,
    RecruiterPOV,
    ReceiptItem,
    CapCheckItem,
    SkillDNACategory,
    compute_verdict,
)
from app.services.local_analyzer import LocalAnalyzer
from app.services.courses import course_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are HireCheck AI, an expert AI recruiter and career coach with a witty, sharp, constructive Gen-Z vibe (like a smart career bestie who gives a reality check).

Your job is to analyze a candidate's resume against a job description (JD) and provide an objective, evidence-based, structured evaluation.

SCORING RULES (Strict 0.0 to 10.0 scale, rounded to 1 decimal place):
- 40% Required Skills (must-have technical competencies in JD)
- 25% Preferred Skills (bonus/nice-to-have competencies in JD)
- 15% Experience (relevance of past roles, projects, depth)
- 10% Education & Qualifications (degrees, certifications)
- 10% Keywords & Responsibilities (domain terminology, duties)

EVIDENCE-BASED MATCHING:
- Confirmed/Matched: Direct receipts/evidence in resume projects or experience.
- Partial/Transferable: Related skills (e.g. Next.js for React, Azure for AWS), but exact tool not confirmed.
- Missing: Required tool is absent or has no receipts.
- Synonyms: Recognize JS=JavaScript, TS=TypeScript, Postgres=PostgreSQL, ML=Machine Learning, NLP=Natural Language Processing, AWS=Amazon Web Services, GCP=Google Cloud Platform.

YOU MUST RETURN STRICT VALID JSON with this exact structure:
{
  "score": 8.7,
  "verdict": "YOU'RE COOKING",
  "verdict_emoji": "🔥",
  "verdict_subtitle": "This resume is seriously aligned with the JD.",
  "breakdown": {
    "required_skills_pct": 85.0,
    "preferred_skills_pct": 75.0,
    "experience_pct": 80.0,
    "education_pct": 95.0,
    "keywords_pct": 80.0
  },
  "required_skills": {
    "matched": ["Python", "SQL", "Machine Learning"],
    "missing": ["AWS", "Docker"],
    "partial": []
  },
  "preferred_skills": {
    "matched": ["React"],
    "missing": ["Kubernetes"],
    "partial": ["FastAPI"]
  },
  "experience_match": {
    "summary": "Strong project foundation in ML and data pipelines.",
    "strengths": ["Hands-on machine learning projects", "API development experience"],
    "gaps": ["Production cloud deployment receipts"]
  },
  "education_match": {
    "summary": "B.Tech Computer Science aligns directly with requirement.",
    "matched": true
  },
  "keyword_match": {
    "matched": ["REST APIs", "Pipelines", "Classification"],
    "missing": ["Containerization", "Cloud Infrastructure"]
  },
  "what_now": "You're already strong on core requirements. Your biggest gaps are AWS and Docker. Fix those with a deployed mini-project before applying.",
  "application_ready": true,
  "application_ready_text": "YES 🔥",
  "application_ready_reason": "Your resume covers the core requirements well enough to move forward.",
  "biggest_gap": {
    "skill": "AWS",
    "priority": "HIGH",
    "reason": "The JD specifically asks for AWS, but your resume lacks direct cloud deployment evidence.",
    "how_to_fix": "Build one small project and deploy it using AWS (EC2/S3/Lambda). Add the measurable deployment result to your resume."
  },
  "roast": {
    "original": "Worked on machine learning projects.",
    "problem": "Too vague / gives 'I did something, trust me' energy",
    "improved": "Built a machine-learning classification pipeline using Python and Scikit-learn, achieving 92% validation accuracy.",
    "why_better": [
      "Specific technology stack",
      "Shows what you actually did",
      "Includes measurable outcome"
    ]
  },
  "recruiter_pov": {
    "first_impression": "Strong technical foundation in core ML and backend.",
    "then": "Interesting and relevant projects in the portfolio.",
    "concerns": "Where are the production deployment receipts?",
    "takeaway": "Your technical skills are solid. Add more specific measurable outcomes to project bullets."
  },
  "receipts": [
    {
      "skill": "Python",
      "status": "MATCHED",
      "evidence": "Built an NLP pipeline using Python and NLTK...",
      "source_location": "Project: AI Resume Analyzer",
      "confidence": "HIGH"
    },
    {
      "skill": "AWS",
      "status": "MISSING",
      "evidence": "No explicit AWS cloud deployments found.",
      "source_location": "Skills & Experience",
      "confidence": "LOW"
    }
  ],
  "cap_checks": [
    {
      "claim": "Hands-on ML Expertise",
      "evidence_found": ["2 Scikit-learn classification projects"],
      "gaps_found": ["No production pipeline monitoring"],
      "verdict": "✅ Legit receipts! No cap detected.",
      "suggestion": "Highlight your model validation metrics prominently."
    }
  ],
  "skill_dna": [
    {"category": "AI / ML", "candidate_pct": 90, "jd_pct": 85},
    {"category": "Backend & APIs", "candidate_pct": 80, "jd_pct": 80},
    {"category": "Data & DBs", "candidate_pct": 85, "jd_pct": 70},
    {"category": "Cloud & DevOps", "candidate_pct": 30, "jd_pct": 80},
    {"category": "Frontend / UI", "candidate_pct": 70, "jd_pct": 50}
  ]
}
"""


class AIService:
    @staticmethod
    def _clean_json_response(raw_text: str) -> str:
        # Extract json content if wrapped in markdown code blocks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Look for outer braces
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return raw_text[start : end + 1].strip()
        return raw_text.strip()

    @classmethod
    async def _analyze_with_gemini(cls, resume_text: str, jd_text: str, model_name: str) -> Optional[Dict[str, Any]]:
        api_key = config.AI_API_KEY
        if not api_key:
            return None

        prompt = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}\n\nAnalyze this resume against the JD and return JSON as specified."

        # Try google-genai library
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name or "gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            raw = response.text
            cleaned = cls._clean_json_response(raw)
            return json.loads(cleaned)
        except Exception as e1:
            logger.warning(f"google-genai client attempt failed: {e1}. Trying openai-compatible Gemini endpoint or direct httpx...")

        # Fallback: OpenAI-compatible Gemini endpoint via httpx
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name or "gemini-2.0-flash",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(cls._clean_json_response(content))
        except Exception as e2:
            logger.warning(f"HTTP Gemini endpoint failed: {e2}")

        return None

    @classmethod
    async def _analyze_with_openai(cls, resume_text: str, jd_text: str, model_name: str) -> Optional[Dict[str, Any]]:
        api_key = config.AI_API_KEY
        if not api_key:
            return None

        try:
            from openai import AsyncOpenAI

            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            if config.AI_BASE_URL:
                client_kwargs["base_url"] = config.AI_BASE_URL

            client = AsyncOpenAI(**client_kwargs)
            prompt = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}\n\nAnalyze this resume against the JD and return JSON as specified."

            response = await client.chat.completions.create(
                model=model_name or config.AI_MODEL or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or ""
            cleaned = cls._clean_json_response(raw)
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"OpenAI API analysis failed: {e}")
            return None

    @classmethod
    async def analyze_resume(
        cls,
        resume_text: str,
        jd_text: str,
        resume_name: str = "Resume.pdf",
        resume_id: int = 1
    ) -> AnalysisResult:
        result_dict: Optional[Dict[str, Any]] = None

        # Check if AI key is configured
        if config.has_ai_key():
            provider = config.AI_PROVIDER
            api_key = config.AI_API_KEY

            # Auto-detect provider if needed
            if provider == "auto":
                if api_key.startswith("AIza"):
                    provider = "gemini"
                elif api_key.startswith("sk-") or "openai" in config.AI_BASE_URL:
                    provider = "openai"
                elif "gemini" in config.AI_MODEL.lower():
                    provider = "gemini"
                else:
                    provider = "openai"

            try:
                if provider == "gemini":
                    result_dict = await cls._analyze_with_gemini(resume_text, jd_text, config.AI_MODEL)
                else:
                    result_dict = await cls._analyze_with_openai(resume_text, jd_text, config.AI_MODEL)
            except Exception as e:
                logger.error(f"AI Provider ({provider}) analysis failed: {e}")

        # If LLM returned structured output, parse and validate
        if result_dict:
            try:
                # Fill missing keys if any
                bd_raw = result_dict.get("breakdown", {})
                breakdown = ScoreBreakdown(
                    required_skills_pct=float(bd_raw.get("required_skills_pct", 80.0)),
                    preferred_skills_pct=float(bd_raw.get("preferred_skills_pct", 70.0)),
                    experience_pct=float(bd_raw.get("experience_pct", 75.0)),
                    education_pct=float(bd_raw.get("education_pct", 90.0)),
                    keywords_pct=float(bd_raw.get("keywords_pct", 75.0)),
                )
                score = float(result_dict.get("score", breakdown.calculate_final_score()))
                verdict, emoji, subtitle = compute_verdict(score)

                # Format required skills
                req_s = result_dict.get("required_skills", {})
                pref_s = result_dict.get("preferred_skills", {})
                req_obj = SkillMatchGroup(
                    matched=req_s.get("matched", []),
                    missing=req_s.get("missing", []),
                    partial=req_s.get("partial", [])
                )
                pref_obj = SkillMatchGroup(
                    matched=pref_s.get("matched", []),
                    missing=pref_s.get("missing", []),
                    partial=pref_s.get("partial", [])
                )

                # Format courses with verified links
                missing_all = req_obj.missing + pref_obj.missing
                recommended_courses = course_service.get_courses_for_skills(missing_all, max_courses=3)
                course_objs = [CourseRec(**c) for c in recommended_courses]

                # Format biggest gap
                bg_raw = result_dict.get("biggest_gap", {})
                biggest_gap_skill = bg_raw.get("skill", missing_all[0] if missing_all else "Cloud & Deployment")
                bg_obj = BiggestGap(
                    skill=biggest_gap_skill,
                    priority=bg_raw.get("priority", "HIGH"),
                    reason=bg_raw.get("reason", f"The JD specifically requires {biggest_gap_skill}, but your resume lacks direct evidence."),
                    how_to_fix=bg_raw.get("how_to_fix", f"Build a project deploying with {biggest_gap_skill} and add measurable outcomes to your resume."),
                    course=recommended_courses[0] if recommended_courses else None
                )

                # Roast
                roast_raw = result_dict.get("roast", {})
                roast_obj = WeakBullet(
                    original=roast_raw.get("original", "Worked on machine learning projects."),
                    problem=roast_raw.get("problem", "Too vague / gives 'I did something, trust me' vibe"),
                    improved=roast_raw.get("improved", "Built and deployed end-to-end ML classification pipelines with Scikit-learn and Python, achieving 92% accuracy."),
                    why_better=roast_raw.get("why_better", ["Specific technology stack", "Shows what you actually did", "Clear measurable outcome"])
                )

                # Recruiter POV
                rec_raw = result_dict.get("recruiter_pov", {})
                rec_obj = RecruiterPOV(
                    first_impression=rec_raw.get("first_impression", "Solid technical stack alignment."),
                    then=rec_raw.get("then", "Relevant project experience."),
                    concerns=rec_raw.get("concerns", "Could show more explicit measurable impact and deployment receipts."),
                    takeaway=rec_raw.get("takeaway", "Good overall match. Polish bullet specificity.")
                )

                # Receipts
                receipts_raw = result_dict.get("receipts", [])
                receipt_objs = []
                for r in receipts_raw[:6]:
                    receipt_objs.append(ReceiptItem(
                        skill=r.get("skill", "Tech Skill"),
                        status=r.get("status", "MATCHED"),
                        evidence=r.get("evidence", "Found in projects."),
                        source_location=r.get("source_location", "Resume"),
                        confidence=r.get("confidence", "HIGH")
                    ))

                # Cap checks
                cap_raw = result_dict.get("cap_checks", [])
                cap_objs = []
                for c in cap_raw[:2]:
                    cap_objs.append(CapCheckItem(
                        claim=c.get("claim", "Skill Claim"),
                        evidence_found=c.get("evidence_found", []),
                        gaps_found=c.get("gaps_found", []),
                        verdict=c.get("verdict", "✅ Legit receipts!"),
                        suggestion=c.get("suggestion", "Keep highlighted.")
                    ))

                # Skill DNA
                dna_raw = result_dict.get("skill_dna", [])
                dna_objs = [SkillDNACategory(**d) for d in dna_raw] if dna_raw else []

                return AnalysisResult(
                    resume_id=resume_id,
                    resume_name=resume_name,
                    score=score,
                    verdict=result_dict.get("verdict", verdict),
                    verdict_emoji=result_dict.get("verdict_emoji", emoji),
                    verdict_subtitle=result_dict.get("verdict_subtitle", subtitle),
                    breakdown=breakdown,
                    required_skills=req_obj,
                    preferred_skills=pref_obj,
                    experience_match=ExperienceMatch(**result_dict.get("experience_match", {})),
                    education_match=EducationMatch(**result_dict.get("education_match", {})),
                    keyword_match=KeywordMatchGroup(**result_dict.get("keyword_match", {})),
                    what_now=result_dict.get("what_now", "Your core skills are strong. Tackle your biggest gaps first before polishing minor bullets."),
                    application_ready=bool(result_dict.get("application_ready", score >= 7.0)),
                    application_ready_text=result_dict.get("application_ready_text", "YES 🔥" if score >= 7.0 else "NO 💀"),
                    application_ready_reason=result_dict.get("application_ready_reason", "Your resume covers the core requirements well enough to move forward."),
                    biggest_gap=bg_obj,
                    courses=course_objs,
                    roast=roast_obj,
                    recruiter_pov=rec_obj,
                    receipts=receipt_objs,
                    weak_bullets=[roast_obj],
                    cap_checks=cap_objs,
                    skill_dna=dna_objs
                )
            except Exception as parse_err:
                logger.error(f"Error parsing AI output: {parse_err}. Falling back to LocalAnalyzer.")

        # Seamless Fallback to LocalAnalyzer
        logger.info("Using LocalAnalyzer for deterministic NLP evaluation.")
        return LocalAnalyzer.analyze(resume_text, jd_text, resume_name=resume_name, resume_id=resume_id)
