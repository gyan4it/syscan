#!/usr/bin/env python
"""
SysCan Web Server - Production Startup Script
Serves Flask API + React WebUI (static files)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import create_app

def main():
    """Start the SysCan Web server."""
    # Create Flask app (with UI serving enabled)
    app = create_app(serve_ui=True)
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print("SysCan Web Server")
    print("=" * 60)
    print(f"Environment: {'DEBUG' if debug else 'PRODUCTION'}")
    print(f"Port: {port}")
    print(f"API Endpoints: http://localhost:{port}/api")
    print(f"WebUI: http://localhost:{port}/")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print()
    
    # Run server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main()
