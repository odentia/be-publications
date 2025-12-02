from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .config import settings
from ..domain.repositories import PostRepository
from ..repo.sql.repositories import SQLAlchemyPostRepository
from ..domain.services import PostService
from ..mq.publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

async def get_post_repository(
    db: AsyncSession = Depends(get_db)
) -> AsyncGenerator[PostRepository, None]:
    yield SQLAlchemyPostRepository(db)

async def get_event_publisher() -> AsyncGenerator[EventPublisher, None]:
    publisher = EventPublisher()
    try:
        await publisher.connect()
        yield publisher
    finally:
        await publisher.close()

async def get_post_service(
    post_repo: PostRepository = Depends(get_post_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> AsyncGenerator[PostService, None]:
    yield PostService(post_repo, event_publisher)