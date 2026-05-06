"""
Flask app factory for SysCan API server.
Serves WebUI static files in production mode.
"""

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

def create_app(config_name=None, serve_ui=True):
    """Application factory pattern for Flask."""
    app = Flask(__name__, 
        static_folder='../webui/build/static',
        template_folder='../webui/build')
    
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
    
    # Serve WebUI static files (production mode)
    if serve_ui and os.path.exists('../webui/build/index.html'):
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_ui(path):
            if path != "" and os.path.exists(app.static_folder + '/' + path):
                return send_from_directory(app.static_folder, path)
            else:
                return send_from_directory('../webui/build', 'index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}, 200
    
    # API root endpoint
    @app.route('/api')
    def api_root():
        return {
            'name': 'SysCan API',
            'version': '0.1.0',
            'endpoints': {
                'health': '/health',
                'scan': '/api/scan',
                'items': '/api/items',
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
