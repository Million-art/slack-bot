"""
Authentication and authorization module for Slack Data Manager Bot.
"""

import os
import logging
from functools import wraps
from flask import request, current_app, jsonify
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Initialize signature verifier
signature_verifier = None

def init_signature_verifier():
    """Initialize the Slack signature verifier."""
    global signature_verifier
    signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    if not signing_secret:
        logger.error("SLACK_SIGNING_SECRET not configured")
        return False
    
    try:
        signature_verifier = SignatureVerifier(signing_secret)
        return True
    except Exception as e:
        logger.error(f"Failed to initialize signature verifier: {e}")
        return False

def verify_slack_request(req):
    """
    Verify that the request is from Slack.
    
    Args:
        req: Flask request object
        
    Returns:
        bool: True if request is valid, False otherwise
    """
    global signature_verifier
    
    if not signature_verifier:
        if not init_signature_verifier():
            logger.error("Cannot verify request - signature verifier not initialized")
            return False
    
    try:
        # Get the request body
        body = req.get_data()
        
        # Get the timestamp header
        timestamp = req.headers.get('X-Slack-Request-Timestamp', '')
        
        # Get the signature header
        signature = req.headers.get('X-Slack-Signature', '')
        
        # Verify the request
        if not signature_verifier.is_valid_request(body, req.headers):
            logger.warning(f"Invalid Slack signature from {req.remote_addr}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying Slack request: {e}")
        return False

def check_user_permission(user_id):
    """
    Check if a user has permission to use the bot.
    
    Args:
        user_id (str): Slack user ID
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    allowed_users = os.getenv('ALLOWED_USER_IDS', '').split(',')
    
    if not allowed_users or not allowed_users[0]:
        logger.warning("No allowed users configured")
        return False
    
    has_permission = user_id in allowed_users
    
    if not has_permission:
        logger.warning(f"Unauthorized access attempt by user: {user_id}")
    
    return has_permission

def require_auth(f):
    """
    Decorator to require authentication for endpoints.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verify Slack request
        if not verify_slack_request(request):
            logger.warning(f"Invalid request signature from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get user ID from request
        user_id = None
        
        # Try to get user ID from different sources
        if request.form:
            user_id = request.form.get('user_id')
            
            # For interactions, user_id might be in the payload
            if not user_id and 'payload' in request.form:
                try:
                    import json
                    payload = json.loads(request.form.get('payload', '{}'))
                    user_id = payload.get('user', {}).get('id')
                except Exception as e:
                    logger.error(f"Error parsing payload: {e}")
        
        if not user_id:
            logger.warning("No user ID found in request")
            return jsonify({'error': 'User ID required'}), 400
        
        # Check user permission
        if not check_user_permission(user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Add user_id to request context
        request.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_request(user_id, action, details=None):
    """
    Log user actions for audit purposes.
    
    Args:
        user_id (str): Slack user ID
        action (str): Action being performed
        details (dict, optional): Additional details
    """
    log_data = {
        'user_id': user_id,
        'action': action,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'timestamp': request.headers.get('X-Slack-Request-Timestamp', ''),
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"AUDIT: {log_data}")

def get_user_info(user_id):
    """
    Get user information from Slack.
    
    Args:
        user_id (str): Slack user ID
        
    Returns:
        dict: User information or None if error
    """
    try:
        from app.services.slack_service import get_slack_client
        client = get_slack_client()
        
        response = client.users_info(user=user_id)
        return response['user']
        
    except SlackApiError as e:
        logger.error(f"Error getting user info for {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting user info: {e}")
        return None 