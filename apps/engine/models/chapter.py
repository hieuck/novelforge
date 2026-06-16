from db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="draft")
    word_count = Column(Integer, nullable=False, default=0)
    scene_order = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    illustration_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships populates later when needed.
