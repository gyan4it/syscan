"""
Utility functions for SysCan agent modules.
"""

import os
import sys
import time
import ctypes  # Moved to top (fix for utils.py)

def format_size(size_bytes):
    """
    Convert bytes to human-readable format (GB, MB, KB).
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string like "1.50 GB" or "500.00 MB"
    """
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"

def format_time(seconds):
    """
    Format seconds into human-readable time.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string like "5m 30s" or "1h 20m"
    """
    if seconds < 60:
        return f'{int(seconds)}s'
    elif seconds < 3600:
        return f'{int(seconds / 60)}m {int(seconds % 60)}s'
    else:
        return f'{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m'

def progress_bar(percent, prefix='Progress', suffix='', length=20):
    """
    Display a text-based progress bar.
    
    Args:
        percent: Progress percentage (0-100)
        prefix: Text before the bar
        suffix: Text after the bar
        length: Length of the bar in characters
    """
    filled = int(length * percent // 100)
    bar = '#' * filled + '-' * (length - filled)
    print(f'{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def display_tree(path, max_depth=3, current_depth=0):
    """
    Display directory tree structure.
    
    Args:
        path: Root path to display
        max_depth: Maximum depth to traverse
        current_depth: Current recursion depth (internal use)
    """
    if current_depth > max_depth:
        return
    try:
        items = os.listdir(path)
    except:
        return
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        prefix = '└── ' if is_last else '├── '
        indent = '    ' * current_depth
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            print(f'{indent}{prefix}{item}/')
            display_tree(full_path, max_depth, current_depth + 1)
        else:
            try:
                size = os.path.getsize(full_path)
                print(f'{indent}{prefix}{item} ({format_size(size)})')
            except:
                print(f'{indent}{prefix}{item} (size unavailable)')

def run_as_admin():
    """
    Request admin privileges (Windows only).
    
    Returns:
        True if already admin, otherwise exits with code 0 after relaunching
    """
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    script = os.path.abspath(sys.argv[0])
    args = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv[1:]])
    ret = ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, f'"{script}" {args}', None, 1)
    if ret > 32:
        sys.exit(0)
    else:
        print("Failed to elevate to admin privileges.")
        sys.exit(1)
