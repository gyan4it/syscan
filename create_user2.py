import sqlite3
import werkzeug.security as security

conn = sqlite3.connect(r'C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository\syscan_web\server\auth.db')
cursor = conn.cursor()

# Delete old user
cursor.execute("DELETE FROM users WHERE username='testadmin'")

# Create with werkzeug hash (same as auth.py expects)
password_hash = security.generate_password_hash('testpass123')
cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
             ('testadmin', password_hash, 'admin'))

conn.commit()

# Verify
cursor.execute("SELECT username, role FROM users WHERE username='testadmin'")
print('User created:', cursor.fetchone())

conn.close()
