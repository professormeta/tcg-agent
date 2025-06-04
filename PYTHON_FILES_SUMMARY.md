# 🐍 Python Files Structure - Clean Production Setup

## ✅ **ESSENTIAL PYTHON FILES (Root Directory)**

### **Production Files:**
- **`agent.py`** - **MASTER COPY** - Complete TCG Agent implementation (40,491 bytes)
- **`aws_config.py`** - AWS region configuration (756 bytes)
- **`websocket_handler.py`** - Enhanced WebSocket handler using agent.py directly (10,915 bytes)
- **`tools/deck_recommender.py`** - Custom deck recommendation tool

### **Total: 4 Python files needed for production deployment**

## 🗂️ **TEST/DEBUG FILES (Moved to tests/ folder)**

### **Successfully Moved:**
- `check_env.py` - Environment checking utility
- `debug_agent.py` - Agent debugging utility
- `test_bedrock_access.py` - Bedrock API access tests
- `test_bedrock_converse.py` - Bedrock conversation tests
- `test_bedrock_models.py` - Bedrock model tests
- `test_deck_recommender_debug.py` - Deck recommender debugging
- `test_gumgum_api.py` - GumGum API tests
- `test_langfuse.py` - Langfuse integration tests
- `test_ssm.py` - AWS SSM parameter tests
- `test_strands_agent.py` - Strands agent tests
- `test_websocket_simple.js`

### **Already in tests/ folder:**
- `test_gumgum_integration.py` - GumGum integration tests
- `test_langfuse_integration.py` - Langfuse integration tests
- `test_shopify_mcp.py` - Shopify MCP tests
- `test_shopify_remix_integration.py` - Shopify Remix tests
- `test_strands_langfuse_integration.py` - Strands + Langfuse tests
- `conftest.py` - Pytest configuration
- `run_tests.py` - Test runner
- `__init__.py` - Python package marker

## 🚀 **Clean Root Directory Structure**

```
tcg-agent/
├── agent.py                    ← MASTER COPY
├── aws_config.py              ← AWS configuration
├── websocket_handler.py       ← WebSocket handler
├── template-production.yml    ← Production deployment
├── requirements.txt           ← Dependencies
├── Dockerfile                 ← Container config
├── samconfig.toml            ← SAM config
├── tools/
│   └── deck_recommender.py   ← Custom tool
└── tests/                    ← All test/debug files
    ├── check_env.py
    ├── debug_agent.py
    ├── test_*.py (18 files)
    └── ...
```

## 🎯 **Benefits Achieved**

### **1. Clean Production Deployment:**
- Only 4 essential Python files in root
- No test/debug clutter
- Clear separation of concerns

### **2. Organized Development:**
- All tests consolidated in tests/ folder
- Easy to run test suites
- Development utilities accessible but separate

### **3. Simplified Maintenance:**
- `agent.py` is the single source of truth
- WebSocket handler imports directly from agent.py
- No wrapper layers or abstractions

## 🔧 **Deployment Impact**

### **SAM Build Process:**
```bash
sam build --template-file template-production.yml
```

**Will only package:**
- `agent.py` (master implementation)
- `aws_config.py` (configuration)
- `websocket_handler.py` (WebSocket handler)
- `tools/deck_recommender.py` (custom tool)
- `requirements.txt` (dependencies)

**Will ignore:**
- All files in `tests/` folder (not needed for production)
- Test and debug utilities

## 🧪 **Testing Structure**

### **Run All Tests:**
```bash
cd tests/
python run_tests.py
```

### **Run Specific Tests:**
```bash
python -m pytest tests/test_strands_agent.py
python -m pytest tests/test_gumgum_api.py
```

### **Debug Utilities:**
```bash
python tests/debug_agent.py
python tests/check_env.py
```

## 📊 **File Count Summary**

- **Production files**: 4 Python files
- **Test files**: 18 Python files (in tests/)
- **Total**: 22 Python files (organized)

**Result: Clean, production-ready codebase with organized testing structure!**
