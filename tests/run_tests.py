#!/usr/bin/env python3
"""
Simple script to run user endpoint tests
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Main function"""
    print("🚀 User Endpoints Test Runner")
    print("=" * 40)
    
    # Check if server is running
    print("Checking if server is running...")
    try:
        import requests
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️  Server responded but not as expected")
    except Exception as e:
        print(f"❌ Server is not running: {str(e)}")
        print("Please start the server first with: python main.py")
        return False
    
    # Run the test script
    success = run_command("python test_users.py", "Running user endpoint tests")
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 