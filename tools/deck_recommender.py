"""
GumGum.gg Deck Recommender Tool for Strands Agent
Integrates with GumGum.gg API to provide One Piece TCG deck recommendations
Combines natural language processing with structured API calls
"""

import os
import json
import requests
import logging
import boto3
from typing import Dict, List, Any, Optional, Tuple
from strands import tool

logger = logging.getLogger(__name__)

@tool
def get_competitive_decks(user_input: str) -> Dict[str, Any]:
    """
    Get competitive One Piece TCG deck recommendations from GumGum.gg database.
    
    Processes natural language input to extract deck search criteria and returns
    tournament-winning deck information with complete deck lists.
    
    Args:
        user_input: Natural language description of deck requirements
                   (e.g., "Show me the latest Red Luffy deck from OP10" or 
                    "I want a competitive deck for Purple Doffy in the west region")
    
    Returns:
        Dictionary containing deck recommendations with complete deck lists,
        tournament information, and metadata. Always mentions data is powered by gumgum.gg.
    """
    
    try:
        logger.info(f"Processing deck request: {user_input}")
        
        # Parse user input to extract filters using LLM
        filters = parse_user_input_with_llm(user_input)
        
        if not filters:
            return create_error_response("Failed to parse deck search criteria from input - AI parsing service unavailable")
        
        # Validate required filters
        is_valid, missing_filters, validated_filters = validate_deck_filters(filters)
        
        if not is_valid:
            return {
                'success': False,
                'error_type': 'insufficient_search_criteria',
                'missing_filters': missing_filters,
                'message': 'Additional information needed to find competitive decks',
                'source': 'gumgum.gg',
                'required_information': [
                    'Tournament region: East (Asia) or West (North America/Europe)',
                    'Game format/set: e.g., OP10, OP09, ST10',
                    'Leader card or character: e.g., Red Luffy, Purple Doffy, Shanks'
                ],
                'example_requests': [
                    'Show me a Red Luffy deck for OP10 in the West region',
                    'I want a competitive Purple Doflamingo deck from the latest set',
                    'Find me tournament decks for Shanks in the East region'
                ]
            }
        
        # Get deck data from API
        deck_data = fetch_competitive_deck_data(validated_filters)
        
        if deck_data['success']:
            return format_competitive_deck_response(deck_data, validated_filters)
        else:
            error_details = deck_data.get('error', 'Unknown error')
            logger.error(f"Failed to retrieve deck data from gumgum.gg API: {error_details}")
            return create_error_response(f"GumGum.gg API error: {error_details}")
            
    except Exception as e:
        logger.error(f"Error in get_competitive_decks: {str(e)}")
        return create_error_response(f"Deck recommendation service error: {str(e)}")

def parse_user_input_with_llm(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse user input using AWS Bedrock to extract deck search criteria
    """
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # System prompt for parsing deck requests
        system_prompt = """Parse the input and output 3 fields in JSON format: set, region, and leader.

Region rules:
- "west" = North America, Europe, or any non-Asian location
- "east" = Asia (Japan, etc.)
- If no region specified, default to "west"

Set rules:
- Can be called "set" or "format"
- If user says "latest set/format" or doesn't specify, use "OP10" for west, "OP11" for east
- Examples: OP01, OP02, OP10, ST10

Leader rules:
- Convert to card ID format (e.g., OP01-001, ST08-001)
- Handle color names (Red Luffy, Purple Doffy, BY Luffy where BY = Black/Yellow)
- Handle character nicknames (Doffy = Doflamingo)
- Research the actual card ID for the leader

Output only valid JSON with set, region, and leader fields."""

        # Prepare the request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system_prompt,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_input}]
                }
            ]
        }
        
        # Call Bedrock
        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content_text = response_body['content'][0]['text']
        
        # Extract JSON from response
        parsed_content = json.loads(content_text)
        
        logger.info(f"Parsed filters from LLM: {parsed_content}")
        return parsed_content
        
    except boto3.exceptions.Boto3Error as e:
        logger.error(f"AWS Bedrock service error: {e}")
        raise RuntimeError(f"AI parsing service unavailable: {e}. Unable to process deck search request without natural language parsing.")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from Bedrock: {e}")
        raise RuntimeError(f"AI parsing service returned invalid response: {e}. Unable to extract deck search criteria.")
    except Exception as e:
        logger.error(f"Failed to parse user input with LLM: {e}")
        raise RuntimeError(f"AI parsing service error: {e}. Cannot process natural language deck requests without this service.")

def validate_deck_filters(filters: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate that required deck search filters are present
    """
    required_filters = {
        'region': 'tournament region (East for Asia, West for North America)',
        'set': 'game format/set (e.g., OP10, OP09)',
        'leader': 'leader card ID (e.g., OP01-060)'
    }
    
    missing_filters = []
    validated_filters = {}
    
    for key, description in required_filters.items():
        if key not in filters or not filters[key]:
            missing_filters.append(description)
        else:
            validated_filters[key] = filters[key]
    
    logger.info(f"Validated filters: {validated_filters}")
    logger.info(f"Missing filters: {missing_filters}")
    
    return len(missing_filters) == 0, missing_filters, validated_filters

def fetch_competitive_deck_data(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch competitive deck data from the GumGum.gg API
    """
    try:
        # Get API credentials from environment
        api_endpoint = os.environ.get('COMPETITIVE_DECK_ENDPOINT')
        api_key = os.environ.get('COMPETITIVE_DECK_SECRET')
        
        if not api_endpoint:
            raise RuntimeError("GumGum.gg API endpoint not configured. Check COMPETITIVE_DECK_ENDPOINT environment variable.")
        
        if not api_key:
            raise RuntimeError("GumGum.gg API key not configured. Check COMPETITIVE_DECK_SECRET environment variable.")
        
        # Prepare API request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'OnePieceTCGStrandsAgent/2.0'
        }
        
        # Make API call
        response = requests.get(
            api_endpoint,
            headers=headers,
            params=filters,
            timeout=10
        )
        
        # Handle specific HTTP errors
        if response.status_code == 401:
            raise RuntimeError("GumGum.gg API authentication failed. Invalid API key.")
        elif response.status_code == 403:
            raise RuntimeError("GumGum.gg API access forbidden. Check API key permissions.")
        elif response.status_code == 404:
            raise RuntimeError("GumGum.gg API endpoint not found. Check API endpoint configuration.")
        elif response.status_code == 429:
            raise RuntimeError("GumGum.gg API rate limit exceeded. Please try again later.")
        elif response.status_code >= 500:
            raise RuntimeError(f"GumGum.gg API server error (HTTP {response.status_code}). Service temporarily unavailable.")
        
        response.raise_for_status()
        
        decks_data = response.json()
        
        # Get the most recent deck
        latest_deck = decks_data[0] if decks_data else None
        
        if latest_deck:
            return {
                'success': True,
                'deck': latest_deck
            }
        else:
            return {
                'success': False,
                'error': f'No tournament decks found for {filters.get("leader", "specified leader")} in {filters.get("region", "specified region")} region for format {filters.get("set", "specified format")}'
            }
            
    except requests.exceptions.Timeout:
        raise RuntimeError("GumGum.gg API request timeout. The service may be experiencing high load.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to GumGum.gg API. Check network connectivity or service availability.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"GumGum.gg API request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error accessing GumGum.gg API: {e}")

def format_competitive_deck_response(deck_data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the competitive deck response for the agent
    """
    deck = deck_data['deck']
    
    return {
        'success': True,
        'source': 'gumgum.gg',
        'message': 'Tournament-winning deck data powered by www.gumgum.gg',
        'deck': {
            'name': f"{deck.get('leader', 'Unknown')} Tournament Deck",
            'set': deck.get('set', filters.get('set')),
            'region': deck.get('region', filters.get('region')),
            'leader': deck.get('leader', filters.get('leader')),
            'author': deck.get('author', 'Tournament Player'),
            'tournament': deck.get('tournament', 'Competitive Tournament'),
            'event': deck.get('event', 'Tournament Event'),
            'decklist': deck.get('decklist', []),
            'total_cards': len(deck.get('decklist', []))
        },
        'metadata': {
            'data_source': 'gumgum.gg tournament database',
            'search_criteria': filters,
            'competitive_level': 'Tournament-winning',
            'disclaimer': 'Deck data powered by www.gumgum.gg'
        }
    }


def create_error_response(error_message: str) -> Dict[str, Any]:
    """
    Create a standardized error response with detailed troubleshooting information
    """
    return {
        'success': False,
        'source': 'gumgum.gg',
        'error': error_message,
        'error_type': 'deck_service_error',
        'message': 'Unable to retrieve competitive deck data',
        'troubleshooting': {
            'possible_causes': [
                'GumGum.gg API service unavailable',
                'Invalid search criteria provided',
                'Network connectivity issues',
                'AI parsing service failure'
            ],
            'user_actions': [
                'Try rephrasing your deck request with specific details',
                'Include region (East/West), format (OP10, OP09), and leader name',
                'Wait a moment and try again if service is temporarily unavailable'
            ],
            'example_requests': [
                'Show me a Red Luffy deck for OP10 in the West region',
                'Find tournament decks for Purple Doflamingo in the latest format'
            ]
        },
        'metadata': {
            'error_type': 'deck_retrieval_error',
            'data_source': 'gumgum.gg',
            'service_status': 'error'
        }
    }
