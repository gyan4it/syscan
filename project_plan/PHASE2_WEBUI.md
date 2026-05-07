# Phase 2: Web UI Development (Months 3-6)

## Overview
**Duration:** 3 months  
**Goal:** Build a modern web interface with file tree checkboxes, star ratings, and delete dialogs.

---

## Why This Phase?

### Problem Statement
The API (Phase 1) provides data, but users need a **friendly interface** to:
1. **See file tree** with checkboxes to select items
2. **Understand what to delete** (star ratings + reasons)
3. **Choose delete method** (Recycle Bin vs Permanent)
4. **Visualize progress** with real-time updates

### User Experience Goals
- ⚡ **Fast interaction** - <100ms response time
- 🎯 **Clear recommendations** - Know exactly what's safe to delete
- 🛡️ **Safe operations** - Confirmations, warnings for system files
- 📊 **Detailed view** - Tree structure, file sizes, last accessed dates

---

## How to Implement

### 2.1 File Tree with Checkboxes

**Goal:** Users can select individual files/folders or "Select All"

```jsx
// webui/src/components/FileTree.jsx
import React, { useState, useEffect } from 'react';
import Tree from 'react-checkbox-tree';
import 'react-checkbox-tree/lib/react-checkbox-tree.css';

function FileTree({ files, onSelectionChange }) {
    const [checked, setChecked] = useState([]);
    const [expanded, setExpanded] = useState([]);
    
    // Convert flat file list to tree structure
    const treeData = useMemo(() => buildTree(files), [files]);
    
    const handleCheck = (checkedItems) => {
        setChecked(checkedItems);
        onSelectionChange(checkedItems);
    };
    
    const handleSelectAll = () => {
        const allPaths = getAllPaths(treeData);
        setChecked(allPaths);
        onSelectionChange(allPaths);
    };
    
    return (
        <div className="file-tree">
            <div className="tree-actions">
                <button onClick={handleSelectAll}>
                    ☑️ Select All ({checked.length} selected)
                </button>
                <button onClick={() => { setChecked([]); onSelectionChange([]); }}>
                    ☐ Clear Selection
                </button>
            </div>
            
            <Tree
                nodes={treeData}
                checked={checked}
                expanded={expanded}
                onCheck={handleCheck}
                onExpand={setExpanded}
                icons={customIcons}
            />
        </div>
    );
}

// Helper: Convert flat list to tree structure
function buildTree(files) {
    const root = [];
    
    files.forEach(file => {
        const parts = file.path.split('/');
        let current = root;
        
        parts.forEach((part, index) => {
            let existing = current.find(item => item.value === part);
            if (!existing) {
                existing = {
                    value: file.path,
                    label: `${part} (${file.size_gb} GB) ⭐${file.stars}`,
                    children: []
                };
                current.push(existing);
            }
            current = existing.children;
        });
    });
    
    return root;
}
```

**Key Features:**
- ✅ Checkboxes on each node
- ✅ "Select All" button (checks all files)
- ✅ Visual indicators (⭐ stars, GB size)
- ✅ Expandable/collapsible nodes

---

### 2.2 Star Ratings & Recommendations

**Goal:** Show why each file should be deleted (1-5 stars)

```jsx
// webui/src/components/StarRating.jsx
function StarRating({ stars, reason, type }) {
    const starColors = {
        5: '#28a745', // Green - Safe to delete
        4: '#17a2b8', // Blue - Probably safe
        3: '#ffc107', // Yellow - Review required
        2: '#fd7e14', // Orange - Be careful
        1: '#dc3545', // Red - Do NOT delete
        0: '#6c757d'  // Gray - System file
    };
    
    return (
        <div className="star-rating" style={{ color: starColors[stars] }}>
            {'⭐'.repeat(stars)}
            {'☆'.repeat(5 - stars)}
            <span className="reason"> - {reason}</span>
            <span className={`type-badge type-${type}`}>{type}</span>
        </div>
    );
}

// Usage in file list:
<FileTree
    files={files.map(f => ({
        ...f,
        label: (
            <div>
                <span>{f.path}</span>
                <StarRating stars={f.stars} reason={f.reason} type={f.type} />
            </div>
        )
    })}
/>
```

**Star Rating Logic (from analyzer.py):**
```python
# agent/analyzer.py
def get_recommendation(file_path, size_gb):
    """Return star rating (1-5) and recommendation"""
    
    # npm cache (safe)
    if 'npm-cache' in file_path:
        return {'stars': 5, 'reason': 'Safe to delete - can re-download', 'type': 'cache'}
    
    # iPhone backup (review needed)
    if 'MobileSync' in file_path:
        return {'stars': 3, 'reason': 'iPhone backup - review if needed', 'type': 'backup'}
    
    # Log files (safe)
    if file_path.endswith('.log'):
        return {'stars': 5, 'reason': 'Old log file - safe to delete', 'type': 'log'}
    
    # System files (never)
    if is_system_file(file_path):
        return {'stars': 0, 'reason': 'SYSTEM FILE - DO NOT DELETE', 'type': 'system'}
    
    # Default (unknown)
    return {'stars': 2, 'reason': 'Unknown file - review before deleting', 'type': 'unknown'}
```

---

### 2.3 Delete Dialog with Options

**Goal:** Choose "Recycle Bin" (restorable) or "Permanent Delete"

```jsx
// webui/src/components/DeleteDialog.jsx
import React, { useState } from 'react';

function DeleteDialog({ selectedFiles, onConfirm, onCancel }) {
    const [method, setMethod] = useState('recycle');
    const [confirmText, setConfirmText] = useState('');
    const [showWarning, setShowWarning] = useState(false);
    
    const totalSize = selectedFiles.reduce((sum, f) => sum + f.size_gb, 0);
    const hasSystemFiles = selectedFiles.some(f => f.stars === 0);
    
    const handleConfirm = () => {
        if (method === 'permanent' && !showWarning) {
            setShowWarning(true);
            return;
        }
        if (hasSystemFiles && confirmText !== 'DELETE') {
            alert('Type "DELETE" to confirm deletion of system files');
            return;
        }
        onConfirm({ paths: selectedFiles.map(f => f.path), method });
    };
    
    return (
        <div className="delete-dialog">
            <h3>Delete {selectedFiles.length} items?</h3>
            <div className="total-size">Total: {totalSize.toFixed(2)} GB</div>
            
            {/* Warning for system files */}
            {hasSystemFiles && (
                <div className="warning">
                    ⚠️ Warning: System files detected! These should NOT be deleted.
                </div>
            )}
            
            {/* Delete method selector */}
            <div className="method-selector">
                <label>
                    <input 
                        type="radio" 
                        name="method" 
                        value="recycle"
                        checked={method === 'recycle'}
                        onChange={() => setMethod('recycle')}
                    />
                    ♻️ Recycle Bin (Restorable)
                </label>
                <label>
                    <input 
                        type="radio" 
                        name="method" 
                        value="permanent"
                        checked={method === 'permanent'}
                        onChange={() => setMethod('permanent')}
                    />
                    ⚠️ Permanent Delete (Irreversible)
                </label>
            </div>
            
            {/* File preview */}
            <div className="file-preview">
                {selectedFiles.map(f => (
                    <div key={f.path} className={`file-item stars-${f.stars}`}>
                        ⭐{f.stars} {f.path} - {f.reason}
                    </div>
                ))}
            </div>
            
            {/* Confirmation for permanent delete */}
            {showWarning && (
                <div className="confirmation">
                    <p>You are about to PERMANENTLY DELETE these files. This cannot be undone!</p>
                    <button onClick={handleConfirm}>Yes, Delete Permanently</button>
                    <button onClick={() => setShowWarning(false)}>Cancel</button>
                </div>
            )}
            
            {/* Confirmation for system files */}
            {hasSystemFiles && (
                <div className="system-confirm">
                    <p>Type "DELETE" to confirm deletion of system files:</p>
                    <input 
                        value={confirmText}
                        onChange={e => setConfirmText(e.target.value)}
                    />
                </div>
            )}
            
            <div className="actions">
                <button className="confirm-btn" onClick={handleConfirm}>
                    Delete {selectedFiles.length} items
                </button>
                <button className="cancel-btn" onClick={onCancel}>
                    Cancel
                </button>
            </div>
        </div>
    );
}
```

---

### 2.4 Real-Time Progress Bar

**Goal:** Show live scan progress (updated every 0.3s via WebSocket)

```jsx
// webui/src/components/ProgressBar.jsx
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

function ProgressBar() {
    const [progress, setProgress] = useState(0);
    const [currentFile, setCurrentFile] = useState('');
    const [found, setFound] = useState(0);
    const [isScanning, setIsScanning] = useState(false);
    
    useEffect(() => {
        const socket = io('http://localhost:5000');
        
        socket.on('scan_started', () => {
            setIsScanning(true);
            setProgress(0);
            setFound(0);
        });
        
        socket.on('scan_progress', (data) => {
            setProgress(data.percent);
            setCurrentFile(data.current_file);
            setFound(data.found_count);
        });
        
        socket.on('scan_complete', (data) => {
            setIsScanning(false);
            setProgress(100);
        });
        
        return () => socket.disconnect();
    }, []);
    
    if (!isScanning && progress === 0) return null;
    
    return (
        <div className="progress-bar">
            <div className="status-text">
                {isScanning ? 'Scanning...' : 'Scan Complete!'}
            </div>
            <div className="current-file" title={currentFile}>
                {currentFile.length > 60 ? currentFile.substring(0, 60) + '...' : currentFile}
            </div>
            <progress value={progress} max="100" />
            <div className="stats">
                Progress: {progress}% | Found: {found} items
            </div>
        </div>
    );
}
```

---

## Impact Analysis

### Positive Impacts
| Impact Area | Before | After | Improvement |
|------------|--------|-------|--------------|
| **User Experience** | CLI only | Modern web UI | ✅ Accessible |
| **File Selection** | Type Y/N for each | Checkboxes + Select All | ✅ 10x faster |
| **Recommendations** | None | Stars + Reasons | ✅ Informed decisions |
| **Visualization** | Text list | Tree view + Progress bar | ✅ Clear overview |
| **Safety** | Confirmation prompt | Warning + Confirmation dialog | ✅ More secure |

### Risks
- ⚠️ **UI complexity** - More code to maintain (React components)
- ⚠️ **Browser compatibility** - Test on Chrome, Firefox, Edge
- ⚠️ **Performance** - Large file trees need virtualization

### Mitigation
- Use **react-window** for virtualized lists (1000+ items)
- **Progressive enhancement** - Start simple, add features
- **Cross-browser testing** - Chrome, Firefox, Edge, Safari

---

## Need Requirements

### Development Needs
| Resource | Requirement | Purpose |
|----------|--------------|---------|
| **React.js 16.8+** | `npx create-react-app` | UI framework |
| **Tailwind CSS** | `npm install tailwindcss` | Styling |
| **react-checkbox-tree** | `npm install react-checkbox-tree` | File tree |
| **Socket.IO-client** | `npm install socket.io-client` | WebSocket |
| **Axios** | `npm install axios` | HTTP requests |

### Human Resources
- **1 Frontend developer** (React/Tailwind) - Full 3 months
- **1 UI/UX designer** (optional) - Month 1 (design mockups)

### Infrastructure
- **Node.js 14+** - For React development
- **npm/yarn** - Package management
- **Webpack/Vite** - Build tool (comes with create-react-app)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| **Page load time** | <2 seconds | Lighthouse audit |
| **Progress update latency** | <100ms | Browser DevTools |
| **File tree render** | <500ms for 200 items | React DevTools Profiler |
| **User satisfaction** | 4+ stars in feedback | Feedback form |
| **UI bug count** | <5 critical bugs | QA testing |

---

## Deliverables

### End of Month 4:
- [ ] **File tree component** - Checkboxes, expand/collapse, select all
- [ ] **Star rating component** - 0-5 stars with colors
- [ ] **Basic delete dialog** - Recycle/Permanent choice

### End of Month 5:
- [ ] **Real-time progress bar** - WebSocket integration
- [ ] **Recommendation engine** - analyzer.py integrated
- [ ] **Responsive design** - Works on mobile/tablet

### End of Month 6:
- [ ] **Complete UI** - All components integrated
- [ ] **E2E tests** - Cypress/Playwright tests
- [ ] **Documentation** - UI component docs (Storybook)

---

**Phase 2 transforms SysScan from an API into a beautiful, user-friendly web application that anyone can use to clean their system safely.**
