"""Cache manager service using Redis for prompt caching."""
from typing import Optional
import hashlib
import json
from config import settings

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheManager:
    """Manages caching of LLM inference results using Redis."""

    def __init__(self):
        """Initialize cache manager."""
        self.enabled = settings.ENABLE_CACHE and REDIS_AVAILABLE
        self.ttl = settings.CACHE_TTL_SECONDS
        self.redis_client: Optional[redis.Redis] = None

        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                print(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self.redis_client = None

        # Statistics
        self.hits = 0
        self.misses = 0

    def _generate_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        # Include relevant parameters in cache key
        cache_data = {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", settings.MODEL_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", settings.MODEL_MAX_TOKENS),
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"llm:{hashlib.sha256(cache_str.encode()).hexdigest()}"

    def get(self, prompt: str, **kwargs) -> Optional[str]:
        """Get cached response for a prompt."""
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(prompt, **kwargs)
            cached_value = self.redis_client.get(cache_key)

            if cached_value:
                self.hits += 1
                return cached_value
            else:
                self.misses += 1
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            self.misses += 1
            return None

    def set(self, prompt: str, response: str, **kwargs) -> bool:
        """Cache a response for a prompt."""
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(prompt, **kwargs)
            self.redis_client.setex(cache_key, self.ttl, response)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def flush(self) -> int:
        """Flush all cache entries (admin operation)."""
        if not self.enabled or not self.redis_client:
            return 0

        try:
            # Get all LLM cache keys
            keys = self.redis_client.keys("llm:*")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache flush error: {e}")
            return 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        stats = {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2)
        }

        if self.enabled and self.redis_client:
            try:
                info = self.redis_client.info("memory")
                stats["memory_used"] = info.get("used_memory_human", "N/A")
                stats["entries"] = self.redis_client.dbsize()
            except Exception:
                pass

        return stats
