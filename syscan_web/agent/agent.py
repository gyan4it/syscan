"""
SysScan Desktop Agent - Phase 3 Implementation.
Runs on user's system, communicates with web server via WebSocket.
"""

import sys
import time
import platform
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import socketio
except ImportError:
    print("ERROR: python-socketio not installed. Run: pip install python-socketio")
    sys.exit(1)

from syscan_web.agent.scanner import GridScanner
from syscan_web.agent.deleter import FileDeleter
from syscan_web.agent.analyzer import FileAnalyzer


class SysScanAgent:
    """Desktop agent that communicates with web server via WebSocket."""
    
    def __init__(self, server_url='http://localhost:5000'):
        self.sio = socketio.Client()
        self.scanner = GridScanner()
        self.deleter = FileDeleter()
        self.analyzer = FileAnalyzer()
        self.server_url = server_url
        self.is_scanning = False
        self.current_version = '1.0.0'
        
    def connect(self):
        """Connect to web server via WebSocket."""
        
        @self.sio.event
        def connect():
            print('✅ Connected to SysCan server')
            self.sio.emit('agent_status', {
                'status': 'ready',
                'version': self.current_version,
                'platform': platform.system()
            })
        
        @self.sio.event
        def scan_command(data):
            """Handle scan command from server."""
            if data['action'] == 'start':
                paths = data.get('paths', ['C:/'])
                self.start_scan(paths)
            elif data['action'] == 'stop':
                self.stop_scan()
        
        @self.sio.event
        def delete_command(data):
            """Handle delete command from server."""
            paths = data.get('paths', [])
            method = data.get('method', 'recycle')
            self.delete_files(paths, method)
        
        try:
            self.sio.connect(self.server_url)
        except Exception as e:
            print(f'❌ Connection failed: {e}')
            sys.exit(1)
    
    def start_scan(self, paths):
        """Start scanning with progress callbacks."""
        self.is_scanning = True
        self.sio.emit('scan_started', {'paths': paths})
        
        try:
            # Define progress callback for real-time updates
            def progress_callback(percent, current_file, found_count):
                if self.sio.connected:
                    self.sio.emit('scan_progress', {
                        'percent': percent,
                        'current_file': current_file,
                        'found_count': found_count
                    })
            
            # Start scan with progress callback
            items = self.scanner.scan(progress_callback=progress_callback)
            
            # Analyze items for star ratings
            analyzed = []
            for path, size in items:
                recommendation = self.analyzer.get_recommendation(path, size / (1024**3))
                analyzed.append({
                    'path': path,
                    'size': size,
                    'size_gb': round(size / (1024**3), 2),
                    'stars': recommendation['stars'],
                    'reason': recommendation['reason'],
                    'type': recommendation['type']
                })
            
            # Send results
            if self.sio.connected:
                self.sio.emit('scan_complete', {
                    'status': 'complete',
                    'items_found': len(items),
                    'items': analyzed
                })
        
        except Exception as e:
            if self.sio.connected:
                self.sio.emit('scan_error', {'error': str(e)})
        finally:
            self.is_scanning = False
    
    def stop_scan(self):
        """Stop ongoing scan."""
        # TODO: Implement scan cancellation in GridScanner
        self.is_scanning = False
        if self.sio.connected:
            self.sio.emit('scan_stopped', {})
    
    def delete_files(self, paths, method):
        """Delete files (recycle or permanent)."""
        results = []
        for path in paths:
            try:
                if method == 'recycle':
                    success = self.deleter.send_to_recycle_bin(path)
                else:
                    success, _ = self.deleter.delete_item(path, method)
                    success = success
                
                results.append({'path': path, 'success': success})
            except Exception as e:
                results.append({'path': path, 'success': False, 'error': str(e)})
        
        if self.sio.connected:
            self.sio.emit('delete_complete', {'results': results})
    
    def run(self):
        """Main loop - keep running."""
        print('🚀 SysScan Agent started')
        print(f'Platform: {platform.system()} {platform.release()}')
        print(f'Server: {self.server_url}')
        print('Press Ctrl+C to stop\n')
        
        self.connect()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                
                # Check for updates periodically
                if int(time.time()) % 3600 == 0:  # Every hour
                    self.check_for_update()
        
        except KeyboardInterrupt:
            print('\n👋 Agent shutting down...')
            self.sio.disconnect()
    
    def check_for_update(self):
        """Check if newer version is available."""
        try:
            from syscan_web.agent.updater import AgentUpdater
            updater = AgentUpdater(current_version=self.current_version)
            latest = updater.check_for_update()
            
            if latest:
                print(f'🔄 Updating to {latest}...')
                updater.download_and_install(latest)
        
        except Exception as e:
            print(f'Update check failed: {e}')


if __name__ == '__main__':
    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    
    agent = SysScanAgent(server_url=server_url)
    agent.run()
