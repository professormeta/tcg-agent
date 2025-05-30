#!/bin/bash

# Build Lambda Layers Script for Strands Migration
# This script builds the required Lambda layers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏗️ Building Lambda Layers for Strands Migration${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf layers/strands-layer/python
rm -rf layers/shopify-mcp-layer/nodejs
rm -f layers/strands-layer/strands-layer.zip
rm -f layers/shopify-mcp-layer/shopify-mcp-layer.zip

# Build Strands Layer
echo -e "\n${YELLOW}📦 Building Strands Layer...${NC}"
cd layers/strands-layer

# Create Python directory structure
mkdir -p python

# Create requirements.txt for the layer
cat > requirements.txt << EOF
strands-agents>=0.1.0
boto3>=1.34.0
langfuse>=2.0.0
requests>=2.31.0
mcp>=1.0.0
anthropic>=0.25.0
pydantic>=2.0.0
typing-extensions>=4.8.0
EOF

echo -e "Installing Python dependencies..."
pip install -r requirements.txt -t python/ --no-deps --platform linux_x86_64 --only-binary=:all:

# Create layer package
echo -e "Creating Strands layer package..."
zip -r strands-layer.zip python/ -q

echo -e "${GREEN}✓ Strands layer built: $(du -h strands-layer.zip | cut -f1)${NC}"

# Build Shopify MCP Layer
echo -e "\n${YELLOW}📦 Building Shopify MCP Layer...${NC}"
cd ../shopify-mcp-layer

# Create Node.js directory structure
mkdir -p nodejs

# Create package.json
cat > nodejs/package.json << EOF
{
  "name": "shopify-mcp-layer",
  "version": "1.0.0",
  "description": "Shopify MCP server for Lambda layer",
  "main": "shopify-mcp-server.js",
  "dependencies": {
    "@shopify/mcp-server-storefront": "^1.0.0"
  }
}
EOF

# Copy the MCP server script
cp shopify-mcp-server.js nodejs/

# Install Node.js dependencies
echo -e "Installing Node.js dependencies..."
cd nodejs
npm install --production --platform=linux --arch=x64
cd ..

# Create layer package
echo -e "Creating Shopify MCP layer package..."
zip -r shopify-mcp-layer.zip nodejs/ -q

echo -e "${GREEN}✓ Shopify MCP layer built: $(du -h shopify-mcp-layer.zip | cut -f1)${NC}"

# Return to project root
cd "$PROJECT_DIR"

# Verify layer sizes
echo -e "\n${YELLOW}📊 Layer Size Summary:${NC}"
STRANDS_SIZE=$(du -h layers/strands-layer/strands-layer.zip | cut -f1)
SHOPIFY_SIZE=$(du -h layers/shopify-mcp-layer/shopify-mcp-layer.zip | cut -f1)

echo -e "Strands Layer: ${GREEN}$STRANDS_SIZE${NC}"
echo -e "Shopify MCP Layer: ${GREEN}$SHOPIFY_SIZE${NC}"

# Check if layers are under AWS limits
STRANDS_BYTES=$(stat -f%z layers/strands-layer/strands-layer.zip 2>/dev/null || stat -c%s layers/strands-layer/strands-layer.zip)
SHOPIFY_BYTES=$(stat -f%z layers/shopify-mcp-layer/shopify-mcp-layer.zip 2>/dev/null || stat -c%s layers/shopify-mcp-layer/shopify-mcp-layer.zip)
TOTAL_BYTES=$((STRANDS_BYTES + SHOPIFY_BYTES))
TOTAL_MB=$((TOTAL_BYTES / 1024 / 1024))

if [ $TOTAL_MB -gt 250 ]; then
    echo -e "${RED}⚠️ Warning: Total layer size ($TOTAL_MB MB) exceeds AWS Lambda limit (250 MB)${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Total layer size: ${TOTAL_MB} MB (under 250 MB limit)${NC}"
fi

echo -e "\n${GREEN}🎉 All layers built successfully!${NC}"
echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo -e "1. Run: ${GREEN}./scripts/deploy.sh [environment]${NC}"
echo -e "2. Test the deployment with: ${GREEN}./scripts/test-deployment.sh${NC}"

# Create layer info file for deployment
cat > layers/layer-info.json << EOF
{
  "strands_layer": {
    "path": "layers/strands-layer/strands-layer.zip",
    "size_mb": $((STRANDS_BYTES / 1024 / 1024)),
    "compatible_runtimes": ["python3.11"]
  },
  "shopify_mcp_layer": {
    "path": "layers/shopify-mcp-layer/shopify-mcp-layer.zip", 
    "size_mb": $((SHOPIFY_BYTES / 1024 / 1024)),
    "compatible_runtimes": ["python3.11"]
  },
  "total_size_mb": $TOTAL_MB,
  "build_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${GREEN}✓ Layer info saved to layers/layer-info.json${NC}"
