#!/bin/bash

# Test Deployment Script for Strands Migration
# This script runs comprehensive tests against the deployed Lambda function

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Testing Strands Migration Deployment${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Load deployment info
if [ ! -f "deployment-info.json" ]; then
    echo -e "${RED}❌ deployment-info.json not found. Please run './scripts/deploy.sh' first.${NC}"
    exit 1
fi

FUNCTION_URL=$(jq -r '.function_url' deployment-info.json)
FUNCTION_NAME=$(jq -r '.function_name' deployment-info.json)
ENVIRONMENT=$(jq -r '.environment' deployment-info.json)

if [ "$FUNCTION_URL" = "null" ] || [ -z "$FUNCTION_URL" ]; then
    echo -e "${RED}❌ Function URL not found in deployment info${NC}"
    exit 1
fi

echo -e "${BLUE}Testing Function: $FUNCTION_NAME${NC}"
echo -e "${BLUE}Function URL: $FUNCTION_URL${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local input_data="$2"
    local expected_pattern="$3"
    local timeout=${4:-30}
    
    echo -e "\n${YELLOW}🧪 Test: $test_name${NC}"
    
    # Make request
    local response=$(curl -s -X POST "$FUNCTION_URL" \
        -H "Content-Type: application/json" \
        -d "$input_data" \
        --max-time "$timeout" 2>/dev/null || echo "TIMEOUT_OR_ERROR")
    
    # Check response
    if [[ "$response" == *"$expected_pattern"* ]]; then
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        echo -e "${RED}Expected pattern: $expected_pattern${NC}"
        echo -e "${RED}Actual response: ${response:0:200}...${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Basic Health Check
run_test "Basic Health Check" \
    '{"inputText": "Hello", "sessionId": "test-health"}' \
    "Ahoy"

# Test 2: Deck Recommendation
run_test "Deck Recommendation" \
    '{"inputText": "Show me a Red Shanks deck for OP09", "sessionId": "test-deck"}' \
    "gumgum.gg" \
    45

# Test 3: Shopify Product Search
run_test "Shopify Product Search" \
    '{"inputText": "Show me booster packs", "sessionId": "test-shopify"}' \
    "treasure" \
    30

# Test 4: Cart Management
run_test "Cart Management" \
    '{"inputText": "What is in my cart?", "sessionId": "test-cart", "cartId": "test-cart-123"}' \
    "cart" \
    25

# Test 5: Error Handling
run_test "Error Handling" \
    '{"invalidJson": true}' \
    "Ahoy" \
    20

# Test 6: Session Management
run_test "Session Management" \
    '{"inputText": "Remember my name is Captain Test", "sessionId": "test-session-persist"}' \
    "Captain" \
    25

# Test 7: Streaming Response
echo -e "\n${YELLOW}🧪 Test: Streaming Response${NC}"
STREAM_TEST=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"inputText": "Tell me about One Piece cards", "sessionId": "test-stream"}' \
    --max-time 30 2>/dev/null | head -c 50)

if [ ${#STREAM_TEST} -gt 10 ]; then
    echo -e "${GREEN}✓ PASSED: Streaming Response${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED: Streaming Response${NC}"
    ((TESTS_FAILED++))
fi

# Performance Test
echo -e "\n${YELLOW}🧪 Test: Performance (Response Time)${NC}"
START_TIME=$(date +%s%N)
PERF_RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"inputText": "Quick test", "sessionId": "test-perf"}' \
    --max-time 10 2>/dev/null || echo "TIMEOUT")
END_TIME=$(date +%s%N)

RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 )) # Convert to milliseconds

if [ $RESPONSE_TIME -lt 5000 ] && [[ "$PERF_RESPONSE" == *"Ahoy"* ]]; then
    echo -e "${GREEN}✓ PASSED: Performance (${RESPONSE_TIME}ms)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED: Performance (${RESPONSE_TIME}ms or timeout)${NC}"
    ((TESTS_FAILED++))
fi

# Load Test (5 concurrent requests)
echo -e "\n${YELLOW}🧪 Test: Load Test (5 concurrent requests)${NC}"
LOAD_TEST_PIDS=()
LOAD_TEST_RESULTS=()

for i in {1..5}; do
    (
        RESULT=$(curl -s -X POST "$FUNCTION_URL" \
            -H "Content-Type: application/json" \
            -d "{\"inputText\": \"Load test $i\", \"sessionId\": \"load-test-$i\"}" \
            --max-time 15 2>/dev/null || echo "FAILED")
        echo "$RESULT" > "/tmp/load_test_$i.txt"
    ) &
    LOAD_TEST_PIDS+=($!)
done

# Wait for all requests to complete
for pid in "${LOAD_TEST_PIDS[@]}"; do
    wait $pid
done

# Check results
LOAD_SUCCESS=0
for i in {1..5}; do
    if [ -f "/tmp/load_test_$i.txt" ] && grep -q "Ahoy" "/tmp/load_test_$i.txt"; then
        ((LOAD_SUCCESS++))
    fi
    rm -f "/tmp/load_test_$i.txt"
done

if [ $LOAD_SUCCESS -ge 4 ]; then
    echo -e "${GREEN}✓ PASSED: Load Test ($LOAD_SUCCESS/5 successful)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED: Load Test ($LOAD_SUCCESS/5 successful)${NC}"
    ((TESTS_FAILED++))
fi

# CloudWatch Metrics Check
echo -e "\n${YELLOW}🧪 Test: CloudWatch Metrics${NC}"
RECENT_INVOCATIONS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
    --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 300 \
    --statistics Sum \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null || echo "None")

if [ "$RECENT_INVOCATIONS" != "None" ] && [ "$RECENT_INVOCATIONS" != "null" ]; then
    echo -e "${GREEN}✓ PASSED: CloudWatch Metrics (${RECENT_INVOCATIONS} recent invocations)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️ SKIPPED: CloudWatch Metrics (no recent data)${NC}"
fi

# Test Summary
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Deployment is healthy.${NC}"
    
    # Generate test report
    cat > test-report.json << EOF
{
  "test_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "function_name": "$FUNCTION_NAME",
  "function_url": "$FUNCTION_URL",
  "total_tests": $TOTAL_TESTS,
  "tests_passed": $TESTS_PASSED,
  "tests_failed": $TESTS_FAILED,
  "response_time_ms": $RESPONSE_TIME,
  "load_test_success_rate": "$(echo "scale=2; $LOAD_SUCCESS/5*100" | bc)%",
  "status": "HEALTHY"
}
EOF
    
    echo -e "\n${YELLOW}📝 Next steps:${NC}"
    echo -e "1. Update Shopify webhook to: ${BLUE}$FUNCTION_URL${NC}"
    echo -e "2. Monitor production traffic"
    echo -e "3. Set up CloudWatch alarms"
    echo -e "4. Schedule regular health checks"
    
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please check the deployment.${NC}"
    
    # Generate failure report
    cat > test-report.json << EOF
{
  "test_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "function_name": "$FUNCTION_NAME",
  "function_url": "$FUNCTION_URL",
  "total_tests": $TOTAL_TESTS,
  "tests_passed": $TESTS_PASSED,
  "tests_failed": $TESTS_FAILED,
  "status": "UNHEALTHY"
}
EOF
    
    echo -e "\n${YELLOW}🔍 Troubleshooting:${NC}"
    echo -e "1. Check logs: ${GREEN}aws logs tail /aws/lambda/$FUNCTION_NAME --follow${NC}"
    echo -e "2. Verify Parameter Store: ${GREEN}aws ssm get-parameters-by-path --path '/tcg-agent/$ENVIRONMENT' --recursive${NC}"
    echo -e "3. Test individual components"
    echo -e "4. Check CloudWatch metrics"
    
    exit 1
fi
