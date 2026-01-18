import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from ..core.db import init_db, close_db, AsyncSessionLocal
from ..mq.consumer import EventConsumer
from ..mq.publisher import EventPublisher
from ..domain.services import PostService
from ..repo.sql.repositories import SQLAlchemyPostRepository
from ..domain.events import PostLikesUpdatedEvent, PostCommentsUpdatedEvent

logger = logging.getLogger(__name__)


async def handle_likes_updated(event_data: dict):
    """Обработчик события обновления лайков"""
    try:
        # Может приходить как post_id, так и другие варианты
        post_id = event_data.get("post_id") or event_data.get("postId")
        like_count = event_data.get("like_count") or event_data.get("likeCount") or event_data.get("count")
        
        if not post_id or like_count is None:
            logger.warning(f"Invalid event data for likes_updated: {event_data}")
            return
        
        async with AsyncSessionLocal() as session:
            try:
                post_repo = SQLAlchemyPostRepository(session)
                # Создаем PostService без publisher, т.к. это обновление статистики от внешнего сервиса
                post_service = PostService(post_repo, None)
                
                result = await post_service.update_post_stats(post_id, like_count=int(like_count))
                if result:
                    await session.commit()
                    logger.info(f"Updated likes for post {post_id}: {like_count}")
                else:
                    logger.warning(f"Post {post_id} not found for likes update")
                    await session.rollback()
            except Exception as e:
                await session.rollback()
                raise
            
    except Exception as e:
        logger.error(f"Error handling likes_updated event: {e}")


async def handle_comments_updated(event_data: dict):
    """Обработчик события обновления комментариев"""
    try:
        # Может приходить как post_id, так и другие варианты
        post_id = event_data.get("post_id") or event_data.get("postId")
        comment_count = event_data.get("comment_count") or event_data.get("commentCount") or event_data.get("count")
        
        if not post_id or comment_count is None:
            logger.warning(f"Invalid event data for comments_updated: {event_data}")
            return
        
        async with AsyncSessionLocal() as session:
            try:
                post_repo = SQLAlchemyPostRepository(session)
                post_service = PostService(post_repo, None)
                
                result = await post_service.update_post_stats(post_id, comment_count=int(comment_count))
                if result:
                    await session.commit()
                    logger.info(f"Updated comments for post {post_id}: {comment_count}")
                else:
                    logger.warning(f"Post {post_id} not found for comments update")
                    await session.rollback()
            except Exception as e:
                await session.rollback()
                raise
            
    except Exception as e:
        logger.error(f"Error handling comments_updated event: {e}")


async def start_consumer(consumer: EventConsumer):
    """Запуск consumer в фоновом режиме"""
    try:
        await consumer.start_consuming()
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    except Exception as e:
        logger.error(f"Consumer error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Posts Service...")
    consumer_task = None

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize event publisher
        publisher = EventPublisher()
        await publisher.connect()
        app.state.event_publisher = publisher
        logger.info("Event publisher initialized successfully")

        # Initialize event consumer
        consumer = EventConsumer()
        await consumer.connect()
        
        # Регистрируем обработчики событий
        consumer.register_handler("post_likes_updated", handle_likes_updated)
        consumer.register_handler("post_comments_updated", handle_comments_updated)
        
        # Запускаем consumer в фоновой задаче
        consumer_task = asyncio.create_task(start_consumer(consumer))
        app.state.consumer = consumer
        app.state.consumer_task = consumer_task
        logger.info("Event consumer started successfully")

        logger.info("Posts Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start Posts Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Posts Service...")

    try:
        # Останавливаем consumer
        if hasattr(app.state, 'consumer_task') and app.state.consumer_task:
            app.state.consumer_task.cancel()
            try:
                await app.state.consumer_task
            except asyncio.CancelledError:
                pass
        
        if hasattr(app.state, 'consumer'):
            await app.state.consumer.close()
            logger.info("Event consumer closed")

        # Close event publisher
        if hasattr(app.state, 'event_publisher'):
            await app.state.event_publisher.close()
            logger.info("Event publisher closed")

        # Close database connections
        await close_db()
        logger.info("Database connections closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Posts Service shutdown completed")