# 🚀 TCG Agent Production Deployment Guide

## 📁 Essential Files for Deployment

### **Core Application Files:**
- `agent.py` - **MASTER COPY** - Complete TCG Agent implementation
- `websocket_handler.py` - Enhanced WebSocket handler (uses agent.py directly)
- `template-production.yml` - **PRODUCTION TEMPLATE** - Clean deployment configuration
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `tools/deck_recommender.py` - Custom deck recommendation tool

### **Configuration Files:**
- `samconfig.toml` - SAM deployment settings
- `aws_config.py` - AWS region configuration

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   REST Handler  │    │ WebSocket Handler│
│   (HTTP API)    │    │   (Real-time)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────────┐
          │     agent.py        │
          │   (MASTER COPY)     │
          │                     │
          │ • Strands Agent     │
          │ • Langfuse Logging  │
          │ • Deck Recommender  │
          │ • Shopify MCP       │
          │ • All Business Logic│
          └─────────────────────┘
```

## 🚀 Deployment Commands

### **1. Build the Application:**
```bash
sam build --template-file template-production.yml
```

### **2. Deploy to Production:**
```bash
sam deploy --template-file .aws-sam/build/template.yaml \
  --stack-name tcg-agent-production \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Environment=production \
  --region us-east-1 \
  --resolve-s3 \
  --confirm-changeset
```

### **3. Get WebSocket URL:**
After deployment, the WebSocket URL will be in the CloudFormation outputs.

## 📊 CloudWatch Log Groups

### **WebSocket Functions:**
```
/aws/lambda/tcg-agent-production-ws-connect
/aws/lambda/tcg-agent-production-ws-disconnect  
/aws/lambda/tcg-agent-production-ws-message
```

### **What to Monitor:**
- Connection establishment/teardown
- **Agent processing logs** (should show real TCG responses)
- Tool usage and API calls
- Error messages and stack traces

## 🧪 Testing the Deployment

### **1. WebSocket Connection Test:**
```json
{
  "action": "message",
  "message": "Can you recommend a competitive One Piece TCG deck?",
  "sessionId": "test-123"
}
```

### **2. Expected Response:**
```json
{
  "type": "agent_response",
  "response": "Based on the current meta, I recommend...",
  "capabilities": {
    "deck_recommendations": true,
    "shopify_integration": true
  }
}
```

## 🗂️ File Cleanup Status

### **✅ Keep These Files:**
- `agent.py` - Master agent implementation
- `websocket_handler.py` - Consolidated WebSocket handler
- `template-production.yml` - Clean production template
- Core dependencies and config files

### **🗑️ Can Remove These Files:**
- `agent_core.py` - No longer needed (functionality moved to agent.py)
- `websocket_handler_simple.py` - Basic echo handler (not needed)
- `websocket_handler_old.py` - Old version backup
- `template-websocket-only.yml` - Superseded by production template
- `template-websocket-enhanced.yml` - Had AWS region issues
- `template-websocket-fixed.yml` - Superseded by production template

## 🔧 Key Improvements Made

### **1. Consolidated Architecture:**
- **Single source of truth**: `agent.py` is the master copy
- **Direct integration**: WebSocket handler imports from `agent.py` directly
- **No wrapper layers**: Eliminated `agent_core.py` abstraction

### **2. Clean Deployment:**
- **One production template**: `template-production.yml`
- **Clear naming**: Functions named with production stack
- **Proper permissions**: All required AWS service access

### **3. Simplified Maintenance:**
- **Update once**: Changes to `agent.py` affect both REST and WebSocket
- **Consistent behavior**: Same agent logic across all interfaces
- **Easy debugging**: Single codebase to troubleshoot

## 🎯 Expected Functionality

### **WebSocket Capabilities:**
- **Real TCG Agent responses** (not echo)
- **Deck recommendations** from gumgum.gg
- **Shopify store integration** for product searches
- **Session management** and continuity
- **Multiple action types**: message, ping, status

### **Message Flow:**
1. **WebSocket receives message**
2. **websocket_handler.py processes request**
3. **Imports and calls agent.py directly**
4. **agent.py provides full TCG Agent response**
5. **Response sent back via WebSocket**

## 🔍 Troubleshooting

### **Common Issues:**
1. **Import errors**: Check that all dependencies are in requirements.txt
2. **Permission errors**: Verify IAM roles have SSM and Bedrock access
3. **Connection issues**: Check API Gateway deployment status
4. **Agent errors**: Monitor CloudWatch logs for detailed error messages

### **Log Analysis:**
Look for these patterns in `/aws/lambda/tcg-agent-production-ws-message`:
```
INFO | Received message from [connectionId]: {"action": "message", ...}
INFO | Agent response generated successfully
INFO | Response sent to [connectionId]
```

This deployment uses **agent.py as the single source of truth** for all TCG Agent functionality!
