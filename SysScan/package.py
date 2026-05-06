"""
SysScan Download Packager
Creates a ZIP file with all project files for distribution
Run: python package.py
"""

import os
import zipfile
from datetime import datetime

def create_package():
    """Create a ZIP package of SysScan project"""
    # Files to include
    files = [
        'system_cleaner.py',
        'feedback_server.py',
        'feedback.html',
        'README.md',
        'LICENSE',
        'requirements.txt'
    ]

    # Create ZIP file
    zip_name = f'SysScan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            if os.path.exists(file):
                print(f'Adding {file}...')
                zipf.write(file)
            else:
                print(f'Warning: {file} not found, skipping...')

    print(f'\nPackage created: {zip_name}')
    print(f'Size: {os.path.getsize(zip_name) / 1024:.1f} KB')

if __name__ == '__main__':
    create_package()
