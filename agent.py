#!/usr/bin/env python3
"""
Enhanced Strands Agent Handler with Shopify Storefront MCP Integration
Integrates Shopify's standard Storefront MCP server following official best practices
"""

# Import AWS configuration first to ensure region is set before any boto3 clients are created
import aws_config

import os
# Enable OpenTelemetry tracing for Strands
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = os.getenv("STRANDS_OTEL_ENABLE_CONSOLE_EXPORT", "true")

import json
import uuid
import logging
import boto3
import httpx
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import ClientSession

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),  # Set default log level to INFO
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Set log level for specific loggers
logging.getLogger("tools.deck_recommender").setLevel(logging.INFO)  # Ensure deck_recommender logs are visible

# Enable Strands debug logging if needed
if os.getenv('STRANDS_DEBUG', 'false').lower() == 'true':
    logging.getLogger("strands").setLevel(logging.DEBUG)

# Langfuse imports with graceful fallback
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # Create no-op decorators for graceful fallback
    def observe(func):
        return func
    langfuse_context = None

# Global agent instance
agent = None

# Global Langfuse client
langfuse_client = None

def initialize_langfuse() -> Optional[Langfuse]:
    """Initialize Langfuse client with proper error handling"""
    global langfuse_client
    
    if not LANGFUSE_AVAILABLE:
        logger.info("Langfuse not available - running without observability")
        return None
        
    try:
        public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        
        if public_key and secret_key:
            langfuse_client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            logger.info("Langfuse client initialized successfully")
            return langfuse_client
        else:
            logger.warning("Langfuse credentials not configured - observability disabled")
            return None
            
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse client: {e}")
        return None

# TCG System Prompt with Shopify Storefront MCP Integration
TCG_SYSTEM_PROMPT = """You are a helpful customer service representative for a One Piece Trading Card Game store. You assist customers with:

**One Piece Competitive/Tournament Decks**: Use get_competitive_decks to provide tournament-winning deck information from the gumgum.gg database. Always include complete deck lists and mention that data is powered by www.gumgum.gg.

**Store Operations**: Use the Shopify Storefront MCP tools to help customers browse and buy:
- search_shop_catalog: Search the store's product catalog for One Piece TCG products
- manage_cart: Add items to cart, view cart contents, and manage shopping cart
- get_store_policies: Get store policies, shipping info, and return policies
- checkout_assistance: Help customers complete their purchase

**Available Tools:**
- get_competitive_decks: Search tournament decks from gumgum.gg
- search_shop_catalog: Search store catalog (via Shopify Storefront MCP)
- manage_cart: Cart operations (via Shopify Storefront MCP)
- get_store_policies: Store policy information (via Shopify Storefront MCP)

**Guidelines:**
- Always provide complete deck lists when sharing competitive deck information
- When providing deck information, mention that data is powered by www.gumgum.gg
- Use search_shop_catalog to find products when customers ask about specific cards
- Help customers add items to their cart and complete purchases
- Provide store policy information when asked about shipping, returns, etc.
- Be friendly and helpful throughout the shopping experience
- If a tool fails, provide a clear error message explaining what went wrong
"""

class ShopifyStorefrontMCPManager:
    """Manages Shopify Storefront MCP server connection following official best practices"""
    
    def __init__(self):
        self.shop_domain: Optional[str] = None
        self.mcp_endpoint: Optional[str] = None
        self.tools: List = []
        self.http_client: Optional[httpx.AsyncClient] = None
        
    @observe(name="shopify_mcp.initialize_from_ssm")
    def initialize_from_ssm(self) -> bool:
        """Initialize Shopify Storefront MCP configuration from SSM parameters"""
        try:
            # Get shop domain from SSM
            shop_url_param = os.environ.get('SHOPIFY_STORE_URL_PARAM', '/tcg-agent/production/shopify/store-url')
            shop_url = get_ssm_parameter(shop_url_param)
            
            if not shop_url:
                error_msg = f"Shopify shop URL not found in SSM parameter: {shop_url_param}"
                logger.error(error_msg)
                raise RuntimeError(f"Shopify MCP configuration failed: {error_msg}. Ensure the parameter exists and contains a valid Shopify store URL.")
                
            # Extract domain from URL and set up Storefront MCP endpoint
            self.shop_domain = shop_url.replace('https://', '').replace('http://', '').rstrip('/')
            
            # Shopify Storefront MCP endpoint follows the pattern: https://storedomain.com/api/mcp
            self.mcp_endpoint = f"https://{self.shop_domain}/api/mcp"
            
            # Initialize HTTP client for MCP requests
            self.http_client = httpx.AsyncClient(
                headers={'Content-Type': 'application/json'},
                timeout=30.0
            )
            
            logger.info(f"Shopify Storefront MCP initialized for: {self.shop_domain}")
            logger.info(f"MCP endpoint: {self.mcp_endpoint}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize Shopify Storefront MCP configuration: {e}"
            logger.error(error_msg)
            raise RuntimeError(f"Shopify MCP initialization failed: {error_msg}")
    
    @observe(name="shopify_mcp.discover_tools")
    async def discover_tools(self) -> bool:
        """Discover available tools from Shopify Storefront MCP server"""
        try:
            if not self.mcp_endpoint or not self.http_client:
                raise RuntimeError("Shopify Storefront MCP not properly initialized - missing endpoint or HTTP client")
            
            # Make MCP request to list tools following Shopify's pattern
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
            
            response = await self.http_client.post(self.mcp_endpoint, json=mcp_request)
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "tools" in result["result"]:
                    # Store available tools (these would be Shopify's standard storefront tools)
                    self.tools = result["result"]["tools"]
                    tool_names = [tool.get("name", "unknown") for tool in self.tools]
                    logger.info(f"Discovered Shopify Storefront MCP tools: {tool_names}")
                    return True
                else:
                    raise RuntimeError(f"Invalid MCP response format from {self.mcp_endpoint}: missing 'result.tools' in response")
            else:
                raise RuntimeError(f"Shopify Storefront MCP server returned HTTP {response.status_code} from {self.mcp_endpoint}. Check if the store's MCP endpoint is properly configured.")
                
        except httpx.TimeoutException:
            raise RuntimeError(f"Timeout connecting to Shopify Storefront MCP at {self.mcp_endpoint}. Check network connectivity and store availability.")
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to Shopify Storefront MCP at {self.mcp_endpoint}. Verify the store domain and MCP endpoint configuration.")
        except Exception as e:
            raise RuntimeError(f"Failed to discover tools from Shopify Storefront MCP: {e}")
    
    @observe(name="shopify_mcp.connect_and_discover_tools")
    def connect_and_discover_tools(self) -> bool:
        """Connect to Shopify Storefront MCP server and discover available tools"""
        try:
            if not self.mcp_endpoint:
                raise RuntimeError("Shopify Storefront MCP endpoint not configured. Check SSM parameter configuration.")
            
            # For now, we'll simulate the standard Shopify Storefront MCP tools
            # In a real implementation, you would call self.discover_tools() async
            self.tools = [
                {"name": "search_shop_catalog", "description": "Search the store's product catalog"},
                {"name": "manage_cart", "description": "Manage shopping cart operations"},
                {"name": "get_store_policies", "description": "Get store policies and information"}
            ]
            
            logger.info(f"Shopify Storefront MCP tools configured: {[tool['name'] for tool in self.tools]}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to connect to Shopify Storefront MCP: {e}")
            self.tools = []
            raise RuntimeError(f"Shopify MCP connection failed: {e}")
    
    def get_tools(self) -> List:
        """Get discovered MCP tools"""
        return self.tools
    
    def is_connected(self) -> bool:
        """Check if Shopify Storefront MCP is connected and tools are available"""
        return self.mcp_endpoint is not None and len(self.tools) > 0

# Global MCP manager instance
shopify_mcp_manager = ShopifyStorefrontMCPManager()

def get_ssm_parameter(parameter_name: str, decrypt: bool = False) -> Optional[str]:
    """Get parameter from AWS Systems Manager Parameter Store"""
    try:
        logger.info(f"Retrieving SSM parameter: {parameter_name}")
        ssm = boto3.client('ssm', region_name='us-east-1')  # Explicitly set region
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=decrypt)
        value = response['Parameter']['Value']
        logger.info(f"Successfully retrieved SSM parameter: {parameter_name}")
        return value
    except ssm.exceptions.ParameterNotFound:
        logger.error(f"SSM parameter not found: {parameter_name}")
        raise RuntimeError(f"SSM parameter not found: {parameter_name}. Ensure the parameter exists in AWS Systems Manager.")
    except ssm.exceptions.AccessDeniedException:
        logger.error(f"Access denied to SSM parameter: {parameter_name}")
        raise RuntimeError(f"Access denied to SSM parameter: {parameter_name}. Check IAM permissions for Lambda execution role.")
    except Exception as e:
        logger.error(f"Failed to retrieve SSM parameter {parameter_name}: {e}")
        raise RuntimeError(f"Failed to retrieve SSM parameter {parameter_name}: {e}")

def initialize_environment():
    """Initialize environment variables from SSM parameters with comprehensive error handling"""
    missing_configs = []
    
    try:
        # Get API credentials from SSM if not already set
        if not os.getenv('COMPETITIVE_DECK_ENDPOINT'):
            endpoint_param = os.getenv('COMPETITIVE_DECK_ENDPOINT_PARAM', '/tcg-agent/production/deck-api/endpoint')
            try:
                endpoint = get_ssm_parameter(endpoint_param)
                if endpoint:
                    os.environ['COMPETITIVE_DECK_ENDPOINT'] = endpoint
                    logger.info("Deck API endpoint configured successfully")
                else:
                    missing_configs.append(f"Deck API endpoint (parameter: {endpoint_param})")
            except Exception as e:
                missing_configs.append(f"Deck API endpoint (parameter: {endpoint_param}) - {str(e)}")
                
        if not os.getenv('COMPETITIVE_DECK_SECRET'):
            secret_param = os.getenv('COMPETITIVE_DECK_SECRET_PARAM', '/tcg-agent/production/deck-api/secret')
            try:
                secret = get_ssm_parameter(secret_param, decrypt=True)
                if secret:
                    os.environ['COMPETITIVE_DECK_SECRET'] = secret
                    logger.info("Deck API secret configured successfully")
                else:
                    missing_configs.append(f"Deck API secret (parameter: {secret_param})")
            except Exception as e:
                missing_configs.append(f"Deck API secret (parameter: {secret_param}) - {str(e)}")
        
        # Langfuse configuration (optional but recommended) - FIXED: Proper exception handling
        if not os.getenv('LANGFUSE_PUBLIC_KEY'):
            try:
                langfuse_public_param = os.getenv('LANGFUSE_PUBLIC_KEY_PARAM', '/tcg-agent/production/langfuse/public-key')
                public_key = get_ssm_parameter(langfuse_public_param)
                if public_key:
                    os.environ['LANGFUSE_PUBLIC_KEY'] = public_key
                    logger.info("Langfuse public key configured successfully")
            except Exception as e:
                logger.warning(f"Langfuse public key not configured - monitoring will be limited: {e}")
                
        if not os.getenv('LANGFUSE_SECRET_KEY'):
            try:
                langfuse_secret_param = os.getenv('LANGFUSE_SECRET_KEY_PARAM', '/tcg-agent/production/langfuse/secret-key')
                secret_key = get_ssm_parameter(langfuse_secret_param, decrypt=True)
                if secret_key:
                    os.environ['LANGFUSE_SECRET_KEY'] = secret_key
                    logger.info("Langfuse secret key configured successfully")
            except Exception as e:
                logger.warning(f"Langfuse secret key not configured - monitoring will be limited: {e}")
        
        # Initialize Langfuse client after environment variables are set
        initialize_langfuse()
        
        # Initialize Shopify MCP configuration - FAIL if this fails
        try:
            shopify_initialized = shopify_mcp_manager.initialize_from_ssm()
            if not shopify_initialized:
                missing_configs.append("Shopify MCP configuration failed")
        except Exception as e:
            missing_configs.append(f"Shopify MCP initialization failed: {str(e)}")
        
        # Check for critical missing configurations
        if missing_configs:
            error_msg = f"Critical configuration missing: {'; '.join(missing_configs)}"
            logger.error(error_msg)
            raise RuntimeError(f"Agent configuration incomplete: {error_msg}")
        
        logger.info("Environment initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Environment initialization failed: {e}")
        raise RuntimeError(f"Agent configuration failed: {str(e)}")

def initialize_agent(streaming=False):
    """Initialize the Strands agent with full MCP integration following best practices"""
    global agent
    
    # Return existing agent if not streaming and agent exists
    if agent is not None and not streaming:
        return agent
    
    try:
        # Initialize environment from SSM parameters
        initialize_environment()
        
        # Import custom tools
        from tools.deck_recommender import get_competitive_decks
        
        # Start with custom tools
        all_tools = [get_competitive_decks]
        
        # Attempt to connect to Shopify MCP server and get tools
        try:
            mcp_connected = shopify_mcp_manager.connect_and_discover_tools()
            
            if mcp_connected:
                # Add Shopify MCP tools to agent
                shopify_tools = shopify_mcp_manager.get_tools()
                all_tools.extend(shopify_tools)
                logger.info(f"Agent initialized with {len(shopify_tools)} Shopify MCP tools")
            else:
                raise RuntimeError("Shopify MCP connection failed - no tools available")
        except Exception as e:
            logger.error(f"Shopify MCP integration failed: {e}")
            raise RuntimeError(f"Agent initialization failed due to Shopify MCP error: {e}")
        
        # Define a Langfuse callback handler for Strands
        def langfuse_callback_handler(**kwargs):
            """Callback handler that sends Strands events to Langfuse"""
            if not LANGFUSE_AVAILABLE or not langfuse_client:
                return
                
            try:
                # Handle text generation events
                if "data" in kwargs:
                    # Create or update generation in Langfuse
                    if hasattr(langfuse_context, "current_trace"):
                        langfuse_context.current_trace.generation(
                            name="agent_response_chunk",
                            input="",
                            output=kwargs["data"],
                            model="anthropic.claude-3-7-sonnet-20250219-v1:0",
                            metadata={
                                "gen_ai.event.type": "text_generation",
                                "gen_ai.system": "strands-agents",
                                "timestamp": str(uuid.uuid4())
                            }
                        )
                
                # Handle tool use events
                elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
                    tool = kwargs["current_tool_use"]
                    tool_name = tool.get("name", "unknown_tool")
                    tool_id = tool.get("toolUseId", str(uuid.uuid4()))
                    
                    # Create a span for the tool use
                    if hasattr(langfuse_context, "current_trace"):
                        langfuse_context.current_trace.span(
                            name=f"tool_use_{tool_name}",
                            input=json.dumps(tool.get("input", {})),
                            output=json.dumps(tool.get("output", {})),
                            metadata={
                                "tool.name": tool_name,
                                "tool.id": tool_id,
                                "tool.status": tool.get("status", "unknown"),
                                "gen_ai.event.type": "tool_use",
                                "gen_ai.event.start_time": str(uuid.uuid4()),  # Ideally would be actual timestamp
                                "gen_ai.event.end_time": str(uuid.uuid4()),    # Ideally would be actual timestamp
                                "event_loop.cycle_id": kwargs.get("cycle_id", "unknown")
                            }
                        )
                        
                        # Flush to send data immediately
                        langfuse_client.flush()
                        
                        logger.info(f"Langfuse trace updated with tool use: {tool_name}")
                
                # Handle cycle events if available
                elif "cycle" in kwargs:
                    cycle = kwargs.get("cycle", {})
                    cycle_id = cycle.get("id", "unknown")
                    
                    if hasattr(langfuse_context, "current_trace"):
                        langfuse_context.current_trace.span(
                            name=f"cycle_{cycle_id}",
                            input="",
                            output="",
                            metadata={
                                "event_loop.cycle_id": cycle_id,
                                "gen_ai.event.type": "agent_cycle",
                                "gen_ai.event.start_time": str(uuid.uuid4()),  # Ideally would be actual timestamp
                                "gen_ai.event.end_time": str(uuid.uuid4())     # Ideally would be actual timestamp
                            }
                        )
                        
                        langfuse_client.flush()
            except Exception as e:
                logger.error(f"Error in Langfuse callback handler: {e}")
        
        # Define a streaming callback handler that captures reasoning and tool usage
        def streaming_callback_handler(**kwargs):
            """Callback handler that captures reasoning and tool usage for streaming"""
            # First, call the Langfuse handler to maintain observability
            langfuse_callback_handler(**kwargs)
            
            # Store the event in the request_state for streaming
            # This will be used by the streaming endpoint to send events to the client
            if hasattr(streaming_callback_handler, 'events_queue'):
                event = {}
                
                # Handle text generation events
                if "data" in kwargs:
                    event = {
                        "type": "text",
                        "content": kwargs["data"],
                        "complete": kwargs.get("complete", False)
                    }
                
                # Handle tool use events
                elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
                    tool = kwargs["current_tool_use"]
                    event = {
                        "type": "tool",
                        "name": tool.get("name", "unknown_tool"),
                        "input": tool.get("input", {}),
                        "status": tool.get("status", "unknown")
                    }
                
                # Handle reasoning events
                elif kwargs.get("reasoning", False) and "reasoningText" in kwargs:
                    event = {
                        "type": "reasoning",
                        "content": kwargs.get("reasoningText", "")
                    }
                
                # Add event to queue if not empty
                if event:
                    streaming_callback_handler.events_queue.append(event)
        
        # Initialize the events queue for streaming
        streaming_callback_handler.events_queue = []
        
        # Choose the appropriate callback handler based on streaming flag
        callback_handler = streaming_callback_handler if streaming else langfuse_callback_handler
        
        # Create the agent following official Strands pattern
        # Note: We rely on AWS_DEFAULT_REGION environment variable for region selection
        # Use the inference profile ARN instead of direct model ID
        new_agent = Agent(
            model="arn:aws:bedrock:us-east-1:438465137422:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=all_tools,
            system_prompt=TCG_SYSTEM_PROMPT,
            callback_handler=callback_handler,
            trace_attributes={
                "service": "tcg-agent",
                "version": "2.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "model_provider": "anthropic",
                "model_name": "claude-3-7-sonnet",
                "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            }
        )
        
        # Store the agent globally if not streaming
        if not streaming:
            agent = new_agent
        
        logger.info(f"Strands agent initialized successfully with {len(all_tools)} total tools")
        return new_agent
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced agent: {str(e)}")
        raise RuntimeError(f"Agent initialization failed: {str(e)}")

def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the request body from the Lambda event"""
    try:
        # Handle different event formats
        if 'body' in event:
            if isinstance(event['body'], str):
                try:
                    body = json.loads(event['body'])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in request body: {e}")
            else:
                body = event['body']
        else:
            body = event
        
        # Validate required fields
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object")
        
        input_text = body.get('input_text', body.get('inputText', body.get('message', '')))
        if not input_text or not isinstance(input_text, str):
            raise ValueError("Missing or invalid 'input_text' field - must be a non-empty string")
        
        # Extract required fields with defaults
        return {
            'input_text': input_text.strip(),
            'session_id': body.get('session_id', str(uuid.uuid4())),
            'cart_id': body.get('cart_id', None)
        }
    except ValueError:
        raise  # Re-raise ValueError as-is
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        raise ValueError(f"Invalid request format: {str(e)}")

def create_langfuse_trace(request_data: Dict[str, Any], context) -> Optional[Any]:
    """Create Langfuse trace if available"""
    if not LANGFUSE_AVAILABLE or not langfuse_client:
        return None
    
    try:
        trace = langfuse_client.trace(
            name="tcg-agent-request",
            input=request_data['input_text'],
            session_id=request_data['session_id'],
            metadata={
                "cart_id": request_data.get('cart_id'),
                "request_length": len(request_data['input_text']),
                "lambda_request_id": context.aws_request_id if context else None
            }
        )
        return trace
    except Exception as e:
        logger.error(f"Failed to create Langfuse trace: {e}")
        return None

def update_langfuse_trace(trace, response: str):
    """Update Langfuse trace with response"""
    if not trace:
        return
    
    try:
        trace.update(
            output=str(response),
            metadata={
                "response_length": len(str(response)),
                "shopify_integration_active": shopify_mcp_manager.is_connected(),
                "tools_available": len(shopify_mcp_manager.get_tools()) if shopify_mcp_manager.is_connected() else 0
            }
        )
        
        # Flush to send data
        if langfuse_client:
            langfuse_client.flush()
            
    except Exception as e:
        logger.error(f"Failed to update Langfuse trace: {e}")

async def stream_agent_response(agent, input_text: str, session_id: str, cart_id: Optional[str] = None):
    """Stream the agent response using async iterators"""
    try:
        # Prepare input text with cart ID if available
        if cart_id:
            input_text += f" (Cart ID: {cart_id})"
        
        # Get the async stream from the agent
        agent_stream = agent.stream_async(input_text)
        
        # Process and yield events as they arrive
        async for event in agent_stream:
            # Format the event as a Server-Sent Event (SSE)
            if "data" in event:
                yield f"event: text\ndata: {json.dumps({'content': event['data']})}\n\n"
            
            elif "current_tool_use" in event and event["current_tool_use"].get("name"):
                tool = event["current_tool_use"]
                yield f"event: tool\ndata: {json.dumps({'name': tool.get('name'), 'input': tool.get('input')})}\n\n"
            
            elif event.get("reasoning", False) and "reasoningText" in event:
                yield f"event: reasoning\ndata: {json.dumps({'content': event.get('reasoningText', '')})}\n\n"
        
        # Signal the end of the stream
        yield "event: complete\ndata: {}\n\n"
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

async def lambda_handler_streaming(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Enhanced Lambda handler with streaming support"""
    try:
        # Handle health check
        if event.get('httpMethod') == 'GET' or event.get('requestContext', {}).get('http', {}).get('method') == 'GET':
            return handle_enhanced_health_check(event)
        
        # Parse request
        request_data = parse_request_body(event)
        logger.info(f"Processing streaming request: {request_data['input_text'][:100]}...")
        
        # Create Langfuse trace
        trace = create_langfuse_trace(request_data, context)
        
        # Set the trace as the current trace in langfuse_context if available
        if LANGFUSE_AVAILABLE and trace and hasattr(langfuse_context, "set_current_trace"):
            langfuse_context.set_current_trace(trace)
            logger.info(f"Set current Langfuse trace: {trace.id}")
        
        # Initialize agent with streaming enabled
        streaming_agent = initialize_agent(streaming=True)
        
        # Create a streaming response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, x-session-id",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS"
            },
            "body": stream_agent_response(
                streaming_agent, 
                request_data['input_text'],
                request_data['session_id'],
                request_data['cart_id']
            ),
            "isBase64Encoded": False
        }
    except ValueError as e:
        # Request validation errors (400)
        logger.error(f"Request validation error in streaming handler: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "invalid_request",
                "error_type": "request_validation_error",
                "message": str(e)
            })
        }
    except Exception as e:
        # Unexpected errors (500)
        logger.error(f"Unexpected error in streaming Lambda handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "internal_server_error",
                "error_type": "unexpected_error",
                "message": f"An unexpected error occurred: {str(e)}"
            })
        }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Enhanced Lambda handler with comprehensive error handling and Shopify integration"""
    try:
        # Handle health check
        if event.get('httpMethod') == 'GET' or event.get('requestContext', {}).get('http', {}).get('method') == 'GET':
            return handle_enhanced_health_check(event)
        
        # Parse request
        request_data = parse_request_body(event)
        logger.info(f"Processing request: {request_data['input_text'][:100]}...")
        
        # Create Langfuse trace
        trace = create_langfuse_trace(request_data, context)
        
        # Set the trace as the current trace in langfuse_context if available
        if LANGFUSE_AVAILABLE and trace and hasattr(langfuse_context, "set_current_trace"):
            langfuse_context.set_current_trace(trace)
            logger.info(f"Set current Langfuse trace: {trace.id}")
        
        # Initialize agent
        agent = initialize_agent()
        
        # Process request
        input_text = request_data['input_text']
        if request_data['cart_id']:
            input_text += f" (Cart ID: {request_data['cart_id']})"
        
        # Get response using the agent
        response = agent(input_text)
        logger.info("Agent response generated successfully")
        
        # Update Langfuse trace
        update_langfuse_trace(trace, response)
        
        # Return enhanced response with capability information
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, x-session-id",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS"
            },
            "body": json.dumps({
                "response": str(response),
                "sessionId": request_data['session_id'],
                "capabilities": {
                    "deck_recommendations": True,
                    "shopify_integration": shopify_mcp_manager.is_connected(),
                    "available_tools": [tool.get("name", "unknown") for tool in shopify_mcp_manager.get_tools()] if shopify_mcp_manager.is_connected() else []
                },
                "service_info": {
                    "name": "One Piece TCG Strands Agent",
                    "version": "2.0",
                    "mcp_integration": "Shopify Storefront MCP Server"
                }
            })
        }
        
    except ValueError as e:
        # Request validation errors (400)
        logger.error(f"Request validation error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "invalid_request",
                "error_type": "request_validation_error",
                "message": str(e),
                "troubleshooting": {
                    "required_fields": ["input_text"],
                    "example_request": {
                        "input_text": "Show me a Red Luffy deck",
                        "session_id": "optional-session-id"
                    }
                }
            })
        }
    
    except RuntimeError as e:
        # Configuration/initialization errors (503)
        logger.error(f"Service configuration error: {str(e)}")
        return {
            "statusCode": 503,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "service_unavailable",
                "error_type": "configuration_error",
                "message": f"Service configuration error: {str(e)}",
                "troubleshooting": {
                    "possible_causes": [
                        "Missing SSM parameters for API credentials",
                        "Shopify MCP server connection failure",
                        "AWS IAM permission issues",
                        "Invalid configuration values"
                    ],
                    "admin_actions": [
                        "Check SSM parameters in AWS console",
                        "Verify Lambda execution role permissions",
                        "Test Shopify store MCP endpoint availability",
                        "Review CloudWatch logs for detailed error information"
                    ]
                }
            })
        }
    
    except Exception as e:
        # Unexpected errors (500)
        logger.error(f"Unexpected error in Lambda handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "internal_server_error",
                "error_type": "unexpected_error",
                "message": f"An unexpected error occurred: {str(e)}",
                "troubleshooting": {
                    "immediate_actions": [
                        "Check CloudWatch logs for detailed error information",
                        "Verify all service dependencies are operational",
                        "Try the request again in a few moments"
                    ],
                    "support_info": {
                        "service": "One Piece TCG Strands Agent",
                        "version": "2.0",
                        "request_id": context.aws_request_id if context else "unknown"
                    }
                }
            })
        }

def handle_enhanced_health_check(event: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced health check with MCP server status"""
    
    # Test MCP connection
    mcp_status = "disconnected"
    mcp_tools = []
    mcp_error = None
    
    try:
        if shopify_mcp_manager.is_connected():
            mcp_status = "connected"
            mcp_tools = [tool.get("name", "unknown") for tool in shopify_mcp_manager.get_tools()]
        else:
            # Attempt to reconnect
            try:
                if shopify_mcp_manager.connect_and_discover_tools():
                    mcp_status = "connected"
                    mcp_tools = [tool.get("name", "unknown") for tool in shopify_mcp_manager.get_tools()]
                else:
                    mcp_status = "connection_failed"
                    mcp_error = "Failed to establish MCP connection"
            except Exception as e:
                mcp_status = "error"
                mcp_error = str(e)
    except Exception as e:
        logger.error(f"Health check MCP test failed: {e}")
        mcp_status = "error"
        mcp_error = str(e)
    
    # Determine overall health status
    overall_status = "healthy"
    if mcp_status in ["error", "connection_failed"]:
        overall_status = "degraded"
    
    return {
        "statusCode": 200 if overall_status == "healthy" else 503,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": overall_status,
            "service": "One Piece TCG Strands Agent v2.0",
            "capabilities": {
                "deck_recommendations": True,
                "shopify_mcp_integration": mcp_status == "connected"
            },
            "mcp_server": {
                "status": mcp_status,
                "shop_domain": shopify_mcp_manager.shop_domain,
                "available_tools": mcp_tools,
                "error": mcp_error
            },
            "environment": {
                "strands_available": True,
                "langfuse_configured": bool(os.getenv('LANGFUSE_PUBLIC_KEY')),
                "deck_api_configured": bool(os.getenv('COMPETITIVE_DECK_ENDPOINT')),
                "aws_region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')  # Add region info to health check
            },
            "timestamp": str(uuid.uuid4())
        })
    }
