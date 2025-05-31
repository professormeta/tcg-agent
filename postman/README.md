# TCG Agent Postman Testing Guide

Complete Postman collection for testing your One Piece TCG Strands Agent v2.0 API.

## 🚀 Quick Setup

### 1. Import Collection and Environment

1. **Open Postman**
2. **Import Collection**: 
   - Click "Import" → Select `TCG_Agent_API_Collection.json`
3. **Import Environment**: 
   - Click "Import" → Select `TCG_Agent_Environment.json`
4. **Select Environment**: 
   - Choose "TCG Agent Environment" from the environment dropdown

### 2. Verify API Endpoint

Your API endpoint is pre-configured as:
```
https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production
```

If your endpoint is different, update the `base_url` variable in the environment.

## 📋 Test Collection Overview

### **9 Test Requests Included:**

1. **Health Check** (GET) - Verify service status
2. **Basic Agent Query** (POST) - Test general functionality
3. **Deck Recommendation Query** (POST) - Test GumGum integration
4. **Shopify Product Search** (POST) - Test Shopify MCP integration
5. **Session Persistence Test** (POST) - Test conversation memory
6. **Error Test - Invalid JSON** (POST) - Test error handling
7. **Error Test - Missing Field** (POST) - Test validation
8. **Performance Test - Large Query** (POST) - Test performance

## 🧪 Running Tests

### **Individual Tests**

#### **1. Start with Health Check**
- **Request**: `Health Check`
- **Expected**: Status 200, service info
- **Purpose**: Verify the agent is running

#### **2. Basic Functionality**
- **Request**: `Basic Agent Query`
- **Expected**: Status 200, agent response
- **Purpose**: Test basic agent capabilities

#### **3. Deck Recommendations**
- **Request**: `Deck Recommendation Query`
- **Expected**: Status 200, deck information
- **Purpose**: Test GumGum.gg integration

#### **4. Shopify Integration**
- **Request**: `Shopify Product Search`
- **Expected**: Status 200, product information
- **Purpose**: Test Shopify MCP functionality

### **Automated Test Suite**

#### **Run Collection**
1. Click the collection name "TCG Agent API Collection"
2. Click "Run collection"
3. Select all requests or specific ones
4. Click "Run TCG Agent API Collection"

#### **Test Results**
- ✅ **Green**: Test passed
- ❌ **Red**: Test failed
- ⚠️ **Yellow**: Test skipped or warning

## 📊 Expected Responses

### **Health Check Response**
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
  }
}
```

### **Agent Query Response**
```json
{
  "response": "Hello! I'm your One Piece TCG assistant...",
  "sessionId": "postman-basic-1234567890",
  "capabilities": {
    "deck_recommendations": true,
    "shopify_integration": true
  }
}
```

### **Error Response**
```json
{
  "error": "Missing required field 'inputText'",
  "error_type": "request_validation_error",
  "troubleshooting": {
    "required_fields": ["inputText"],
    "example_request": {
      "inputText": "Show me cards",
      "sessionId": "optional-session-id"
    }
  }
}
```

## 🔧 Customizing Tests

### **Environment Variables**

You can modify these in the "TCG Agent Environment":

- `base_url`: Your API Gateway endpoint
- `session_id`: Session identifier for basic tests
- `deck_session_id`: Session for deck recommendation tests
- `shopify_session_id`: Session for Shopify tests
- `cart_id`: Cart identifier for e-commerce tests

### **Dynamic Variables**

The collection uses dynamic variables:
- `{{$timestamp}}`: Current timestamp
- `{{$randomUUID}}`: Random UUID
- `Date.now()`: JavaScript timestamp

### **Custom Test Queries**

#### **Deck Recommendation Examples:**
```json
{
  "inputText": "Show me a Blue Nami deck for OP09",
  "sessionId": "{{deck_session_id}}"
}
```

```json
{
  "inputText": "I need a tournament-winning Red Luffy deck",
  "sessionId": "{{deck_session_id}}"
}
```

#### **Shopify Product Examples:**
```json
{
  "inputText": "Show me One Piece booster packs",
  "sessionId": "{{shopify_session_id}}",
  "cartId": "{{cart_id}}"
}
```

```json
{
  "inputText": "Add OP10 booster box to my cart",
  "sessionId": "{{shopify_session_id}}",
  "cartId": "{{cart_id}}"
}
```

## 📈 Test Validation

### **Automatic Validations**

Each request includes automatic tests for:

- **Status Codes**: 200 for success, 400 for errors
- **Response Format**: Required fields present
- **Data Types**: Correct field types
- **Response Time**: Performance thresholds
- **Content Validation**: Expected keywords in responses

### **Manual Validation**

Check these manually:

1. **Response Quality**: Is the agent response helpful?
2. **Deck Accuracy**: Are deck recommendations valid?
3. **Product Relevance**: Are Shopify results appropriate?
4. **Session Continuity**: Does the agent remember context?

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Connection Errors**
```
Error: getaddrinfo ENOTFOUND
```
**Solution**: Check `base_url` in environment variables

#### **2. 403 Forbidden**
```
{"message": "Forbidden"}
```
**Solution**: Verify API Gateway permissions and deployment

#### **3. 500 Internal Server Error**
```
{"errorMessage": "Configuration error"}
```
**Solution**: Check Lambda function logs in CloudWatch

#### **4. Timeout Errors**
```
Error: Request timeout
```
**Solution**: Increase timeout in Postman settings or check Lambda performance

### **Debug Steps**

1. **Check Health Endpoint**: Start with health check
2. **Verify Environment**: Ensure correct environment selected
3. **Check Variables**: Verify all variables are set correctly
4. **Review Logs**: Check CloudWatch logs for detailed errors
5. **Test Incrementally**: Start with simple requests

### **Response Time Guidelines**

- **Health Check**: < 5 seconds
- **Basic Query**: < 30 seconds
- **Deck Query**: < 45 seconds (includes GumGum API call)
- **Shopify Query**: < 30 seconds
- **Error Responses**: < 5 seconds

## 🔄 Testing Workflows

### **Development Testing**
1. Health Check
2. Basic Agent Query
3. Error Tests
4. Performance Test

### **Feature Testing**
1. Health Check
2. Deck Recommendation Query
3. Shopify Product Search
4. Session Persistence Test

### **Integration Testing**
1. Run entire collection
2. Verify all integrations work
3. Check error handling
4. Validate performance

### **Pre-deployment Testing**
1. Health Check (verify deployment)
2. All functional tests
3. Error scenarios
4. Performance validation

## 📝 Test Documentation

### **Adding New Tests**

1. **Duplicate existing request**
2. **Modify request body/URL**
3. **Update test scripts**
4. **Add documentation**

### **Test Script Examples**

#### **Basic Status Check**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});
```

#### **Response Content Validation**
```javascript
pm.test("Response contains deck info", function () {
    const jsonData = pm.response.json();
    const response = jsonData.response.toLowerCase();
    pm.expect(response).to.include("deck");
});
```

#### **Performance Testing**
```javascript
pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(30000);
});
```

## 🚀 Advanced Usage

### **Collection Runner**

Use Postman's Collection Runner for:
- **Automated testing**
- **Performance monitoring**
- **Regression testing**
- **CI/CD integration**

### **Newman CLI**

Run tests from command line:
```bash
# Install Newman
npm install -g newman

# Run collection
newman run TCG_Agent_API_Collection.json -e TCG_Agent_Environment.json

# Generate reports
newman run TCG_Agent_API_Collection.json -e TCG_Agent_Environment.json --reporters html
```

### **Monitoring**

Set up Postman monitoring for:
- **Uptime monitoring**
- **Performance tracking**
- **Alert notifications**
- **Scheduled testing**

---

**Last Updated**: May 31, 2025  
**Collection Version**: 1.0.0  
**Compatible with**: TCG Agent v2.0  
**API Endpoint**: https://mxrm5uczs2.execute-api.us-east-1.amazonaws.com/production
