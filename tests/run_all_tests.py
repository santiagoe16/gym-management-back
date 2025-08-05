#!/usr/bin/env python3
"""
Master test runner for all Gym Management API endpoints
Run this script to test all endpoints
"""

import subprocess
import sys
import os
from datetime import datetime

# Test modules to run (legacy tests)
LEGACY_TEST_MODULES = [
    "test_users.py",
    "test_gyms.py", 
    "test_plans.py",
    "test_measurements.py",
    "test_sales.py"
]

# Pytest test modules (run with pytest command)
PYTEST_TEST_MODULES = [
    "test_auth_pytest.py",
    "test_attendances_pytest.py",
    "test_products_pytest.py",
    "test_user_plans_pytest.py"
]

def run_test_module(module_name, description):
    """Run a legacy test module and return success status"""
    print(f"\n🔄 Running {description}...")
    print("=" * 60)
    
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(script_dir, module_name)
        
        result = subprocess.run([sys.executable, module_path], 
                              capture_output=True, 
                              text=True, 
                              check=False,
                              cwd=script_dir)  # Run from the tests directory
        
        if result.returncode == 0:
            print(f"PASS {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"FAIL {description} failed")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"FAIL {description} failed with exception: {str(e)}")
        return False

def run_pytest_module(module_name, description):
    """Run a pytest test module and return success status"""
    print(f"\n🔄 Running {description} (pytest)...")
    print("=" * 60)
    
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Go up to the main project directory
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            os.path.join(script_dir, module_name),
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--color=no"  # No color for better output capture
        ], 
        capture_output=True, 
        text=True,
        check=False,
        cwd=parent_dir)  # Run from the main project directory
        
        if result.returncode == 0:
            print(f"PASS {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"FAIL {description} failed")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"FAIL {description} failed with exception: {str(e)}")
        return False

def check_server_running():
    """Check if the server is running"""
    print("🔍 Checking if server is running...")
    
    try:
        import requests
        response = requests.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200:
            print("PASS Server is running on port 8001")
            return True
        else:
            print("⚠️  Server responded but not as expected")
            return False
    except Exception as e:
        print(f"FAIL Server is not running: {str(e)}")
        print("Please start the server first with: python start.py")
        return False

def main():
    """Main function"""
    print("🚀 Gym Management API - Complete Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if server is running
    if not check_server_running():
        return False
    
    print(f"\n📋 Running {len(LEGACY_TEST_MODULES)} legacy test modules...")
    
    # Run legacy test modules
    results = {}
    total_passed = 0
    total_modules = len(LEGACY_TEST_MODULES)
    
    for module in LEGACY_TEST_MODULES:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(script_dir, module)
        
        if os.path.exists(module_path):
            description = module.replace("test_", "").replace(".py", "").title()
            success = run_test_module(module, description)
            results[module] = success
            if success:
                total_passed += 1
        else:
            print(f"⚠️  Test module {module} not found at {module_path}, skipping...")
            results[module] = False
    
    print(f"\n📋 Running {len(PYTEST_TEST_MODULES)} pytest test modules...")
    
    # Run pytest test modules
    for module in PYTEST_TEST_MODULES:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(script_dir, module)
        
        if os.path.exists(module_path):
            description = module.replace("test_", "").replace("_pytest.py", "").title()
            success = run_pytest_module(module, description)
            results[module] = success
            if success:
                total_passed += 1
            total_modules += 1
        else:
            print(f"⚠️  Test module {module} not found at {module_path}, skipping...")
            results[module] = False
            total_modules += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    for module, success in results.items():
        status = "PASS" if success else "FAIL"
        description = module.replace("test_", "").replace(".py", "").title()
        print(f"{status} {description}")
    
    print(f"\n📈 Summary: {total_passed}/{total_modules} test modules passed")
    
    if total_passed == total_modules:
        print("PASS All test modules passed!")
        print("Your Gym Management API is working perfectly!")
    else:
        print("⚠️  Some test modules failed. Check the output above for details.")
        print("🔧 Review the failed tests and fix any issues.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_passed == total_modules

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 