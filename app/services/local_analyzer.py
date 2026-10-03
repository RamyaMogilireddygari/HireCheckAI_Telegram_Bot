import re
from typing import List, Dict, Set, Tuple, Any
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
from app.services.courses import course_service

# Tech skill synonyms dictionary
TECH_SYNONYMS = {
    "javascript": ["js", "ecmascript", "javascript"],
    "typescript": ["ts", "typescript"],
    "postgresql": ["postgres", "postgresql", "psql"],
    "machine learning": ["ml", "machine learning", "supervised learning", "unsupervised learning"],
    "deep learning": ["dl", "deep learning", "neural networks", "cnn", "rnn", "transformers"],
    "natural language processing": ["nlp", "natural language processing", "text processing", "tokenization"],
    "amazon web services": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "google cloud platform": ["gcp", "google cloud", "google cloud platform", "bigquery"],
    "microsoft azure": ["azure", "microsoft azure"],
    "react": ["react", "react.js", "reactjs"],
    "next.js": ["next.js", "nextjs", "next js"],
    "node.js": ["node", "node.js", "nodejs"],
    "fastapi": ["fastapi", "fast-api"],
    "docker": ["docker", "containerization", "containers", "dockerfile"],
    "kubernetes": ["k8s", "kubernetes"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "github actions", "gitlab ci", "jenkins"],
    "sql": ["sql", "mysql", "sqlite", "relational database"],
    "mongodb": ["mongodb", "mongo", "nosql", "document database"],
    "redis": ["redis", "caching", "in-memory"],
    "rest apis": ["rest", "restful", "rest api", "rest apis", "api development", "api", "apis"],
    "graphql": ["graphql", "apollo"],
    "system design": ["system design", "distributed systems", "microservices", "architecture"],
    "git": ["git", "github", "gitlab", "version control"],
    "python": ["python", "python3", "py"],
    "pandas": ["pandas", "dataframe"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf", "keras"],
}

# Common tech skills catalog for detection
COMMON_TECH_SKILLS = list(TECH_SYNONYMS.keys()) + [
    "html", "css", "tailwind", "sass", "vue", "angular", "svelte",
    "flask", "django", "express", "spring boot", "java", "c++", "c#", "golang", "go", "rust",
    "kafka", "rabbitmq", "spark", "hadoop", "airflow",
    "linux", "bash", "terraform", "ansible",
    "testing", "pytest", "jest", "unit testing", "agile", "scrum"
]


class LocalAnalyzer:
    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^\w\s]", " ", text.lower())

    @classmethod
    def _extract_skills_from_text(cls, text: str) -> List[str]:
        found_skills: Set[str] = set()
        norm_text = f" {cls._normalize(text)} "

        for canonical, synonyms in TECH_SYNONYMS.items():
            for syn in synonyms:
                pattern = r"(?:\b|_)" + re.escape(syn) + r"(?:\b|_)"
                if re.search(pattern, norm_text):
                    found_skills.add(canonical.title() if len(canonical) > 3 else canonical.upper())
                    break

        for skill in COMMON_TECH_SKILLS:
            pattern = r"(?:\b|_)" + re.escape(skill) + r"(?:\b|_)"
            if re.search(pattern, norm_text):
                found_skills.add(skill.title() if len(skill) > 3 else skill.upper())

        return sorted(list(found_skills))

    @classmethod
    def _extract_jd_sections(cls, jd_text: str) -> Tuple[List[str], List[str], List[str]]:
        lines = jd_text.split("\n")
        required_text = []
        preferred_text = []
        general_text = []

        current_mode = "general"
        for line in lines:
            lower_line = line.lower()
            if any(k in lower_line for k in ["required", "must have", "minimum qualifications", "requirements", "what you need", "what you'll need"]):
                current_mode = "required"
            elif any(k in lower_line for k in ["preferred", "nice to have", "bonus", "plus", "good to have", "desired"]):
                current_mode = "preferred"
            elif any(k in lower_line for k in ["responsibilities", "about the role", "what you will do", "overview"]):
                current_mode = "general"

            if current_mode == "required":
                required_text.append(line)
            elif current_mode == "preferred":
                preferred_text.append(line)
            else:
                general_text.append(line)

        req_skills = cls._extract_skills_from_text("\n".join(required_text))
        pref_skills = cls._extract_skills_from_text("\n".join(preferred_text))
        all_skills = cls._extract_skills_from_text(jd_text)

        # Fallback if JD didn't explicitly separate sections
        if not req_skills and not pref_skills:
            if len(all_skills) >= 4:
                req_skills = all_skills[: len(all_skills) * 2 // 3]
                pref_skills = all_skills[len(all_skills) * 2 // 3 :]
            else:
                req_skills = all_skills
                pref_skills = []

        return req_skills, pref_skills, all_skills

    @classmethod
    def _find_evidence_in_resume(cls, skill: str, resume_text: str) -> Tuple[str, str, str]:
        # Return status, snippet, confidence
        skill_lower = skill.lower()
        synonyms = TECH_SYNONYMS.get(skill_lower, [skill_lower])

        for line in resume_text.split("\n"):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 15:
                continue
            line_lower = line_clean.lower()
            for syn in synonyms:
                pattern = r"(?:\b|_)" + re.escape(syn) + r"(?:\b|_)"
                if re.search(pattern, line_lower):
                    return "MATCHED", line_clean, "HIGH"

        # Check for related skills
        if skill_lower in ["aws", "gcp", "azure"] and "cloud" in resume_text.lower():
            return "PARTIAL", "Resume mentions general cloud technologies, but specific provider lacks direct project receipts.", "MEDIUM"
        if skill_lower in ["fastapi", "flask", "django"] and any(k in resume_text.lower() for k in ["api", "rest", "backend"]):
            return "PARTIAL", "Resume mentions backend/API work, showing transferable capability.", "MEDIUM"
        if skill_lower in ["docker", "kubernetes"] and "deployment" in resume_text.lower():
            return "PARTIAL", "Resume mentions deployment experience, but container orchestration is not explicitly confirmed.", "LOW"

        return "MISSING", "No direct receipts or specific technology mentions found in the resume.", "LOW"

    @classmethod
    def _extract_weak_bullet(cls, resume_text: str) -> WeakBullet:
        # Find candidate bullet points
        lines = resume_text.split("\n")
        candidates = []
        for line in lines:
            clean = line.strip()
            if len(clean) > 20 and len(clean) < 150:
                if any(clean.startswith(b) for b in ["•", "-", "*", "–", "—"]) or any(clean.lower().startswith(v) for v in ["worked", "built", "created", "developed", "managed", "helped", "assisted", "responsible for"]):
                    # Remove bullet symbol
                    content = re.sub(r"^[\s•\-*–—]+", "", clean).strip()
                    has_metrics = bool(re.search(r"\d+%|\d+x|\$\d+|\d+\s*users|\d+\s*ms", content))
                    if not has_metrics and len(content) > 20:
                        candidates.append(content)

        if candidates:
            # Pick a representative candidate
            chosen = candidates[0]
            # Formulate improved version without inventing fake numbers
            improved = f"Engineered {chosen.lower() if not chosen.startswith(('Built', 'Developed', 'Engineered')) else chosen}, focusing on modular architecture, performance optimization, and reliable delivery."
            if "website" in chosen.lower() or "app" in chosen.lower() or "project" in chosen.lower():
                improved = re.sub(r"(?i)\bcreated a website\b", "Architected and deployed a responsive web platform with modular components", chosen)
                improved = re.sub(r"(?i)\bworked on\b", "Engineered and shipped", improved)
                if not improved.endswith("."):
                    improved += ", improving modularity and user experience."
            return WeakBullet(
                original=chosen,
                problem="Too vague / lacks specific impact and active technical framing",
                improved=improved,
                why_better=[
                    "Strong action verbs (Architected / Engineered)",
                    "Highlights technical depth and modular design",
                    "Clear outcome and professional framing"
                ]
            )

        return WeakBullet(
            original="Worked on machine learning and software projects.",
            problem="Too vague / gives 'I did something, trust me' vibe",
            improved="Engineered end-to-end ML classification pipelines with Scikit-learn and Python, establishing structured data preprocessing and validation workflows.",
            why_better=[
                "Specific technology stack",
                "Demonstrates end-to-end execution",
                "Clear engineering rigor"
            ]
        )

    @classmethod
    def analyze(cls, resume_text: str, jd_text: str, resume_name: str = "Resume.pdf", resume_id: int = 1) -> AnalysisResult:
        req_skills, pref_skills, all_jd_skills = cls._extract_jd_sections(jd_text)

        matched_req = []
        missing_req = []
        partial_req = []
        receipts: List[ReceiptItem] = []

        for skill in req_skills:
            status, snippet, conf = cls._find_evidence_in_resume(skill, resume_text)
            if status == "MATCHED":
                matched_req.append(skill)
                receipts.append(ReceiptItem(skill=skill, status="MATCHED", evidence=snippet, confidence=conf))
            elif status == "PARTIAL":
                partial_req.append(skill)
                receipts.append(ReceiptItem(skill=skill, status="PARTIAL", evidence=snippet, confidence=conf))
            else:
                missing_req.append(skill)
                receipts.append(ReceiptItem(skill=skill, status="MISSING", evidence=snippet, confidence=conf))

        matched_pref = []
        missing_pref = []
        partial_pref = []

        for skill in pref_skills:
            status, snippet, conf = cls._find_evidence_in_resume(skill, resume_text)
            if status == "MATCHED":
                matched_pref.append(skill)
            elif status == "PARTIAL":
                partial_pref.append(skill)
            else:
                missing_pref.append(skill)

        # Calculate percentages
        total_req = max(1, len(req_skills))
        req_score = min(100.0, ((len(matched_req) * 1.0 + len(partial_req) * 0.5) / total_req) * 100.0)

        total_pref = max(1, len(pref_skills)) if pref_skills else 1
        pref_score = min(100.0, ((len(matched_pref) * 1.0 + len(partial_pref) * 0.5) / total_pref) * 100.0) if pref_skills else 80.0

        # Experience check
        exp_score = 75.0
        exp_strengths = []
        exp_gaps = []
        resume_lower = resume_text.lower()
        if any(w in resume_lower for w in ["senior", "lead", "staff", "3+ years", "5+ years", "architect"]):
            exp_score = 90.0
            exp_strengths.append("Demonstrated solid track record and mid/senior engineering context.")
        elif any(w in resume_lower for w in ["intern", "student", "fresher", "entry level", "graduate"]):
            exp_score = 70.0
            exp_strengths.append("Foundational project and internship experience.")
            exp_gaps.append("Production-scale deployment and long-term maintenance exposure.")
        else:
            exp_score = 80.0
            exp_strengths.append("Practical hands-on technical project history.")

        # Education check
        edu_score = 90.0
        edu_summary = "Relevant degree/technical education matches baseline qualification."
        if any(deg in resume_lower for deg in ["b.tech", "b.e", "b.s", "computer science", "engineering", "m.s", "m.tech", "bachelor", "master"]):
            edu_score = 95.0
            edu_summary = "Degree in Computer Science / STEM strongly aligns with requirements."

        # Keyword match
        all_missing = missing_req + missing_pref
        all_matched = matched_req + matched_pref
        keyword_score = max(50.0, min(100.0, (len(all_matched) / max(1, len(all_matched) + len(all_missing))) * 100.0))

        breakdown = ScoreBreakdown(
            required_skills_pct=round(req_score, 1),
            preferred_skills_pct=round(pref_score, 1),
            experience_pct=round(exp_score, 1),
            education_pct=round(edu_score, 1),
            keywords_pct=round(keyword_score, 1)
        )

        final_score = breakdown.calculate_final_score()
        verdict, emoji, subtitle = compute_verdict(final_score)

        # Biggest Gap
        biggest_gap_skill = missing_req[0] if missing_req else (missing_pref[0] if missing_pref else "Advanced System Architecture")
        courses_raw = course_service.get_courses_for_skills([biggest_gap_skill] + missing_req + missing_pref, max_courses=3)
        course_objs = [CourseRec(**c) for c in courses_raw]

        biggest_gap = BiggestGap(
            skill=biggest_gap_skill,
            priority="HIGH" if biggest_gap_skill in missing_req else "MEDIUM",
            reason=f"The JD emphasizes {biggest_gap_skill}, but your resume doesn't show verified receipts or project execution yet.",
            how_to_fix=f"Build one focused mini-project with {biggest_gap_skill}, deploy it, and add bullet points showcasing hands-on execution.",
            course=courses_raw[0] if courses_raw else None
        )

        # What now recommendation
        if missing_req:
            top_missing = ", ".join(missing_req[:2])
            what_now = f"You're already solid on core foundations. Your primary gap is {top_missing}. Tackle those with a targeted project before applying."
        else:
            what_now = "Strong alignment with the job description! Polish your project impact bullets and submit your application with confidence."

        app_ready = final_score >= 7.0
        app_ready_text = "YES 🔥" if app_ready else "NO 💀"
        app_ready_reason = (
            "Your resume covers the core requirements well enough to move forward."
            if app_ready
            else "Important required technical foundations are missing. Fix the highlighted gaps first."
        )

        # Roast and Weak bullet
        weak_bullet = cls._extract_weak_bullet(resume_text)

        # Recruiter POV
        recruiter = RecruiterPOV(
            first_impression=f"Strong match on {matched_req[0] if matched_req else 'core technologies'} and clean project portfolio.",
            then=f"Demonstrates practical hands-on building capability.",
            concerns=f"Looking for more concrete production deployment experience ({biggest_gap_skill}).",
            takeaway="Strong technical capability. Needs clearer evidence of quantifiable business or system impact."
        )

        # Cap check
        cap_checks = [
            CapCheckItem(
                claim=f"Hands-on with {matched_req[0] if matched_req else 'Software Engineering'}",
                evidence_found=[f"Documented in resume projects with direct technical evidence."],
                gaps_found=[] if len(matched_req) > 2 else ["Could showcase broader system architecture."],
                verdict="✅ Legit receipts! No cap detected.",
                suggestion="Keep this highlighted at the top of your experience section."
            )
        ]
        if missing_req:
            cap_checks.append(
                CapCheckItem(
                    claim=f"Full-stack readiness for {biggest_gap_skill}",
                    evidence_found=[],
                    gaps_found=[f"No direct receipts found for {biggest_gap_skill} in project descriptions."],
                    verdict="🟡 Missing receipts 😭",
                    suggestion=f"Don't list {biggest_gap_skill} in skills without at least one tangible project bullet."
                )
            )

        # Skill DNA
        skill_dna = [
            SkillDNACategory(category="AI / ML", candidate_pct=90 if "Machine Learning" in all_matched or "Python" in all_matched else 40, jd_pct=85 if "Machine Learning" in all_jd_skills else 50),
            SkillDNACategory(category="Backend & APIs", candidate_pct=80 if any(k in all_matched for k in ["SQL", "Fastapi", "Rest Apis", "Node.Js", "Python"]) else 45, jd_pct=80),
            SkillDNACategory(category="Data & DBs", candidate_pct=85 if any(k in all_matched for k in ["SQL", "Postgresql", "Mongodb", "Pandas"]) else 50, jd_pct=75),
            SkillDNACategory(category="Cloud & DevOps", candidate_pct=30 if any(k in all_missing for k in ["Aws", "Docker", "Kubernetes", "Gcp"]) else 80, jd_pct=80),
            SkillDNACategory(category="Frontend / UI", candidate_pct=75 if any(k in all_matched for k in ["React", "Typescript", "Javascript", "Next.Js"]) else 40, jd_pct=60),
        ]

        return AnalysisResult(
            resume_id=resume_id,
            resume_name=resume_name,
            score=final_score,
            verdict=verdict,
            verdict_emoji=emoji,
            verdict_subtitle=subtitle,
            breakdown=breakdown,
            required_skills=SkillMatchGroup(matched=matched_req, missing=missing_req, partial=partial_req),
            preferred_skills=SkillMatchGroup(matched=matched_pref, missing=missing_pref, partial=partial_pref),
            experience_match=ExperienceMatch(summary=exp_strengths[0] if exp_strengths else "Good match", strengths=exp_strengths, gaps=exp_gaps, score_pct=exp_score),
            education_match=EducationMatch(summary=edu_summary, matched=True, score_pct=edu_score),
            keyword_match=KeywordMatchGroup(matched=all_matched, missing=all_missing, score_pct=keyword_score),
            what_now=what_now,
            application_ready=app_ready,
            application_ready_text=app_ready_text,
            application_ready_reason=app_ready_reason,
            biggest_gap=biggest_gap,
            courses=course_objs,
            roast=weak_bullet,
            recruiter_pov=recruiter,
            receipts=receipts[:6],
            weak_bullets=[weak_bullet],
            cap_checks=cap_checks,
            skill_dna=skill_dna
        )
