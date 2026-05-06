"""
Flask app factory for SysCan API server.
"""

from flask import Flask
from flask_cors import CORS
import os

def create_app(config_name=None):
    """Application factory pattern for Flask."""
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-prod'),
        API_PREFIX='/api',
        DEBUG=True
    )

    # Register blueprints
    register_blueprints(app)

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}, 200

    # Root endpoint
    @app.route('/')
    def root():
        return {
            'name': 'SysCan API',
            'version': '0.1.0',
            'endpoints': {
                'health': '/health',
                'api': '/api',
                'scan': '/api/scan',
                'report': '/api/report'
            }
        }

    return app

def register_blueprints(app):
    """Register all blueprints with the app."""
    from .api import api_bp
    from .websocket import ws_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(ws_bp)
