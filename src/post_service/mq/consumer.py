import json
import logging
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from typing import Dict, Callable, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(self):
        self.connection: AbstractRobustConnection = None
        self.channel: aio_pika.abc.AbstractChannel = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()

            await self.channel.set_qos(prefetch_count=10)

            logger.info("Event consumer connected to RabbitMQ successfully")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        self.handlers[event_type] = handler
        logger.debug(f"Handler registered for event type: {event_type}")

    async def start_consuming(self, queue_name: str = "posts_events"):
        if not self.channel:
            await self.connect()

        exchange = await self.channel.declare_exchange(
            "blog_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dead_letters",
                "x-dead-letter-routing-key": "posts_events_dl"
            }
        )

        await queue.bind(exchange, "posts.*")
        await queue.bind(exchange, "likes.updated")
        await queue.bind(exchange, "comments.updated")
        
        # Также биндим на возможные варианты от других сервисов
        await queue.bind(exchange, "likes.post_likes_updated")
        await queue.bind(exchange, "comments.post_comments_updated")

        logger.info(f"Started consuming from queue: {queue_name}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        event_data = json.loads(message.body.decode())
                        routing_key = message.routing_key or ""
                        
                        # Определяем тип события по routing_key или по event_type в теле сообщения
                        if routing_key.startswith("posts."):
                            event_type = event_data.get("event_type")
                        elif routing_key == "likes.updated":
                            event_type = "post_likes_updated"
                        elif routing_key == "comments.updated":
                            event_type = "post_comments_updated"
                        else:
                            event_type = event_data.get("event_type")

                        if event_type and event_type in self.handlers:
                            await self.handlers[event_type](event_data)
                            logger.debug(f"Event processed: {event_type} (routing_key: {routing_key})")
                        else:
                            logger.warning(f"No handler for event type: {event_type} (routing_key: {routing_key})")

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Message will be rejected and go to DLQ

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Event consumer connection closed")