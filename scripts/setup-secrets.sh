#!/bin/bash

# Setup Secrets Script for Strands Migration
# This script stores all secrets in AWS Parameter Store securely

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}

echo -e "${GREEN}🔐 Setting up secrets for Strands Migration (Environment: $ENVIRONMENT)${NC}"

# Function to prompt for secret
prompt_secret() {
    local param_name=$1
    local description=$2
    local is_secret=${3:-true}
    
    echo -e "${YELLOW}Enter $description:${NC}"
    if [ "$is_secret" = "true" ]; then
        read -s value
        echo
    else
        read value
    fi
    
    if [ -z "$value" ]; then
        echo -e "${RED}Error: $description cannot be empty${NC}"
        exit 1
    fi
    
    echo "$value"
}

# Function to store parameter
store_parameter() {
    local name=$1
    local value=$2
    local type=${3:-SecureString}
    
    echo -e "Storing parameter: $name"
    
    aws ssm put-parameter \
        --name "$name" \
        --value "$value" \
        --type "$type" \
        --overwrite \
        --description "TCG Strands Agent configuration for $ENVIRONMENT" \
        > /dev/null
    
    echo -e "${GREEN}✓ Stored: $name${NC}"
}

echo -e "\n${YELLOW}📋 Please provide the following configuration values:${NC}\n"

# Shopify Configuration
echo -e "${YELLOW}=== Shopify Configuration ===${NC}"
SHOPIFY_URL=$(prompt_secret "shopify-url" "Shopify Store URL (e.g., https://your-store.myshopify.com)" false)
SHOPIFY_ACCESS_TOKEN=$(prompt_secret "shopify-access-token" "Shopify Admin API Access Token (shpat_...)")
SHOPIFY_STOREFRONT_TOKEN=$(prompt_secret "shopify-storefront-token" "Shopify Storefront Access Token")

# One Piece TCG API
echo -e "\n${YELLOW}=== One Piece TCG API Configuration ===${NC}"
DECK_API_SECRET=$(prompt_secret "deck-api-secret" "GumGum API Secret Key")
DECK_API_ENDPOINT=$(prompt_secret "deck-api-endpoint" "GumGum API Endpoint (e.g., https://api.gumgum.gg/decks)" false)

# Langfuse Configuration
echo -e "\n${YELLOW}=== Langfuse Monitoring Configuration ===${NC}"
LANGFUSE_PUBLIC_KEY=$(prompt_secret "langfuse-public-key" "Langfuse Public Key (pk_...)" false)
LANGFUSE_SECRET_KEY=$(prompt_secret "langfuse-secret-key" "Langfuse Secret Key (sk_...)")
LANGFUSE_API_URL=$(prompt_secret "langfuse-api-url" "Langfuse API URL (e.g., https://cloud.langfuse.com)" false)

echo -e "\n${GREEN}🚀 Storing parameters in AWS Parameter Store...${NC}\n"

# Store all parameters
store_parameter "/tcg-agent/$ENVIRONMENT/shopify/store-url" "$SHOPIFY_URL" "String"
store_parameter "/tcg-agent/$ENVIRONMENT/shopify/access-token" "$SHOPIFY_ACCESS_TOKEN" "SecureString"
store_parameter "/tcg-agent/$ENVIRONMENT/shopify/storefront-token" "$SHOPIFY_STOREFRONT_TOKEN" "SecureString"

store_parameter "/tcg-agent/$ENVIRONMENT/deck-api/secret" "$DECK_API_SECRET" "SecureString"
store_parameter "/tcg-agent/$ENVIRONMENT/deck-api/endpoint" "$DECK_API_ENDPOINT" "String"

store_parameter "/tcg-agent/$ENVIRONMENT/langfuse/public-key" "$LANGFUSE_PUBLIC_KEY" "String"
store_parameter "/tcg-agent/$ENVIRONMENT/langfuse/secret-key" "$LANGFUSE_SECRET_KEY" "SecureString"
store_parameter "/tcg-agent/$ENVIRONMENT/langfuse/host" "$LANGFUSE_API_URL" "String"

echo -e "\n${GREEN}✅ All secrets stored successfully!${NC}"
echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo -e "1. Run: ${GREEN}./scripts/build-layers.sh${NC}"
echo -e "2. Run: ${GREEN}./scripts/deploy.sh $ENVIRONMENT${NC}"
echo -e "3. Test the deployment with: ${GREEN}./scripts/test-deployment.sh${NC}"

echo -e "\n${YELLOW}🔍 To verify stored parameters:${NC}"
echo -e "aws ssm get-parameters-by-path --path \"/tcg-agent/$ENVIRONMENT\" --recursive --with-decryption"
