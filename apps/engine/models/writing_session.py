"""Writing session model for daily word-count tracking."""

from __future__ import annotations

from db.base import Base
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func


class WritingSession(Base):
    __tablename__ = "writing_sessions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    words_added = Column(Integer, nullable=False, default=0)
    words_total = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
