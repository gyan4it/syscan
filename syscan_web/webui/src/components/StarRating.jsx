import React from 'react';

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

// Usage in file list
export function FileListItem({ file, onSelect }) {
    return (
        <div className={`file-item stars-${file.stars}`}>
            <input 
                type="checkbox" 
                checked={file.selected}
                onChange={() => onSelect(file.path)}
            />
            <span className="file-path">{file.path}</span>
            <StarRating stars={file.stars} reason={file.reason} type={file.type} />
            <span className="file-size">{file.size_gb} GB</span>
        </div>
    );
}

export default StarRating;
