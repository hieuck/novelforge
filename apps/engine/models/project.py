from db.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    language = Column(String, nullable=False, default="vi")
    style_guide = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    daily_goal = Column(Integer, nullable=False, default=500)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
