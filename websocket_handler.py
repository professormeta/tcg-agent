"""
WebSocket Handler for Streaming Responses
Manages WebSocket connections and streaming functionality
"""

import json
import os
import boto3
import logging
from typing import Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def get_connections_table():
    """Get the DynamoDB connections table"""
    table_name = os.environ.get('CONNECTIONS_TABLE_NAME')
    if not table_name:
        raise ValueError("CONNECTIONS_TABLE_NAME environment variable not set")
    return dynamodb.Table(table_name)

def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    WebSocket handler for connection management and message routing
    """
    try:
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        logger.info(f"WebSocket event - Route: {route_key}, Connection: {connection_id}")
        
        if route_key == '$connect':
            return handle_connect(connection_id, event)
        elif route_key == '$disconnect':
            return handle_disconnect(connection_id)
        elif route_key == 'message':
            return handle_message(connection_id, event)
        else:
            logger.warning(f"Unknown route: {route_key}")
            return {"statusCode": 400}
            
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {str(e)}")
        return {"statusCode": 500}

def handle_connect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle new WebSocket connection"""
    try:
        table = get_connections_table()
        
        # Extract session info from query parameters
        query_params = event.get('queryStringParameters') or {}
        session_id = query_params.get('sessionId', f"ws-session-{int(time.time())}")
        
        # Store connection info
        table.put_item(
            Item={
                'connectionId': connection_id,
                'sessionId': session_id,
                'connectedAt': int(time.time()),
                'ttl': int(time.time()) + 3600  # 1 hour TTL
            }
        )
        
        logger.info(f"WebSocket connection established: {connection_id} for session {session_id}")
        
        return {"statusCode": 200}
        
    except Exception as e:
        logger.error(f"Error handling connect: {str(e)}")
        return {"statusCode": 500}

def handle_disconnect(connection_id: str) -> Dict[str, Any]:
    """Handle WebSocket disconnection"""
    try:
        table = get_connections_table()
        
        # Remove connection from table
        table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        logger.info(f"WebSocket connection closed: {connection_id}")
        
        return {"statusCode": 200}
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {str(e)}")
        return {"statusCode": 500}

def handle_message(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming WebSocket message"""
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', 'chat')
        
        if action == 'chat':
            return handle_chat_message(connection_id, body)
        else:
            logger.warning(f"Unknown action: {action}")
            return {"statusCode": 400}
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        return {"statusCode": 500}

def handle_chat_message(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle chat message and invoke main Lambda function"""
    try:
        # Get connection info
        table = get_connections_table()
        response = table.get_item(Key={'connectionId': connection_id})
        
        if 'Item' not in response:
            logger.error(f"Connection not found: {connection_id}")
            return {"statusCode": 404}
        
        connection_info = response['Item']
        session_id = connection_info['sessionId']
        
        # Prepare payload for main Lambda function
        payload = {
            'body': json.dumps({
                'message': message.get('message', ''),
                'sessionId': session_id,
                'connectionId': connection_id,
                'stream': True,
                'cartId': message.get('cartId'),
                'action': 'chat'
            })
        }
        
        # Invoke main Lambda function asynchronously for streaming
        main_function_name = os.environ.get('MAIN_FUNCTION_NAME')
        if not main_function_name:
            raise ValueError("MAIN_FUNCTION_NAME environment variable not set")
        
        lambda_client.invoke(
            FunctionName=main_function_name,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Chat message forwarded to main function for connection {connection_id}")
        
        return {"statusCode": 200}
        
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}")
        return {"statusCode": 500}
