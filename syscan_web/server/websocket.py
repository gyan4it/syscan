"""
WebSocket handler for SysCan.
Provides real-time scan progress updates via Socket.IO.
"""

from flask import Blueprint
from flask_socketio import emit, join_room, leave_room
import threading
import time

ws_bp = Blueprint('websocket', __name__, url_prefix='/ws')

# Socket.IO instance (will be initialized in app factory)
socketio = None

def init_socketio(sio):
    """Initialize Socket.IO instance and register event handlers."""
    global socketio
    socketio = sio

    # Register event handlers after socketio is initialized
    @socketio.on('connect', namespace='/scan')
    def handle_connect():
        """Client connected to scan namespace."""
        emit('status', {'status': 'connected'})
        join_room('scan')

    @socketio.on('disconnect', namespace='/scan')
    def handle_disconnect():
        """Client disconnected from scan namespace."""
        leave_room('scan')

    @socketio.on('start_scan', namespace='/scan')
    def handle_start_scan():
        """Start a new scan via WebSocket."""
        emit('scan_started', {'status': 'scanning'}, room='scan')

        def do_scan():
            try:
                from syscan_web.agent import GridScanner
                from syscan_web.agent.analyzer import FileAnalyzer
                
                # Define progress callback for real-time updates
                def progress_callback(percent, current_file, found_count):
                    socketio.emit('scan_progress', {
                        'percent': percent,
                        'current_file': current_file,
                        'found_count': found_count
                    }, room='scan', namespace='/scan')

                # Start scan with progress callback
                scanner = GridScanner()
                items = scanner.scan(progress_callback=progress_callback)

                # Analyze items for star ratings
                analyzer = FileAnalyzer()
                analyzed_items = []
                for path, size in items:
                    recommendation = analyzer.get_recommendation(path, size / (1024**3))
                    analyzed_items.append({
                        'path': path,
                        'size': size,
                        'size_gb': round(size / (1024**3), 2),
                        'stars': recommendation['stars'],
                        'reason': recommendation['reason'],
                        'type': recommendation['type']
                    })

                # Send results
                socketio.emit('scan_complete', {
                    'status': 'complete',
                    'items_found': len(items),
                    'items': analyzed_items
                }, room='scan', namespace='/scan')

            except Exception as e:
                socketio.emit('scan_error', {'error': str(e)}, room='scan', namespace='/scan')

        thread = threading.Thread(target=do_scan, daemon=True)
        thread.start()

    @socketio.on('stop_scan', namespace='/scan')
    def handle_stop_scan():
        """Stop the current scan."""
        emit('scan_status', {'status': 'stopping'}, room='scan')
        # TODO: Implement scan cancellation

    @socketio.on('request_status', namespace='/scan')
    def handle_status_request():
        """Send current scan status."""
        emit('scan_status', {'status': 'idle'})  # TODO: Track actual status
