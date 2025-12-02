from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import logging
from ...domain.models import Post
from ...domain.repositories import PostRepository
from ...core.exeptions import DatabaseError

logger = logging.getLogger(__name__)


class SQLAlchemyPostRepository(PostRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, post: Post) -> Post:
        try:
            self.session.add(post)
            await self.session.flush()
            await self.session.refresh(post)
            return post
        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            await self.session.rollback()
            raise DatabaseError(f"Failed to save post: {str(e)}")

    async def find_by_id(self, post_id: str) -> Optional[Post]:
        try:
            result = await self.session.execute(
                select(Post).where(Post.id == post_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to find post by id: {e}")
            raise DatabaseError(f"Failed to find post: {str(e)}")

    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            result = await self.session.execute(
                select(Post)
                .where(Post.user_id == user_id)
                .order_by(Post.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to find posts by user: {e}")
            raise DatabaseError(f"Failed to find posts: {str(e)}")

    async def find_published(self, skip: int = 0, limit: int = 100,
                             tags: List[str] = None) -> List[Post]:
        try:
            query = select(Post).where(
                Post.status == "published",
                Post.is_deleted == False
            )

            if tags:
                # Filter by tags (PostgreSQL JSONB array contains)
                query = query.where(Post.tags.contains(tags))

            result = await self.session.execute(
                query.order_by(Post.published_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to find published posts: {e}")
            raise DatabaseError(f"Failed to find posts: {str(e)}")

    async def find_popular(self, days: int = 7, limit: int = 10) -> List[Post]:
        try:
            # This would need a more complex query with view statistics
            # Simplified version for now
            result = await self.session.execute(
                select(Post)
                .where(
                    Post.status == "published",
                    Post.is_deleted == False
                )
                .order_by(Post.view_count.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to find popular posts: {e}")
            raise DatabaseError(f"Failed to find posts: {str(e)}")

    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            search_filter = or_(
                Post.title.ilike(f"%{query}%"),
                Post.content.ilike(f"%{query}%")
            )

            result = await self.session.execute(
                select(Post)
                .where(
                    search_filter,
                    Post.status == "published",
                    Post.is_deleted == False
                )
                .order_by(Post.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to search posts: {e}")
            raise DatabaseError(f"Failed to search posts: {str(e)}")

    async def delete(self, post_id: str) -> bool:
        try:
            result = await self.session.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(is_deleted=True)
            )
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete post: {str(e)}")

    async def increment_view_count(self, post_id: str) -> bool:
        try:
            result = await self.session.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(view_count=Post.view_count + 1)
            )
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to increment view count: {e}")
            await self.session.rollback()
            raise DatabaseError(f"Failed to update post: {str(e)}")