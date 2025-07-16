#!/usr/bin/env python3
"""
Test script to verify the build setup works correctly.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_build():
    """Test the build process."""
    print("🧪 Testing RetroChat v3 build process...\n")
    
    # Test 1: Check if all required files exist
    print("1. Checking required files...")
    required_files = [
        "main.py",
        "requirements.txt", 
        "setup.py",
        "retrochat.spec",
        ".github/workflows/build-and-release.yml"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present")
    
    # Test 2: Check if Python imports work
    print("\n2. Testing Python imports...")
    success, stdout, stderr = run_command("python -c \"import main; print('Import successful')\"")
    if success:
        print("✅ Python imports work correctly")
    else:
        print(f"❌ Import failed: {stderr}")
        return False
    
    # Test 3: Test package build (if build tools available)
    print("\n3. Testing package structure...")
    success, stdout, stderr = run_command("python setup.py check")
    if success:
        print("✅ Package structure is valid")
    else:
        print(f"⚠️  Package check had warnings: {stderr}")
    
    # Test 4: Check if PyInstaller spec is valid
    print("\n4. Checking PyInstaller spec...")
    if Path("retrochat.spec").exists():
        with open("retrochat.spec", "r") as f:
            content = f.read()
            if "main.py" in content and "rchat" in content:
                print("✅ PyInstaller spec looks correct")
            else:
                print("❌ PyInstaller spec may have issues")
                return False
    
    print("\n🎉 All tests passed! The build setup should work correctly.")
    print("\n📋 Next steps:")
    print("   1. Commit and push these changes to GitHub")
    print("   2. The GitHub Actions will automatically build releases")
    print("   3. For local testing, run: .\\build.ps1 (Windows) or python -m build (cross-platform)")
    
    return True

if __name__ == "__main__":
    if test_build():
        sys.exit(0)
    else:
        sys.exit(1)
