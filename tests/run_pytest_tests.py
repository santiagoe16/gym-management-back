#!/usr/bin/env python3
"""
Run all pytest tests for the gym management API
"""

import subprocess
import sys
import os
from datetime import datetime

def run_pytest_tests():
    """Run all pytest tests"""
    print("🚀 Running Gym Management API Pytest Tests")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # Go up to the main project directory
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            script_dir,  # Test directory
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--color=yes"  # Colored output
        ], 
        capture_output=False,  # Show output in real-time
        text=True,
        check=False,
        cwd=parent_dir)  # Run from the main project directory
        
        if result.returncode == 0:
            print(f"\n✅ All pytest tests passed!")
            return True
        else:
            print(f"\n❌ Some pytest tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run pytest tests: {str(e)}")
        return False

def main():
    """Main function"""
    success = run_pytest_tests()
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test suite failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 