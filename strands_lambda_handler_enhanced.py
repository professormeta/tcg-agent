"""
Test Lambda Handler - Minimal version for debugging
"""

import json
import os
import uuid
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_health_check(event):
    """Handle health check requests"""
    try:
        # Test basic imports
        import boto3
        boto3_version = boto3.__version__
        
        # Test Strands import
        strands_available = False
        strands_error = None
        try:
            from strands import Agent
            strands_available = True
            strands_version = "Available"
        except ImportError as e:
            strands_error = str(e)
            strands_version = f"Failed: {strands_error}"
        
        # Test tools import
        tools_available = False
        tools_error = None
        try:
            from tools.deck_recommender import get_competitive_decks
            tools_available = True
            tools_status = "Available"
        except ImportError as e:
            tools_error = str(e)
            tools_status = f"Failed: {tools_error}"
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "healthy",
                "service": "Test One Piece TCG Strands Agent",
                "debug_info": {
                    "boto3_version": boto3_version,
                    "strands_available": strands_available,
                    "strands_status": strands_version,
                    "tools_available": tools_available,
                    "tools_status": tools_status,
                    "python_path": os.environ.get('PYTHONPATH', 'Not set'),
                    "lambda_runtime_dir": os.environ.get('LAMBDA_RUNTIME_DIR', 'Not set'),
                    "lambda_task_root": os.environ.get('LAMBDA_TASK_ROOT', 'Not set')
                },
                "timestamp": str(uuid.uuid4())
            })
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "error",
                "error": str(e),
                "service": "Test Strands Agent"
            })
        }

def handler(event, context):
    """
    Test Lambda handler for debugging
    """
    try:
        logger.info(f"Test handler received event: {json.dumps(event)}")
        
        # Handle health check
        if event.get('httpMethod') == 'GET' or event.get('requestContext', {}).get('http', {}).get('method') == 'GET':
            return handle_health_check(event)
        
        # For non-GET requests, return basic response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "response": "🏴‍☠️ Ahoy! Test handler is working, matey!",
                "service": "Test Strands Agent",
                "timestamp": str(uuid.uuid4())
            })
        }
        
    except Exception as e:
        logger.error(f"Error in test Lambda handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Test handler error",
                "details": str(e)
            })
        }
