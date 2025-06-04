# One Piece TCG Assistant

A specialized AI assistant for One Piece Trading Card Game stores and players.

## 🎯 Business Value

The One Piece TCG Assistant helps card game stores and players by:

- **Increasing Sales** - Connecting players with products they need through intelligent Shopify integration
- **Enhancing Player Experience** - Providing expert deck recommendations based on tournament data
- **Saving Time** - Automating customer service for common TCG-related questions
- **Building Community** - Supporting players with competitive insights and product information
- **Building Trust** - Real-time streaming of agent reasoning and tool usage for transparency

## ✨ Key Features

### 🏆 Competitive Deck Recommendations

Get winning deck strategies powered by real tournament data:

- Find decks by color, character, set, or region
- Access tournament-winning strategies from GumGum.gg
- Get complete deck lists with card quantities
- Filter by format (OP01-OP11) and region (East/West)

Example: *"Show me a Red Luffy deck for OP10 in the West region"*

### 🛍️ Seamless Shopping Experience

Complete Shopify integration for card game stores:

- Search product catalog with natural language
- Manage shopping cart directly through the assistant
- Check product availability and pricing
- Access store policies and shipping information

Example: *"Find OP10 booster packs in stock"*

### 🔄 Real-Time Streaming Responses

Watch the assistant's thought process in real-time:

- See reasoning as it happens
- View tool usage as the agent works
- Understand how recommendations are formed
- Faster time-to-first-byte for improved user experience

Example: *Open the WebSocket client to see the agent's reasoning as it builds a deck recommendation*

### 🤖 Natural Conversation

Powered by AWS Bedrock (Claude 3 Haiku):

- Understands complex TCG terminology and queries
- Maintains context throughout conversations
- Provides helpful responses to card game questions
- Handles both deck advice and shopping needs seamlessly

## 📊 Performance & Reliability

- **High Availability** - AWS-hosted with enterprise-grade uptime
- **Fast Responses** - Optimized for quick, helpful answers with streaming support
- **Comprehensive Monitoring** - Langfuse tracking ensures quality
- **Secure** - Enterprise-level security for all operations
- **Real-Time Streaming** - WebSocket API for instant feedback and transparency
- **Scalable Architecture** - DynamoDB for connection tracking and WebSocket management

## 🚀 Getting Started

### For Store Owners

1. Configure your Shopify store connection
2. Set up your GumGum.gg API access
3. Deploy the assistant to your channels
4. Integrate the WebSocket client for real-time streaming responses

### For Developers

Basic setup:

```bash
# Clone and setup
git clone <repository-url>
cd tcg-agent

# Configure secrets
./scripts/setup-secrets.sh production

# Deploy
./scripts/deploy.sh production
```

### Testing Streaming Functionality

```bash
# Run local tests
cd tests/streaming_tests
python run_tests.py --verbose

# Test streaming agent manually
python manual_test.py agent --input "Show me a Red Luffy deck"

# Run local WebSocket server
python manual_test.py server

# Test WebSocket client
python manual_test.py websocket --input "Show me a Red Luffy deck"
```

### Deploying with Streaming Support

```bash
# Deploy with streaming support
./scripts/deploy-streaming.sh --environment production

# Deploy to staging environment
./scripts/deploy-streaming.sh --environment staging

# Skip build and push (for testing)
./scripts/deploy-streaming.sh --skip-build --skip-push
```

### WebSocket Integration

To integrate the WebSocket client in your application:

```javascript
// Connect to WebSocket API
const socket = new WebSocket('wss://your-api-id.execute-api.region.amazonaws.com/production');

// Send a message
socket.send(JSON.stringify({
  action: 'message',
  message: 'Show me a Red Luffy deck',
  sessionId: 'user-session-id'
}));

// Handle responses
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'text':
      // Handle text response
      console.log('Text:', data.content);
      break;
    case 'reasoning':
      // Handle reasoning
      console.log('Reasoning:', data.content);
      break;
    case 'tool':
      // Handle tool usage
      console.log('Tool:', data.name, data.input);
      break;
    case 'complete':
      // Handle completion
      console.log('Response complete');
      break;
  }
};
```

For more details, see the [STREAMING.md](STREAMING.md) documentation.

## 📈 Business Impact

The One Piece TCG Assistant delivers measurable results:

- **Customer Satisfaction** - Instant, accurate responses to TCG queries
- **Operational Efficiency** - Automated customer service for common questions
- **Data-Driven Insights** - Analytics on popular decks and products
- **Competitive Edge** - Tournament-level deck recommendations
- **Enhanced Trust** - Transparent AI reasoning builds customer confidence
- **Improved Engagement** - Real-time streaming keeps users engaged during responses

---

**Version:** 2.1.0  
**Status:** Production Ready  
**Last Updated:** June 2, 2025
