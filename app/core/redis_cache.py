"""Redis cache service for analytics data."""

import json
import redis
from typing import Optional, Dict, Any
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class RedisCache:
    """Redis cache service for storing and retrieving analytics data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning("Redis not available, falling back to no-cache", error=str(e))
            self.client = None
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Redis is enabled and available."""
        if not self.enabled or not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_enabled():
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Failed to get from cache", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.is_enabled():
            return False
        
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error("Failed to set cache", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_enabled():
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Failed to delete from cache", key=key, error=str(e))
            return False
    
    def clear_session_cache(self, session_id: str) -> bool:
        """Clear all cache entries for a session."""
        if not self.is_enabled():
            return False
        
        try:
            # Clear analytics cache
            self.delete(f"analytics:{session_id}")
            # Clear heatmap cache
            self.delete(f"heatmap:{session_id}")
            # Clear stats cache
            self.delete(f"stats:{session_id}")
            return True
        except Exception as e:
            logger.error("Failed to clear session cache", session_id=session_id, error=str(e))
            return False


# Global Redis cache instance
redis_cache = RedisCache()

