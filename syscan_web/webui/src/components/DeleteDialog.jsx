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

export default DeleteDialog;
