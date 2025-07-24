import pymysql
from app.core.config import settings

def check_database_connection():
    """Check database connection and diagnose issues"""
    
    print("=== Gym Management Database Connection Diagnostic ===")
    print(f"Database Name: {settings.DB_NAME}")
    print(f"Database User: {settings.DB_USER}")
    print(f"Database Host: {settings.DB_HOST}")
    print(f"Database Port: {settings.DB_PORT}")
    print()
    
    # Test 1: Try to connect without specifying database
    print("Test 1: Connecting to MySQL server without database...")
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=int(settings.DB_PORT)
        )
        print("✅ Successfully connected to MySQL server")
        
        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]
            
            if settings.DB_NAME in databases:
                print(f"✅ Database '{settings.DB_NAME}' exists")
            else:
                print(f"❌ Database '{settings.DB_NAME}' does not exist")
                print("   You need to create the database first.")
                print("   You can do this by:")
                print("   1. Connecting to MySQL as root")
                print(f"   2. Running: CREATE DATABASE {settings.DB_NAME};")
                print(f"   3. Running: GRANT ALL PRIVILEGES ON {settings.DB_NAME}.* TO '{settings.DB_USER}'@'localhost';")
                print("   4. Running: FLUSH PRIVILEGES;")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to MySQL server: {str(e)}")
        print("   Possible solutions:")
        print("   1. Check if MySQL is running")
        print("   2. Verify host, port, username, and password")
        print("   3. Make sure the user has permission to connect")
        return False
    
    # Test 2: Try to connect with database
    print("\nTest 2: Connecting to specific database...")
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        print(f"✅ Successfully connected to database '{settings.DB_NAME}'")
        
        with conn.cursor() as cursor:
            # Check if tables exist
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            # All expected tables based on our models
            expected_tables = [
                'gyms',           # Gym model
                'users',          # User model
                'plans',          # Plan model
                'user_plans',     # UserPlan model
                'products',       # Product model
                'sales',          # Sale model
                'measurements',   # Measurement model
                'attendance'      # Attendance model
            ]
            
            print(f"\nChecking for {len(expected_tables)} expected tables:")
            missing_tables = []
            
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                    
                    # Check table structure
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    print(f"   - Columns: {len(columns)}")
                    
                else:
                    print(f"❌ Table '{table}' does not exist")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n❌ Missing {len(missing_tables)} tables: {', '.join(missing_tables)}")
                print("   You need to run the database initialization:")
                print("   python -m app.core.init_db")
            else:
                print(f"\n✅ All {len(expected_tables)} tables exist!")
                
                # Check for sample data
                print("\nChecking for sample data:")
                for table in expected_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table}: {count} records")
        
        conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Failed to connect to database '{settings.DB_NAME}': {str(e)}")
        print("   This usually means:")
        print("   1. The database doesn't exist")
        print("   2. The user doesn't have permission to access this database")
        print("   3. The user doesn't have permission to create tables")
        return False

def create_database_simple():
    """Simple database creation without root access"""
    print("\n=== Simple Database Creation ===")
    print("This will try to create the database using the configured user.")
    print("Note: This will only work if the user has CREATE DATABASE privileges.")
    
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
            print(f"✅ Database '{settings.DB_NAME}' created or already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        print("   You need to create the database manually or use root access.")
        return False

def test_table_operations():
    """Test basic operations on tables"""
    print("\n=== Testing Table Operations ===")
    
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            # Test inserting and selecting from gyms table
            print("Testing gyms table operations...")
            cursor.execute("INSERT INTO gyms (name, address, is_active, created_at, updated_at) VALUES ('Test Gym', 'Test Address', 1, NOW(), NOW())")
            cursor.execute("SELECT * FROM gyms WHERE name = 'Test Gym'")
            result = cursor.fetchone()
            if result:
                print("✅ Successfully inserted and retrieved from gyms table")
                # Clean up test data
                cursor.execute("DELETE FROM gyms WHERE name = 'Test Gym'")
            else:
                print("❌ Failed to retrieve data from gyms table")
            
            conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Table operations test failed: {str(e)}")
        return False

def check_alembic_status():
    """Check Alembic migration status"""
    print("\n=== Checking Alembic Migration Status ===")
    
    try:
        import subprocess
        import os
        
        # Check if alembic.ini exists
        if not os.path.exists("alembic.ini"):
            print("❌ alembic.ini not found - Alembic not configured")
            return False
        
        # Check if alembic directory exists
        if not os.path.exists("alembic"):
            print("❌ alembic directory not found - Alembic not configured")
            return False
        
        # Try to get current migration status
        try:
            result = subprocess.run(
                ["alembic", "current"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            current_revision = result.stdout.strip()
            if current_revision:
                print(f"✅ Current migration: {current_revision}")
            else:
                print("⚠️  No migrations applied yet")
            
            # Check for pending migrations
            result = subprocess.run(
                ["alembic", "show"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            if "head" in result.stdout:
                print("✅ Database is up to date with migrations")
            else:
                print("⚠️  Database may not be up to date with migrations")
                print("   Run 'python migrate.py upgrade' to apply pending migrations")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not check Alembic status: {e.stderr}")
            print("   This is normal if no migrations have been created yet")
            return False
            
    except ImportError:
        print("⚠️  Alembic not available - skipping migration check")
        return False
    except Exception as e:
        print(f"⚠️  Error checking Alembic status: {str(e)}")
        return False

def check_schema_compatibility():
    """Check if database schema is compatible with current models"""
    print("\n=== Checking Schema Compatibility ===")
    
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            # Check for required columns in key tables
            required_columns = {
                'users': ['id', 'email', 'full_name', 'role', 'gym_id', 'is_active', 'created_at', 'updated_at'],
                'gyms': ['id', 'name', 'address', 'is_active', 'created_at', 'updated_at'],
                'plans': ['id', 'name', 'price', 'duration_days', 'gym_id', 'is_active', 'created_at', 'updated_at'],
                'products': ['id', 'name', 'price', 'quantity', 'gym_id', 'is_active', 'created_at', 'updated_at'],
                'sales': ['id', 'product_id', 'quantity', 'unit_price', 'total_amount', 'sold_by_id', 'gym_id', 'sale_date', 'created_at', 'updated_at'],
                'attendance': ['id', 'user_id', 'attendance_date', 'check_in_time', 'check_out_time', 'recorded_by_id', 'notes', 'created_at', 'updated_at'],
                'measurements': ['id', 'user_id', 'measurement_date', 'weight', 'height', 'created_at', 'updated_at'],
                'user_plans': ['id', 'user_id', 'plan_id', 'purchased_at', 'expires_at', 'is_active', 'created_at', 'updated_at']
            }
            
            missing_columns = []
            
            for table, expected_columns in required_columns.items():
                cursor.execute(f"DESCRIBE {table}")
                actual_columns = [row[0] for row in cursor.fetchall()]
                
                for column in expected_columns:
                    if column not in actual_columns:
                        missing_columns.append(f"{table}.{column}")
            
            if missing_columns:
                print(f"⚠️  Missing {len(missing_columns)} expected columns:")
                for column in missing_columns[:10]:  # Show first 10
                    print(f"   - {column}")
                if len(missing_columns) > 10:
                    print(f"   ... and {len(missing_columns) - 10} more")
                print("   Consider running migrations to update the schema")
            else:
                print("✅ Database schema appears compatible with current models")
        
        conn.close()
        return len(missing_columns) == 0
        
    except Exception as e:
        print(f"⚠️  Could not check schema compatibility: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting database diagnostic...")
    success = check_database_connection()
    
    if success:
        print("\n" + "="*50)
        print("DATABASE IS READY!")
        print("="*50)
        print("✅ Database connection successful")
        print("✅ All tables exist")
        print("✅ Ready to run the application")
        print()
        print("You can now start the application with:")
        print("   uvicorn main:app --reload")
        print()
        
        # Test table operations
        test_table_operations()
        
        # Check Alembic migration status
        check_alembic_status()
        
        # Check schema compatibility
        check_schema_compatibility()
        
    else:
        print("\n" + "="*50)
        print("MANUAL SETUP REQUIRED")
        print("="*50)
        print("To fix the database connection, you need to:")
        print()
        print("1. Connect to MySQL as root:")
        print("   mysql -u root -p")
        print()
        print("2. Create the database:")
        print(f"   CREATE DATABASE {settings.DB_NAME};")
        print()
        print("3. Create the user (if it doesn't exist):")
        print(f"   CREATE USER '{settings.DB_USER}'@'localhost' IDENTIFIED BY '{settings.DB_PASSWORD}';")
        print()
        print("4. Grant permissions:")
        print(f"   GRANT ALL PRIVILEGES ON {settings.DB_NAME}.* TO '{settings.DB_USER}'@'localhost';")
        print("   FLUSH PRIVILEGES;")
        print()
        print("5. Exit MySQL:")
        print("   EXIT;")
        print()
        print("6. Initialize the database:")
        print("   python -m app.core.init_db")
        print()
        print("7. Set up Alembic migrations (optional but recommended):")
        print("   python migrate.py init")
        print()
        print("8. Start the application:")
        print("   uvicorn main:app --reload")
        print() 