"""
REST API endpoints for SysCan.
Provides scan, analyze, and delete operations via HTTP.
"""

from flask import Blueprint, request, jsonify
import time
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

# In-memory storage for scan results
# NOTE: This is NOT thread-safe for multiple users (Bug #11)
scan_results = {
    'items': [],
    'status': 'idle',  # idle, scanning, complete, error
    'progress': 0,
    'start_time': None,
    'end_time': None
}

@api_bp.route('/scan', methods=['POST'])
def start_scan():
    """Start a new system scan."""
    global scan_results

    if scan_results['status'] == 'scanning':
        return jsonify({'error': 'Scan already in progress'}), 409

    # Reset results
    scan_results = {
        'items': [],
        'status': 'scanning',
        'progress': 0,
        'start_time': time.time(),
        'end_time': None
    }

    # Start scan in background thread
    import threading
    def do_scan():
        global scan_results
        try:
            from syscan_web.agent import GridScanner
            scanner = GridScanner()
            items = scanner.scan()
            # FIX #3: Correct dict syntax (added missing colon)
            scan_results['items'] = [{'path': p, 'size': s} for p, s in items]
            scan_results['status'] = 'complete'
            scan_results['end_time'] = time.time()
        except Exception as e:
            scan_results['status'] = 'error'
            scan_results['error'] = str(e)

    thread = threading.Thread(target=do_scan, daemon=True)
    thread.start()

    return jsonify({
        'message': 'Scan started',
        'status': 'scanning'
    }), 202

@api_bp.route('/scan/status', methods=['GET'])
def get_scan_status():
    """Get current scan status and progress."""
    global scan_results

    response = {
        'status': scan_results['status'],
        'progress': scan_results.get('progress', 0)
    }

    if scan_results.get('start_time'):
        if scan_results.get('end_time'):
            response['duration'] = scan_results['end_time'] - scan_results['start_time']
        else:
            response['duration'] = time.time() - scan_results['start_time']

    if scan_results['status'] == 'complete':
        response['items_found'] = len(scan_results['items'])

    return jsonify(response), 200

@api_bp.route('/items', methods=['GET'])
def get_items():
    """Get list of scanned items."""
    global scan_results

    if scan_results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    items = scan_results['items']
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
    global scan_results

    if scan_results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404

    from syscan_web.agent import FileAnalyzer

    analyzer = FileAnalyzer()

    items = [(item['path'], item['size']) for item in scan_results['items']]
    analysis = analyzer.analyze_items(items)

    return jsonify(analysis), 200

@api_bp.route('/export', methods=['GET'])
def export_report():
    """Export scan results as JSON file."""
    global scan_results

    if scan_results['status'] != 'complete':
        return jsonify({'error': 'No scan results available'}), 404

    from flask import make_response
    import json

    report = {
        'items': scan_results['items'],
        'scan_time': scan_results.get('end_time', 0) - scan_results.get('start_time', 0)
    }

    response = make_response(json.dumps(report, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=cleanup_report.json'

    return response
