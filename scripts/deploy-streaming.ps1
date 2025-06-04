# PowerShell script for deploying TCG Agent with streaming support

# Parse command line arguments
param(
    [switch]$SkipBuild,
    [switch]$SkipPush,
    [switch]$SkipDeploy,
    [string]$Environment = "production"
)

# Configuration
$STACK_NAME = "tcg-agent-prod"
$REGION = "us-east-1"  # Change to your preferred region
$S3_BUCKET = "tcg-agent-deployment"  # S3 bucket for deployment artifacts
$ECR_REPOSITORY = "${STACK_NAME}-agent"

# Update stack name with environment if not production
if ($Environment -ne "production") {
    $STACK_NAME = "${STACK_NAME}-${Environment}"
    $ECR_REPOSITORY = "${ECR_REPOSITORY}-${Environment}"
}

Write-Host "Deploying TCG Agent with streaming support" -ForegroundColor Blue
Write-Host "Stack name: ${STACK_NAME}" -ForegroundColor Blue
Write-Host "Region: ${REGION}" -ForegroundColor Blue
Write-Host "Environment: ${Environment}" -ForegroundColor Blue
Write-Host "ECR Repository: ${ECR_REPOSITORY}" -ForegroundColor Blue

# Check if AWS CLI is installed
try {
    aws --version
}
catch {
    Write-Host "AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
try {
    docker --version
}
catch {
    Write-Host "Docker is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if SAM CLI is installed
try {
    sam --version
}
catch {
    Write-Host "SAM CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Get AWS account ID
$AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
Write-Host "AWS Account ID: ${AWS_ACCOUNT_ID}" -ForegroundColor Blue

# Create ECR repository if it doesn't exist
try {
    aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${REGION} | Out-Null
}
catch {
    Write-Host "Creating ECR repository: ${ECR_REPOSITORY}" -ForegroundColor Yellow
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${REGION}
}

# Build Docker image
if (-not $SkipBuild) {
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t ${ECR_REPOSITORY}:latest .
    Write-Host "Docker image built successfully" -ForegroundColor Green
}

# Push Docker image to ECR
if (-not $SkipPush) {
    Write-Host "Logging in to ECR..." -ForegroundColor Yellow
    aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
    
    Write-Host "Tagging Docker image..." -ForegroundColor Yellow
    docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
    
    Write-Host "Pushing Docker image to ECR..." -ForegroundColor Yellow
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
    Write-Host "Docker image pushed successfully" -ForegroundColor Green
}

# Deploy SAM template
if (-not $SkipDeploy) {
    Write-Host "Packaging SAM template..." -ForegroundColor Yellow
    sam package `
        --template-file template.yml `
        --output-template-file packaged.yml `
        --s3-bucket ${S3_BUCKET} `
        --region ${REGION}
    
    Write-Host "Deploying SAM template..." -ForegroundColor Yellow
    sam deploy `
        --template-file packaged.yml `
        --stack-name ${STACK_NAME} `
        --capabilities CAPABILITY_IAM `
        --parameter-overrides Environment=${Environment} `
        --region ${REGION}
    
    Write-Host "Deployment completed successfully" -ForegroundColor Green
    
    # Get API Gateway URL
    $API_URL = aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
    Write-Host "API Gateway URL: ${API_URL}" -ForegroundColor Green
    
    # Get WebSocket API URL
    $WEBSOCKET_URL = aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='WebSocketApiUrl'].OutputValue" --output text
    Write-Host "WebSocket API URL: ${WEBSOCKET_URL}" -ForegroundColor Green
    
    # Get DynamoDB table name
    $DYNAMODB_TABLE = aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='ConnectionsTableName'].OutputValue" --output text
    Write-Host "DynamoDB table name: ${DYNAMODB_TABLE}" -ForegroundColor Green
}

Write-Host "Deployment script completed" -ForegroundColor Green
