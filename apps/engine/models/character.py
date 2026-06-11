from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    role = Column(String, nullable=True)
    age = Column(String, nullable=True)
    personality = Column(Text, nullable=True)
    appearance = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    secrets = Column(Text, nullable=True)
    relationships = Column(Text, nullable=True)
    first_appearance = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
