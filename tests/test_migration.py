"""
Test Suite for Strands Migration
Comprehensive testing for the migrated One Piece TCG customer service agent
"""

import json
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from strands_lambda_handler import lambda_handler, parse_request_body, initialize_agent
from tools.deck_recommender import get_competitive_decks, validate_deck_filters, get_competitive_decks_api

class TestStrandsLambdaHandler(unittest.TestCase):
    """Test the main Lambda handler functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.sample_event = {
            'body': json.dumps({
                'inputText': 'Show me a Red Shanks deck for OP09',
                'sessionId': 'test-session-123',
                'cartId': 'test-cart-456'
            })
        }
        
        self.mock_response_stream = Mock()
        self.mock_context = Mock()

    def test_parse_request_body_valid(self):
        """Test parsing valid request body"""
        result = parse_request_body(self.sample_event)
        
        self.assertEqual(result['input_text'], 'Show me a Red Shanks deck for OP09')
        self.assertEqual(result['session_id'], 'test-session-123')
        self.assertEqual(result['cart_id'], 'test-cart-456')
        self.assertFalse(result['end_session'])

    def test_parse_request_body_invalid_json(self):
        """Test parsing invalid JSON in request body"""
        invalid_event = {'body': 'invalid json'}
        result = parse_request_body(invalid_event)
        
        self.assertEqual(result['input_text'], 'Hello')
        self.assertIsNotNone(result['session_id'])
        self.assertIsNone(result['cart_id'])

    def test_parse_request_body_missing_fields(self):
        """Test parsing request body with missing fields"""
        minimal_event = {'body': json.dumps({})}
        result = parse_request_body(minimal_event)
        
        self.assertEqual(result['input_text'], 'Hello')
        self.assertIsNotNone(result['session_id'])
        self.assertIsNone(result['cart_id'])

    @patch.dict(os.environ, {
        'SHOPIFY_URL': 'https://test-store.myshopify.com',
        'SHOPIFY_ACCESS_TOKEN': 'test-token',
        'SHOPIFY_STOREFRONT_ACCESS_TOKEN': 'test-storefront-token'
    })
    @patch('strands_lambda_handler.Agent')
    @patch('strands_lambda_handler.MCPClient')
    def test_initialize_agent(self, mock_mcp_client, mock_agent):
        """Test agent initialization"""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        
        result = initialize_agent()
        
        self.assertEqual(result, mock_agent_instance)
        mock_agent.assert_called_once()

class TestDeckRecommender(unittest.TestCase):
    """Test the deck recommender tool functionality"""
    
    def setUp(self):
        """Set up test environment for deck recommender"""
        self.sample_filters = {
            'region': 'west',
            'set': 'OP09',
            'leader': 'OP01-060'
        }

    def test_validate_deck_filters_valid(self):
        """Test validation with valid filters"""
        is_valid, missing, validated = validate_deck_filters(self.sample_filters)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
        self.assertEqual(validated, self.sample_filters)

    def test_validate_deck_filters_missing_required(self):
        """Test validation with missing required filters"""
        incomplete_filters = {'region': 'west'}
        is_valid, missing, validated = validate_deck_filters(incomplete_filters)
        
        self.assertFalse(is_valid)
        self.assertIn('the game format (e.g., OP09, OP08)', missing)
        self.assertIn('the leader card id (e.g. OP01-060)', missing)

    @patch.dict(os.environ, {
        'COMPETITIVE_DECK_SECRET': 'test-api-key',
        'COMPETITIVE_DECK_ENDPOINT': 'https://api.test.com/decks'
    })
    @patch('tools.deck_recommender.requests.get')
    def test_get_competitive_decks_api_success(self, mock_get):
        """Test successful API call to competitive decks service"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'set': 'OP09',
            'region': 'west',
            'leader': 'OP01-060',
            'author': 'Test Player',
            'tournament': 'Test Tournament',
            'event': 'Test Event',
            'decklist': ['Card 1', 'Card 2', 'Card 3']
        }]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = get_competitive_decks_api(self.sample_filters)
        
        self.assertTrue(result['success'])
        self.assertIn('deck', result)
        self.assertEqual(result['deck']['set'], 'OP09')
        self.assertEqual(result['deck']['leader'], 'OP01-060')

    @patch.dict(os.environ, {
        'COMPETITIVE_DECK_SECRET': 'test-api-key',
        'COMPETITIVE_DECK_ENDPOINT': 'https://api.test.com/decks'
    })
    @patch('tools.deck_recommender.requests.get')
    def test_get_competitive_decks_api_no_results(self, mock_get):
        """Test API call with no results"""
        # Mock API response with empty results
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = get_competitive_decks_api(self.sample_filters)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'No decks available')

    @patch('tools.deck_recommender.invoke_llm_bedrock')
    @patch('tools.deck_recommender.get_competitive_decks_api')
    def test_get_competitive_decks_tool_success(self, mock_api, mock_llm):
        """Test the complete deck recommender tool"""
        # Mock LLM response
        mock_llm.return_value = {
            'content': [{
                'text': json.dumps({
                    'set': 'OP09',
                    'region': 'west',
                    'leader': 'OP01-060'
                })
            }]
        }
        
        # Mock API response
        mock_api.return_value = {
            'success': True,
            'deck': {
                'set': 'OP09',
                'region': 'west',
                'leader': 'OP01-060',
                'author': 'Test Player',
                'tournament': 'Test Tournament',
                'event': 'Test Event',
                'decklist': ['Card 1', 'Card 2', 'Card 3']
            }
        }
        
        result = get_competitive_decks('Show me a Red Shanks deck for OP09')
        
        self.assertIn('Ahoy! I found a treasure of a deck for ye!', result)
        self.assertIn('OP01-060', result)
        self.assertIn('www.gumgum.gg', result)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    @patch.dict(os.environ, {
        'SHOPIFY_URL': 'https://test-store.myshopify.com',
        'SHOPIFY_ACCESS_TOKEN': 'test-token',
        'SHOPIFY_STOREFRONT_ACCESS_TOKEN': 'test-storefront-token',
        'COMPETITIVE_DECK_SECRET': 'test-api-key',
        'COMPETITIVE_DECK_ENDPOINT': 'https://api.test.com/decks'
    })
    @patch('strands_lambda_handler.Agent')
    @patch('strands_lambda_handler.MCPClient')
    def test_end_to_end_deck_request(self, mock_mcp_client, mock_agent):
        """Test end-to-end deck request processing"""
        # Mock agent streaming response
        mock_agent_instance = Mock()
        mock_agent_instance.stream.return_value = [
            "🏴‍☠️ Ahoy! Let me search for that deck...",
            "I found a great Red Shanks deck for ye!",
            "This deck won a recent tournament..."
        ]
        mock_agent.return_value = mock_agent_instance
        
        # Mock response stream
        mock_response_stream = Mock()
        written_chunks = []
        mock_response_stream.write.side_effect = lambda chunk: written_chunks.append(chunk)
        
        # Test event
        event = {
            'body': json.dumps({
                'inputText': 'Show me a Red Shanks deck for OP09',
                'sessionId': 'test-session',
                'cartId': None
            })
        }
        
        # Call the handler
        lambda_handler(event, mock_response_stream, {})
        
        # Verify streaming behavior
        mock_response_stream.setContentType.assert_called_with("text/plain")
        self.assertGreater(len(written_chunks), 0)
        mock_response_stream.end.assert_called_once()

class TestPerformance(unittest.TestCase):
    """Performance and load testing"""
    
    def test_session_id_generation_performance(self):
        """Test session ID generation performance"""
        from strands_lambda_handler import generate_session_id
        import time
        
        start_time = time.time()
        session_ids = [generate_session_id() for _ in range(1000)]
        end_time = time.time()
        
        # Should generate 1000 session IDs in under 1 second
        self.assertLess(end_time - start_time, 1.0)
        
        # All session IDs should be unique
        self.assertEqual(len(session_ids), len(set(session_ids)))
        
        # All session IDs should be 15 characters
        for session_id in session_ids[:10]:  # Check first 10
            self.assertEqual(len(session_id), 15)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
