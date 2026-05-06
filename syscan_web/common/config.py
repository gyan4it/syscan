"""
Configuration management for SysCan.
Handles loading/saving settings from config files.
"""

import os
import json

DEFAULT_CONFIG = {
    'scan': {
        'min_size_gb': 1,
        'exclude_patterns': [
            'C:/Users/*/Documents',
            'C:/Users/*/Pictures',
            'C:/Users/*/Videos',
            'C:/Users/*/Music',
            'C:/Users/*/Desktop',
            'C:/Windows',
            'C:/ProgramData',
            'C:/Program Files',
            'C:/Program Files (x86)'
        ],
        'specific_paths': [
            '%APPDATA%\\Apple Computer\\MobileSync\\Backup',
            '%USERPROFILE%\\.local\\share\\opencode\\log',
            '%LOCALAPPDATA%\\npm-cache',
            '%TEMP%',
            '%LOCALAPPDATA%\\Temp'
        ]
    },
    'parallel': {
        'max_workers': 256,
        'mem_per_worker_mb': 50
    },
    'output': {
        'report_path': '~/Desktop/SystemChecking/cleanup_report.json',
        'log_level': 'INFO'
    }
}

class Config:
    """Manages SysCan configuration."""

    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.expanduser('~/.syscan/config.json')
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    self._deep_update(self.config, user_config)
            except Exception as e:
                print(f'Warning: Could not load config: {e}')

    def save(self):
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _deep_update(self, base, update):
        """Deep merge update dict into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, *keys, default=None):
        """Get config value by nested keys."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value):
        """Set config value by nested keys."""
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
