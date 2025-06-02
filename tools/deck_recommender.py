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
import datetime
from typing import Dict, List, Any, Optional, Tuple
from strands import tool

logger = logging.getLogger(__name__)

# Enable debug mode from environment variable
DEBUG_MODE = os.environ.get('DECK_RECOMMENDER_DEBUG', 'false').lower() == 'true'

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
    request_id = f"req_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(user_input) % 10000}"
    
    # FORCED ERROR LOGS FOR TESTING - These should appear in CloudWatch regardless of log level settings
    logger.error(f"DEPLOYMENT_VERIFICATION_20250602_1547: Starting get_competitive_decks function")
    logger.error(f"DEPLOYMENT_VERIFICATION_20250602_1547: Request ID: {request_id}")
    logger.error(f"DEPLOYMENT_VERIFICATION_20250602_1547: User input: {user_input}")
    
    try:
        if DEBUG_MODE:
            logger.info(f"=== DECK RECOMMENDER DEBUG MODE ENABLED ===")
            logger.info(f"Request ID: {request_id}")
            
        logger.info(f"[{request_id}] Processing deck request: {user_input}")
        
        # Parse user input to extract filters using LLM
        logger.info(f"[{request_id}] Parsing user input with LLM")
        filters = parse_user_input_with_llm(user_input)
        
        if not filters:
            logger.error(f"[{request_id}] Failed to parse deck search criteria")
            return create_error_response(
                "Failed to parse deck search criteria from input - AI parsing service unavailable",
                {"request_id": request_id, "user_input": user_input}
            )
        
        # Validate required filters
        logger.info(f"[{request_id}] Validating filters")
        is_valid, missing_filters, validated_filters = validate_deck_filters(filters)
        
        if not is_valid:
            logger.warning(f"[{request_id}] Invalid filters - missing: {missing_filters}")
            return {
                'success': False,
                'error_type': 'insufficient_search_criteria',
                'missing_filters': missing_filters,
                'message': 'Additional information needed to find competitive decks',
                'source': 'gumgum.gg',
                'request_id': request_id,
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
        logger.info(f"[{request_id}] Fetching deck data from API with filters: {validated_filters}")
        deck_data = fetch_competitive_deck_data(validated_filters)
        
        if deck_data['success']:
            logger.info(f"[{request_id}] Successfully retrieved deck data")
            response = format_competitive_deck_response(deck_data, validated_filters)
            if DEBUG_MODE:
                logger.info(f"[{request_id}] Response: {json.dumps(response)[:500]}...")
            return response
        else:
            error_details = deck_data.get('error', 'Unknown error')
            logger.error(f"[{request_id}] Failed to retrieve deck data from gumgum.gg API: {error_details}")
            return create_error_response(
                f"GumGum.gg API error: {error_details}",
                {
                    "request_id": request_id,
                    "filters": validated_filters,
                    "api_error": error_details
                }
            )
            
    except Exception as e:
        logger.error(f"[{request_id}] Error in get_competitive_decks: {str(e)}")
        import traceback
        logger.error(f"[{request_id}] Stack trace: {traceback.format_exc()}")
        return create_error_response(
            f"Deck recommendation service error: {str(e)}",
            {
                "request_id": request_id,
                "error_type": type(e).__name__,
                "user_input": user_input
            }
        )

def parse_user_input_with_llm(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse user input using AWS Bedrock to extract deck search criteria
    """
    try:
        # Log the user input
        logger.info(f"LLM Parsing - User Input: {user_input}")
        
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        logger.info("LLM Parsing - Initialized Bedrock client")
        
        # System prompt for parsing deck requests
        system_prompt = """Parse the input and output 3 fields in JSON format: set, region, and leader.

Region rules:
- "west" = North America, Europe, or any non-Asian location
- "east" = Asia (Japan, etc.)
- If no region specified, default to "west"

Set rules:
- Can be called "set" or "format"
- If user says "latest set/format" or doesn't specify, use "OP10" for west, "OP11" for east
- Examples: OP01, OP02, OP10, ST10, EB01, EB02

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
        
        if DEBUG_MODE:
            logger.info(f"LLM Parsing - Request Body: {json.dumps(request_body)}")
        
        # Call Bedrock
        logger.info("LLM Parsing - Calling Bedrock API")
        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        logger.info("LLM Parsing - Received response from Bedrock API")
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content_text = response_body['content'][0]['text']
        
        # Log the raw response (truncated if too long)
        content_sample = content_text[:500] + "..." if len(content_text) > 500 else content_text
        logger.info(f"LLM Parsing - Raw Response: {content_sample}")
        
        # Extract JSON from response
        parsed_content = json.loads(content_text)
        
        # Log the parsed result
        logger.info(f"LLM Parsing - Parsed Result: {parsed_content}")
        
        # Log validation of each required field
        for field in ['set', 'region', 'leader']:
            if field in parsed_content:
                logger.info(f"LLM Parsing - Field '{field}': {parsed_content[field]}")
            else:
                logger.warning(f"LLM Parsing - Missing required field: {field}")
        
        return parsed_content
        
    except boto3.exceptions.Boto3Error as e:
        logger.error(f"LLM Parsing - AWS Bedrock Error: {type(e).__name__}: {str(e)}")
        logger.error(f"LLM Parsing - AWS Bedrock Error Details: {e}")
        raise RuntimeError(f"AI parsing service unavailable: {e}. Unable to process deck search request without natural language parsing.")
    except json.JSONDecodeError as e:
        logger.error(f"LLM Parsing - JSON Decode Error: {type(e).__name__}: {str(e)}")
        logger.error(f"LLM Parsing - JSON Decode Error at position {e.pos}: {e.msg}")
        if hasattr(e, 'doc'):
            doc_sample = e.doc[:100] + "..." if e.doc and len(e.doc) > 100 else e.doc
            logger.error(f"LLM Parsing - JSON Decode Error - Content: {doc_sample}")
        raise RuntimeError(f"AI parsing service returned invalid response: {e}. Unable to extract deck search criteria.")
    except Exception as e:
        logger.error(f"LLM Parsing - Unexpected Error: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"LLM Parsing - Stack Trace: {traceback.format_exc()}")
        raise RuntimeError(f"AI parsing service error: {type(e).__name__}: {str(e)}. Cannot process natural language deck requests without this service.")

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
        
        logger.info(f"GumGum API - Using endpoint: {api_endpoint}")
        if api_key:
            logger.info(f"GumGum API - API key available: {api_key[:5]}...")
        else:
            logger.error("GumGum API - API key not available")
        
        if not api_endpoint:
            error_msg = "GumGum.gg API endpoint not configured. Check COMPETITIVE_DECK_ENDPOINT environment variable."
            logger.error(f"GumGum API - Error: {error_msg}")
            raise RuntimeError(error_msg)
        
        if not api_key:
            error_msg = "GumGum.gg API key not configured. Check COMPETITIVE_DECK_SECRET environment variable."
            logger.error(f"GumGum API - Error: {error_msg}")
            raise RuntimeError(error_msg)
        
        # Prepare API request
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OnePieceTCGStrandsAgent/2.0'
        }
        
        # Add secret to query parameters instead of using Authorization header
        params = filters.copy()
        params['secret'] = api_key
        
        # Log the API request details (without exposing the full secret)
        safe_params = params.copy()
        if 'secret' in safe_params:
            safe_params['secret'] = safe_params['secret'][:5] + '...'
        
        logger.info(f"GumGum API Request - Endpoint: {api_endpoint}")
        logger.info(f"GumGum API Request - Headers: {headers}")
        logger.info(f"GumGum API Request - Params: {safe_params}")
        
        # Make API call
        logger.info("GumGum API - Sending request")
        response = requests.get(
            api_endpoint,
            headers=headers,
            params=params,
            timeout=10
        )
        
        # Log the API response
        logger.info(f"GumGum API Response - Status Code: {response.status_code}")
        logger.info(f"GumGum API Response - URL: {response.url}")
        
        # Log response headers
        logger.info(f"GumGum API Response - Headers: {dict(response.headers)}")
        
        # Handle specific HTTP errors
        if response.status_code == 401:
            error_msg = "GumGum.gg API authentication failed. Invalid API key."
            logger.error(f"GumGum API - Error: {error_msg}")
            logger.error(f"GumGum API Response - Error Content: {response.text}")
            raise RuntimeError(error_msg)
        elif response.status_code == 403:
            error_msg = "GumGum.gg API access forbidden. Check API key permissions."
            logger.error(f"GumGum API - Error: {error_msg}")
            logger.error(f"GumGum API Response - Error Content: {response.text}")
            raise RuntimeError(error_msg)
        elif response.status_code == 404:
            error_msg = "GumGum.gg API endpoint not found or no decks matching criteria."
            logger.error(f"GumGum API - Error: {error_msg}")
            logger.error(f"GumGum API Response - Error Content: {response.text}")
            raise RuntimeError(error_msg)
        elif response.status_code == 429:
            error_msg = "GumGum.gg API rate limit exceeded. Please try again later."
            logger.error(f"GumGum API - Error: {error_msg}")
            logger.error(f"GumGum API Response - Error Content: {response.text}")
            raise RuntimeError(error_msg)
        elif response.status_code >= 500:
            error_msg = f"GumGum.gg API server error (HTTP {response.status_code}). Service temporarily unavailable."
            logger.error(f"GumGum API - Error: {error_msg}")
            logger.error(f"GumGum API Response - Error Content: {response.text}")
            raise RuntimeError(error_msg)
        
        # Log response content for successful responses
        if response.status_code == 200:
            try:
                # Log a sample of the response content
                content_sample = str(response.text)[:500] + "..." if len(response.text) > 500 else response.text
                logger.info(f"GumGum API Response - Content Sample: {content_sample}")
            except Exception as e:
                logger.error(f"GumGum API - Error logging response content: {e}")
        
        response.raise_for_status()
        
        # Parse JSON response
        try:
            decks_data = response.json()
            logger.info(f"GumGum API - Successfully parsed JSON response")
            logger.info(f"GumGum API - Number of decks returned: {len(decks_data) if isinstance(decks_data, list) else 'Not a list'}")
        except json.JSONDecodeError as e:
            logger.error(f"GumGum API - JSON Decode Error: {e}")
            logger.error(f"GumGum API - Response Content: {response.text[:500]}...")
            raise RuntimeError(f"GumGum.gg API returned invalid JSON: {e}")
        
        # Get the most recent deck
        latest_deck = decks_data[0] if isinstance(decks_data, list) and decks_data else None
        
        if latest_deck:
            logger.info(f"GumGum API - Successfully retrieved deck: {latest_deck.get('leader', 'Unknown')} from {latest_deck.get('tournament', 'Unknown')}")
            return {
                'success': True,
                'deck': latest_deck
            }
        else:
            error_msg = f'No tournament decks found for {filters.get("leader", "specified leader")} in {filters.get("region", "specified region")} region for format {filters.get("set", "specified format")}'
            logger.error(f"GumGum API - Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
            
    except requests.exceptions.Timeout:
        error_msg = "GumGum.gg API request timeout. The service may be experiencing high load."
        logger.error(f"GumGum API - Error: {error_msg}")
        raise RuntimeError(error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Cannot connect to GumGum.gg API. Check network connectivity or service availability. Error: {e}"
        logger.error(f"GumGum API - Error: {error_msg}")
        raise RuntimeError(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"GumGum.gg API request failed: {e}"
        logger.error(f"GumGum API - Error: {error_msg}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error accessing GumGum.gg API: {type(e).__name__}: {str(e)}"
        logger.error(f"GumGum API - Error: {error_msg}")
        import traceback
        logger.error(f"GumGum API - Stack Trace: {traceback.format_exc()}")
        raise RuntimeError(error_msg)

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


def create_error_response(error_message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response with detailed troubleshooting information
    
    Args:
        error_message: The main error message to display
        details: Optional dictionary with additional error details
    
    Returns:
        A standardized error response dictionary
    """
    # Log the error
    logger.error(f"Creating error response: {error_message}")
    if details:
        logger.error(f"Error details: {details}")
    
    # Create the response
    response = {
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
                'AI parsing service failure',
                'Expansion set (EB) or specific card ID not found in tournament database'
            ],
            'user_actions': [
                'Try rephrasing your deck request with specific details',
                'Include region (East/West), format (OP10, OP09), and leader name',
                'For expansion sets (EB), try using a main set (OP) instead',
                'Verify the card ID is correct (e.g., OP01-001 is Monkey D. Luffy, not Zoro)',
                'Wait a moment and try again if service is temporarily unavailable'
            ],
            'example_requests': [
                'Show me a Red Luffy deck for OP10 in the West region',
                'Find tournament decks for Purple Doflamingo in the latest format',
                'Get a competitive deck with OP01-001 as leader'
            ]
        },
        'metadata': {
            'error_type': 'deck_retrieval_error',
            'data_source': 'gumgum.gg',
            'service_status': 'error',
            'timestamp': datetime.datetime.now().isoformat()
        }
    }
    
    # Add additional error details if provided
    if details:
        response['error_details'] = details
    
    return response
