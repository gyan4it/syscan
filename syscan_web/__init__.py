"""
SysCan Web Package.
Modular Python system analyzer and cleaner.
"""

__version__ = '0.1.0'

from .common import Config
from .agent import GridScanner, FileAnalyzer, FileDeleter

__all__ = [
    'Config',
    'GridScanner',
    'FileAnalyzer',
    'FileDeleter'
]
