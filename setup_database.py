import pymysql
from app.core.config import settings

def setup_database():
    """Setup database and user with proper permissions"""
    
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
            
            print(f"Creating user '{settings.DB_USER}' if it doesn't exist...")
            cursor.execute(f"CREATE USER IF NOT EXISTS '{settings.DB_USER}'@'localhost' IDENTIFIED BY '{settings.DB_PASSWORD}'")
            
            print(f"Granting permissions to user '{settings.DB_USER}' on database '{settings.DB_NAME}'...")
            cursor.execute(f"GRANT ALL PRIVILEGES ON {settings.DB_NAME}.* TO '{settings.DB_USER}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print("Database setup completed successfully!")
            
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def test_connection():
    """Test the connection with the configured user"""
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
            print(f"Connection test successful: {result}")
            
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Gym Management Database Setup Script ===")
    print(f"Database Name: {settings.DB_NAME}")
    print(f"Database User: {settings.DB_USER}")
    print(f"Database Host: {settings.DB_HOST}")
    print(f"Database Port: {settings.DB_PORT}")
    print()
    
    setup_database()
    print()
    test_connection() 