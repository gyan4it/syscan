"""
JWT Authentication for SysCan Phase 4.
Provides login, token refresh, and protected route decorators.
"""

from flask import request, jsonify, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
import sqlite3
import os
from datetime import datetime, timedelta

# Initialize JWT
jwt = JWTManager()

# SQLite database for users and audit logs
AUTH_DB = os.path.join(os.path.dirname(__file__), 'auth.db')

def init_auth_db():
    """Initialize authentication database."""
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            ('admin', 'pbkdf2:sha256:150000$ABC123DEF456', 'admin')  # Simplified - use werkzeug.security.generate_password_hash
        )
    
    conn.commit()
    conn.close()

def log_action(user_id, action, resource=None):
    """Log user action to audit database."""
    ip = request.remote_addr if request else 'system'
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO audit_logs (user_id, action, resource, ip_address) VALUES (?, ?, ?, ?)',
        (user_id, action, resource, ip)
    )
    conn.commit()
    conn.close()

def create_auth_blueprint():
    """Create authentication blueprint."""
    from flask import Blueprint
    import werkzeug.security as security
    
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect(AUTH_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash, role FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        # Simplified password check (in production, use proper hash verification)
        if user and password == 'admin123':  # CHANGE THIS!
            user_id, _, role = user
            access_token = create_access_token(identity={'id': user_id, 'username': username, 'role': role})
            refresh_token = create_refresh_token(identity=user_id)
            
            log_action(user_id, 'login', 'auth')
            
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {'id': user_id, 'username': username, 'role': role}
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    @auth_bp.route('/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)
        return jsonify({'access_token': access_token}), 200
    
    @auth_bp.route('/logout', methods=['POST'])
    @jwt_required()
    def logout():
        user_id = get_jwt_identity()['id']
        log_action(user_id, 'logout', 'auth')
        # In production, add token to blacklist
        return jsonify({'message': 'Logged out'}), 200
    
    @auth_bp.route('/audit-logs', methods=['GET'])
    @jwt_required()
    def get_audit_logs():
        user = get_jwt_identity()
        if user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        conn = sqlite3.connect(AUTH_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, a.action, a.resource, a.ip_address, a.timestamp 
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC LIMIT 100
        ''')
        logs = cursor.fetchall()
        conn.close()
        
        return jsonify({'logs': [
            {'user': log[0], 'action': log[1], 'resource': log[2], 'ip': log[3], 'timestamp': log[4]}
            for log in logs
        ]}), 200
    
    return auth_bp
