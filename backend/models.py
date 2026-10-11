from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
now = datetime.utcnow
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(80), default="Learner")
    goals: Mapped[list] = mapped_column(JSON, default=list)
    thresholds: Mapped[dict] = mapped_column(JSON, default=lambda: {"weak": 50, "strong": 75})
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
class Question(Base):  # assessment question bank persisted for reference/auditing
    __tablename__ = "assessment_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(60)); difficulty: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text); options: Mapped[list] = mapped_column(JSON); correct: Mapped[int] = mapped_column(Integer)
class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
    accuracy: Mapped[float] = mapped_column(Float); correct: Mapped[int] = mapped_column(Integer); total: Mapped[int] = mapped_column(Integer)
    topic_scores: Mapped[dict] = mapped_column(JSON); answers: Mapped[list] = mapped_column(JSON)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
class Competency(Base):
    __tablename__ = "competency_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(60)); score: Mapped[float] = mapped_column(Float)
    updated: Mapped[datetime] = mapped_column(DateTime, default=now)
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(200)); stored_name: Mapped[str] = mapped_column(String(80))  # never exposed
    pages: Mapped[list] = mapped_column(JSON); topics: Mapped[list] = mapped_column(JSON)
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    topic: Mapped[str] = mapped_column(String(60)); difficulty: Mapped[str] = mapped_column(String(10))
    questions: Mapped[list] = mapped_column(JSON)  # includes answer keys: server side only
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    score: Mapped[int] = mapped_column(Integer); total: Mapped[int] = mapped_column(Integer); accuracy: Mapped[float] = mapped_column(Float)
    topic: Mapped[str] = mapped_column(String(60)); created: Mapped[datetime] = mapped_column(DateTime, default=now)
class Activity(Base):
    __tablename__ = "learning_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(60)); kind: Mapped[str] = mapped_column(String(20))
    minutes: Mapped[int] = mapped_column(Integer, default=0); detail: Mapped[str] = mapped_column(String(200), default="")
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
class CourseRec(Base):
    __tablename__ = "course_recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(60)); title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="recommended"); created: Mapped[datetime] = mapped_column(DateTime, default=now)
