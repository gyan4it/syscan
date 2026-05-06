"""
macOS-specific scanner and deleter for SysScan Agent.
"""

import os
import subprocess


class MacScanner:
    """macOS-specific scanner using native tools."""
    
    def get_scan_paths(self):
        """Return macOS-specific paths to scan."""
        return [
            '/Users',
            os.path.expanduser('~/Library/Caches'),
            os.path.expanduser('~/Library/Logs'),
            os.path.expanduser('~/Library/Application Support'),
            os.path.expanduser('~/Downloads'),
            '/tmp',
            '/var/tmp'
        ]
    
    def get_size_fast(self, path):
        """
        Fast size calculation using os.scandir.
        Returns (total_size, error_count) tuple.
        """
        total = 0
        error_count = 0
        
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        size, errors = self.get_size_fast(entry.path)
                        total += size
                        error_count += errors
                except (PermissionError, OSError):
                    error_count += 1
        except (PermissionError, OSError):
            error_count += 1
        
        return total, error_count
    
    def collect_grid_cells(self):
        """Collect directories to scan in parallel."""
        cells = []
        scan_paths = self.get_scan_paths()
        
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            
            try:
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    cells.append(item_path)
            except (PermissionError, OSError):
                pass
        
        return cells


class MacDeleter:
    """macOS-specific deletion using Finder (trash)."""
    
    def send_to_trash(self, path):
        """
        Send file/folder to macOS trash (restorable).
        Uses osascript to tell Finder to delete.
        """
        try:
            script = f'osascript -e "tell app \\"Finder\\" to delete POSIX file \\"{path}\\""'
            result = subprocess.run(
                script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"Error sending to trash: {e}")
            return False
    
    def permanent_delete(self, path):
        """Permanently delete file/folder."""
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting {path}: {e}")
            return False
    
    def delete_multiple(self, paths, method='trash'):
        """Delete multiple items."""
        results = []
        deleter_func = self.send_to_trash if method == 'trash' else self.permanent_delete
        
        for path in paths:
            success = deleter_func(path)
            results.append((path, success))
        
        return results
