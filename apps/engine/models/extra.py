from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, func

from db.base import Base


class Settings(Base):
    __tablename__ = "settings"
    id = Column(String, primary_key=True, default="app-settings")
    project_id = Column(String, nullable=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    is_secret = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AppSettings(Base):
    __tablename__ = "app_settings"
    id = Column(String, primary_key=True, default="app-settings")
    active = Column(Boolean, nullable=False, default=True, index=True)
    provider = Column(String, nullable=False, default="ollama")
    base_url = Column(String, nullable=False, default="http://localhost:11434")
    api_key = Column(String, nullable=True)
    model = Column(String, nullable=False, default="llama3.1:8b")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=2048)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Character(Base):
    __tablename__ = "characters"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
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
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Lore(Base):
    __tablename__ = "lore"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
    lore_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    related_chapters = Column(Text, nullable=True)
    related_characters = Column(Text, nullable=True)
    meta_data = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class TimelineItem(Base):
    __tablename__ = "timeline"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    event_date = Column(String, nullable=True)
    relative_order = Column(String, nullable=True)
    involved_characters = Column(Text, nullable=True)
    related_chapters = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    meta_data = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    kind = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    params = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
