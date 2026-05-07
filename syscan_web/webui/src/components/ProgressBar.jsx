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
        <div className="progress-bar" data-testid="progress-bar">
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

export default ProgressBar;
