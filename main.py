from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.v1.endpoints import websocket
from app.core.init_db import init_db

app = FastAPI(
    title="Gym Management API",
    description="Backend API for Gym Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["GET, POST, PUT, DELETE, OPTIONS"],
    allow_headers=["*"],
)

# Include WebSocket router first (without prefix)
app.include_router(websocket.router)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startapp")
async def startapp():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Gym Management API is running!"}

@app.get("/health")
def health():
    return {"message": "Gym Management API is running!"}