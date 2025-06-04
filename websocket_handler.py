#!/usr/bin/env python3
"""
Enhanced WebSocket Handler with Direct TCG Agent Integration
Uses agent.py directly as the master copy for consistent behavior
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def get_table():
    """Get DynamoDB table for connections"""
    table_name = os.environ.get('CONNECTIONS_TABLE_NAME')
    if not table_name:
        raise ValueError("CONNECTIONS_TABLE_NAME environment variable not set")
    return dynamodb.Table(table_name)

def connect_handler(event, context):
    """Handle WebSocket connection"""
    try:
        connection_id = event['requestContext']['connectionId']
        table = get_table()
        
        # Store connection with TTL (24 hours from now)
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        
        table.put_item(
            Item={
                'connectionId': connection_id,
                'ttl': ttl,
                'connectedAt': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Connection {connection_id} stored successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error in connect_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to connect'})
        }

def disconnect_handler(event, context):
    """Handle WebSocket disconnection"""
    try:
        connection_id = event['requestContext']['connectionId']
        table = get_table()
        
        # Remove connection from table
        table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        logger.info(f"Connection {connection_id} removed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error in disconnect_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to disconnect'})
        }

def send_message_to_connection(endpoint_url: str, connection_id: str, message: Dict[str, Any]) -> bool:
    """Send message to a specific WebSocket connection"""
    try:
        client = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        return True
    except client.exceptions.GoneException:
        logger.info(f"Connection {connection_id} is gone")
        return False
    except Exception as e:
        logger.error(f"Error sending message to {connection_id}: {str(e)}")
        return False

def parse_websocket_message(body: str) -> Dict[str, Any]:
    """Parse and validate WebSocket message"""
    try:
        message_data = json.loads(body)
        
        # Validate required fields
        if not isinstance(message_data, dict):
            raise ValueError("Message must be a JSON object")
        
        action = message_data.get('action', 'message')
        message_text = message_data.get('message', '')
        session_id = message_data.get('sessionId', message_data.get('session_id'))
        cart_id = message_data.get('cartId', message_data.get('cart_id'))
        
        # Validate message content for message actions
        if action == 'message' and not message_text:
            raise ValueError("Message content is required for 'message' action")
        
        return {
            'action': action,
            'message': message_text,
            'session_id': session_id,
            'cart_id': cart_id,
            'raw_data': message_data
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Message parsing error: {e}")

def process_streaming_message(endpoint_url: str, connection_id: str, input_text: str, session_id: str, cart_id: Optional[str] = None) -> bool:
    """Process a message with streaming agent and send events to WebSocket client"""
    try:
        from agent import initialize_agent
        
        # Initialize streaming agent
        streaming_agent = initialize_agent(streaming=True)
        
        # Prepare input text
        if cart_id:
            input_text += f" (Cart ID: {cart_id})"
        
        # Access the streaming callback handler's events queue
        callback_handler = streaming_agent.callback_handler
        if hasattr(callback_handler, 'events_queue'):
            # Clear any existing events
            callback_handler.events_queue.clear()
        else:
            logger.error("Streaming callback handler not properly configured")
            return False
        
        # Process the message with the agent
        logger.info(f"Processing streaming message: {input_text[:100]}...")
        response = streaming_agent(input_text)
        
        # Send all captured events to the WebSocket client
        events_sent = 0
        if hasattr(callback_handler, 'events_queue'):
            for event in callback_handler.events_queue:
                success = send_message_to_connection(endpoint_url, connection_id, event)
                if success:
                    events_sent += 1
                else:
                    logger.warning(f"Failed to send event to {connection_id}: {event.get('type', 'unknown')}")
        
        # Send final response as text if no events were captured
        if events_sent == 0:
            final_message = {
                'type': 'text',
                'content': str(response),
                'complete': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            send_message_to_connection(endpoint_url, connection_id, final_message)
            events_sent = 1
        
        logger.info(f"Sent {events_sent} streaming events to {connection_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in process_streaming_message: {e}")
        
        # Send error message to client
        error_message = {
            'type': 'error',
            'error': f"Streaming processing failed: {str(e)}",
            'error_type': 'streaming_processing_error',
            'timestamp': datetime.utcnow().isoformat()
        }
        send_message_to_connection(endpoint_url, connection_id, error_message)
        return False

def message_handler(event, context):
    """Handle WebSocket messages with direct TCG Agent integration"""
    try:
        connection_id = event['requestContext']['connectionId']
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        endpoint_url = f"https://{domain_name}/{stage}"
        
        # Parse the incoming message
        try:
            message_data = parse_websocket_message(event.get('body', '{}'))
        except ValueError as e:
            # Send error response for invalid messages
            error_response = {
                'type': 'error',
                'error': str(e),
                'error_type': 'invalid_message',
                'timestamp': datetime.utcnow().isoformat(),
                'connectionId': connection_id
            }
            send_message_to_connection(endpoint_url, connection_id, error_response)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(e)})
            }
        
        logger.info(f"Received {message_data['action']} from {connection_id}: {message_data['message'][:100]}...")
        
        # Handle different action types
        if message_data['action'] == 'ping':
            # Handle ping requests
            response_message = {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat(),
                'connectionId': connection_id
            }
            
        elif message_data['action'] == 'status':
            # Handle status requests using agent.py directly
            try:
                from agent import handle_enhanced_health_check
                health_response = handle_enhanced_health_check({})
                health_data = json.loads(health_response['body'])
                
                response_message = {
                    'type': 'status',
                    'status': health_data,
                    'timestamp': datetime.utcnow().isoformat(),
                    'connectionId': connection_id
                }
            except Exception as e:
                response_message = {
                    'type': 'error',
                    'error': f"Status check failed: {str(e)}",
                    'error_type': 'status_error',
                    'timestamp': datetime.utcnow().isoformat(),
                    'connectionId': connection_id
                }
                
        elif message_data['action'] == 'message':
            # Handle message requests with streaming TCG Agent
            try:
                # Send processing status first
                status_message = {
                    'type': 'status',
                    'status': 'processing',
                    'timestamp': datetime.utcnow().isoformat(),
                    'connectionId': connection_id
                }
                send_message_to_connection(endpoint_url, connection_id, status_message)
                
                # Process with streaming agent
                success = process_streaming_message(
                    endpoint_url, 
                    connection_id, 
                    message_data['message'],
                    message_data['session_id'] or f"ws-{connection_id}",
                    message_data['cart_id']
                )
                
                if success:
                    # Send completion message
                    response_message = {
                        'type': 'complete',
                        'timestamp': datetime.utcnow().isoformat(),
                        'connectionId': connection_id
                    }
                else:
                    response_message = {
                        'type': 'error',
                        'error': 'Failed to process streaming message',
                        'error_type': 'streaming_error',
                        'timestamp': datetime.utcnow().isoformat(),
                        'connectionId': connection_id
                    }
                    
            except Exception as e:
                logger.error(f"Agent processing error: {e}")
                response_message = {
                    'type': 'error',
                    'error': f"Agent processing failed: {str(e)}",
                    'error_type': 'agent_error',
                    'timestamp': datetime.utcnow().isoformat(),
                    'connectionId': connection_id
                }
        else:
            # Handle unknown actions
            response_message = {
                'type': 'error',
                'error': f"Unknown action: {message_data['action']}",
                'error_type': 'unknown_action',
                'supported_actions': ['message', 'ping', 'status'],
                'timestamp': datetime.utcnow().isoformat(),
                'connectionId': connection_id
            }
        
        # Send response back to the client
        success = send_message_to_connection(endpoint_url, connection_id, response_message)
        
        if success:
            logger.info(f"Response sent to {connection_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Message processed successfully'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send response'})
            }
        
    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        
        # Try to send error response to client
        try:
            connection_id = event['requestContext']['connectionId']
            domain_name = event['requestContext']['domainName']
            stage = event['requestContext']['stage']
            endpoint_url = f"https://{domain_name}/{stage}"
            
            error_response = {
                'type': 'error',
                'error': f"Internal server error: {str(e)}",
                'error_type': 'internal_error',
                'timestamp': datetime.utcnow().isoformat(),
                'connectionId': connection_id
            }
            send_message_to_connection(endpoint_url, connection_id, error_response)
        except:
            pass  # If we can't send error response, just log it
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process message'})
        }
