#!/usr/bin/env python3
"""
Main entry point for the Slack Data Manager Bot.
"""

import logging
import os
from flask import Flask, request, jsonify
from app.config import Config
from app.core.logger import setup_logging
from app.core.auth import require_auth
from app.core.rate_limiter import rate_limit
from app.handlers.command_handler import command_bp

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Register blueprints
    app.register_blueprint(command_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'slack-data-bot',
            'version': '1.0.0'
        })
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Slack Data Manager Bot',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'commands': '/api/command'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def main():
    """Main application entry point."""
    try:
        app = create_app()
        
        # Get configuration
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Starting Slack Data Manager Bot on {host}:{port}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main() 