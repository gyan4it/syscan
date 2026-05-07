"""
SysCan Common Package.
Shared configuration and constants.
"""

from .config import Config
from .constants import (
    DEFAULT_SCAN_PATHS,
    SPECIFIC_PATHS,
    DEFAULT_EXCLUDES,
    MIN_SIZE_BYTES,
    DEFAULT_MAX_WORKERS,
    API_HOST,
    API_PORT,
    API_PREFIX
)

__all__ = [
    'Config',
    'DEFAULT_SCAN_PATHS',
    'SPECIFIC_PATHS',
    'DEFAULT_EXCLUDES',
    'MIN_SIZE_BYTES',
    'DEFAULT_MAX_WORKERS',
    'API_HOST',
    'API_PORT',
    'API_PREFIX'
]
