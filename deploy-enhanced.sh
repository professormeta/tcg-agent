#!/bin/bash

# Enhanced Strands Deployment Script
# Deploys the full infrastructure with API Gateway, WebSocket, and streaming support

set -e

echo "🏴‍☠️ Starting Enhanced Strands Deployment..."

# Configuration
STACK_NAME="one-piece-tcg-strands-enhanced"
ENVIRONMENT="production"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS CLI not configured or no valid credentials found"
    exit 1
fi

print_success "AWS CLI configured successfully"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    print_error "SAM CLI not found. Please install AWS SAM CLI first."
    exit 1
fi

print_success "SAM CLI found"

# Build the layers first
print_status "Building Lambda layers..."

# Build Strands layer if it doesn't exist
if [ ! -f "layers/strands-layer/strands-layer.zip" ]; then
    print_warning "Strands layer not found. Building..."
    cd layers/strands-layer
    pip install -r requirements.txt -t python/
    zip -r strands-layer.zip python/
    cd ../..
    print_success "Strands layer built"
else
    print_success "Strands layer already exists"
fi

# Build Shopify MCP layer if it doesn't exist
if [ ! -f "layers/shopify-mcp-layer/shopify-mcp-layer.zip" ]; then
    print_warning "Shopify MCP layer not found. Building..."
    cd layers/shopify-mcp-layer
    npm install
    zip -r shopify-mcp-layer.zip nodejs/
    cd ../..
    print_success "Shopify MCP layer built"
else
    print_success "Shopify MCP layer already exists"
fi

# Build the SAM application
print_status "Building SAM application..."
sam build --template-file template-enhanced.yaml

if [ $? -eq 0 ]; then
    print_success "SAM build completed successfully"
else
    print_error "SAM build failed"
    exit 1
fi

# Deploy the application
print_status "Deploying enhanced infrastructure..."

sam deploy \
    --template-file template-enhanced.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        ProvisionedConcurrency=2 \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
    print_success "Enhanced deployment completed successfully!"
else
    print_error "Deployment failed"
    exit 1
fi

# Get the outputs
print_status "Retrieving deployment outputs..."

HTTP_API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`HttpApiUrl`].OutputValue' \
    --output text)

WEBSOCKET_API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`WebSocketApiUrl`].OutputValue' \
    --output text)

CHAT_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ChatEndpoint`].OutputValue' \
    --output text)

HEALTH_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`HealthEndpoint`].OutputValue' \
    --output text)

# Display results
echo ""
echo "🏴‍☠️ =================================="
echo "🏴‍☠️ ENHANCED DEPLOYMENT COMPLETE!"
echo "🏴‍☠️ =================================="
echo ""
print_success "HTTP API URL: $HTTP_API_URL"
print_success "WebSocket API URL: $WEBSOCKET_API_URL"
print_success "Chat Endpoint: $CHAT_ENDPOINT"
print_success "Health Endpoint: $HEALTH_ENDPOINT"
echo ""

# Test the health endpoint
print_status "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_success "Health check passed! ✅"
else
    print_warning "Health check returned status: $HEALTH_RESPONSE"
fi

# Save endpoints to file
cat > deployment-endpoints.txt << EOF
Enhanced Strands Deployment Endpoints
=====================================

HTTP API URL: $HTTP_API_URL
WebSocket API URL: $WEBSOCKET_API_URL
Chat Endpoint: $CHAT_ENDPOINT
Health Endpoint: $HEALTH_ENDPOINT

Features Deployed:
- ✅ API Gateway HTTP API (stable endpoints)
- ✅ WebSocket API (streaming support)
- ✅ DynamoDB (connection management)
- ✅ Enhanced Lambda with all tools
- ✅ Competitive deck recommendations
- ✅ Shopify MCP integration
- ✅ Streaming responses
- ✅ Session management
- ✅ Error handling & monitoring

Test Commands:
--------------

# Test health endpoint
curl "$HEALTH_ENDPOINT"

# Test chat endpoint
curl -X POST "$CHAT_ENDPOINT" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello! Show me a Red Shanks deck for OP09"}'

# WebSocket connection (use a WebSocket client)
# Connect to: $WEBSOCKET_API_URL
# Send: {"action": "message", "message": "Hello pirate!"}

Deployment completed at: $(date)
EOF

print_success "Endpoints saved to deployment-endpoints.txt"

echo ""
echo "🏴‍☠️ Ready to sail the digital seas with enhanced functionality!"
echo "🏴‍☠️ All tools and streaming capabilities are now available!"
echo ""
