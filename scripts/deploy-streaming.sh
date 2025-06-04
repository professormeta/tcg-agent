#!/bin/bash
# Deployment script for TCG Agent with streaming support

# Exit on error
set -e

# Configuration
STACK_NAME="tcg-agent-prod"
REGION="us-east-1"  # Change to your preferred region
S3_BUCKET="tcg-agent-deployment"  # S3 bucket for deployment artifacts
ECR_REPOSITORY="${STACK_NAME}-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_color $RED "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_color $RED "Docker is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    print_color $RED "SAM CLI is not installed. Please install it first."
    exit 1
fi

# Parse command line arguments
SKIP_BUILD=false
SKIP_PUSH=false
SKIP_DEPLOY=false
ENVIRONMENT="production"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-push)
            SKIP_PUSH=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift
            shift
            ;;
        *)
            print_color $RED "Unknown option: $key"
            exit 1
            ;;
    esac
done

# Update stack name with environment if not production
if [ "$ENVIRONMENT" != "production" ]; then
    STACK_NAME="${STACK_NAME}-${ENVIRONMENT}"
    ECR_REPOSITORY="${ECR_REPOSITORY}-${ENVIRONMENT}"
fi

print_color $BLUE "Deploying TCG Agent with streaming support"
print_color $BLUE "Stack name: ${STACK_NAME}"
print_color $BLUE "Region: ${REGION}"
print_color $BLUE "Environment: ${ENVIRONMENT}"
print_color $BLUE "ECR Repository: ${ECR_REPOSITORY}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_color $BLUE "AWS Account ID: ${AWS_ACCOUNT_ID}"

# Create ECR repository if it doesn't exist
if ! aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${REGION} &> /dev/null; then
    print_color $YELLOW "Creating ECR repository: ${ECR_REPOSITORY}"
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${REGION}
fi

# Build Docker image
if [ "$SKIP_BUILD" = false ]; then
    print_color $YELLOW "Building Docker image..."
    docker build -t ${ECR_REPOSITORY}:latest .
    print_color $GREEN "Docker image built successfully"
fi

# Push Docker image to ECR
if [ "$SKIP_PUSH" = false ]; then
    print_color $YELLOW "Logging in to ECR..."
    aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
    
    print_color $YELLOW "Tagging Docker image..."
    docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
    
    print_color $YELLOW "Pushing Docker image to ECR..."
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
    print_color $GREEN "Docker image pushed successfully"
fi

# Deploy SAM template
if [ "$SKIP_DEPLOY" = false ]; then
    print_color $YELLOW "Packaging SAM template..."
    sam package \
        --template-file template.yml \
        --output-template-file packaged.yml \
        --s3-bucket ${S3_BUCKET} \
        --region ${REGION}
    
    print_color $YELLOW "Deploying SAM template..."
    sam deploy \
        --template-file packaged.yml \
        --stack-name ${STACK_NAME} \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides Environment=${ENVIRONMENT} \
        --region ${REGION}
    
    print_color $GREEN "Deployment completed successfully"
    
    # Get API Gateway URL
    API_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
    print_color $GREEN "API Gateway URL: ${API_URL}"
    
    # Get WebSocket API URL
    WEBSOCKET_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='WebSocketApiUrl'].OutputValue" --output text)
    print_color $GREEN "WebSocket API URL: ${WEBSOCKET_URL}"
    
    # Get DynamoDB table name
    DYNAMODB_TABLE=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='ConnectionsTableName'].OutputValue" --output text)
    print_color $GREEN "DynamoDB table name: ${DYNAMODB_TABLE}"
fi

print_color $GREEN "Deployment script completed"
