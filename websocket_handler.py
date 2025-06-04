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
            # Handle message requests with TCG Agent directly
            try:
                from agent import initialize_agent
                
                # Initialize the agent
                agent = initialize_agent()
                
                # Prepare input text
                input_text = message_data['message']
                if message_data['cart_id']:
                    input_text += f" (Cart ID: {message_data['cart_id']})"
                
                # Get response from the agent
                agent_response = agent(input_text)
                
                # Send successful agent response
                response_message = {
                    'type': 'agent_response',
                    'response': str(agent_response),
                    'session_id': message_data['session_id'] or f"ws-{connection_id}",
                    'capabilities': {
                        'deck_recommendations': True,
                        'shopify_integration': True,
                        'available_tools': ['get_competitive_decks', 'search_shop_catalog']
                    },
                    'service_info': {
                        'name': 'One Piece TCG Strands Agent',
                        'version': '2.0',
                        'interface': 'WebSocket'
                    },
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
