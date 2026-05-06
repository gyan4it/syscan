"""
Platform detection and scanner factory for SysScan Agent.
Provides cross-platform support (Windows, Linux, macOS).
"""

import platform
from pathlib import Path

# Import platform-specific modules
try:
    from .windows import WindowsScanner, WindowsDeleter
except ImportError:
    WindowsScanner = None
    WindowsDeleter = None

try:
    from .linux import LinuxScanner, LinuxDeleter
except ImportError:
    LinuxScanner = None
    LinuxDeleter = None

try:
    from .macos import MacScanner, MacDeleter
except ImportError:
    MacScanner = None
    MacDeleter = None


def get_platform_scanner():
    """
    Factory function to get the appropriate scanner for current platform.
    
    Returns:
        Tuple of (scanner, deleter) for current platform
        
    Raises:
        Exception if platform is not supported
    """
    system = platform.system()
    
    if system == 'Windows':
        if WindowsScanner is None:
            raise Exception("Windows support not available")
        return WindowsScanner(), WindowsDeleter()
    
    elif system == 'Linux':
        if LinuxScanner is None:
            raise Exception("Linux support not available")
        return LinuxScanner(), LinuxDeleter()
    
    elif system == 'Darwin':  # macOS
        if MacScanner is None:
            raise Exception("macOS support not available")
        return MacScanner(), MacDeleter()
    
    else:
        raise Exception(f'Unsupported platform: {system}')


def get_platform_info():
    """
    Get current platform information.
    
    Returns:
        Dictionary with platform details
    """
    return {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor()
    }


__all__ = [
    'get_platform_scanner',
    'get_platform_info',
    'WindowsScanner',
    'WindowsDeleter',
    'LinuxScanner',
    'LinuxDeleter',
    'MacScanner',
    'MacDeleter'
]
