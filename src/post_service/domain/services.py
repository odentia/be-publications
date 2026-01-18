from typing import List, Optional
from .models import Post
from .repositories import PostRepository
from .events import PostPublishedEvent, PostCreatedEvent, PostDeletedEvent, PostViewedEvent
from ..mq.publisher import EventPublisher


class PostService:
    def __init__(self, post_repo: PostRepository, event_publisher: Optional[EventPublisher] = None):
        self.post_repo = post_repo
        self.event_publisher = event_publisher

    async def create_post(self, title: str, description: Optional[str], page: dict,
                          author_id: str, author_username: Optional[str] = None,
                          game: Optional[str] = None, tags: List[str] = None) -> Post:
        post = Post(
            title=title,
            description=description,
            page=page,
            author_id=author_id,
            game=game,
            tags=tags or []
        )

        saved_post = await self.post_repo.save(post)

        # Публикуем событие создания поста
        if self.event_publisher:
            await self.event_publisher.publish(
                PostCreatedEvent(
                    post_id=saved_post.id,
                    author_id=author_id,
                    author_username=author_username,
                    title=title
                )
            )

        return saved_post

    async def publish_post(self, post_id: str, author_id: str, author_username: Optional[str] = None) -> Optional[Post]:
        post = await self.post_repo.find_by_id(post_id)

        if not post or post.author_id != author_id:
            return None

        post.publish()
        updated_post = await self.post_repo.save(post)

        # Публикуем событие публикации поста
        if self.event_publisher:
            await self.event_publisher.publish(
                PostPublishedEvent(
                    post_id=post_id,
                    author_id=author_id,
                    author_username=author_username or "unknown",
                    title=post.title,
                    published_at=updated_post.published_at.isoformat()
                )
            )

        return updated_post

    async def view_post(self, post_id: str) -> Optional[Post]:
        post = await self.post_repo.find_by_id(post_id)

        if not post or post.status != "published":
            return None

        await self.post_repo.increment_view_count(post_id)

        # Публикуем событие просмотра поста
        if self.event_publisher:
            await self.event_publisher.publish(
                PostViewedEvent(
                    post_id=post_id,
                    author_id=post.author_id
                )
            )

        return post

    async def update_post_stats(self, post_id: str, like_count: int = None,
                                comment_count: int = None) -> Optional[Post]:
        post = await self.post_repo.find_by_id(post_id)

        if not post:
            return None

        if like_count is not None:
            post.update_like_count(like_count)

        if comment_count is not None:
            post.update_comment_count(comment_count)

        return await self.post_repo.save(post)