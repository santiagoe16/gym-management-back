#!/usr/bin/env python3
"""
Gym Management Backend Startup Script
Initializes database and starts the FastAPI server
"""

import uvicorn
from app.core.init_db import init_db

if __name__ == "__main__":
    print("🚀 Starting Gym Management Backend...")
    
    # Initialize database and create default users
    print("📊 Initializing database...")
    init_db()
    
    # Start the server
    print("🌐 Starting server...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    ) 