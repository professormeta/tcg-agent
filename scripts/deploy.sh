#!/bin/bash

# Deploy Script for Strands Migration
# This script deploys the Strands agent using SAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}
STACK_NAME="strands-tcg-agent-full-$ENVIRONMENT"

echo -e "${GREEN}🚀 Deploying Strands Migration (Environment: $ENVIRONMENT)${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Verify prerequisites
echo -e "${YELLOW}🔍 Verifying prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI.${NC}"
    exit 1
fi

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI not found. Please install SAM CLI.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure'.${NC}"
    exit 1
fi

# Check if secrets are configured
echo -e "Checking Parameter Store configuration..."
if ! aws ssm get-parameters-by-path --path "/tcg-agent/$ENVIRONMENT" --recursive &> /dev/null; then
    echo -e "${RED}❌ Secrets not configured. Please run './scripts/setup-secrets.sh $ENVIRONMENT' first.${NC}"
    exit 1
fi

# Check if layers are built
if [ ! -f "layers/strands-layer/strands-layer.zip" ] || [ ! -f "layers/shopify-mcp-layer/shopify-mcp-layer.zip" ]; then
    echo -e "${RED}❌ Lambda layers not built. Please run './scripts/build-layers.sh' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites verified${NC}"

# Build the SAM application
echo -e "\n${YELLOW}🏗️ Building SAM application...${NC}"
sam build --use-container

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ SAM build completed${NC}"

# Deploy the application
echo -e "\n${YELLOW}🚀 Deploying to AWS...${NC}"

# Check if this is first deployment
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" &> /dev/null; then
    echo -e "${BLUE}📦 Updating existing stack: $STACK_NAME${NC}"
    GUIDED=""
else
    echo -e "${BLUE}🆕 Creating new stack: $STACK_NAME${NC}"
    GUIDED="--guided"
fi

# Deploy with SAM
sam deploy \
    $GUIDED \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProvisionedConcurrency=2 \
    --tags \
        Environment="$ENVIRONMENT" \
        Project="TCG-Strands-Agent" \
        ManagedBy="SAM"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Get deployment outputs
echo -e "\n${YELLOW}📋 Retrieving deployment information...${NC}"

FUNCTION_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
    --output text)

FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionName`].OutputValue' \
    --output text)

FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionArn`].OutputValue' \
    --output text)

# Save deployment info
cat > deployment-info.json << EOF
{
  "environment": "$ENVIRONMENT",
  "stack_name": "$STACK_NAME",
  "function_url": "$FUNCTION_URL",
  "function_name": "$FUNCTION_NAME",
  "function_arn": "$FUNCTION_ARN",
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "region": "$(aws configure get region)"
}
EOF

echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "\n${YELLOW}📋 Deployment Summary:${NC}"
echo -e "Environment: ${BLUE}$ENVIRONMENT${NC}"
echo -e "Stack Name: ${BLUE}$STACK_NAME${NC}"
echo -e "Function URL: ${BLUE}$FUNCTION_URL${NC}"
echo -e "Function Name: ${BLUE}$FUNCTION_NAME${NC}"

# Test the deployment
echo -e "\n${YELLOW}🧪 Running basic health check...${NC}"

HEALTH_CHECK=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"inputText": "Hello", "sessionId": "health-check"}' \
    --max-time 30 || echo "FAILED")

if [[ "$HEALTH_CHECK" == *"Ahoy"* ]]; then
    echo -e "${GREEN}✓ Health check passed - Agent is responding${NC}"
else
    echo -e "${YELLOW}⚠️ Health check inconclusive - Check logs for details${NC}"
fi

echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo -e "1. Update your Shopify webhook to: ${BLUE}$FUNCTION_URL${NC}"
echo -e "2. Run comprehensive tests: ${GREEN}./scripts/test-deployment.sh${NC}"
echo -e "3. Monitor logs: ${GREEN}aws logs tail /aws/lambda/$FUNCTION_NAME --follow${NC}"
echo -e "4. View CloudWatch metrics in AWS Console"

echo -e "\n${YELLOW}🔍 Useful commands:${NC}"
echo -e "View logs: ${GREEN}aws logs tail /aws/lambda/$FUNCTION_NAME --follow${NC}"
echo -e "Test function: ${GREEN}./scripts/test-deployment.sh${NC}"
echo -e "Update stack: ${GREEN}./scripts/deploy.sh $ENVIRONMENT${NC}"
echo -e "Delete stack: ${GREEN}aws cloudformation delete-stack --stack-name $STACK_NAME${NC}"

echo -e "\n${GREEN}✅ Deployment info saved to deployment-info.json${NC}"
