"""
Migrated Deck Recommender Tool for Strands
Preserves all existing business logic from the original Lambda function
"""

import os
import json
import boto3
import requests
import time
import uuid
from typing import Dict, Any, List, Tuple
from strands import tool
from langfuse import Langfuse
from langfuse.decorators import observe
from langfuse.decorators import langfuse_context

# Initialize Langfuse client (preserve existing monitoring)
LANGFUSE_PUBLIC_KEY = os.environ.get('LANGFUSE_PUBLIC_KEY')
LANGFUSE_SECRET_KEY = os.environ.get('LANGFUSE_SECRET_KEY')
LANGFUSE_API_URL = os.environ.get('LANGFUSE_API_URL')

if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    langfuse = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_API_URL
    )
else:
    langfuse = None

# Environment Setup (preserve existing configuration)
API_KEY = os.environ.get('COMPETITIVE_DECK_SECRET')
API_ENDPOINT = os.environ.get('COMPETITIVE_DECK_ENDPOINT')

# Initialize monitoring (preserve existing monitoring)
try:
    from chatbot_monitoring.monitoring import ChatbotMonitoring
    monitor = ChatbotMonitoring()
    store_id = 'Store123'
except ImportError:
    # Fallback if custom monitoring package not available
    class MockMonitoring:
        def log_metric(self, *args, **kwargs):
            pass
    monitor = MockMonitoring()
    store_id = 'Store123'

@observe(as_type="generation", name="Invoke LLM Bedrock to parse user input")
def invoke_llm_bedrock(inputText: str, **kwargs) -> Dict[str, Any]:
    """
    Parse user input using Bedrock to extract set, region, and leader
    Preserves existing LLM parsing logic
    """
    # Initialize the Bedrock client
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    kwargs_clone = kwargs.copy()
    input_text = inputText
    model = kwargs_clone.pop('model_id', None)

    if langfuse:
        langfuse_context.update_current_observation(
            input=input_text,
            model=model,
            metadata=kwargs_clone
        )

    inference_profile = "arn:aws:bedrock:us-east-1:438465137422:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0"

    try:
        # Call the Bedrock model using the Messages API (preserve existing logic)
        response = bedrock_client.invoke_model(
            modelId=inference_profile,  
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",  
                "max_tokens": 1024, 
                "system": "Parse the input and output 3 fields in JSON format: set and region and leader. Region can only be west or east. West is defined as any tournament location not in Asia and in North America. East is defined as any location in Asia. If the input does not contain any information about a region, make region equal to west.  Set can also be referred to as format. If the user says 'latest set' or 'latest format' or does not specify a set at all, please use set equal to OP10 when the region is set to west and use set equal to OP11 when the region is set to east. Here are examples of sets, but not limited to: 'OP01' or 'OP02' or 'OP10' or 'ST10'.  Leader is the leader card specified by the user and should be in the format of OP01-001 (as an example only) or maybe OP01-060 (as another example).  The user may also specify the leader card by their color or colors (BY means Black and Yellow) and their name (i.e. Purple Luffy or Red Shanks or BY Luffy) or nick name (i.e. Doffy), please research the leader and convert the card to its card id.  Leader must be output in the right format (i.e. OP01-001 or ST08-001).    Output the response in a JSON format with set and format and leader.  Don't include anything else but a properly formatted JSON file in the output.", 
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": inputText
                            }
                        ]
                    }
                ],            
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        print("LLM response body:", response_body)
        return response_body

    except Exception as e:
        print(f"Error invoking AWS Bedrock model: {e}")
        raise

def validate_deck_filters(filters: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate deck filters (preserve existing validation logic)
    """
    required_filters = {
        'region': 'the tournament region (e.g., East, West)',
        'set': 'the game format (e.g., OP09, OP08)',
        'leader': 'the leader card id (e.g. OP01-060)'
    }
    
    missing_filters = []
    validated_filters = {}
    
    for key, description in required_filters.items():
        if key not in filters or not filters[key]:
            missing_filters.append(description)
        else:
            validated_filters[key] = filters[key]
    
    print("Validated filters:", validated_filters)
    print("Missing filters:", missing_filters)

    return len(missing_filters) == 0, missing_filters, validated_filters

@observe(name="API call to gumgum")
def get_competitive_decks_api(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call the competitive decks API (preserve existing API logic)
    """
    print("Inside competitive decks API function")
    try:
        start_time = time.time()

        is_valid, missing_filters, validated_filters = validate_deck_filters(filters or {})
        
        if not is_valid:
            print("Additional information needed for deck search")
            return {
                'success': False,
                'missing_filters': missing_filters,
                'message': 'Additional information needed'
            }
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{API_ENDPOINT}",
            headers=headers,
            params=validated_filters
        )
        response.raise_for_status()
                
        # Log successful API call (preserve existing monitoring)
        monitor.log_metric('APICallSuccess', 1, store_id=store_id)
        monitor.log_metric('DeckLookupsWithSuccessRate', 100, store_id=store_id)

        decks_data = response.json()

        # Get only the first deck (assuming decks_data is already sorted by recency)
        latest_deck = decks_data[0] if decks_data else None

        if latest_deck:
            return {
                'success': True,
                'deck': {
                    'set': latest_deck.get('set'),
                    'region': latest_deck.get('region'),
                    'author': latest_deck.get('author'),
                    'tournament': latest_deck.get('tournament'),
                    'event': latest_deck.get('event'),
                    'leader': latest_deck.get('leader'),
                    'decklist': latest_deck.get('decklist', [])
                }
            }
        else:
            return {
                'success': False,
                'message': 'No decks available'
            }

    except requests.exceptions.Timeout:
        # Log API timeout (preserve existing monitoring)
        monitor.log_metric('APICallTimeouts', 1, store_id=store_id)
        return {
            'success': False,
            'error': 'API request timed out'
        }

    except Exception as error:
        # Log other API errors (preserve existing monitoring)
        monitor.log_metric('APICallErrors', 1, store_id=store_id)
        monitor.log_metric('DeckLookupsWithSuccessRate', 0, store_id=store_id)
        print(f'Error fetching competitive decks: {error}')
        return {
            'success': False,
            'error': str(error)
        }

    finally:
        latency = (time.time() - start_time) * 1000
        monitor.log_metric('APICallLatency', latency, store_id=store_id)

@tool
@observe(name="get_competitive_decks_strands_tool")
def get_competitive_decks(user_query: str) -> str:
    """
    Get competitive One Piece TCG decks from gumgum.gg database.
    
    This tool helps users find tournament-winning decks for the One Piece Trading Card Game.
    It searches the gumgum.gg database for competitive decks based on leader, set, and region.
    
    Args:
        user_query: User's request for deck information. Can include:
                   - Leader name (e.g., "Red Shanks", "Purple Luffy", "BY Luffy")
                   - Set/Format (e.g., "OP09", "OP10", "latest set")
                   - Region (e.g., "West", "East", tournament location)
                   
    Returns:
        Formatted deck information including decklist and tournament details
        
    Examples:
        - "Show me a Red Shanks deck for OP09 West"
        - "Latest Purple Luffy deck from East region"
        - "Doffy deck OP08"
    """
    try:
        # Log deck lookup (preserve existing monitoring)
        monitor.log_metric('DeckLookups', 1, store_id=store_id)
        
        # Parse user input for set, region and leader using existing LLM logic
        trace_id = str(uuid.uuid4())
        agentId = '9YPRBXYN2H'  # Preserve existing agent ID for monitoring
        agentAliasId = 'FK0NHPPG6L'  # Preserve existing alias ID
        sessionId = f"session-{int(time.time())}"
        userId = "strands-user"
        agent_model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        # Tags for filtering in Langfuse (preserve existing monitoring)
        tags = ["bedrock-llm-3-5-haiku", "strands-migration", "deck-recommender"]
        project_name = "One Piece TCG Deck Recommender"
        environment = "production"

        # Invoke LLM via Bedrock to parse user input
        llm_response = invoke_llm_bedrock(
            user_query,
            agentId=agentId,
            agentAliasId=agentAliasId,
            sessionId=sessionId,
            userId=userId,
            tags=tags,
            trace_id=trace_id,
            project_name=project_name,
            environment=environment,
            model_id=agent_model_id
        )
        
        print("LLM parsing response:", llm_response)

        # Extract the JSON string from the 'content' field
        content_text = llm_response['content'][0]['text']
        print("Parsed content text:", content_text)

        # Parse the JSON string to extract 'set', 'region', and 'leader'
        parsed_content = json.loads(content_text)
        print("Parsed content:", parsed_content)

        # Use parsed values (with fallbacks matching original logic)
        set_value = parsed_content.get('set', 'OP09')  # Default to OP09
        region_value = parsed_content.get('region', 'west')
        leader_value = parsed_content.get('leader', 'OP01-060')

        print(f"Extracted - Set: {set_value}, Region: {region_value}, Leader: {leader_value}")

        # Call the competitive decks API
        filters = {
            'region': region_value,
            'set': set_value,
            'leader': leader_value
        }
        
        deck_result = get_competitive_decks_api(filters)
        
        if deck_result.get('success'):
            deck = deck_result['deck']
            
            # Format response with pirate theme (matching system prompt)
            deck_info = f"""🏴‍☠️ **Ahoy! I found a treasure of a deck for ye!**

**Leader:** {deck.get('leader', 'Unknown')}
**Set/Format:** {deck.get('set', 'Unknown')}
**Region:** {deck.get('region', 'Unknown')}
**Deck Author:** {deck.get('author', 'Unknown Pirate')}
**Tournament:** {deck.get('tournament', 'Unknown Tournament')}
**Event:** {deck.get('event', 'Unknown Event')}

**⚔️ Complete Decklist:**
{chr(10).join(deck.get('decklist', ['No decklist available']))}

*This competitive deck data is powered by [www.gumgum.gg](https://www.gumgum.gg) - the premier source for One Piece TCG tournament data!*

Would ye like me to help ye find any of these cards in our store inventory, matey?"""

            return deck_info
            
        elif not deck_result.get('success') and deck_result.get('missing_filters'):
            return f"Arrr! I need more information to find the perfect deck for ye! Please specify: {', '.join(deck_result['missing_filters'])}"
            
        else:
            return f"Blast! No competitive decks found for those criteria, matey! Try searching for a different leader, set, or region. The seas of tournament data might not have what ye seek!"
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return "Arrr! Had trouble parsing yer request, matey! Could ye try rephrasing what deck ye be lookin' for?"
        
    except Exception as e:
        print(f"Error in get_competitive_decks: {e}")
        return f"Shiver me timbers! Encountered an error while searching for decks: {str(e)}. Please try again, ye scurvy dog!"
        
    finally:
        # Flush Langfuse context (preserve existing monitoring)
        if langfuse:
            langfuse_context.flush()
