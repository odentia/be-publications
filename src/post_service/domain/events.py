from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PostEvent(BaseModel):
    event_type: str
    timestamp: datetime = datetime.utcnow()
    service: str = "posts-service"

class PostCreatedEvent(PostEvent):
    event_type: str = "post_created"
    post_id: str
    author_id: str
    author_username: str
    title: str

class PostPublishedEvent(PostEvent):
    event_type: str = "post_published"
    post_id: str
    author_id: str
    author_username: str
    title: str
    published_at: str

class PostDeletedEvent(PostEvent):
    event_type: str = "post_deleted"
    post_id: str
    author_id: str

class PostViewedEvent(PostEvent):
    event_type: str = "post_viewed"
    post_id: str
    author_id: str

# События от других сервисов
class PostLikesUpdatedEvent(PostEvent):
    event_type: str = "post_likes_updated"
    post_id: str
    like_count: int

class PostCommentsUpdatedEvent(PostEvent):
    event_type: str = "post_comments_updated"
    post_id: str
    comment_count: int