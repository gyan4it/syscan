"""
Auto-update mechanism for SysScan Agent.
Checks GitHub Releases for newer versions and auto-updates.
"""

import requests
import os
import sys
import zipfile
import tempfile
from packaging import version


class AgentUpdater:
    """Handles checking and applying updates for the agent."""
    
    def __init__(self, current_version='1.0.0'):
        self.current_version = current_version
        self.update_url = 'https://api.github.com/repos/gyan4it/syscan/releases/latest'
        self.download_url_template = 'https://github.com/gyan4it/syscan/releases/download/{version}/SysScanAgent-{platform}.zip'
    
    def check_for_update(self):
        """
        Check if a newer version is available.
        
        Returns:
            Version string if update available, None otherwise
        """
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(self.update_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            latest = response.json()['tag_name'].lstrip('v')
            
            if version.parse(latest) > version.parse(self.current_version):
                print(f"🔄 Update available: v{latest} (current: v{self.current_version})")
                return latest
            else:
                print(f"✅ Agent is up-to-date (v{self.current_version})")
                return None
                
        except Exception as e:
            print(f"❌ Update check failed: {e}")
            return None
    
    def download_and_install(self, version):
        """
        Download and install the update.
        
        Args:
            version: Version string to install (e.g., '1.1.0')
        """
        try:
            # Detect platform
            import platform
            system = platform.system()
            
            if system == 'Windows':
                platform_name = 'Windows'
            elif system == 'Linux':
                platform_name = 'Linux'
            elif system == 'Darwin':
                platform_name = 'macOS'
            else:
                print(f"❌ Unsupported platform: {system}")
                return False
            
            # Download URL
            url = self.download_url_template.format(
                version=version,
                platform=platform_name
            )
            
            print(f"⬇️ Downloading update from {url}...")
            
            # Download to temp file
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'update.zip')
            
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ Downloaded to {zip_path}")
            
            # Extract update
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"✅ Extracted to {extract_dir}")
            
            # TODO: Replace current executable with new one
            # This is platform-specific and requires careful handling
            print("⚠️ Auto-update install not yet implemented")
            print(f"Please manually replace the agent executable with the new version in {extract_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
            return False


if __name__ == '__main__':
    # Test update check
    updater = AgentUpdater(current_version='1.0.0')
    latest = updater.check_for_update()
    
    if latest:
        print(f"Would update to: {latest}")
        # updater.download_and_install(latest)
