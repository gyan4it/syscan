import React, { useState, useMemo } from 'react';
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
        <div className="bg-white p-4 rounded-lg shadow-md mb-4">
            <div className="flex gap-2 mb-3">
                <button 
                    onClick={handleSelectAll}
                    className="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded border border-gray-300"
                >
                    ☑️ Select All ({checked.length} selected)
                </button>
                <button 
                    onClick={() => { setChecked([]); onSelectionChange([]); }}
                    className="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded border border-gray-300"
                >
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

// Helper: Get all paths from tree
function getAllPaths(nodes) {
    let paths = [];
    nodes.forEach(node => {
        paths.push(node.value);
        if (node.children && node.children.length > 0) {
            paths = paths.concat(getAllPaths(node.children));
        }
    });
    return paths;
}

// Custom icons for tree nodes
const customIcons = {
    check: <i className="fas fa-check-square text-blue-500" />,
    uncheck: <i className="far fa-square" />,
    halfCheck: <i className="fas fa-minus-square text-blue-400" />,
    expand: <i className="fas fa-chevron-right text-gray-600" />,
    collapse: <i className="fas fa-chevron-down text-gray-600" />
};

export default FileTree;
