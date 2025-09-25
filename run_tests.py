#!/usr/bin/env python3
"""
Test runner script for version support assistant.
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main test runner function."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = True
    
    # Run unit tests only (fast)
    if not run_command(
        ["python3", "-m", "pytest", "tests/test_models.py", "tests/test_utils.py", "tests/test_release_signoff.py", "-v"],
        "Unit Tests (Models, Utils & Release Sign-off)"
    ):
        success = False
    
    # Run MCP tool tests with mocking
    if not run_command(
        ["python3", "-m", "pytest", "tests/test_version_support.py", "tests/test_release_signoff.py", "-v"],
        "Unit Tests (Version Support & Release Sign-off)"
    ):
        success = False
    
    # Run integration tests with mocks
    if not run_command(
        ["python3", "-m", "pytest", "tests/test_integration.py", "-v", "-m", "integration", "--ignore-glob=*live*"],
        "Integration Tests (Mocked)"
    ):
        success = False
    
    # Run all tests
    if not run_command(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"],
        "All Tests"
    ):
        success = False
    
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print('='*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())