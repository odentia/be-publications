from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    status = Column(String(20), default="draft")  # draft, published, archived
    tags = Column(JSON, default=list)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)  # Синхронизируется с comments-service
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)

    def publish(self):
        self.status = "published"
        self.published_at = datetime.utcnow()

    def increment_view_count(self):
        self.view_count += 1

    def update_like_count(self, count: int):
        self.like_count = count

    def update_comment_count(self, count: int):
        self.comment_count = count