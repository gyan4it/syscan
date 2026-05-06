"""
Linux-specific scanner and deleter for SysScan Agent.
"""

import os
import subprocess


class LinuxScanner:
    """Linux-specific scanner using native tools."""
    
    def get_scan_paths(self):
        """Return Linux-specific paths to scan."""
        return [
            '/home',
            '/var/tmp',
            '/tmp',
            os.path.expanduser('~/.cache'),
            os.path.expanduser('~/.local/share'),
            '/var/log',
            '/usr/local/src'
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


class LinuxDeleter:
    """Linux-specific deletion using trash-cli or permanent delete."""
    
    def send_to_trash(self, path):
        """
        Send file/folder to Linux trash (restorable).
        Uses trash-cli if available, otherwise uses permanent delete.
        """
        try:
            # Try trash-cli first
            result = subprocess.run(
                ['trash', path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # trash-cli not installed, fall back to permanent delete
            print(f"trash-cli not found, permanently deleting {path}")
            return self.permanent_delete(path)
    
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
