import pymysql
from app.core.config import settings

def setup_database():
    """Setup database and user with proper permissions"""
    
    print("=== Gym Management Database Setup Script ===")
    print(f"Database Name: {settings.DB_NAME}")
    print(f"Database User: {settings.DB_USER}")
    print(f"Database Host: {settings.DB_HOST}")
    print(f"Database Port: {settings.DB_PORT}")
    print()
    
    # Connect to MySQL as root (you'll need to provide root credentials)
    print("Connecting to MySQL as root...")
    print("Please enter your MySQL root password when prompted.")
    
    try:
        # Connect to MySQL server without specifying database
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user='root',  # Use root user
            password=input("Enter MySQL root password: "),
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            print(f"Creating database '{settings.DB_NAME}' if it doesn't exist...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
            print(f"✅ Database '{settings.DB_NAME}' created or already exists")
            
            print(f"Creating user '{settings.DB_USER}' if it doesn't exist...")
            # Drop user if exists and recreate (in case of permission issues)
            cursor.execute(f"DROP USER IF EXISTS '{settings.DB_USER}'@'localhost'")
            cursor.execute(f"CREATE USER '{settings.DB_USER}'@'localhost' IDENTIFIED BY '{settings.DB_PASSWORD}'")
            print(f"✅ User '{settings.DB_USER}' created")
            
            print(f"Granting permissions to user '{settings.DB_USER}' on database '{settings.DB_NAME}'...")
            cursor.execute(f"GRANT ALL PRIVILEGES ON {settings.DB_NAME}.* TO '{settings.DB_USER}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"✅ Permissions granted to user '{settings.DB_USER}'")
            
            print("Database setup completed successfully!")
            
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        print("Possible solutions:")
        print("1. Make sure MySQL is running")
        print("2. Verify root password is correct")
        print("3. Make sure root user has CREATE USER and GRANT privileges")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def test_connection():
    """Test the connection with the configured user"""
    print("\n=== Testing Connection ===")
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Connection test successful: {result}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def verify_database_structure():
    """Verify that the database has the correct structure"""
    print("\n=== Verifying Database Structure ===")
    
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            # Check if tables exist
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'gyms', 'users', 'plans', 'user_plans', 
                'products', 'sales', 'measurements', 'attendance'
            ]
            
            print(f"Found {len(tables)} tables in database")
            print(f"Expected {len(expected_tables)} tables")
            
            missing_tables = []
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
                print("You need to run the database initialization:")
                print("python -m app.core.init_db")
                return False
            else:
                print(f"\n✅ All {len(expected_tables)} tables exist!")
                return True
                
    except Exception as e:
        print(f"❌ Database structure verification failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_sample_data():
    """Create sample data for testing"""
    print("\n=== Creating Sample Data ===")
    
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=int(settings.DB_PORT)
        )
        
        with conn.cursor() as cursor:
            # Check if sample data already exists
            cursor.execute("SELECT COUNT(*) FROM gyms")
            gym_count = cursor.fetchone()[0]
            
            if gym_count == 0:
                print("Creating sample gym...")
                cursor.execute("""
                    INSERT INTO gyms (name, address, is_active, created_at, updated_at) 
                    VALUES ('Sample Gym', '123 Sample Street, City, State 12345', 1, NOW(), NOW())
                """)
                print("✅ Sample gym created")
            else:
                print(f"✅ Sample data already exists ({gym_count} gyms)")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Sample data creation failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    try:
        # Step 1: Setup database and user
        setup_database()
        
        # Step 2: Test connection
        test_connection()
        
        # Step 3: Verify structure (after running init_db)
        print("\n" + "="*50)
        print("DATABASE SETUP COMPLETED!")
        print("="*50)
        print("✅ Database created")
        print("✅ User created with permissions")
        print("✅ Connection test successful")
        print()
        print("Next steps:")
        print("1. Run database initialization:")
        print("   python -m app.core.init_db")
        print()
        print("2. Verify database structure:")
        print("   python check_database.py")
        print()
        print("3. Start the application:")
        print("   uvicorn main:app --reload")
        print()
        
        # Step 4: Ask if user wants to run init_db now
        response = input("Do you want to run the database initialization now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\nRunning database initialization...")
            import subprocess
            try:
                subprocess.run(["python", "-m", "app.core.init_db"], check=True)
                print("✅ Database initialization completed!")
                
                # Verify structure after init
                if verify_database_structure():
                    create_sample_data()
                    print("\n🎉 Everything is ready! You can now start the application.")
                else:
                    print("\n❌ Database structure verification failed.")
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ Database initialization failed: {e}")
        else:
            print("\nRemember to run 'python -m app.core.init_db' before starting the application.")
            
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("Please check the error messages above and try again.") 