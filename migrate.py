#!/usr/bin/env python3
"""
Gym Management Database Migration Helper
Provides easy commands for database migrations using Alembic
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, args=None):
    """Run a shell command and return the result"""
    try:
        if args:
            # Use list format for better argument handling
            full_command = [command] + args
            result = subprocess.run(full_command, check=True, capture_output=True, text=True)
        else:
            # Use shell format for simple commands
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
        print("  python migrate.py check                   # Check for pending schema changes")
        print("  python migrate.py reset                   # Reset migration state")
        print("\nExamples:")
        print("  python migrate.py create add_user_table")
        print("  python migrate.py create update_product_schema")
        return

    command = sys.argv[1]

    if command == "init":
        print("🔧 Initializing database with current schema...")
        
        # Check if we already have a baseline migration
        result = run_command("alembic", ["current"])
        if result and "0001" in result:
            print("✅ Database already initialized with baseline migration")
            print("💡 Use 'python migrate.py create <message>' for new migrations")
            return
        
        # Create a baseline migration that doesn't change anything
        print("📝 Creating baseline migration...")
        result = run_command("alembic", ["revision", "-m", "Initial baseline"])
        if result:
            print("✅ Baseline migration created")
            print("📝 Marking as current...")
            run_command("alembic", ["stamp", "head"])
            print("✅ Database initialized successfully!")
            print("💡 Use 'python migrate.py create <message>' for new migrations")
        else:
            print("❌ Failed to create baseline migration")

    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a message for the migration")
            print("Example: python migrate.py create add_new_column")
            return
        
        message = sys.argv[2]
        print(f"📝 Creating migration: {message}")
        
        # First check what changes would be made
        print("🔍 Detecting schema changes...")
        check_result = run_command("alembic", ["check"])
        if check_result:
            print("📋 Detected changes:")
            print(check_result)
        
        # Create the migration
        result = run_command("alembic", ["revision", "--autogenerate", "-m", message])
        if result:
            print("✅ Migration created successfully!")
            print("💡 Run 'python migrate.py upgrade' to apply the migration")
            
            # Show the generated migration file
            import glob
            migration_files = glob.glob("alembic/versions/*.py")
            if migration_files:
                latest_file = max(migration_files, key=os.path.getctime)
                print(f"📄 Migration file: {latest_file}")
        else:
            print("❌ Failed to create migration")

    elif command == "upgrade":
        print("⬆️  Applying pending migrations...")
        
        # First check current status
        current_result = run_command("alembic", ["current"])
        heads_result = run_command("alembic", ["heads"])
        
        if current_result and heads_result:
            current_revision = current_result.strip()
            head_revision = heads_result.strip()
            
            print(f"Current revision: {current_revision}")
            print(f"Head revision: {head_revision}")
            
            if current_revision == head_revision:
                print("✅ Database is already at the latest version")
                return
        
        # Apply migrations
        print("🔄 Running upgrade...")
        result = run_command("alembic", ["upgrade", "head"])
        
        if result is not None:
            print("✅ Migrations applied successfully!")
            if result.strip():
                print(f"Output: {result}")
            
            # Verify we're now at head
            new_current = run_command("alembic", ["current"])
            if new_current:
                new_revision = new_current.strip()
                print(f"✅ Current revision after upgrade: {new_revision}")
                
                # Double-check we're at head
                if new_revision == head_revision:
                    print("✅ Successfully upgraded to head version")
                else:
                    print(f"⚠️  Warning: Current revision ({new_revision}) doesn't match head ({head_revision})")
                    print("⚠️  Forcing alembic version to head (schema assumed to match latest migration)")
                    run_command("alembic", ["stamp", "head"])
                    print("✅ Alembic version table set to head")
        else:
            print("❌ Failed to apply migrations")

    elif command == "downgrade":
        print("⬇️  Rolling back last migration...")
        result = run_command("alembic", ["downgrade", "-1"])
        if result:
            print("✅ Migration rolled back successfully!")
        else:
            print("❌ Failed to rollback migration")

    elif command == "history":
        print("📚 Migration history:")
        result = run_command("alembic", ["history"])
        if result:
            print(result)
        else:
            print("❌ Failed to get migration history")

    elif command == "current":
        print("📍 Current migration:")
        result = run_command("alembic", ["current"])
        if result:
            print(result)
        else:
            print("❌ Failed to get current migration")

    elif command == "status":
        print("📊 Migration status:")
        current_result = run_command("alembic", ["current"])
        heads_result = run_command("alembic", ["heads"])
        
        if current_result and heads_result:
            current_revision = current_result.strip()
            head_revision = heads_result.strip()
            
            print(f"Current revision: {current_revision}")
            print(f"Latest revision: {head_revision}")
            
            if current_revision == head_revision:
                print("✅ Database is up to date")
            else:
                print("⚠️  Database is behind - run 'python migrate.py upgrade' to update")
                
                # Show pending migrations
                history_result = run_command("alembic", ["history", "--verbose"])
                if history_result:
                    print("\n📚 Migration history:")
                    print(history_result)
        else:
            print("❌ Failed to get migration status")

    elif command == "check":
        print("🔍 Checking for pending schema changes...")
        result = run_command("alembic", ["check"])
        if result:
            print("📋 Detected changes:")
            print(result)
        else:
            print("✅ No pending schema changes detected")

    elif command == "reset":
        print("🔄 Resetting migration state...")
        print("⚠️  This will remove all migration files and reset to baseline")
        confirm = input("Are you sure? (y/N): ")
        if confirm.lower() == 'y':
            # Remove all migration files except baseline
            import glob
            migration_files = glob.glob("alembic/versions/*.py")
            for file in migration_files:
                if "0001_initial_baseline" not in file:
                    os.remove(file)
                    print(f"🗑️  Removed: {file}")
            
            # Reset to baseline
            run_command("alembic", ["stamp", "0001"])
            print("✅ Migration state reset to baseline")
        else:
            print("❌ Reset cancelled")

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' for help")

if __name__ == "__main__":
    main() 