"""
Deleter module for SysCan.
Handles file/folder deletion (recycle bin & permanent).
"""

import os
import shutil
import ctypes
from ctypes import wintypes

# Define SHFILEOPSTRUCT at module level (FIX for efficiency)
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

class FileDeleter:
    """Handles deletion of files and folders."""

    # Constants at class level (FIX: removed typo underscores)
    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x40
    FOF_NOCONFIRMATION = 0x10
    FOF_SILENT = 0x4

    @staticmethod
    def send_to_recycle_bin(path):
        """Send file/folder to Windows Recycle Bin (restorable)."""
        op = SHFILEOPSTRUCT()
        op.wFunc = FileDeleter.FO_DELETE
        op.pFrom = ctypes.c_wchar_p(path + '\0')
        op.fFlags = FileDeleter.FOF_ALLOWUNDO | FileDeleter.FOF_NOCONFIRMATION | FileDeleter.FOF_SILENT

        ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return ret == 0 and not op.fAnyOperationsAborted

    @staticmethod
    def delete_permanent(path):
        """Permanently delete file/folder (non-restorable)."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_item(self, path, method='recycle'):
        """
        Delete an item.
        method: 'recycle' (default, restorable) or 'permanent'
        Returns: (success: bool, message: str)
        """
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"

        if method == 'recycle':
            print(f'Sending {path} to Recycle Bin...')
            if self.send_to_recycle_bin(path):
                return True, 'Successfully sent to Recycle Bin.'
            else:
                return False, 'Failed to send to Recycle Bin.'  # FIX: Added missing comma
        else:
            print(f'Permanently deleting {path}...')
            success, error = self.delete_permanent(path)
            if success:
                return True, 'Successfully deleted permanently.'
            else:
                return False, f'Error: {error}'

    def delete_multiple(self, items, method='recycle'):
        """
        Delete multiple items.
        items: list of paths
        Returns: list of (path, success, message) tuples
        """
        results = []
        for path in items:
            success, message = self.delete_item(path, method)
            results.append((path, success, message))
        return results
