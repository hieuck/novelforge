from sqlalchemy import Column, String, Text, DateTime, func

from db.base import Base


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    prompt = Column(Text, nullable=True)
    entity_type = Column(String, nullable=True)  # 'character', 'chapter', 'scene'
    entity_id = Column(String, nullable=True, index=True)
    mime = Column(String, nullable=True)
    file_size = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
