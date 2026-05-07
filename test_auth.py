import sys
sys.path.insert(0, r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository')

from server.app import create_app
from server.auth import jwt, init_auth_db, User, log_action, create_access_token, create_refresh_token, bcrypt
from flask_jwt_extended import get_jwt_identity
import sqlite3

app = create_app()

with app.app_context():
    # Initialize auth db
    init_auth_db()
    
    # Check if test user exists
    conn = sqlite3.connect(r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository\syscan_web\server\auth.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username='testadmin'")
    user = cursor.fetchone()
    
    if not user:
        # Create test user
        password_hash = bcrypt.generate_password_hash('testpass123').decode('utf-8')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                     ('testadmin', password_hash, 'admin'))
        conn.commit()
        print('Created test user: testadmin/testpass123')
    else:
        print('User exists: testadmin')
    
    # Generate token using Flask-JWT-Extended
    with app.test_request_context():
        token = create_access_token(identity=1)  # Assuming user id=1
        print(f'JWT Token (first 50 chars): {token[:50]}...')
    
    print('Auth module working!')
    print('Login endpoint: POST /api/auth/login')
    print('Test with: curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"testadmin\",\"password\":\"testpass123\"}"')
