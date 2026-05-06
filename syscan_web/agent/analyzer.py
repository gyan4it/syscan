"""
Analyzer module for SysCan.
Handles registry leftovers scanning and file analysis.
"""

import os
import subprocess

# Import constants
from syscan_web.common.constants import REGISTRY_PATHS

# Registry scan PowerShell script
PS_REGISTRY_LEFTOVERS = """
$regPaths = @(
    'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
)
$leftovers = @()
foreach ($regPath in $regPaths) {{
    Get-ItemProperty $regPath -ErrorAction SilentlyContinue | ForEach-Object {{
        $installLocation = $_.InstallLocation
        $uninstallString = $_.UninstallString
        $displayName = $_.DisplayName
        if (-not $displayName) {{ return }}
        if ($installLocation -and (Test-Path $installLocation)) {{
            $hasExe = Get-ChildItem -Path $installLocation -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $hasExe) {{
                $leftovers += $installLocation
            }}
        }}
        if ($uninstallString) {{
            $path = $uninstallString -replace '.*?"([^"]+)".*', '$1' -replace '^([^"]+)\\.exe.*', '$1'
            if ($path -and $path -match '^[A-Za-z]:\\\\') {{
                $uninstallerExists = Test-Path $path
                $parentDir = Split-Path $path -Parent
                if (-not $uninstallerExists -and $parentDir -and (Test-Path $parentDir)) {{
                    $hasOtherExe = Get-ChildItem -Path $parentDir -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
                    if (-not $hasOtherExe) {{
                        $leftovers += $parentDir
                    }}
                }}
            }}
        }}
    }}
}}
$leftovers | Sort-Object -Unique | ForEach-Object {{ Write-Output $_ }}
"""

class FileAnalyzer:
    """
    Analyzes found items and scans for registry leftovers.
    
    Provides methods to analyze scan results and scan Windows registry
    for program leftovers (uninstalled programs with remaining folders).
    """
    
    def scan_registry_leftovers(self):
        """
        Scan Windows registry for program leftovers.
        
        Returns:
            List of tuples (path, size) for leftover folders
        """
        try:
            result = subprocess.run(
                ['powershell', '-Command', PS_REGISTRY_LEFTOVERS],
                capture_output=True,
                text=True,
                timeout=60
            )
            leftovers = []
            for line in result.stdout.strip().split('\n'):
                path = line.strip()
                if path and os.path.exists(path):
                    size = self._get_size(path)
                    leftovers.append((path, size))
            return leftovers
        except Exception as e:
            print(f'\nError scanning registry: {e}')
            return []
    
    def _get_size(self, path):
        """
        Calculate total size of a path.
        
        Args:
            path: File or directory path
            
        Returns:
            Total size in bytes
        """
        total = 0
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        except:
            pass
        return total
    
    def analyze_items(self, items):
        """
        Analyze scanned items and return summary.
        
        Args:
            items: List of (path, size) tuples
            
        Returns:
            Dictionary with analysis results
        """
        if not items:
            return {
                'total_items': 0,
                'total_size_gb': 0,
                'largest_item': None,
                'categories': {}
            }
        
        total_size = sum(size for _, size in items)
        total_size_gb = total_size / (1024**3)
        
        # Find largest item
        largest = max(items, key=lambda x: x[1])
        
        # Categorize by parent directory
        categories = {}
        for path, size in items:
            parent = os.path.dirname(path)
            categories[parent] = categories.get(parent, 0) + size
        
        return {
            'total_items': len(items),
            'total_size_gb': round(total_size_gb, 2),
            'largest_item': {'path': largest[0], 'size_gb': round(largest[1] / (1024**3), 2)},
            'categories': {k: round(v / (1024**3), 2) for k, v in categories.items()}
        }
