import json
import logging
from typing import List, Dict, Any, Optional
from app.config import config

logger = logging.getLogger(__name__)


class CourseService:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._load_courses()

    def _load_courses(self):
        try:
            if config.COURSES_FILE.exists():
                with open(config.COURSES_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                logger.warning(f"Courses file not found at {config.COURSES_FILE}")
                self._data = {"skills": {}, "default_courses": []}
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            self._data = {"skills": {}, "default_courses": []}

    def get_courses_for_skills(self, missing_skills: List[str], max_courses: int = 3) -> List[Dict[str, str]]:
        skills_db = self._data.get("skills", {})
        default_courses = self._data.get("default_courses", [])
        recommended: List[Dict[str, str]] = []
        seen_titles = set()

        for skill in missing_skills:
            if len(recommended) >= max_courses:
                break
            skill_clean = skill.strip().lower()

            # Exact match
            matched_entry = None
            if skill_clean in skills_db:
                matched_entry = skills_db[skill_clean]
            else:
                # Substring or synonym match
                for key, val in skills_db.items():
                    if key in skill_clean or skill_clean in key:
                        matched_entry = val
                        break

            if matched_entry and matched_entry["title"] not in seen_titles:
                recommended.append({
                    "title": matched_entry["title"],
                    "url": matched_entry["url"],
                    "provider": matched_entry.get("provider", "Verified Academy"),
                    "reason": matched_entry.get("reason", f"Master core competencies in {skill}.")
                })
                seen_titles.add(matched_entry["title"])

        # If fewer than max_courses, fill with relevant default foundational courses
        if len(recommended) < max_courses:
            for course in default_courses:
                if len(recommended) >= max_courses:
                    break
                if course["title"] not in seen_titles:
                    recommended.append({
                        "title": course["title"],
                        "url": course["url"],
                        "provider": course.get("provider", "Industry Standard"),
                        "reason": course.get("reason", "Level up core software engineering and architecture skills.")
                    })
                    seen_titles.add(course["title"])

        return recommended[:max_courses]


course_service = CourseService()
