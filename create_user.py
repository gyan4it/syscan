import sqlite3
import sys
sys.path.insert(0, r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository\syscan_web')
import bcrypt

conn = sqlite3.connect(r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository\syscan_web\server\auth.db')
cursor = conn.cursor()

# Check if user exists
cursor.execute("SELECT * FROM users WHERE username='testadmin'")
user = cursor.fetchone()

if user:
    print('User exists:', user)
else:
    # Create user with bcrypt
    password_hash = bcrypt.hashpw('testpass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                     ('testadmin', password_hash, 'admin'))
    conn.commit()
    print('Created user: testadmin')

conn.close()
