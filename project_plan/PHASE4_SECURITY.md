# Phase 4: Security & Scale (Months 9-12)

## Overview
**Duration:** 3 months  
**Goal:** Add authentication, audit logging, and prepare for enterprise multi-user support.

---

## Why This Phase?

### Problem Statement
As SysScan gains users, we need:
1. **Authentication** - Only authorized users can access their agents
2. **Audit logs** - Track who deleted what, when, and why
3. **Compliance** - GDPR/HIPAA requirements for enterprise
4. **Scalability** - Support 1000+ concurrent users

### Current Limitations
- ❌ No authentication (anyone can access API)
- ❌ No audit trail (deletions not logged)
- ❌ Single-user only (no multi-tenancy)
- ❌ No rate limiting (DDoS risk)

---

## How to Implement

### 4.1 Authentication (JWT)

**Goal:** Secure API endpoints so only logged-in users can scan/delete.

```python
# server/auth.py
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

jwt = JWTManager()

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Hash password (bcrypt)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    # Save to DB (users table)
    db.users.insert({'username': username, 'password': hashed})
    
    return jsonify({'msg': 'Registered'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.json
    user = db.users.find_one({'username': data.get('username')})
    
    if user and bcrypt.checkpw(data.get('password').encode(), user['password']):
        token = create_access_token(identity=user['username'])
        return jsonify(access_token=token), 200
    
    return jsonify({'msg': 'Bad credentials'}), 401

# Protect endpoints
@app.route('/api/scan/start', methods=['POST'])
@jwt_required()
def start_scan():
    user = get_jwt_identity()  # Get logged-in username
    # ...
```

**Frontend Integration:**
```javascript
// webui/src/services/api.js
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:5000'
});

// Add token to all requests
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const login = (username, password) =>
    api.post('/api/login', { username, password });

export const startScan = (paths) =>
    api.post('/api/scan/start', { paths });
```

---

### 4.2 Confirmation for Deletions

**Goal:** Prevent accidental deletions with extra confirmation for risky files.

```javascript
// webui/src/components/DeleteConfirm.jsx
function DeleteConfirm({ selectedFiles, onConfirm, onCancel }) {
    const [confirmText, setConfirmText] = useState('');
    const [doubleCheck, setDoubleCheck] = useState(false);
    
    const hasSystemFiles = selectedFiles.some(f => f.stars <= 2);
    const totalSize = selectedFiles.reduce((sum, f) => sum + f.size_gb, 0);
    
    const handleConfirm = () => {
        // System files need "DELETE" typed
        if (hasSystemFiles && confirmText !== 'DELETE') {
            alert('Type "DELETE" to confirm deletion of system files');
            return;
        }
        
        // Permanent delete needs double checkbox
        if (selectedFiles.some(f => f.method === 'permanent') && !doubleCheck) {
            alert('Check the box to confirm permanent deletion');
            return;
        }
        
        onConfirm();
    };
    
    return (
        <div className="delete-confirm">
            <h3>⚠️ Confirm Deletion</h3>
            <p>Deleting {selectedFiles.length} items ({totalSize.toFixed(2)} GB)</p>
            
            {hasSystemFiles && (
                <div className="system-warning">
                    <p>⚠️ System files detected! Type "DELETE" to confirm:</p>
                    <input 
                        value={confirmText}
                        onChange={e => setConfirmText(e.target.value)}
                        placeholder='Type "DELETE"'
                    />
                </div>
            )}
            
            {selectedFiles.some(f => f.method === 'permanent') && (
                <label>
                    <input 
                        type="checkbox"
                        checked={doubleCheck}
                        onChange={e => setDoubleCheck(e.target.checked)}
                    />
                    I understand this is IRREVERSIBLE
                </label>
            )}
            
            <div className="file-list">
                {selectedFiles.map(f => (
                    <div key={f.path} className={`file-item stars-${f.stars}`}>
                        ⭐{f.stars} {f.path} - {f.reason}
                    </div>
                ))}
            </div>
            
            <button onClick={handleConfirm}>Confirm Delete</button>
            <button onClick={onCancel}>Cancel</button>
        </div>
    );
}
```

---

### 4.3 Audit Logging

**Goal:** Track all deletions with user, timestamp, reason, and outcome.

```python
# server/audit.py
import sqlite3
from datetime import datetime

class AuditLogger:
    def __init__(self, db_path='audit.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS deletions (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user TEXT,
                path TEXT,
                size_gb REAL,
                method TEXT,
                reason TEXT,
                outcome TEXT,
                ip_address TEXT
            )
        ''')
        self.conn.commit()
    
    def log_deletion(self, user, path, size_gb, method, reason, outcome, ip):
        self.conn.execute('''
            INSERT INTO deletions (timestamp, user, path, size_gb, method, reason, outcome, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), user, path, size_gb, method, reason, outcome, ip))
        self.conn.commit()
    
    def get_logs(self, user=None, limit=100):
        query = 'SELECT * FROM deletions'
        params = []
        if user:
            query += ' WHERE user = ?'
            params.append(user)
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()
```

**Usage in API:**
```python
# server/api.py
from .audit import AuditLogger

audit = AuditLogger()

@app.route('/api/delete', methods=['POST'])
@jwt_required()
def delete_files():
    user = get_jwt_identity()
    paths = request.json.get('paths', [])
    method = request.json.get('method', 'recycle')
    
    for path in paths:
        # ... perform deletion ...
        outcome = 'success' if success else 'failed'
        
        # Log to audit
        audit.log_deletion(
            user=user,
            path=path,
            size_gb=size_gb,
            method=method,
            reason='User requested',
            outcome=outcome,
            ip=request.remote_addr
        )
    
    return jsonify({'status': 'complete'}), 200

# Admin endpoint to view logs
@app.route('/api/admin/audit', methods=['GET'])
@jwt_required()
def view_audit_logs():
    user = get_jwt_identity()
    if not is_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403
    
    logs = audit.get_logs(limit=1000)
    return jsonify({'logs': logs}), 200
```

---

### 4.4 Rate Limiting

**Goal:** Prevent abuse (DDoS, rapid scans).

```python
# server/ratelimit.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/scan/start', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")  # Max 5 scans per minute
def start_scan():
    # ...
```

---

## Impact Analysis

### Positive Impacts
| Impact Area | Before | After | Improvement |
|------------|--------|-------|--------------|
| **Security** | None | JWT auth + rate limiting | ✅ Enterprise-ready |
| **Accountability** | None | Audit logs | ✅ GDPR/HIPAA compliant |
| **Safety** | Y/N prompt | Typed confirm + double-check | ✅ 2x safer |
| **Scalability** | Single user | Multi-user support | ✅ 1000+ users |

### Risks
- ⚠️ **Complexity** - JWT, audit logs add 1000+ lines of code
- ⚠️ **Performance** - Audit logging adds ~10ms per deletion
- ⚠️ **User friction** - Login required, extra confirmations

### Mitigation
- **Progressive rollout** - Make auth optional at first (Phase 4 ends)
- **Async logging** - Audit writes in background thread
- **Remember me** - Long-lived JWT tokens (30 days)

---

## Need Requirements

### Development Needs
| Resource | Requirement | Purpose |
|----------|--------------|---------|
| **Flask-JWT-Extended** | `pip install flask-jwt-extended` | Authentication |
| **SQLite** | Built-in | Audit logs (Phase 4) |
| **PostgreSQL** | `pip install psycopg2` | Multi-user (Phase 5) |
| **Flask-Limiter** | `pip install flask-limiter` | Rate limiting |

### Human Resources
- **1 Backend developer** (Python/Auth) - 2 months
- **1 Security auditor** (part-time) - 2 weeks (review)
- **1 DevOps engineer** (DB setup) - 2 weeks

### Infrastructure
- **PostgreSQL server** - For multi-user support
- **Redis** - For JWT token blacklist (logout)
- **Log monitoring** - ELK stack (Elasticsearch, Logstash, Kibana)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| **Auth success rate** | >99% | Login endpoint logs |
| **Audit log completeness** | 100% | Manual audit |
| **Rate limit triggers** | <1% of users | Limiter logs |
| **Security vulnerabilities** | 0 critical | Penetration testing |
| **User complaints** | <5/month | Support tickets |

---

## Deliverables

### End of Month 9:
- [ ] JWT authentication (register, login, protected endpoints)
- [ ] Login form in web UI
- [ ] Token stored in localStorage

### End of Month 10:
- [ ] Audit logging (SQLite) for all deletions
- [ ] Admin panel to view audit logs
- [ ] Rate limiting (5 scans/minute per user)

### End of Month 11:
- [ ] PostgreSQL migration (from SQLite)
- [ ] Multi-user support (user isolation)
- [ ] Documentation (`docs/SECURITY.md`)

### End of Month 12:
- [ ] Penetration testing complete
- [ ] Security audit passed
- [ ] Load testing (1000+ concurrent users)
- [ ] **SysScan v2.0 released** (Enterprise-ready!)

---

**Phase 4 transforms SysScan from a consumer tool into an enterprise-grade, secure, auditable platform ready for organizational deployment.**
