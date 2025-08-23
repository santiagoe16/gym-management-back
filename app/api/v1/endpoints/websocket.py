from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
import json
from datetime import datetime
import base64

import pytz
from sqlmodel import Session, select
from app.core.database import get_normal_session
from app.core.methods import get_user_by_email
from app.core.security import verify_password
from app.core.websocket_service import websocket_service
from app.core.encryption_service import encryption_service
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter()

# WebSocket with user authentication
@router.websocket( "/user/{user_id}/{gym_id}" )
async def websocket_user_endpoint( websocket: WebSocket, user_id: str, gym_id: str ):
    await websocket_service.connect( websocket, user_id, None )

    try:
        while True:
            data = await websocket.receive_text()

            print( data )

            gym_websocket = await websocket_service.get_gym_connection( gym_id )

            if not gym_websocket:
                await websocket_service.send_message( websocket, {
                    "type": "error",
                    "error": "No se encontró la conexión del gimnasio"
                } )

                continue

            try:
                message_data = json.loads( data )

                type = message_data.get( "type" )

                if type == "user":
                    await websocket_service.send_message( 
                        gym_websocket, {
                            "type": "user",
                            "id": message_data.get( "id" )
                        } 
                    )

                else:
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
async def websocket_gym_endpoint( websocket: WebSocket, gym_id: str ):
    await websocket_service.connect( websocket, None, gym_id )

    try:
        last_index = 0
        user_id = None

        while True:
            data = await websocket.receive_text()

            if user_id:
                user_websocket = await websocket_service.get_user_connection( user_id )

                if not user_websocket:
                    await websocket_service.send_message( user_websocket, {
                        "type": "error",
                        "error": "No se encontró la conexión del usuario"
                    } )

                    continue

            try:
                message_data = json.loads( data )

                type = message_data.get( "type" )

                if type == "login":
                    session = get_normal_session()

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

                    user_id = user.id

                    user_websocket = await websocket_service.get_user_connection( user_id )

                    if not user_websocket:
                        await websocket_service.send_message( user_websocket, {
                            "type": "error",
                            "error": "No se encontró la conexión del usuario"
                        } )

                        continue

                    await websocket_service.send_message( websocket, { "type": "connected" } )
                    await websocket_service.send_message( user_websocket, { "type": "fingerprint_connected" } )
           
                elif type == "user":
                    session = get_normal_session()
                    id = message_data.get( "id" )

                    user = session.exec( select( User ).where( User.id == id ) ).first()

                    if not user:
                        await websocket_service.send_message( websocket, {
                            "type": "error",
                            "error": "Usuario no encontrado"
                        } )

                        await websocket_service.send_message( user_websocket, {
                            "type": "user_error",
                            "error": "Usuario no encontrado"
                        } )

                        continue

                    await websocket_service.send_message( user_websocket, { "type": "user_established" } )

                    await websocket_service.send_message( 
                        websocket, 
                        { 
                            "type": "start_enrollment",
                            "id": user.id,
                            "document_id": user.document_id,
                            "full_name": user.full_name,
                            "email": user.email
                        } 
                    )

                elif type == "disconnect":
                    await websocket_service.disconnect( websocket )

                    break

                elif type == "download_templates":
                    session = get_normal_session()
                    
                    users = session.exec( 
                        select( User ).where( User.gym_id == user.gym_id, User.role == UserRole.USER )
                        .offset( last_index )
                        .limit( 20 )
                    ).all()

                    if len( users ) == 0:
                        await websocket_service.send_message( websocket, { "type": "download_templates_completed" } )

                        last_index = 0

                        continue

                    users_data = []

                    for user in users:
                        users_data.append( {
                            "id": user.id,
                            "document_id": user.document_id,
                            "full_name": user.full_name,
                            "email": user.email,
                            "fingerprint1": base64.b64encode( await encryption_service.decrypt_byte_array( user.fingerprint1 ) ).decode() if user.fingerprint1 else None,
                            "fingerprint2": base64.b64encode( await encryption_service.decrypt_byte_array( user.fingerprint2 ) ).decode() if user.fingerprint2 else None
                        } )

                    last_index += len( users ) + 1

                    await websocket_service.send_message( websocket, {
                        "type": "template_data_set",
                        "data": users_data
                    } )
                    
                elif type == "enrollment_completed":
                    fingerprint_data = message_data.get( "fingerprint1" )
                    fingerprint_data2 = message_data.get( "fingerprint2" )
                    
                    if not fingerprint_data:
                        await websocket_service.send_message( websocket, {
                            "type": "enrollment_error",
                            "error": "Huella digital 1 faltante"
                        })

                        await websocket_service.send_message( user_websocket, {
                            "type": "enrollment_error",
                            "error": "Huella digital 1 faltante"
                        })

                        continue

                    if not fingerprint_data2:
                        await websocket_service.send_message( websocket, {
                            "type": "enrollment_error",
                            "error": "Huella digital 2 faltante"
                        })

                        await websocket_service.send_message( user_websocket, {
                            "type": "enrollment_error",
                            "error": "Huella digital 2 faltante"
                        })

                        continue
                        
                    # Decode base64 fingerprint data
                    fingerprint_bytes = base64.b64decode( fingerprint_data )
                    
                    # Encrypt the fingerprint data
                    encrypted_fingerprint = await encryption_service.encrypt_byte_array( fingerprint_bytes )

                    user.fingerprint1 = encrypted_fingerprint

                    fingerprint_bytes = base64.b64decode( fingerprint_data2 )

                    encrypted_fingerprint = await encryption_service.encrypt_byte_array( fingerprint_bytes )

                    user.fingerprint2 = encrypted_fingerprint

                    user.updated_at = datetime.now( pytz.timezone('America/Bogota') )

                    session.add( user )
                    session.commit()
                    session.refresh( user )

                    await websocket_service.send_message( user_websocket, {
                        "type": "enrollment_completed",
                        "message": "Huella digital almacenada exitosamente"
                    } )

                else:
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
