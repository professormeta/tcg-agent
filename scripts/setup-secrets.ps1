# Setup Secrets Script for Strands Migration (PowerShell)
# This script stores all secrets in AWS Parameter Store securely

param(
    [string]$Environment = "production"
)

Write-Host "🔐 Setting up secrets for Strands Migration (Environment: $Environment)" -ForegroundColor Green

# Function to prompt for secret
function Get-SecretInput {
    param(
        [string]$Description,
        [bool]$IsSecret = $true
    )
    
    Write-Host "Enter ${Description}:" -ForegroundColor Yellow
    if ($IsSecret) {
        $value = Read-Host -AsSecureString
        $value = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($value))
    } else {
        $value = Read-Host
    }
    
    if ([string]::IsNullOrEmpty($value)) {
        Write-Host "Error: $Description cannot be empty" -ForegroundColor Red
        exit 1
    }
    
    return $value
}

# Function to store parameter
function Store-Parameter {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Type = "SecureString"
    )
    
    Write-Host "Storing parameter: $Name"
    
    aws ssm put-parameter --name $Name --value $Value --type $Type --overwrite --description "TCG Strands Agent configuration for $Environment" | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stored: $Name" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to store: $Name" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n📋 Please provide the following configuration values:`n" -ForegroundColor Yellow

# Shopify Configuration
Write-Host "=== Shopify Configuration ===" -ForegroundColor Yellow
$ShopifyUrl = Get-SecretInput "Shopify Store URL (e.g., https://your-store.myshopify.com)" $false
$ShopifyAccessToken = Get-SecretInput "Shopify Admin API Access Token (shpat_...)"

# One Piece TCG API
Write-Host "`n=== One Piece TCG API Configuration ===" -ForegroundColor Yellow
$DeckApiSecret = Get-SecretInput "Deck API Secret Key"
$DeckApiEndpoint = Get-SecretInput "Deck API Endpoint (e.g., https://api.example.com/decks)" $false

# Langfuse Configuration
Write-Host "`n=== Langfuse Monitoring Configuration ===" -ForegroundColor Yellow
$LangfusePublicKey = Get-SecretInput "Langfuse Public Key (pk_...)" $false
$LangfuseSecretKey = Get-SecretInput "Langfuse Secret Key (sk_...)"
$LangfuseHost = Get-SecretInput "Langfuse Host URL (e.g., https://cloud.langfuse.com)" $false

Write-Host "`n🚀 Storing parameters in AWS Parameter Store...`n" -ForegroundColor Green

# Store all parameters
Store-Parameter "/tcg-agent/$Environment/shopify/store-url" $ShopifyUrl "String"
Store-Parameter "/tcg-agent/$Environment/shopify/access-token" $ShopifyAccessToken "SecureString"

Store-Parameter "/tcg-agent/$Environment/deck-api/secret" $DeckApiSecret "SecureString"
Store-Parameter "/tcg-agent/$Environment/deck-api/endpoint" $DeckApiEndpoint "String"

Store-Parameter "/tcg-agent/$Environment/langfuse/public-key" $LangfusePublicKey "String"
Store-Parameter "/tcg-agent/$Environment/langfuse/secret-key" $LangfuseSecretKey "SecureString"
Store-Parameter "/tcg-agent/$Environment/langfuse/host" $LangfuseHost "String"

Write-Host "`n✅ All secrets stored successfully!" -ForegroundColor Green
Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the deployment with: " -NoNewline
Write-Host "curl https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production/health" -ForegroundColor Green

Write-Host "`n🔍 To verify stored parameters:" -ForegroundColor Yellow
Write-Host "aws ssm get-parameters-by-path --path `"/tcg-agent/$Environment`" --recursive --with-decryption"
