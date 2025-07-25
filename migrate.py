#!/usr/bin/env python3
"""
Migration helper script for the gym management system.
This script provides easy commands for managing database migrations.
"""

import subprocess
import sys
import os
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
    if len(sys.argv) < 2:
        print("""
🚀 Gym Management Migration Helper

Usage:
  python migrate.py <command>

Commands:
  status      - Show current migration status
  create      - Create a new migration (use: python migrate.py create "migration message")
  upgrade     - Apply all pending migrations
  downgrade   - Rollback last migration
  history     - Show migration history
  reset       - Reset database (WARNING: This will delete all data!)
  """)
        return

    command = sys.argv[1].lower()

    if command == "status":
        run_command("alembic current", "Checking migration status")
        run_command("alembic heads", "Checking migration heads")
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message: python migrate.py create 'your message'")
            return
        message = sys.argv[2]
        run_command(f'alembic revision --autogenerate -m "{message}"', f"Creating migration: {message}")
        
    elif command == "upgrade":
        run_command("alembic upgrade head", "Applying all pending migrations")
        
    elif command == "downgrade":
        run_command("alembic downgrade -1", "Rolling back last migration")
        
    elif command == "history":
        run_command("alembic history", "Showing migration history")
        
    elif command == "reset":
        print("⚠️  WARNING: This will delete all data in the database!")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        if confirm.lower() == "yes":
            run_command("alembic downgrade base", "Resetting to base")
            run_command("alembic upgrade head", "Applying all migrations")
        else:
            print("❌ Reset cancelled")
            
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' for help")

if __name__ == "__main__":
    main() 