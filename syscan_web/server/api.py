"""
REST API endpoints for SysCan.
Provides scan, analyze, and delete operations via HTTP.
"""

from flask import Blueprint, request, jsonify
import time
import os
import threading

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Thread-safe storage for scan results using a lock
_scan_lock = threading.Lock()
_scan_results = {
    'items': [],
    'status': 'idle',  # idle, scanning, complete, error
    'progress': 0,
    'start_time': None,
    'end_time': None
}

def get_scan_results():
    """Get current scan results (thread-safe)."""
    with _scan_lock:
        return _scan_results.copy()

def update_scan_results(**kwargs):
    """Update scan results (thread-safe)."""
    global _scan_results
    with _scan_lock:
        _scan_results.update(kwargs)

def reset_scan_results():
    """Reset scan results for new scan (thread-safe)."""
    global _scan_results
    with _scan_lock:
        _scan_results = {
            'items': [],
            'status': 'scanning',
            'progress': 0,
            'start_time': time.time(),
            'end_time': None
        }

@api_bp.route('/scan', methods=['POST'])
def start_scan():
    """Start a new system scan."""
    results = get_scan_results()
    
    if results['status'] == 'scanning':
        return jsonify({'error': 'Scan already in progress'}), 409
    
    # Reset results for new scan
    reset_scan_results()
    
    # Start scan in background thread
    def do_scan():
        try:
            from syscan_web.agent import GridScanner
            scanner = GridScanner()
            items = scanner.scan()
            update_scan_results(
                items=[{'path': p, 'size': s} for p, s in items],
                status='complete',
                end_time=time.time()
            )
        except Exception as e:
            update_scan_results(
                status='error',
                error=str(e)
            )
    
    thread = threading.Thread(target=do_scan, daemon=True)
    thread.start()
    
    return jsonify({
        'message': 'Scan started',
        'status': 'scanning'
    }), 202

@api_bp.route('/scan/status', methods=['GET'])
def get_scan_status():
    """Get current scan status and progress."""
    results = get_scan_results()
    
    response = {
        'status': results['status'],
        'progress': results.get('progress', 0)
    }
    
    if results.get('start_time'):
        if results.get('end_time'):
            response['duration'] = results['end_time'] - results['start_time']
        else:
            response['duration'] = time.time() - results['start_time']
    
    if results['status'] == 'complete':
        response['items_found'] = len(results['items'])
    
    return jsonify(response), 200

@api_bp.route('/items', methods=['GET'])
def get_items():
    """Get list of scanned items."""
    results = get_scan_results()
    
    if results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    items = results['items']
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'items': items[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@api_bp.route('/items/<path:item_path>', methods=['DELETE'])
def delete_item(item_path):
    """Delete a specific item."""
    from syscan_web.agent import FileDeleter
    import urllib.parse
    
    # Decode the path
    item_path = urllib.parse.unquote(item_path)
    
    if not os.path.exists(item_path):
        return jsonify({'error': 'Item not found'}), 404
    
    method = request.args.get('method', 'recycle')  # recycle or permanent
    
    deleter = FileDeleter()
    success, message = deleter.delete_item(item_path, method)
    
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 500

@api_bp.route('/report', methods=['GET'])
def get_report():
    """Get summary report of scan results."""
    results = get_scan_results()
    
    if results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404
    
    from syscan_web.agent import FileAnalyzer
    
    analyzer = FileAnalyzer()
    items = [(item['path'], item['size']) for item in results['items']]
    analysis = analyzer.analyze_items(items)
    
    return jsonify(analysis), 200

@api_bp.route('/export', methods=['GET'])
def export_report():
    """Export scan results as JSON file."""
    results = get_scan_results()
    
    if results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404
    
    from flask import make_response
    import json
    
    report = {
        'items': results['items'],
        'scan_time': results.get('end_time', 0) - results.get('start_time', 0)
    }
    
    response = make_response(json.dumps(report, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=cleanup_report.json'
    
    return response
