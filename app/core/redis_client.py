import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
import aiohttp
import os
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.upstash_url: Optional[str] = None
        self.upstash_token: Optional[str] = None
        self.use_upstash = False
    
    async def init_redis(self):
        """Initialize Redis connection - try Upstash first, then standard Redis"""
        try:
            # Check for Upstash credentials first
            self.upstash_url = os.getenv("UPSTASH_REDIS_REST_URL") or settings.UPSTASH_REDIS_REST_URL
            self.upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN") or settings.UPSTASH_REDIS_REST_TOKEN
            
            if self.upstash_url and self.upstash_token:
                logger.info("Using Upstash Redis REST API")
                self.use_upstash = True
                # Test Upstash connection
                await self._upstash_request("PING")
                logger.info("Upstash Redis connection established")
                return
            
            # Fallback to standard Redis
            env_redis_url = os.getenv("REDIS_URL")
            redis_url = env_redis_url if env_redis_url else settings.REDIS_URL
            logger.info(f"Using standard Redis URL: {redis_url}")
            
            self.redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            logger.info("Standard Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Redis connection failed - continuing without cache")
            self.redis = None
            self.use_upstash = False
    
    async def _upstash_request(self, *args):
        """Make request to Upstash REST API"""
        if not self.upstash_url or not self.upstash_token:
            return None
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.upstash_token}",
                "Content-Type": "application/json"
            }
            data = json.dumps(args)
            
            async with session.post(f"{self.upstash_url}/", headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result")
                else:
                    logger.error(f"Upstash request failed: {response.status}")
                    return None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if self.use_upstash:
            return await self._upstash_request("GET", key)
        
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        if self.use_upstash:
            if expire:
                result = await self._upstash_request("SETEX", key, expire, value)
            else:
                result = await self._upstash_request("SET", key, value)
            return result == "OK"
        
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """Delete key"""
        if self.use_upstash:
            result = await self._upstash_request("DEL", key)
            return result or 0
        
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return 0
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.use_upstash:
            result = await self._upstash_request("EXISTS", key)
            return bool(result)
        
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        return bool(await self.redis.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if self.use_upstash:
            result = await self._upstash_request("EXPIRE", key, seconds)
            return bool(result)
        
        if not self.redis:
            await self.init_redis()
        if not self.redis:
            return False
        return await self.redis.expire(key, seconds)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment key value"""
        if self.use_upstash:
            result = await self._upstash_request("INCRBY", key, amount)
            return result or 0
        
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
    
    async def reset_notification_count(self, device_id: str, period: str):
        """Reset notification count for device (development only)"""
        key = f"notification_count:{period}:{device_id}"
        await self.delete(key)
    
    @asynccontextmanager
    async def lock(self, key: str, timeout: int = 10):
        """Distributed lock context manager"""
        lock_key = f"lock:{key}"
        identifier = f"{os.getpid()}:{id(asyncio.current_task())}"
        
        # Try to acquire lock
        acquired = False
        try:
            # Use SET with NX (not exists) and EX (expiry)
            if self.use_upstash:
                result = await self._upstash_request("SET", lock_key, identifier, "NX", "EX", timeout)
                acquired = result == "OK"
            else:
                if not self.redis:
                    await self.init_redis()
                if self.redis:
                    acquired = await self.redis.set(lock_key, identifier, nx=True, ex=timeout)
            
            if not acquired:
                raise Exception(f"Failed to acquire lock for {key}")
            
            yield
        
        finally:
            # Release lock only if we own it
            if acquired:
                try:
                    if self.use_upstash:
                        # Check if we still own the lock before deleting
                        current_value = await self._upstash_request("GET", lock_key)
                        if current_value == identifier:
                            await self._upstash_request("DEL", lock_key)
                    else:
                        if self.redis:
                            # Use Lua script to atomically check and delete
                            lua_script = """
                            if redis.call("get", KEYS[1]) == ARGV[1] then
                                return redis.call("del", KEYS[1])
                            else
                                return 0
                            end
                            """
                            await self.redis.eval(lua_script, 1, lock_key, identifier)
                except Exception as e:
                    logger.warning(f"Failed to release lock {key}: {e}")

# Global Redis client instance
redis_client = RedisClient()

async def init_redis():
    """Initialize Redis connection"""
    await redis_client.init_redis()