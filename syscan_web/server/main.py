"""
Main entry point for SysCan Web server.
Run this file to start the Flask + Socket.IO server.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_socketio import SocketIO
from server.app import create_app
from server.websocket import init_socketio

def main():
    """Start the SysCan Web server."""
    # Create Flask app
    app = create_app()

    # Create Socket.IO instance
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize websocket handlers
    init_socketio(socketio)

    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print(f"Starting SysCan Web server on http://localhost:{port}")
    print("Press Ctrl+C to stop")

    # Run server
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
