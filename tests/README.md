# Version Support Assistant Test Suite

This directory contains comprehensive tests for the Version Support Assistant MCP tool.

## Test Structure

### Test Files

- **`test_models.py`** - Unit tests for Pydantic data models
- **`test_utils.py`** - Unit tests for utility functions (release notes extraction)
- **`test_mcp_tools.py`** - Unit tests for MCP tool functions with mocking
- **`test_integration.py`** - Integration tests with mocked and optional live connections
- **`conftest.py`** - Pytest configuration and shared fixtures

### Test Categories

#### Unit Tests (`@pytest.mark.unit`)
- Fast-running tests with full mocking
- Test individual components in isolation
- Cover all data model validation scenarios
- Test utility functions with various input formats
- Mock all external dependencies (HTTP, subprocess)

#### Integration Tests (`@pytest.mark.integration`)
- Test complete workflows end-to-end
- Use mocked external dependencies for consistency
- Include error handling scenarios
- Optional live connection tests (when credentials available)

#### Slow Tests (`@pytest.mark.slow`)
- Tests that may take longer to run
- Live API connection tests
- Comprehensive end-to-end scenarios

## Running Tests

### Quick Test Run
```bash
# Run all tests
python -m pytest tests/ -v

# Run only unit tests
python -m pytest tests/ -v -m unit

# Run only integration tests  
python -m pytest tests/ -v -m integration

# Run with coverage
python -m pytest tests/ --cov=mcp_tools --cov-report=html
```

### Using the Test Runner
```bash
python run_tests.py
```

### Test Configuration

The test suite uses `pytest.ini` for configuration:
- Async test support with `pytest-asyncio`
- Custom markers for test categorization
- Verbose output and short tracebacks
- Auto-discovery of test files

## Test Features

### Mocking Strategy
- **HTTP Clients**: Mock `httpx.AsyncClient` for Jira API testing
- **Subprocess**: Mock `subprocess.run` for Git operations
- **Environment Variables**: Mock environment variables for testing different configurations

### Fixtures
- `mock_env_vars`: Provides test environment variables
- `mock_env_vars_missing`: Tests missing credential scenarios
- `mock_httpx_client`: Reusable HTTP client mock
- `sample_jira_response`: Realistic Jira API response data
- `mock_subprocess`: Git operation mocking

### Test Coverage

#### Data Models
- ✅ All Pydantic model validation
- ✅ Default value handling
- ✅ Optional field behavior
- ✅ Error conditions and edge cases

#### Utility Functions
- ✅ Release notes extraction from structured descriptions
- ✅ Plain text description handling
- ✅ Edge cases (None, empty, malformed data)
- ✅ Multiple URL scenarios

#### MCP Tools
- ✅ `fetch_tickets`: Success, errors, custom parameters
- ✅ `add_comment`: Success, errors, credential handling
- ✅ `accept_ticket`: Success, errors, API failures
- ✅ `create_gerrit_pr`: Success, Git failures, Change-ID extraction

#### Integration Scenarios
- ✅ Complete ticket workflow (fetch → comment → accept)
- ✅ Ticket to Gerrit PR workflow
- ✅ Error handling and recovery
- ✅ Network timeout and authentication failures
- ✅ Malformed API responses

#### Live Testing (Optional)
- ✅ Live Jira connection tests (when credentials available)
- ✅ Graceful handling of missing credentials
- ✅ Real API error scenarios

## Environment Variables for Testing

For live integration tests, set these environment variables:
```bash
JIRA_URL=https://your-instance.atlassian.net
JIRA_USER=your-username
JIRA_TOKEN=your-api-token
```

Tests will automatically skip live tests if credentials are not available.

## Adding New Tests

### Unit Test Template
```python
@pytest.mark.unit
@pytest.mark.asyncio  # For async tests
@patch('external.dependency')
async def test_new_feature(self, mock_dependency, mock_env_vars):
    # Setup mocks
    mock_dependency.return_value = expected_result
    
    # Execute
    result = await function_under_test(input_data)
    
    # Verify
    assert result.success is True
    mock_dependency.assert_called_once()
```

### Integration Test Template
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_integration(self):
    # Test complete workflow with mocked dependencies
    pass
```

## Troubleshooting

### Common Issues

1. **Async Test Failures**: Ensure `@pytest.mark.asyncio` decorator is present
2. **Mock Not Working**: Check import paths and mock target locations
3. **Environment Variables**: Use fixtures for consistent test environments
4. **Live Tests Failing**: Verify credentials and network connectivity

### Debug Mode
```bash
# Run with detailed output
python -m pytest tests/ -v -s --tb=long

# Run specific test with debugging
python -m pytest tests/test_mcp_tools.py::TestFetchTickets::test_fetch_tickets_success -v -s
```