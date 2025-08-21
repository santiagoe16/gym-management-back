from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
import json
from datetime import datetime
import base64

from sqlmodel import Session, select
from app.core.database import get_session
from app.core.methods import get_user_by_email
from app.core.security import verify_password
from app.core.websocket_service import websocket_service
from app.core.encryption_service import encryption_service
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter()

# WebSocket with user authentication
@router.websocket( "/user/{user_id}" )
async def websocket_user_endpoint( websocket: WebSocket, user_id: str ):
    await websocket_service.connect( websocket, user_id )

    gym_websocket = None

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads( data )

                type = message_data.get( "type" )

                if type == "fingerprint_connected":
                    gym_id = message_data.get( "gym_id" )

                    gym_websocket = await websocket_service.get_gym_connection( gym_id )
                    
                    if not gym_websocket:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "No se encontró la conexión del gimnasio"
                        } )

                        continue

                    await websocket_service.send_message( websocket, {
                        "type": "fingerprint_connection_stablished",
                        "gym_id": gym_id
                    } )

                elif type == "user":
                    if not gym_websocket:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "No se encontró la conexión del gimnasio"
                        } )
                        
                        continue

                    await websocket_service.send_message( gym_websocket, message_data )
            except json.JSONDecodeError as e:
                await websocket_service.send_message( websocket, {
                    "type": "error",
                    "error": f"Error description: { e }",
                    "timestamp": datetime.now().isoformat()
                } )
    except WebSocketDisconnect:
        websocket_service.disconnect( websocket )

# WebSocket with user authentication
@router.websocket( "/gym/{gym_id}" )
async def websocket_gym_endpoint( websocket: WebSocket, gym_id: str, session: Session = Depends( get_session ) ):
    await websocket_service.connect( websocket, None, gym_id )

    user_websocket = None
    user = None
    last_index = 0

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads( data )

                type = message_data.get( "type" )

                if type == "login":
                    login_data = message_data.get( "login_data" )

                    user = get_user_by_email( session, login_data[ "email" ] )
                    
                    if user.role == UserRole.USER:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "Los usuarios no pueden iniciar sesión en el sistema"
                        } )

                        continue
                    
                    if not user.is_active:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "Usuario inactivo"
                        } )

                        continue
                    
                    if not verify_password( login_data[ "password" ], user.hashed_password ):
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "Correo electrónico o contraseña incorrectos"
                        } )
                        
                        continue

                    user_websocket = await websocket_service.get_user_connection( user.id )

                    if not user_websocket:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "No se encontró la conexión del usuario"
                        } )

                        continue

                    await websocket_service.send_message( websocket, { "type": "connected" } )

                    await websocket_service.send_message( user_websocket, { 
                        "type": "fingerprint_connected",
                        "gym_id": gym_id
                    } )
           
                elif type == "user":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    user_id = message_data.get( "user_id" )

                    user = session.exec( select( User ).where( User.id == user_id ) ).first()

                    if not user:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "Usuario no encontrado"
                        } )

                        await websocket_service.send_message( websocket, {
                            "type": "user_error",
                            "error": "Usuario no encontrado"
                        } )

                    await websocket_service.send_message( user_websocket, { "type": "user_established" } )

                    await websocket_service.send_message( 
                        websocket, 
                        { 
                            "type": "start_enrollment",
                            "user_id": user_id,
                            "full_name": user.full_name,
                            "email": user.email
                        } 
                    )

                elif type == "disconnect":
                    await websocket_service.disconnect( websocket )

                    break

                elif type == "store_fingerprint":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    if websocket_service.check_user( user ):
                        continue

                    try:
                        # Get fingerprint data from message
                        fingerprint_data = message_data.get( "fingerprint_data" )

                        if not fingerprint_data:
                            await websocket_service.send_message( websocket, {
                                "type": "store_error",
                                "error": "Datos de huella digital faltantes"
                            })

                            continue
                        
                        # Decode base64 fingerprint data
                        fingerprint_bytes = base64.b64decode( fingerprint_data )
                        
                        # Encrypt the fingerprint data
                        encrypted_fingerprint = encryption_service.encrypt_byte_array( fingerprint_bytes )

                        finger = message_data.get( "finger" )
                        
                        await websocket_service.store_fingerprint_on_user( user, finger, encrypted_fingerprint, session )
                        
                        await websocket_service.send_message( websocket, {
                            "type": "fingerprint_stored",
                            "message": "Huella digital almacenada exitosamente",
                            "user_id": user.id
                        })

                    except Exception as e:
                        await websocket_service.send_message( websocket, {
                            "type": "store_error",
                            "error": f"Error al almacenar huella digital: { str( e ) }"
                        })

                elif type == "finger1_captured":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    await websocket_service.send_message( user_websocket, message_data )

                elif type == "download_templates":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    users = session.exec( 
                        select( User ).where( User.gym_id == user.gym_id, User.role == UserRole.USER )
                        .offset( last_index )
                        .limit( 100 )
                    ).all()

                    if len( users ) == 0:
                        await websocket_service.send_message( websocket, { "type": "download_templates_completed" } )

                        last_index = 0

                        continue

                    last_index += len( users ) + 1

                    await websocket_service.send_message( websocket, {
                        "type": "template_data_set",
                        "data": users
                    } )

                elif type == "user_found":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    await websocket_service.send_message( user_websocket, message_data )
            
                elif type == "user_not_found":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    await websocket_service.send_message( user_websocket, message_data )
            
                elif type == "enrollment_completed":
                    if websocket_service.check_user_connection( user_websocket ):
                        continue

                    await websocket_service.send_message( user_websocket, message_data )
            except json.JSONDecodeError as e:
                await websocket_service.send_message( websocket, {
                    "type": "error",
                    "error": f"Error description: { e }",
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        websocket_service.disconnect( websocket )

# Health check endpoint for WebSocket connections
@router.get( "/ws/health" )
async def websocket_health():
    return {
        "active_connections": len( websocket_service.active_connections ),
        "connected_users": list( websocket_service.user_connections.keys() ),
        "gym_subscriptions": { gym_id: len( connections ) for gym_id, connections in websocket_service.gym_connections.items() },
        "status": "healthy"
    }
