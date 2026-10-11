from pydantic import BaseModel, Field
from typing import Optional, List, Any
class Register(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(default="Learner", max_length=80)
    goals: List[str] = Field(default_factory=list, max_length=9)
class Login(BaseModel):
    email: str; password: str
class Answer(BaseModel):
    question_id: int; selected: Optional[int] = None; confidence: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
class AssessmentSubmit(BaseModel):
    answers: List[Answer] = Field(min_length=1, max_length=60)
class Thresholds(BaseModel):
    weak: float = Field(gt=0, le=100); strong: float = Field(gt=0, le=100)
class NotesReq(BaseModel):
    document_id: int
class QuizReq(BaseModel):
    document_id: Optional[int] = None; topic: str = "Any"
    n: int = Field(default=5, ge=1, le=15); difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    format: str = Field(default="mcq", pattern="^(mcq|tf|short|numeric|mixed)$")
class QuizSubmit(BaseModel):
    answers: dict  # {question_id(str): answer}
class MistakeReq(BaseModel):
    source: str = Field(pattern="^(assessment|quiz)$"); question_id: int; quiz_id: Optional[int] = None; selected: Any = None
class ActivityReq(BaseModel):
    topic: str; kind: str = Field(pattern="^(notes|example|practice|followup)$"); minutes: int = Field(default=10, ge=0, le=240)
class ChatReq(BaseModel):
    message: str = Field(min_length=1, max_length=1000); document_id: Optional[int] = None; history: List[dict] = Field(default_factory=list, max_length=12)
class CourseTrack(BaseModel):
    topic: str; title: str = Field(max_length=200)
class PracticeCheck(BaseModel):
    bank_id: int; selected: int
