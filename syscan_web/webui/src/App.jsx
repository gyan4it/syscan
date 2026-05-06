import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProgressBar from './components/ProgressBar';
import FileTree from './components/FileTree';
import StarRating, { FileListItem } from './components/StarRating';
import DeleteDialog from './components/DeleteDialog';

function App() {
    const [files, setFiles] = useState([]);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [isScanning, setIsScanning] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);

    // Fetch files from API
    const fetchFiles = async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/items');
            const filesWithMeta = response.data.items.map(file => ({
                ...file,
                selected: false,
                stars: calculateStars(file.path, file.size_gb),
                reason: getReason(file.path),
                type: getType(file.path)
            }));
            setFiles(filesWithMeta);
        } catch (error) {
            console.error('Error fetching files:', error);
        }
    };

    // Start scan
    const startScan = async () => {
        try {
            setIsScanning(true);
            await axios.post('http://localhost:5000/api/scan');
        } catch (error) {
            console.error('Error starting scan:', error);
        }
    };

    // Calculate star rating based on file path and size
    const calculateStars = (path, sizeGb) => {
        if (path.includes('npm-cache')) return 5;
        if (path.includes('MobileSync')) return 3;
        if (path.endsWith('.log')) return 5;
        if (path.includes('Windows') || path.includes('Program Files')) return 0;
        return 2;
    };

    // Get reason for star rating
    const getReason = (path) => {
        if (path.includes('npm-cache')) return 'Safe to delete - can re-download';
        if (path.includes('MobileSync')) return 'iPhone backup - review if needed';
        if (path.endsWith('.log')) return 'Old log file - safe to delete';
        if (path.includes('Windows')) return 'SYSTEM FILE - DO NOT DELETE';
        return 'Unknown file - review before deleting';
    };

    // Get file type
    const getType = (path) => {
        if (path.includes('npm-cache')) return 'cache';
        if (path.includes('MobileSync')) return 'backup';
        if (path.endsWith('.log')) return 'log';
        if (path.includes('Windows')) return 'system';
        return 'unknown';
    };

    // Handle file selection
    const handleSelectionChange = (selectedPaths) => {
        const selected = files.filter(f => selectedPaths.includes(f.path));
        setSelectedFiles(selected);
    };

    // Handle delete confirmation
    const handleDelete = async ({ paths, method }) => {
        try {
            for (const path of paths) {
                await axios.delete(`http://localhost:5000/api/items/${encodeURIComponent(path)}`, {
                    params: { method }
                });
            }
            setShowDeleteDialog(false);
            fetchFiles(); // Refresh file list
        } catch (error) {
            console.error('Error deleting files:', error);
        }
    };

    // Poll for scan status
    useEffect(() => {
        let interval;
        if (isScanning) {
            interval = setInterval(async () => {
                try {
                    const response = await axios.get('http://localhost:5000/api/scan/status');
                    if (response.data.status === 'complete') {
                        setIsScanning(false);
                        fetchFiles();
                    }
                } catch (error) {
                    console.error('Error checking scan status:', error);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isScanning]);

    return (
        <div className="app">
            <header className="app-header">
                <h1>SysCan Web UI</h1>
                <button 
                    className="scan-btn"
                    onClick={startScan}
                    disabled={isScanning}
                >
                    {isScanning ? 'Scanning...' : 'Start Scan'}
                </button>
            </header>

            <ProgressBar />

            <main className="app-main">
                <div className="file-list">
                    <h2>Found Items ({files.length})</h2>
                    <FileTree 
                        files={files}
                        onSelectionChange={handleSelectionChange}
                    />
                </div>

                {selectedFiles.length > 0 && (
                    <div className="selection-info">
                        <h3>Selected: {selectedFiles.length} items</h3>
                        <button 
                            className="delete-btn"
                            onClick={() => setShowDeleteDialog(true)}
                        >
                            Delete Selected
                        </button>
                    </div>
                )}

                {showDeleteDialog && (
                    <DeleteDialog
                        selectedFiles={selectedFiles}
                        onConfirm={handleDelete}
                        onCancel={() => setShowDeleteDialog(false)}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
