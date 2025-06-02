# One Piece TCG Assistant

A specialized AI assistant for One Piece Trading Card Game stores and players.

## 🎯 Business Value

The One Piece TCG Assistant helps card game stores and players by:

- **Increasing Sales** - Connecting players with products they need through intelligent Shopify integration
- **Enhancing Player Experience** - Providing expert deck recommendations based on tournament data
- **Saving Time** - Automating customer service for common TCG-related questions
- **Building Community** - Supporting players with competitive insights and product information

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

### 🤖 Natural Conversation

Powered by AWS Bedrock (Claude 3 Haiku):

- Understands complex TCG terminology and queries
- Maintains context throughout conversations
- Provides helpful responses to card game questions
- Handles both deck advice and shopping needs seamlessly

## 📊 Performance & Reliability

- **High Availability** - AWS-hosted with enterprise-grade uptime
- **Fast Responses** - Optimized for quick, helpful answers
- **Comprehensive Monitoring** - Langfuse tracking ensures quality
- **Secure** - Enterprise-level security for all operations

## 🚀 Getting Started

### For Store Owners

1. Configure your Shopify store connection
2. Set up your GumGum.gg API access
3. Deploy the assistant to your channels

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

## 📈 Business Impact

The One Piece TCG Assistant delivers measurable results:

- **Customer Satisfaction** - Instant, accurate responses to TCG queries
- **Operational Efficiency** - Automated customer service for common questions
- **Data-Driven Insights** - Analytics on popular decks and products
- **Competitive Edge** - Tournament-level deck recommendations

---

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** May 31, 2025
