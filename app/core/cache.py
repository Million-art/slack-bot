"""
Simple in-memory caching module for the Slack Data Manager Bot.
"""

import json
import logging
import time
from typing import Any, Optional, Dict
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache = OrderedDict()
_cache_timeouts = {}

def init_cache(app):
    """
    Initialize simple in-memory cache.
    
    Args:
        app: Flask application instance
    """
    global _cache, _cache_timeouts
    _cache.clear()
    _cache_timeouts.clear()
    logger.info("In-memory cache initialized successfully")

def get_cache(key: str, default: Any = None) -> Any:
    """
    Get value from cache.
    
    Args:
        key (str): Cache key
        default (Any): Default value if key not found
        
    Returns:
        Any: Cached value or default
    """
    try:
        # Check if key exists and is not expired
        if key in _cache:
            if key in _cache_timeouts:
                if time.time() > _cache_timeouts[key]:
                    # Key expired, remove it
                    delete_cache(key)
            return default
        
            value = _cache[key]
        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
            
        return default
        
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {e}")
        return default

def set_cache(key: str, value: Any, timeout: int = 300) -> bool:
    """
    Set value in cache.
    
    Args:
        key (str): Cache key
        value (Any): Value to cache
        timeout (int): Timeout in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Serialize value to JSON
        if isinstance(value, (dict, list, tuple)):
            serialized_value = json.dumps(value)
        else:
            serialized_value = str(value)
        
        _cache[key] = serialized_value
        _cache_timeouts[key] = time.time() + timeout
        
        # Keep cache size manageable (max 1000 entries)
        if len(_cache) > 1000:
            # Remove oldest entry
            oldest_key = next(iter(_cache))
            delete_cache(oldest_key)
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting cache key {key}: {e}")
        return False

def delete_cache(key: str) -> bool:
    """
    Delete value from cache.
    
    Args:
        key (str): Cache key to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if key in _cache:
            del _cache[key]
        if key in _cache_timeouts:
            del _cache_timeouts[key]
        return True
        
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {e}")
        return False

def cache_result(timeout: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            set_cache(cache_key, result, timeout)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        dict: Cache statistics
    """
    try:
        return {
            "total_entries": len(_cache),
            "total_timeouts": len(_cache_timeouts),
            "cache_size": len(_cache),
            "memory_usage": "In-memory cache"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}

def clear_cache_pattern(pattern: str) -> int:
    """
    Clear cache entries matching a pattern.
    
    Args:
        pattern (str): Pattern to match (simple string matching)
        
    Returns:
        int: Number of keys deleted
    """
    try:
        deleted_count = 0
        keys_to_delete = []
        
        for key in list(_cache.keys()):
            if pattern in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if delete_cache(key):
                deleted_count += 1
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error clearing cache pattern {pattern}: {e}")
        return 0

def health_check() -> Dict[str, Any]:
    """
    Check cache health.
    
    Returns:
        dict: Health status
    """
    try:
        return {
            "status": "healthy",
            "cache_type": "in-memory",
            "entries": len(_cache),
            "connected": True
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        } 