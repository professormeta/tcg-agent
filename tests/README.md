# TCG Agent Test Suite

Comprehensive test suite for the One Piece TCG Strands Agent v2.0, covering all major components and integrations.

## 📋 Test Categories

### 1. **GumGum Integration Tests** (`test_gumgum_integration.py`)
- **API Connectivity**: Test connection to GumGum.gg API
- **Authentication**: Verify API key and endpoint configuration
- **Query Parsing**: Test Bedrock-powered natural language processing
- **Data Retrieval**: Validate deck data format and completeness
- **Error Handling**: Test API failures and recovery

### 2. **Shopify MCP Tests** (`test_shopify_mcp.py`)
- **MCP Connection**: Test Shopify MCP server connectivity
- **Tool Discovery**: Verify all MCP tools are available
- **Product Search**: Test catalog search functionality
- **Cart Management**: Test cart operations
- **Error Recovery**: Test MCP server failures

### 3. **Langfuse Integration Tests** (`test_langfuse_integration.py`)
- **Connection**: Test Langfuse client initialization
- **Observability**: Verify request/response tracking
- **Metrics**: Test performance metric collection
- **Error Tracking**: Validate error logging
- **Lambda Integration**: Test observability in Lambda context

### 4. **Shopify Remix Integration Tests** (`test_shopify_remix_integration.py`)
- **API Gateway**: Test REST API endpoint connectivity
- **Request Format**: Validate Shopify Remix request structure
- **Response Format**: Verify agent response compatibility
- **Session Management**: Test session persistence
- **Cart Integration**: Test cart ID handling

## 🚀 Quick Start

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Ensure AWS credentials are configured (for integration tests)
aws configure
```

### Running Tests

#### **Basic Usage**
```bash
# Run all unit tests (no external dependencies)
python tests/run_tests.py

# Run specific test category
python tests/run_tests.py --type gumgum
python tests/run_tests.py --type shopify
python tests/run_tests.py --type langfuse
python tests/run_tests.py --type remix

# Run with verbose output
python tests/run_tests.py --verbose
```

#### **Integration Tests** (requires real credentials)
```bash
# Run all tests including integration tests
python tests/run_tests.py --integration

# Run only integration tests
python tests/run_tests.py --type integration

# Run integration tests for specific component
python tests/run_tests.py --type gumgum --integration
```

#### **Direct pytest Usage**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_gumgum_integration.py -v

# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run with coverage
pytest tests/ --cov=agent --cov-report=html
```

## ⚙️ Configuration

### Test Markers

- `@pytest.mark.unit` - Unit tests (use mocks, no external dependencies)
- `@pytest.mark.integration` - Integration tests (require real API access)
- `@pytest.mark.slow` - Slow running tests

### Environment Variables

Tests automatically retrieve configuration from:

1. **AWS SSM Parameters** (preferred for integration tests)
2. **Environment Variables** (fallback)
3. **Mock Values** (for unit tests)

#### Required for Integration Tests:
```bash
# GumGum API
export GUMGUM_ENDPOINT="https://gumgum.gg/api/decklists"
export GUMGUM_SECRET="your-api-key"

# Shopify
export SHOPIFY_STORE_URL="https://your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="your-access-token"

# Langfuse
export LANGFUSE_PUBLIC_KEY="pk_your-public-key"
export LANGFUSE_SECRET_KEY="sk_your-secret-key"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

## 📊 Test Output

### Success Example
```
Running TCG Agent tests...
Test type: all
Integration tests: disabled
--------------------------------------------------

tests/test_gumgum_integration.py::TestGumGumIntegration::test_deck_query_parsing_with_mock PASSED
tests/test_shopify_mcp.py::TestShopifyMCP::test_mcp_tool_discovery_mock PASSED
tests/test_langfuse_integration.py::TestLangfuseIntegration::test_langfuse_initialization_with_mock PASSED
tests/test_shopify_remix_integration.py::TestShopifyRemixIntegration::test_shopify_remix_response_format_validation PASSED

✅ 4 passed in 2.34s
```

### Integration Test Example
```bash
python tests/run_tests.py --type gumgum --integration --verbose
```

```
tests/test_gumgum_integration.py::TestGumGumIntegration::test_gumgum_api_connectivity 
✅ GumGum API connectivity test passed - Status: 200
PASSED

tests/test_gumgum_integration.py::TestGumGumIntegration::test_end_to_end_deck_recommendation 
✅ End-to-end deck recommendation test passed
PASSED
```

## 🔧 Test Development

### Adding New Tests

1. **Create test file** following naming convention: `test_<component>_<type>.py`
2. **Use appropriate markers**: `@pytest.mark.unit` or `@pytest.mark.integration`
3. **Add fixtures** to `conftest.py` for shared test data
4. **Update this README** with new test descriptions

### Test Structure Template

```python
import pytest
from unittest.mock import patch, Mock

class TestNewComponent:
    """Test new component functionality"""
    
    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test basic functionality with mocks"""
        # Unit test implementation
        pass
    
    @pytest.mark.integration
    def test_real_integration(self, test_parameters):
        """Test with real external services"""
        # Skip if using mock credentials
        if test_parameters.get("param").startswith("mock_"):
            pytest.skip("Using mock credentials")
        
        # Integration test implementation
        pass
```

### Mocking Guidelines

- **Unit tests**: Always use mocks for external dependencies
- **Integration tests**: Use real services when credentials available
- **Graceful degradation**: Skip tests when credentials unavailable
- **Error simulation**: Test error conditions with mocked failures

## 📈 CI/CD Integration

### GitHub Actions Example

```yaml
name: Test TCG Agent
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      
      - name: Run unit tests
        run: python tests/run_tests.py --type unit --output test-results.xml
      
      - name: Run integration tests
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: python tests/run_tests.py --type integration
        continue-on-error: true
```

### Pre-deployment Testing

```bash
# Add to deployment script
echo "Running pre-deployment tests..."
python tests/run_tests.py --type unit
if [ $? -ne 0 ]; then
    echo "Unit tests failed - aborting deployment"
    exit 1
fi

echo "Running integration tests..."
python tests/run_tests.py --type integration
# Continue deployment regardless of integration test results
```

## 🐛 Troubleshooting

### Common Issues

#### 1. **Import Errors**
```bash
# Ensure parent directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python tests/run_tests.py
```

#### 2. **AWS Credentials**
```bash
# Check AWS configuration
aws sts get-caller-identity

# Test SSM parameter access
aws ssm get-parameter --name "/tcg-agent/production/shopify/store-url"
```

#### 3. **Missing Dependencies**
```bash
# Check test dependencies
python tests/run_tests.py --check-deps

# Install missing dependencies
pip install -r tests/requirements.txt
```

#### 4. **Integration Test Failures**
- Verify API credentials are valid
- Check network connectivity
- Review service-specific troubleshooting in main README

### Debug Mode

```bash
# Run with maximum verbosity
pytest tests/ -vvv -s --tb=long

# Run single test with debugging
pytest tests/test_gumgum_integration.py::TestGumGumIntegration::test_gumgum_api_connectivity -vvv -s
```

## 📝 Test Coverage

Generate coverage reports:

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest tests/ --cov=agent --cov=tools --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## 🔄 Maintenance

### Regular Tasks

- **Weekly**: Run full integration test suite
- **Monthly**: Update test dependencies
- **Quarterly**: Review and update test scenarios
- **Release**: Run comprehensive test suite before deployment

### Test Data Updates

- Update sample queries for new card sets
- Refresh API response examples
- Validate error scenarios still trigger correctly
- Update expected response formats for API changes

---

**Last Updated**: May 31, 2025  
**Test Suite Version**: 1.0.0  
**Compatible with**: TCG Agent v2.0
