from fastapi import WebSocket
from typing import Dict
import json
from datetime import datetime

import pytz
from sqlmodel import Session, select

from app.models.user import User

class WebSocketService:
    def __init__( self ):
        self.user_connections  : Dict[ str, WebSocket ] = {}
        self.gym_connections   : Dict[ str, WebSocket ] = {}
    
    async def connect( self, websocket: WebSocket, user_id: str = None, gym_id: str = None ):
        """Accept WebSocket connection and store it"""
        await websocket.accept()

        if gym_id:
            self.gym_connections[ gym_id ] = websocket
        
        if user_id:
            self.user_connections[ user_id ] = websocket
        
        print( f"WebSocket connected. Total connections: { len( self.user_connections ) + len( self.gym_connections ) }" )
    
    def disconnect( self, websocket: WebSocket ):
        """Remove WebSocket connection"""
        if self.gym_connections:
            for gym_name, connection in self.gym_connections.items():
                if connection == websocket:
                    del self.gym_connections[ gym_name ]

                    break
        
        if self.user_connections:
            for user_id, connection in self.user_connections.items():
                if connection == websocket:
                    del self.user_connections[ user_id ]

                    break
        
        print( f"WebSocket disconnected. Total connections: { len( self.user_connections ) + len( self.gym_connections ) }" )
    
    async def check_user_connection( 
        self,
        websocket: WebSocket,
        user_websocket: WebSocket
    ) -> bool:
        if not user_websocket:
            await websocket_service._send_message( websocket, {
                "type": "error",
                "error": "No se encontró la conexión del usuario"
            } )

            return True
        
        return False
    
    async def check_user( 
        self,
        websocket: WebSocket,
        user: User
    ) -> bool:
        if not user:
            await websocket_service._send_message( websocket, {
                "type": "store_error",
                "error": "Usuario no establecido"
            } )

            return True
        
        return False
    
    async def send_message( self, websocket: WebSocket, message: dict ):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text( json.dumps( message ) )
        except Exception as e:
            print( f"Error sending message: { e }" )

            self.disconnect( websocket )
    
    async def get_user_connection( self, user_id: int ) -> WebSocket:
        """Get the connection of a specific user"""
        for user_id, connection in self.user_connections.items():
            if user_id == user_id:
                return connection
        
        return None
    
    async def get_gym_connection( self, gym_id: int ) -> WebSocket:
        """Get the connection of a specific gym"""
        for gym_id, connection in self.gym_connections.items():
            if gym_id == gym_id:
                return connection
        
        return None

    async def send_to_user( self, user_id: str, message: dict ):
        """Send message to a specific user"""
        for user_id, connection in self.user_connections.items():
            if user_id == user_id:
                await self._send_message( connection, message )
    
    async def send_to_gym( self, gym_id: int, message: dict ):
        """Send message to all connections subscribed to a gym"""
        if gym_id in self.gym_connections:
            await self._send_message( self.gym_connections[ gym_id ], message )
    
    async def handle_fingerprint_message( self, websocket: WebSocket, message_data: dict ):
        """Handle incoming WebSocket messages"""
        try:
            message_type = message_data.get( "type" )
            
            if message_type in self.message_handlers:
                await self.message_handlers[ message_type ]( websocket, message_data )
            else:
                await self._send_message( websocket, {
                    "type": "echo",
                    "original_message": message_data,
                    "timestamp": datetime.now().isoformat()
                } )
                
        except Exception as e:
            await self._send_message( websocket, {
                "type": "error",
                "error": str( e ),
                "timestamp": datetime.now().isoformat()
            }) 
    
    
# Global WebSocket service instance
websocket_service = WebSocketService()
