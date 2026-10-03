import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ResumeDoc:
    id: int
    filename: str
    text: str
    char_count: int
    uploaded_at: float = field(default_factory=time.time)


@dataclass
class JobDescriptionDoc:
    text: str
    source_type: str  # "text" or "file"
    filename: Optional[str] = None
    char_count: int = 0
    uploaded_at: float = field(default_factory=time.time)


@dataclass
class UserSession:
    user_id: int
    resumes: List[ResumeDoc] = field(default_factory=list)
    jd: Optional[JobDescriptionDoc] = None
    results: Dict[int, Any] = field(default_factory=dict)  # resume_id -> AnalysisResult
    current_resume_id: Optional[int] = None
    active_view: str = "main"  # "main", "score", "roast", "gap", "receipts", "recruiter", "glowup", "dna", "cap"
    vibe: str = "genz"  # "genz", "clean", "spicy"
    last_action_time: float = field(default_factory=time.time)

    def add_resume(self, filename: str, text: str) -> ResumeDoc:
        resume_id = len(self.resumes) + 1
        doc = ResumeDoc(
            id=resume_id,
            filename=filename,
            text=text,
            char_count=len(text)
        )
        self.resumes.append(doc)
        self.current_resume_id = resume_id
        self.last_action_time = time.time()
        return doc

    def set_jd(self, text: str, source_type: str = "text", filename: Optional[str] = None) -> JobDescriptionDoc:
        self.jd = JobDescriptionDoc(
            text=text,
            source_type=source_type,
            filename=filename,
            char_count=len(text)
        )
        self.last_action_time = time.time()
        return self.jd

    def get_current_resume(self) -> Optional[ResumeDoc]:
        if not self.resumes:
            return None
        if self.current_resume_id is not None:
            for r in self.resumes:
                if r.id == self.current_resume_id:
                    return r
        return self.resumes[0]

    def get_current_result(self) -> Optional[Any]:
        curr = self.get_current_resume()
        if curr and curr.id in self.results:
            return self.results[curr.id]
        if self.results:
            return next(iter(self.results.values()))
        return None

    def clear(self):
        self.resumes.clear()
        self.jd = None
        self.results.clear()
        self.current_resume_id = None
        self.active_view = "main"
        self.last_action_time = time.time()


class SessionManager:
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get_session(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
        self._sessions[user_id].last_action_time = time.time()
        return self._sessions[user_id]

    def reset_session(self, user_id: int) -> UserSession:
        session = self.get_session(user_id)
        session.clear()
        return session


session_manager = SessionManager()
