"""
Rate limiting module for the Slack Data Manager Bot.
"""

import os
import time
import logging
from typing import Dict, Tuple, Optional
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Rate limit storage (simple in-memory)
rate_limit_storage = {}

def init_rate_limiter(app):
    """
    Initialize rate limiter.
    
    Args:
        app: Flask application instance
    """
    # Rate limiting configuration
    app.config['RATE_LIMIT_REQUESTS'] = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    app.config['RATE_LIMIT_WINDOW'] = int(os.getenv('RATE_LIMIT_WINDOW', 3600))  # 1 hour
    
    logger.info(f"Rate limiter initialized: {app.config['RATE_LIMIT_REQUESTS']} requests per {app.config['RATE_LIMIT_WINDOW']} seconds")

def get_rate_limit_key(user_id: str, action: str = "default") -> str:
    """
    Generate rate limit key for user and action.
    
    Args:
        user_id (str): User ID
        action (str): Action being performed
        
    Returns:
        str: Rate limit key
    """
    return f"rate_limit:{user_id}:{action}"

def check_rate_limit(user_id: str, action: str = "default", max_requests: int = None, window: int = None) -> Tuple[bool, Dict]:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id (str): User ID
        action (str): Action being performed
        max_requests (int, optional): Maximum requests allowed
        window (int, optional): Time window in seconds
        
    Returns:
        tuple: (is_allowed, rate_limit_info)
    """
    from flask import current_app
    
    # Get configuration
    if max_requests is None:
        max_requests = current_app.config.get('RATE_LIMIT_REQUESTS', 100)
    if window is None:
        window = current_app.config.get('RATE_LIMIT_WINDOW', 3600)
    
    key = get_rate_limit_key(user_id, action)
    current_time = time.time()
    
    # Get current rate limit data
    rate_data = rate_limit_storage.get(key, {
        'requests': 0,
        'reset_time': current_time + window
    })
    
    # Check if window has reset
    if current_time > rate_data['reset_time']:
        rate_data = {
            'requests': 0,
            'reset_time': current_time + window
        }
    
    # Check if limit exceeded
    if rate_data['requests'] >= max_requests:
        remaining_time = int(rate_data['reset_time'] - current_time)
        return False, {
            'limit_exceeded': True,
            'remaining_time': remaining_time,
            'reset_time': rate_data['reset_time'],
            'requests_used': rate_data['requests'],
            'max_requests': max_requests
        }
    
    # Increment request count
    rate_data['requests'] += 1
    rate_data['remaining'] = max_requests - rate_data['requests']
    rate_limit_storage[key] = rate_data
    
    return True, {
        'limit_exceeded': False,
        'remaining': rate_data['remaining'],
        'reset_time': rate_data['reset_time'],
        'requests_used': rate_data['requests'],
        'max_requests': max_requests
    }

def rate_limit(max_requests: int = None, window: int = None, action: str = "default"):
    """
    Decorator to apply rate limiting to endpoints.
    
    Args:
        max_requests (int, optional): Maximum requests allowed
        window (int, optional): Time window in seconds
        action (str): Action name for rate limiting
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user ID from request
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                # Try to get from different sources
                if request.form:
                    user_id = request.form.get('user_id')
                elif request.json:
                    user_id = request.json.get('user', {}).get('id')
            
            if not user_id:
                logger.warning("No user ID found for rate limiting")
                return jsonify({'error': 'User ID required'}), 400
            
            # Check rate limit
            is_allowed, rate_info = check_rate_limit(user_id, action, max_requests, window)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}: {rate_info}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_info['remaining_time'],
                    'details': rate_info
                }), 429
            
            # Add rate limit info to response headers
            response = func(*args, **kwargs)
            
            # If response is a tuple (response, status_code)
            if isinstance(response, tuple):
                response_obj, status_code = response
            else:
                response_obj = response
                status_code = 200
            
            # Add rate limit headers
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Limit'] = str(rate_info['max_requests'])
                response_obj.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response_obj.headers['X-RateLimit-Reset'] = str(int(rate_info['reset_time']))
            
            # Return the response in the same format as received
            if isinstance(response, tuple):
                return response_obj, status_code
            else:
                return response_obj
        
        return wrapper
    return decorator

def get_rate_limit_info(user_id: str, action: str = "default") -> Dict:
    """
    Get rate limit information for a user.
    
    Args:
        user_id (str): User ID
        action (str): Action name
        
    Returns:
        dict: Rate limit information
    """
    from flask import current_app
    
    max_requests = current_app.config.get('RATE_LIMIT_REQUESTS', 100)
    window = current_app.config.get('RATE_LIMIT_WINDOW', 3600)
    
    key = get_rate_limit_key(user_id, action)
    current_time = time.time()
    
    rate_data = rate_limit_storage.get(key, {
        'requests': 0,
        'reset_time': current_time + window
    })
    
    # Check if window has reset
    if current_time > rate_data['reset_time']:
        rate_data = {
            'requests': 0,
            'reset_time': current_time + window
        }
    
    return {
        'user_id': user_id,
        'action': action,
        'requests_used': rate_data['requests'],
        'max_requests': max_requests,
        'remaining': max_requests - rate_data['requests'],
        'reset_time': rate_data['reset_time'],
        'window_seconds': window
    }

def reset_rate_limit(user_id: str, action: str = "default") -> bool:
    """
    Reset rate limit for a user.
    
    Args:
        user_id (str): User ID
        action (str): Action name
        
    Returns:
        bool: True if reset successful
    """
    try:
        key = get_rate_limit_key(user_id, action)
        if key in rate_limit_storage:
            del rate_limit_storage[key]
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limit for {user_id}: {e}")
        return False

def get_rate_limit_stats() -> Dict:
    """
    Get rate limiting statistics.
    
    Returns:
        dict: Rate limiting statistics
    """
    current_time = time.time()
    active_limits = 0
    total_requests = 0
    
    for key, data in rate_limit_storage.items():
        if current_time <= data['reset_time']:
            active_limits += 1
            total_requests += data['requests']
    
    return {
        'active_limits': active_limits,
        'total_requests': total_requests,
        'storage_size': len(rate_limit_storage)
    }

def cleanup_expired_limits():
    """
    Clean up expired rate limit entries.
    """
    current_time = time.time()
    expired_keys = []
    
    for key, data in rate_limit_storage.items():
        if current_time > data['reset_time']:
            expired_keys.append(key)
    
    for key in expired_keys:
        del rate_limit_storage[key]
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired rate limit entries") 