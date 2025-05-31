# One Piece TCG Strands Agent v2.0

**Published:** May 31, 2025  
**Last Updated:** May 31, 2025  
**Version:** 2.0.0  
**Status:** Production Ready  
**Documentation Analysis Date:** May 31, 2025

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)

---

## 🎯 Overview

The **One Piece TCG Strands Agent** is an AI-powered customer service agent designed specifically for One Piece Trading Card Game stores. Built with the Strands Agents SDK and powered by AWS Bedrock (Claude 3 Haiku), it provides intelligent assistance for competitive deck recommendations and e-commerce operations through Shopify integration.

### Key Capabilities

- **🏆 Competitive Deck Recommendations** - Tournament-winning deck analysis from GumGum.gg
- **🛍️ E-commerce Integration** - Full Shopify storefront operations
- **🤖 Natural Language Processing** - AWS Bedrock-powered query understanding
- **📊 Advanced Monitoring** - Langfuse observability and CloudWatch metrics
- **🔒 Enterprise Security** - AWS SSM Parameter Store for secure configuration

---

## ✨ Features

### 🏆 Competitive Deck Analysis

**Powered by GumGum.gg Tournament Database**

- **Natural Language Queries**: "Show me a Red Luffy deck for OP10 in the West region"
- **Tournament Data**: Real competitive deck lists from tournament winners
- **Regional Support**: East (Asia) and West (North America/Europe) tournament data
- **Format Coverage**: OP01-OP11, ST sets, and latest releases
- **Complete Deck Lists**: Full card lists with quantities and metadata

**Technical Implementation:**
- AWS Bedrock (Claude 3 Haiku) for query parsing
- RESTful API integration with GumGum.gg
- Intelligent filter extraction from natural language
- Comprehensive error handling and fallbacks

### 🛍️ Shopify E-commerce Integration

**Full Storefront Operations via MCP Server**

- **Product Catalog Search**: "Show me booster packs" or "Find OP10 cards"
- **Shopping Cart Management**: Add items, view cart, update quantities
- **Store Information**: Policies, shipping, returns, and store details
- **Session Management**: Persistent cart and user preferences

**MCP Integration Features:**
- Shopify Storefront MCP server connection
- Real-time product availability
- Secure cart operations
- Store policy retrieval

### 🤖 AI-Powered Intelligence

**AWS Bedrock Integration**

- **Model**: Claude 3 Haiku (us.anthropic.claude-3-haiku-20240307-v1:0)
- **Natural Language Understanding**: Complex query parsing and intent recognition
- **Context Awareness**: Session-based conversation memory
- **Error Recovery**: Intelligent fallback responses

### 📊 Monitoring & Observability

**Comprehensive Tracking**

- **Langfuse Integration**: Request tracking, performance metrics, conversation analysis
- **CloudWatch Logs**: Detailed application logging with structured data
- **Health Monitoring**: Enhanced health checks with dependency status
- **Performance Metrics**: Response times, error rates, and usage analytics

### 🔒 Security & Configuration

**Enterprise-Grade Security**

- **AWS SSM Parameter Store**: Secure secret management
- **IAM Role-Based Access**: Least privilege security model
- **Environment Isolation**: Production/staging parameter separation
- **Encrypted Storage**: All secrets encrypted at rest

---

## 🏗️ Architecture

### Infrastructure Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Lambda Function │────│  AWS Bedrock    │
│   (REST API)    │    │  (Container)     │    │  (Claude 3)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Shopify MCP   │    │  SSM Parameters  │    │   GumGum.gg     │
│    Server       │    │   (Secrets)      │    │     API         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudWatch    │    │    Langfuse      │    │      ECR        │
│     Logs        │    │   Monitoring     │    │  (Container)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack

- **Runtime**: Python 3.12
- **Framework**: Strands Agents SDK
- **AI Model**: AWS Bedrock (Claude 3 Haiku)
- **Deployment**: AWS SAM + Docker containers
- **API**: AWS API Gateway (REST)
- **Storage**: AWS SSM Parameter Store
- **Monitoring**: Langfuse + CloudWatch
- **Container Registry**: Amazon ECR

### Current Deployment

- **Stack Name**: `tcg-agent-prod`
- **Region**: `us-east-1`
- **Environment**: `production`
- **API Endpoint**: `https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production`
- **Lambda Function**: `tcg-agent-prod-agent`
- **Container Image**: ECR-hosted with multi-stage build

---

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Docker Desktop installed and running
- SAM CLI installed
- Python 3.12+

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tcg-agent
```

### 2. Configure Secrets

```bash
# Interactive secret setup
./scripts/setup-secrets.sh production

# Or manually configure SSM parameters
aws ssm put-parameter --name "/tcg-agent/production/shopify/store-url" \
  --value "https://your-store.myshopify.com" --type "String"
```

### 3. Deploy

```bash
# Build and deploy
./scripts/deploy.sh production
```

### 4. Test

```bash
# Run comprehensive tests
./scripts/test-deployment.sh
```

### 5. Verify

```bash
# Test the API
curl -X POST https://your-api-endpoint/production \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Show me a Red Luffy deck", "sessionId": "test"}'
```

---

## ⚙️ Configuration

### Required SSM Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `/tcg-agent/{env}/shopify/store-url` | String | Shopify store URL |
| `/tcg-agent/{env}/shopify/access-token` | SecureString | Shopify Admin API token |
| `/tcg-agent/{env}/shopify/storefront-token` | SecureString | Shopify Storefront token |
| `/tcg-agent/{env}/deck-api/endpoint` | String | GumGum.gg API endpoint |
| `/tcg-agent/{env}/deck-api/secret` | SecureString | GumGum.gg API key |
| `/tcg-agent/{env}/langfuse/public-key` | String | Langfuse public key |
| `/tcg-agent/{env}/langfuse/secret-key` | SecureString | Langfuse secret key |
| `/tcg-agent/{env}/langfuse/host` | String | Langfuse host URL |

### Environment Variables

The Lambda function automatically loads configuration from SSM parameters:

```python
# Automatically configured from SSM
COMPETITIVE_DECK_ENDPOINT = "https://gumgum.gg/api/decklists"
SHOPIFY_STORE_URL = "https://tcg-ai.myshopify.com/"
LANGFUSE_HOST = "https://cloud.langfuse.com"
```

---

## 📡 API Documentation

### Base URL
```
https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production
```

### Endpoints

#### POST `/` - Main Agent Interaction

**Request:**
```json
{
  "inputText": "Show me a Red Luffy deck for OP10",
  "sessionId": "user-session-123",
  "cartId": "optional-cart-id"
}
```

**Response:**
```json
{
  "response": "Here's a tournament-winning Red Luffy deck from OP10...",
  "sessionId": "user-session-123",
  "capabilities": {
    "deck_recommendations": true,
    "shopify_integration": true,
    "available_tools": ["get_competitive_decks", "search_shop_catalog"]
  },
  "service_info": {
    "name": "One Piece TCG Strands Agent",
    "version": "2.0",
    "mcp_integration": "Shopify Storefront MCP Server"
  }
}
```

#### GET `/health` - Health Check

**Response:**
```json
{
  "status": "healthy",
  "service": "One Piece TCG Strands Agent v2.0",
  "capabilities": {
    "deck_recommendations": true,
    "shopify_mcp_integration": true
  },
  "mcp_server": {
    "status": "connected",
    "shop_domain": "tcg-ai.myshopify.com",
    "available_tools": ["search_shop_catalog", "manage_cart"]
  },
  "environment": {
    "strands_available": true,
    "langfuse_configured": true,
    "deck_api_configured": true
  }
}
```

### Error Responses

#### 400 - Bad Request
```json
{
  "error": "invalid_request",
  "error_type": "request_validation_error",
  "message": "Missing or invalid 'input_text' field",
  "troubleshooting": {
    "required_fields": ["inputText"],
    "example_request": {
      "inputText": "Show me a Red Luffy deck",
      "sessionId": "optional-session-id"
    }
  }
}
```

#### 503 - Service Unavailable
```json
{
  "error": "service_unavailable",
  "error_type": "configuration_error",
  "message": "Service configuration error: Shopify MCP connection failed",
  "troubleshooting": {
    "possible_causes": [
      "Missing SSM parameters for API credentials",
      "Shopify MCP server connection failure"
    ]
  }
}
```

---

## 🚀 Deployment

### Deployment Architecture

The system uses AWS SAM for infrastructure as code with container-based Lambda deployment:

```yaml
# template.yml structure
Resources:
  - StrandsAgentFunction (Lambda)
  - StrandsApi (API Gateway)
  - IAM Roles and Policies
  - Lambda Permissions
```

### Deployment Process

1. **Build Container**: Multi-stage Docker build for optimized size
2. **Push to ECR**: Automatic container registry management
3. **SAM Deploy**: Infrastructure and code deployment
4. **Health Check**: Automated deployment verification

### Deployment Scripts

- `./scripts/setup-secrets.sh` - Configure SSM parameters
- `./scripts/deploy.sh` - Build and deploy application
- `./scripts/test-deployment.sh` - Comprehensive testing

### Container Details

- **Base Image**: `public.ecr.aws/lambda/python:3.12`
- **Multi-stage Build**: Optimized for size and performance
- **Dependencies**: Installed in separate layer for caching
- **Handler**: `lambda_function.lambda_handler`

---

## 📊 Monitoring

### Langfuse Integration

**Observability Features:**
- Request/response tracking
- Performance metrics
- Conversation analysis
- Error monitoring
- Usage analytics

**Configuration:**
```python
# Automatic observability with decorators
@observe
def lambda_handler(event, context):
    # Automatic request tracking
    pass
```

### CloudWatch Monitoring

**Metrics Tracked:**
- Lambda invocations
- Error rates
- Response times
- Memory usage
- API Gateway metrics

**Log Groups:**
- `/aws/lambda/tcg-agent-prod-agent`

### Health Monitoring

**Health Check Features:**
- Service dependency status
- MCP server connectivity
- Configuration validation
- Performance benchmarks

---

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export COMPETITIVE_DECK_ENDPOINT="https://api.gumgum.gg/decks"
export COMPETITIVE_DECK_SECRET="your-api-key"

# Run locally (requires SAM CLI)
sam local start-api
```

### Testing

```bash
# Unit tests
python -m pytest tests/

# Integration tests
./scripts/test-deployment.sh

# Load testing
# Included in test-deployment.sh (5 concurrent requests)
```

### Code Structure

```
tcg-agent/
├── agent.py                 # Main Lambda handler
├── tools/
│   └── deck_recommender.py  # GumGum.gg integration
├── scripts/
│   ├── deploy.sh           # Deployment automation
│   ├── setup-secrets.sh    # Secret management
│   └── test-deployment.sh  # Testing suite
├── template.yml            # SAM infrastructure
├── Dockerfile             # Container definition
└── requirements.txt       # Python dependencies
```

### Key Components

1. **Agent Handler** (`agent.py`):
   - Strands Agent initialization
   - Shopify MCP integration
   - Error handling and observability

2. **Deck Recommender** (`tools/deck_recommender.py`):
   - GumGum.gg API integration
   - Natural language processing
   - Tournament data formatting

3. **Infrastructure** (`template.yml`):
   - Lambda function definition
   - API Gateway configuration
   - IAM permissions

---

## 🔧 Troubleshooting

### Common Issues

#### 1. MCP Connection Failures
```bash
# Check Shopify store URL
aws ssm get-parameter --name "/tcg-agent/production/shopify/store-url"

# Verify MCP endpoint accessibility
curl https://your-store.myshopify.com/api/mcp
```

#### 2. Deck API Errors
```bash
# Verify API credentials
aws ssm get-parameter --name "/tcg-agent/production/deck-api/secret" --with-decryption

# Test API endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" https://gumgum.gg/api/decklists
```

#### 3. Lambda Timeout Issues
```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/tcg-agent-prod-agent --follow

# Monitor performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=tcg-agent-prod-agent
```

### Debug Mode

Enable detailed logging:
```bash
# Set environment variable
aws lambda update-function-configuration \
  --function-name tcg-agent-prod-agent \
  --environment Variables='{STRANDS_DEBUG=true,DEBUG_SSM=true}'
```

### Performance Optimization

- **Cold Start**: Container images reduce cold start time
- **Memory**: Currently set to 1024MB (optimal for Claude 3 Haiku)
- **Timeout**: 30 seconds (sufficient for most operations)
- **Concurrency**: No reserved concurrency (scales automatically)

---

## 📈 Version History

| Version | Date | Key Features | Breaking Changes |
|---------|------|--------------|------------------|
| **2.0.0** | May 31, 2025 | Shopify MCP integration, Enhanced monitoring, Container deployment | MCP server required |
| **1.x** | Previous | Basic deck recommendations, REST API | - |

### Current Version (2.0.0) - May 31, 2025

**New Features:**
- ✅ Shopify Storefront MCP integration
- ✅ Enhanced error handling and observability
- ✅ Container-based Lambda deployment
- ✅ Comprehensive testing suite
- ✅ Advanced health monitoring

**Technical Improvements:**
- ✅ Multi-stage Docker builds
- ✅ SSM Parameter Store integration
- ✅ Langfuse observability
- ✅ AWS Bedrock Claude 3 Haiku
- ✅ Automated deployment scripts

**Infrastructure:**
- ✅ AWS SAM template
- ✅ ECR container registry
- ✅ API Gateway REST API
- ✅ CloudWatch monitoring

---

## 📞 Support

### Documentation
- **API Reference**: See [API Documentation](#api-documentation)
- **Deployment Guide**: See [Deployment](#deployment)
- **Troubleshooting**: See [Troubleshooting](#troubleshooting)

### Monitoring
- **Langfuse Dashboard**: Monitor at configured Langfuse host
- **CloudWatch**: AWS Console → CloudWatch → Log Groups
- **Health Check**: `GET /health` endpoint

### Maintenance
- **Regular Updates**: Monitor for Strands SDK updates
- **Security**: Rotate API keys quarterly
- **Performance**: Review CloudWatch metrics monthly

---

**Last Updated:** May 31, 2025  
**Next Review:** June 30, 2025  
**Maintainer:** TCG Agent Development Team
