"""
Slack Data Manager Bot - Main Application
A professional Slack bot for managing Google Sheets, CSV, and Excel files.
"""

import os
import logging
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern for Flask app creation."""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config.from_object('app.config.Config')
    
    # Setup logging
    from app.core.logger import setup_logging
    setup_logging()
    
    # Initialize extensions
    from app.core.cache import init_cache
    from app.core.rate_limiter import init_rate_limiter
    
    init_cache(app)
    init_rate_limiter(app)
    
    # Register blueprints
    from app.handlers.command_handler import command_bp
    
    app.register_blueprint(command_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return {'error': 'An unexpected error occurred'}, 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '1.0.0'}
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 