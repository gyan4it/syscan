"""
Flask app factory for SysCan API server.
Serves WebUI static files in production mode.
"""

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

def create_app(config_name=None, serve_ui=True):
    """Application factory pattern for Flask."""
    # Get the absolute path to the server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(server_dir)
    
    app = Flask(__name__, 
        static_folder=os.path.join(project_dir, 'webui', 'build', 'static'),
        template_folder=os.path.join(project_dir, 'webui', 'build'))
    
    # Enable CORS for all routes (allow CDN resources)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-prod'),
        API_PREFIX='/api',
        DEBUG=True,
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET', 'jwt-secret-change-in-prod')
    )
    
    # Import limiter after app creation to avoid circular imports
    from .api import limiter
    limiter.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Serve WebUI static files (production mode)
    if serve_ui and os.path.exists(os.path.join(project_dir, 'webui', 'build', 'index.html')):
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_ui(path):
            build_dir = os.path.join(project_dir, 'webui', 'build')
            static_dir = os.path.join(build_dir, 'static')
            if path != "" and os.path.exists(os.path.join(static_dir, path)):
                return send_from_directory(static_dir, path)
            else:
                return send_from_directory(build_dir, 'index.html')
    
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
    from .auth import create_auth_blueprint
    
    app.register_blueprint(api_bp)
    app.register_blueprint(ws_bp)
    app.register_blueprint(create_auth_blueprint())
