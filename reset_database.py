#!/usr/bin/env python3
"""
Complete database reset script for gym management system.
This will completely erase all data and start fresh.
"""

import subprocess
import os
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Complete Database Reset for Gym Management System")
    print("⚠️  WARNING: This will completely erase all data!")
    confirm = input("Are you absolutely sure you want to continue? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Reset cancelled")
        return

    print("\n🔄 Starting complete database reset...")

    # Step 1: Drop and recreate database
    print("\n📊 Step 1: Recreating database...")
    if not run_command(
        'mysql -u root -p -e "DROP DATABASE IF EXISTS gym_management; CREATE DATABASE gym_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"',
        "Dropping and recreating database"
    ):
        print("❌ Failed to recreate database")
        return

    # Step 2: Remove all migration files except __init__.py
    print("\n🗂️  Step 2: Cleaning migration files...")
    migration_dir = Path("alembic/versions")
    for file in migration_dir.glob("*.py"):
        if file.name != "__init__.py":
            file.unlink()
            print(f"🗑️  Removed: {file.name}")

    # Step 3: Create fresh initial migration
    print("\n📝 Step 3: Creating initial migration...")
    if not run_command(
        'alembic revision --autogenerate -m "Initial database schema"',
        "Creating initial migration"
    ):
        print("❌ Failed to create initial migration")
        return

    # Step 4: Apply the migration
    print("\n⬆️  Step 4: Applying migration...")
    if not run_command(
        'alembic upgrade head',
        "Applying initial migration"
    ):
        print("❌ Failed to apply migration")
        return

    # Step 5: Verify the setup
    print("\n✅ Step 5: Verifying setup...")
    if not run_command(
        'alembic current',
        "Checking current migration status"
    ):
        print("❌ Failed to verify migration status")
        return

    print("\n🎉 Database reset completed successfully!")
    print("\n📋 What was done:")
    print("   ✅ Database dropped and recreated")
    print("   ✅ All migration files removed")
    print("   ✅ Fresh initial migration created")
    print("   ✅ Migration applied successfully")
    print("   ✅ Database is now ready for use")
    
    print("\n💡 Next steps:")
    print("   1. Run your application")
    print("   2. Create initial data (gyms, admin users, etc.)")
    print("   3. Use 'python migrate.py create \"description\"' for future changes")

if __name__ == "__main__":
    main() 