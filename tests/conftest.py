"""
Pytest configuration and shared fixtures for TCG Agent tests
"""

import os
import pytest
import boto3
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

# Test configuration
TEST_CONFIG = {
    "api_gateway_endpoint": "https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production",
    "test_session_id": "test-session-12345",
    "test_timeout": 30,
    "environment": "production"
}

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def ssm_client():
    """AWS SSM client for parameter retrieval"""
    try:
        return boto3.client('ssm', region_name='us-east-1')
    except Exception:
        # Return mock if AWS credentials not available
        return Mock()

@pytest.fixture(scope="session")
def test_parameters(ssm_client):
    """Retrieve test parameters from SSM or environment variables"""
    params = {}
    
    # Parameter mappings
    param_mappings = {
        "gumgum_endpoint": "/tcg-agent/production/deck-api/endpoint",
        "gumgum_secret": "/tcg-agent/production/deck-api/secret",
        "shopify_store_url": "/tcg-agent/production/shopify/store-url",
        "shopify_access_token": "/tcg-agent/production/shopify/access-token",
        "langfuse_public_key": "/tcg-agent/production/langfuse/public-key",
        "langfuse_secret_key": "/tcg-agent/production/langfuse/secret-key",
        "langfuse_host": "/tcg-agent/production/langfuse/host"
    }
    
    for key, param_name in param_mappings.items():
        try:
            # Try to get from SSM first
            if hasattr(ssm_client, 'get_parameter'):
                response = ssm_client.get_parameter(
                    Name=param_name, 
                    WithDecryption=True
                )
                params[key] = response['Parameter']['Value']
            else:
                # Fall back to environment variables or defaults
                params[key] = os.getenv(key.upper(), f"mock_{key}")
        except Exception:
            # Use mock values for testing
            params[key] = f"mock_{key}"
    
    return params

@pytest.fixture
def mock_bedrock_client():
    """Mock AWS Bedrock client for testing"""
    mock_client = Mock()
    mock_response = {
        'body': Mock()
    }
    mock_response['body'].read.return_value = b'{"content": [{"text": "{\\"set\\": \\"OP10\\", \\"region\\": \\"west\\", \\"leader\\": \\"OP01-060\\"}"}]}'
    mock_client.invoke_model.return_value = mock_response
    return mock_client

@pytest.fixture
def sample_deck_query():
    """Sample deck query for testing"""
    return "Show me a Red Luffy deck for OP10 in the West region"

@pytest.fixture
def sample_shopify_request():
    """Sample Shopify Remix request format"""
    return {
        "inputText": "Show me booster packs",
        "sessionId": "shopify-test-session",
        "cartId": "test-cart-123"
    }

@pytest.fixture
def expected_agent_response_format():
    """Expected agent response format"""
    return {
        "response": str,
        "sessionId": str,
        "capabilities": dict,
        "service_info": dict
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    test_env = {
        "ENVIRONMENT": "test",
        "AWS_DEFAULT_REGION": "us-east-1",
        "STRANDS_DEBUG": "false"
    }
    
    with patch.dict(os.environ, test_env):
        yield

# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require real API access)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (use mocks, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
