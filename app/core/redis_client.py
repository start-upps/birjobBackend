import redis.asyncio as redis
from typing import Optional, Any
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            logger.info(f"Attempting to connect to Redis: {settings.REDIS_URL}")
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.error(f"Redis URL used: {settings.REDIS_URL}")
            logger.warning("Redis connection failed - continuing without cache")
            self.redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """Delete key"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return 0
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        return bool(await self.redis.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        return await self.redis.expire(key, seconds)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment key value"""
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return 0
        return await self.redis.incrby(key, amount)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON for key: {key}")
        return None
    
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """Set JSON value"""
        return await self.set(key, json.dumps(value), expire)
    
    async def get_device_keywords(self, device_id: str) -> list:
        """Get cached keywords for device"""
        key = f"device_keywords:{device_id}"
        keywords = await self.get_json(key)
        return keywords or []
    
    async def cache_device_keywords(self, device_id: str, keywords: list, expire: int = 3600):
        """Cache device keywords"""
        key = f"device_keywords:{device_id}"
        await self.set_json(key, keywords, expire)
    
    async def mark_job_processed(self, device_id: str, job_id: int, expire: int = 86400):
        """Mark job as processed for device"""
        key = f"processed:{device_id}:{job_id}"
        await self.set(key, "1", expire)
    
    async def is_job_processed(self, device_id: str, job_id: int) -> bool:
        """Check if job was already processed for device"""
        key = f"processed:{device_id}:{job_id}"
        return await self.exists(key)
    
    async def get_notification_count(self, device_id: str, period: str) -> int:
        """Get notification count for device in period (hour/day)"""
        key = f"notification_count:{period}:{device_id}"
        count = await self.get(key)
        return int(count) if count else 0
    
    async def increment_notification_count(self, device_id: str, period: str, expire: int):
        """Increment notification count for device"""
        key = f"notification_count:{period}:{device_id}"
        count = await self.increment(key)
        if count == 1:  # First increment, set expiration
            await self.expire(key, expire)
        return count

# Global Redis client instance
redis_client = RedisClient()

async def init_redis():
    """Initialize Redis connection"""
    await redis_client.init_redis()