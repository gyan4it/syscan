"""
SysScan Feedback Server
Simple Flask server to collect feedback and store in CSV
Run: python feedback_server.py
Then access: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

FEEDBACK_CSV = 'feedback.csv'
FEEDBACK_FIELDS = ['timestamp', 'name', 'email', 'type', 'rating', 'message', 'system']

# Initialize CSV if it doesn't exist
def init_csv():
    if not os.path.exists(FEEDBACK_CSV):
        with open(FEEDBACK_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FEEDBACK_FIELDS)
            writer.writeheader()

@app.route('/')
def index():
    return send_file('feedback.html')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if not data.get('message') or not data.get('type'):
            return jsonify({'error': 'Missing required fields'}), 400

        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()

        # Write to CSV
        with open(FEEDBACK_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FEEDBACK_FIELDS)
            writer.writerow({
                'timestamp': data.get('timestamp', ''),
                'name': data.get('name', 'Anonymous'),
                'email': data.get('email', 'N/A'),
                'type': data.get('type', ''),
                'rating': data.get('rating', 'N/A'),
                'message': data.get('message', ''),
                'system': data.get('system', 'N/A')
            })

        return jsonify({'success': True, 'message': 'Feedback received!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Admin endpoint to view all feedback (simple auth needed in production)"""
    try:
        feedbacks = []
        with open(FEEDBACK_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                feedbacks.append(row)
        return jsonify(feedbacks), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_panel():
    """Simple admin panel to view feedback"""
    try:
        feedbacks = []
        with open(FEEDBACK_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                feedbacks.append(row)

        html = '''
        <html>
        <head>
            <title>SysScan - Feedback Admin</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #667eea; color: white; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .type-bug { color: #dc3545; font-weight: bold; }
                .type-feature { color: #28a745; font-weight: bold; }
                .type-improvement { color: #007bff; font-weight: bold; }
                .type-praise { color: #ffc107; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>SysScan Feedback Admin Panel</h1>
            <p>Total feedback entries: ''' + str(len(feedbacks)) + '''</p>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Type</th>
                    <th>Rating</th>
                    <th>Message</th>
                    <th>System</th>
                </tr>
        '''

        for fb in feedbacks:
            type_class = f"type-{fb.get('type', '')}"
            html += f'''
                <tr>
                    <td>{fb.get('timestamp', '')}</td>
                    <td>{fb.get('name', 'Anonymous')}</td>
                    <td>{fb.get('email', 'N/A')}</td>
                    <td class="{type_class}">{fb.get('type', '')}</td>
                    <td>{fb.get('rating', 'N/A')}</td>
                    <td>{fb.get('message', '')}</td>
                    <td>{fb.get('system', 'N/A')}</td>
                </tr>
            '''

        html += '''
            </table>
            <p><a href="/api/feedback">View as JSON</a> | <a href="/">Back to Form</a></p>
        </body>
        </html>
        '''

        return html

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    init_csv()
    print("SysScan Feedback Server starting...")
    print("Access feedback form at: http://localhost:5000")
    print("Access admin panel at: http://localhost:5000/admin")
    app.run(host='0.0.0.0', port=5000, debug=True)
