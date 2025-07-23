#!/usr/bin/env python3
"""
Gym Management Database Migration Helper
Provides easy commands for database migrations using Alembic
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def main():
    if len(sys.argv) < 2:
        print("🚀 Gym Management Database Migration Helper")
        print("\nUsage:")
        print("  python migrate.py init                    # Initialize database with current schema")
        print("  python migrate.py create <message>        # Create a new migration")
        print("  python migrate.py upgrade                 # Apply pending migrations")
        print("  python migrate.py downgrade               # Rollback last migration")
        print("  python migrate.py history                 # Show migration history")
        print("  python migrate.py current                 # Show current migration")
        print("  python migrate.py status                  # Show migration status")
        print("\nExamples:")
        print("  python migrate.py create add_user_table")
        print("  python migrate.py create update_product_schema")
        return

    command = sys.argv[1]

    if command == "init":
        print("🔧 Initializing database with current schema...")
        # Create initial migration
        result = run_command("alembic revision --autogenerate -m 'Initial migration'")
        if result:
            print("✅ Initial migration created")
            print("📝 Applying migration...")
            run_command("alembic upgrade head")
            print("✅ Database initialized successfully!")
        else:
            print("❌ Failed to create initial migration")

    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a message for the migration")
            print("Example: python migrate.py create add_new_column")
            return
        
        message = sys.argv[2]
        print(f"📝 Creating migration: {message}")
        result = run_command(f"alembic revision --autogenerate -m '{message}'")
        if result:
            print("✅ Migration created successfully!")
            print("💡 Run 'python migrate.py upgrade' to apply the migration")
        else:
            print("❌ Failed to create migration")

    elif command == "upgrade":
        print("⬆️  Applying pending migrations...")
        result = run_command("alembic upgrade head")
        if result:
            print("✅ Migrations applied successfully!")
        else:
            print("❌ Failed to apply migrations")

    elif command == "downgrade":
        print("⬇️  Rolling back last migration...")
        result = run_command("alembic downgrade -1")
        if result:
            print("✅ Migration rolled back successfully!")
        else:
            print("❌ Failed to rollback migration")

    elif command == "history":
        print("📚 Migration history:")
        result = run_command("alembic history")
        if result:
            print(result)
        else:
            print("❌ Failed to get migration history")

    elif command == "current":
        print("📍 Current migration:")
        result = run_command("alembic current")
        if result:
            print(result)
        else:
            print("❌ Failed to get current migration")

    elif command == "status":
        print("📊 Migration status:")
        result = run_command("alembic show")
        if result:
            print(result)
        else:
            print("❌ Failed to get migration status")

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' for help")

if __name__ == "__main__":
    main() 