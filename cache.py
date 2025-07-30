import redis
import json
import pickle
from functools import wraps
from datetime import datetime, timedelta
from config import Config

# Initialize Redis connection
redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    password=Config.REDIS_PASSWORD,
    decode_responses=False  # Keep as bytes for pickle compatibility
)

class Cache:
    """Redis cache wrapper with helper methods"""
    
    def __init__(self, prefix='quizmaster_'):
        self.prefix = prefix
        self.client = redis_client
    
    def _get_key(self, key):
        """Add prefix to cache key"""
        return f"{self.prefix}{key}"
    
    def set(self, key, value, timeout=300):
        """Set a value in cache with timeout (default 5 minutes)"""
        try:
            cache_key = self._get_key(key)
            if isinstance(value, (dict, list, tuple)):
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value).encode('utf-8')
            
            self.client.setex(cache_key, timeout, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a value from cache"""
        try:
            cache_key = self._get_key(key)
            value = self.client.get(cache_key)
            
            if value is None:
                return default
            
            # Try to deserialize as pickle first, then as string
            try:
                return pickle.loads(value)
            except:
                return value.decode('utf-8')
                
        except Exception as e:
            print(f"Cache get error: {e}")
            return default
    
    def delete(self, key):
        """Delete a key from cache"""
        try:
            cache_key = self._get_key(key)
            return self.client.delete(cache_key)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key):
        """Check if a key exists in cache"""
        try:
            cache_key = self._get_key(key)
            return self.client.exists(cache_key)
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    def expire(self, key, timeout):
        """Set expiration time for a key"""
        try:
            cache_key = self._get_key(key)
            return self.client.expire(cache_key, timeout)
        except Exception as e:
            print(f"Cache expire error: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear all keys matching a pattern"""
        try:
            pattern_key = self._get_key(pattern)
            keys = self.client.keys(pattern_key)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0
    
    def get_or_set(self, key, callback, timeout=300):
        """Get value from cache or set it using callback function"""
        value = self.get(key)
        if value is None:
            value = callback()
            self.set(key, value, timeout)
        return value

# Create global cache instance
cache = Cache()

def cached(timeout=300, key_prefix=''):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f"_{hash(str(args))}"
            if kwargs:
                cache_key += f"_{hash(str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching a pattern"""
    return cache.clear_pattern(pattern)

# Cache helper functions for specific use cases
def cache_quiz_data(quiz_id, data, timeout=1800):  # 30 minutes
    """Cache quiz data"""
    return cache.set(f"quiz_{quiz_id}", data, timeout)

def get_cached_quiz_data(quiz_id):
    """Get cached quiz data"""
    return cache.get(f"quiz_{quiz_id}")

def cache_user_dashboard(user_id, data, timeout=600):  # 10 minutes
    """Cache user dashboard data"""
    return cache.set(f"dashboard_{user_id}", data, timeout)

def get_cached_dashboard(user_id):
    """Get cached dashboard data"""
    return cache.get(f"dashboard_{user_id}")

def cache_quiz_statistics(stats, timeout=3600):  # 1 hour
    """Cache quiz statistics"""
    return cache.set("quiz_statistics", stats, timeout)

def get_cached_quiz_statistics():
    """Get cached quiz statistics"""
    return cache.get("quiz_statistics")

def cache_subject_data(subject_id, data, timeout=1800):  # 30 minutes
    """Cache subject data"""
    return cache.set(f"subject_{subject_id}", data, timeout)

def get_cached_subject_data(subject_id):
    """Get cached subject data"""
    return cache.get(f"subject_{subject_id}")

def invalidate_quiz_cache(quiz_id):
    """Invalidate all cache related to a specific quiz"""
    patterns = [
        f"quiz_{quiz_id}",
        "quiz_statistics",
        "dashboard_*"  # Invalidate all dashboard caches
    ]
    for pattern in patterns:
        cache.clear_pattern(pattern)

def invalidate_user_cache(user_id):
    """Invalidate all cache related to a specific user"""
    patterns = [
        f"dashboard_{user_id}",
        f"user_{user_id}_*"
    ]
    for pattern in patterns:
        cache.clear_pattern(pattern)

def invalidate_subject_cache(subject_id):
    """Invalidate all cache related to a specific subject"""
    patterns = [
        f"subject_{subject_id}",
        "quiz_statistics",
        "dashboard_*"
    ]
    for pattern in patterns:
        cache.clear_pattern(pattern)

# Session storage in Redis (alternative to Flask session)
class RedisSession:
    """Redis-based session storage"""
    
    def __init__(self, prefix='session_'):
        self.prefix = prefix
        self.client = redis_client
    
    def set(self, session_id, data, timeout=3600):  # 1 hour default
        """Set session data"""
        try:
            key = f"{self.prefix}{session_id}"
            serialized_data = pickle.dumps(data)
            return self.client.setex(key, timeout, serialized_data)
        except Exception as e:
            print(f"Session set error: {e}")
            return False
    
    def get(self, session_id):
        """Get session data"""
        try:
            key = f"{self.prefix}{session_id}"
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Session get error: {e}")
            return None
    
    def delete(self, session_id):
        """Delete session data"""
        try:
            key = f"{self.prefix}{session_id}"
            return self.client.delete(key)
        except Exception as e:
            print(f"Session delete error: {e}")
            return False
    
    def exists(self, session_id):
        """Check if session exists"""
        try:
            key = f"{self.prefix}{session_id}"
            return self.client.exists(key)
        except Exception as e:
            print(f"Session exists error: {e}")
            return False

# Create global session instance
redis_session = RedisSession()

# Rate limiting with Redis
class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, prefix='rate_limit_'):
        self.prefix = prefix
        self.client = redis_client
    
    def is_allowed(self, key, max_requests, window_seconds):
        """Check if request is allowed within rate limit"""
        try:
            rate_key = f"{self.prefix}{key}"
            current = self.client.get(rate_key)
            
            if current is None:
                # First request in window
                self.client.setex(rate_key, window_seconds, 1)
                return True
            
            current_count = int(current)
            if current_count < max_requests:
                # Increment counter
                self.client.incr(rate_key)
                return True
            
            return False
            
        except Exception as e:
            print(f"Rate limiter error: {e}")
            return True  # Allow on error
    
    def get_remaining(self, key, max_requests):
        """Get remaining requests allowed"""
        try:
            rate_key = f"{self.prefix}{key}"
            current = self.client.get(rate_key)
            
            if current is None:
                return max_requests
            
            current_count = int(current)
            return max(0, max_requests - current_count)
            
        except Exception as e:
            print(f"Rate limiter get_remaining error: {e}")
            return max_requests

# Create global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests=100, window_seconds=3600):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use IP address or user ID as key
            from flask import request
            key = request.remote_addr
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                from flask import jsonify
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 