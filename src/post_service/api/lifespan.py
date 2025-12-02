from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from ..core.db import init_db, close_db
from ..mq.consumer import EventConsumer
from ..mq.publisher import EventPublisher

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Posts Service...")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize event publisher
        """publisher = EventPublisher()
        await publisher.connect()
        app.state.event_publisher = publisher
        logger.info("Event publisher initialized successfully")

        # Initialize event consumer (if needed)
        # consumer = EventConsumer()
        # await consumer.start()  # Run in background task if needed
"""
        logger.info("Posts Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start Posts Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Posts Service...")

    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")

        # Close event publisher
        if hasattr(app.state, 'event_publisher'):
            await app.state.event_publisher.close()
            logger.info("Event publisher closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Posts Service shutdown completed")