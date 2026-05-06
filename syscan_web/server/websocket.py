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
        emit('scan_status', {'status': 'starting'}, room='scan')

        def do_scan():
            try:
                from syscan_web.agent import GridScanner
                scanner = GridScanner()

                # Start scan
                items = scanner.scan()

                # Send results
                emit('scan_complete', {
                    'status': 'complete',
                    'items_found': len(items),
                    'items': [{'path': p, 'size': s} for p, s in items]
                }, room='scan')

            except Exception as e:
                emit('scan_error', {'error': str(e)}, room='scan')

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
