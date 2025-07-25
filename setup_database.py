#!/usr/bin/env python3
"""
Direct database setup script using SQLModel.
This bypasses Alembic and creates tables directly.
"""

import os
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv

# Import all models to register them with SQLModel
from app.models import *

def main():
    print("🚀 Setting up database directly with SQLModel...")
    
    # Load environment variables
    load_dotenv()
    
    # Create database URL
    db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
    
    print(f"📊 Connecting to database: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
    
    # Create engine
    engine = create_engine(db_url, echo=True)
    
    print("🔄 Creating all tables...")
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    print("✅ Database setup completed successfully!")
    print("\n📋 Tables created:")
    
    # List all tables
    with engine.connect() as conn:
        result = conn.execute("SHOW TABLES")
        tables = [row[0] for row in result]
        
        for table in tables:
            print(f"   ✅ {table}")
    
    print(f"\n🎉 Database is ready with {len(tables)} tables!")
    print("\n💡 Next steps:")
    print("   1. Run your application")
    print("   2. Create initial data (gyms, admin users, etc.)")
    print("   3. For future schema changes, use SQLModel's create_all() or switch back to Alembic")

if __name__ == "__main__":
    main() 