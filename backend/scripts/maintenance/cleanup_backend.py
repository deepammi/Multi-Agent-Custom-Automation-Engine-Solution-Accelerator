#!/usr/bin/env python3
"""
Backend cleanup script for removing temporary files and organizing directories
"""
import os
import shutil
import glob
from pathlib import Path

def cleanup_backend():
    """Clean up backend directory"""
    
    # Remove Python cache directories
    cache_dirs = [
        '__pycache__',
        '.pytest_cache',
        '.hypothesis',
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"Removed {cache_dir}")
    
    # Remove .DS_Store files (macOS)
    for ds_store in glob.glob('**/.DS_Store', recursive=True):
        os.remove(ds_store)
        print(f"Removed {ds_store}")
    
    # Clean up temp directory (keep structure)
    temp_dir = Path('temp')
    if temp_dir.exists():
        for item in temp_dir.rglob('*'):
            if item.is_file() and item.name not in ['.gitignore', 'README.md']:
                item.unlink()
                print(f"Removed temp file: {item}")
    
    # Move any remaining Python files to appropriate directories
    remaining_py_files = glob.glob('*.py')
    if remaining_py_files:
        maintenance_dir = Path('scripts/maintenance')
        maintenance_dir.mkdir(parents=True, exist_ok=True)
        
        for py_file in remaining_py_files:
            if py_file != 'organize_files.py':  # Keep the organizer
                shutil.move(py_file, maintenance_dir / py_file)
                print(f"Moved {py_file} to scripts/maintenance/")
    
    print("Backend cleanup complete!")

if __name__ == "__main__":
    cleanup_backend()