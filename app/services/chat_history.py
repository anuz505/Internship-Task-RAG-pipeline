import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import redis.asyncio as redis

from app.models.schemas import ChatMessage
from app.config import settings
from app.logger import logger


class ChatMemoryService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = settings.chat_memory_ttl
        self.max_messages = settings.max_messages_per_session

    def get_session_key(self, session_id: UUID) -> str:
        return f"chat:session:{session_id}"

    async def add_message(self, session_id: UUID, role: str, content: str) -> None:
        key = self.get_session_key(session_id=session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.redis.rpush(key, json.dumps(message))

        await self.redis.ltrim(key, -self.max_messages, -1)

        await self.redis.expire(key, self.ttl)

        logger.debug(f"Added {role} message to sesion {session_id}")

    async def get_messages(self, session_id: UUID) -> List[ChatMessage]:
        key = self.get_session_key(session_id=session_id)

        messages_data = await self.redis.lrange(key, 0, -1)

        messages = []

        for msg_data in messages_data:
            msg_dict = json.loads(msg_data)
            messages.append(
                ChatMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"]),
                )
            )
        logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages

    async def get_recent_messages(
        self, session_id: UUID, count: int = 10
    ) -> List[ChatMessage]:
        key = self.get_session_key(session_id=session_id)

        messages_data = await self.redis.lrange(key, -count, -1)

        messages = []

        for msg_data in messages_data:
            msg_dict = json.loads(msg_data)
            messages.append(
                ChatMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"]),
                )
            )
        logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages

    async def clear_session(self, session_id: UUID) -> None:
        key = self.get_session_key(session_id=session_id)
        await self.redis.delete(key)
        logger.info(f"cleared chat session{session_id}")

    async def session_exists(self, session_id: UUID) -> bool:
        key = self.get_session_key(session_id=session_id)
        exists = await self.redis.exists(key)
        return bool(exists)

    async def extend_session_ttl(self, session_id: UUID) -> None:

        key = self._get_session_key(session_id)
        await self.redis.expire(key, self.ttl)


_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )
        logger.info("Connected to Redis")

    return _redis_client


async def close_redis_client() -> None:
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Closed Redis connection")


async def get_chat_memory() -> ChatMemoryService:
    redis_client = await get_redis_client()
    return ChatMemoryService(redis_client)
