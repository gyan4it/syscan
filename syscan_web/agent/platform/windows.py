"""
Windows-specific scanner and deleter for SysScan Agent.
"""

import os
import ctypes
from ctypes import wintypes


class WindowsScanner:
    """Windows-specific scanner using Windows APIs."""
    
    def get_scan_paths(self):
        """Return Windows-specific paths to scan."""
        paths = ['C:/']
        
        # Add common Windows paths
        specific_paths = [
            os.path.expandvars(r'%APPDATA%\Apple Computer\MobileSync\Backup'),
            os.path.expandvars(r'%USERPROFILE%\.local\share\opencode\log'),
            os.path.expandvars(r'%LOCALAPPDATA%\npm-cache'),
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%LOCALAPPDATA%\Temp'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\Docker'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache')
        ]
        
        for path in specific_paths:
            if os.path.exists(path):
                paths.append(path.replace('\\', '/'))
        
        return paths
    
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
        scan_paths_norm = [os.path.normpath(p) for p in scan_paths]
        
        current_user = os.environ.get('USERNAME', '')
        
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            
            try:
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    
                    # Skip root-level scan folders
                    if item_path in scan_paths_norm:
                        continue
                    
                    # Skip direct user profile root
                    if current_user and item_path.lower() == os.path.normpath(f'C:/Users/{current_user}').lower():
                        continue
                    
                    cells.append(item_path)
            except (PermissionError, OSError):
                pass
        
        return cells


class WindowsDeleter:
    """Windows-specific deletion using Recycle Bin."""
    
    def send_to_recycle_bin(self, path):
        """Send file/folder to Windows Recycle Bin (restorable)."""
        class SHFILEOPSTRUCT(ctypes.Structure):
            _fields_ = [
                ('hwnd', wintypes.HWND),
                ('wFunc', wintypes.UINT),
                ('pFrom', wintypes.LPCWSTR),
                ('pTo', wintypes.LPCWSTR),
                ('fFlags', wintypes.UINT),
                ('fAnyOperationsAborted', wintypes.BOOL),
                ('hNameMapping', wintypes.LPVOID),
                ('lpszProgressTitle', wintypes.LPCWSTR)
            ]
        
        FO_DELETE = 3
        FOF_ALLOWUNDO = 0x40
        FOF_NOCONFIRMATION = 0x10
        FOF_SILENT = 0x4
        
        op = SHFILEOPSTRUCT()
        op.wFunc = FO_DELETE
        op.pFrom = ctypes.c_wchar_p(path + '\0')
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
        
        ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return ret == 0 and not op.fAnyOperationsAborted
    
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
    
    def delete_multiple(self, paths, method='recycle'):
        """Delete multiple items."""
        results = []
        
        for path in paths:
            if method == 'recycle':
                success = self.send_to_recycle_bin(path)
            else:
                success = self.permanent_delete(path)
            
            results.append((path, success))
        
        return results
