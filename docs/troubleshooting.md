# 🔧 Troubleshooting Guide

Common issues and solutions for the RockAuto API Client.

## 🔐 Authentication Issues

### CAPTCHA Required Error
```
Exception: Login failed: CAPTCHA required: RockAuto is requiring a security code for login
```

**Cause**: RockAuto's anti-automation system has been triggered.

**Solutions**:
1. **Wait**: Try again in 5-10 minutes
2. **Different IP**: Use different network/VPN if available
3. **Manual Login**: Log in through browser first to "warm up" the session
4. **Reduce Frequency**: Space out login attempts during testing

**Prevention**: Use environment variables for credentials and avoid repeated automated logins.

### Login Returns False
```python
login_success = await client.login(email, password)
# login_success is False but no exception
```

**Possible Causes**:
- Incorrect credentials
- Account locked/suspended
- Network connectivity issues
- RockAuto service issues

**Debug Steps**:
```python
# Check authentication status for details
status = client.get_authentication_status()
print(f"Auth status: {status}")

# Enable detailed error checking
try:
    result = await client.login(email, password)
    print(f"Login result: {result}")
except Exception as e:
    print(f"Login error details: {e}")
```

## 🧪 Testing Issues

### ModuleNotFoundError
```
ModuleNotFoundError: No module named 'rockauto_api'
```

**Solution**: Always use `PYTHONPATH=src` when running tests:
```bash
PYTHONPATH=src python tests/test_unauthenticated_features.py
```

### Model Attribute Errors
```
AttributeError: 'PartSearchOption' object has no attribute 'display_name'
```

**Solution**: Use correct attribute names:
```python
# ❌ Wrong
manufacturer.display_name

# ✅ Correct
manufacturer.text
```

**Common Model Attributes**:
- `PartSearchOption`: Use `.text` not `.display_name`
- `Engine`: Use `.description` not `.name`
- `VehicleYears`: Requires `make` field in constructor

### Missing Method Errors
```
AttributeError: 'RockAutoClient' object has no attribute 'get_order_status'
```

**Solution**: Use correct method names:
```python
# ❌ Wrong
await client.get_order_status(email, order_number)

# ✅ Correct
await client.lookup_order_status(email, order_number)
```

## 🌐 Network Issues

### Connection Timeouts
```
httpx.TimeoutException: The operation timed out
```

**Solutions**:
1. **Check Internet**: Verify connectivity to rockauto.com
2. **Increase Timeout**: Extend client timeout if needed
3. **Retry Logic**: Implement retry with exponential backoff
4. **Network Issues**: Check for firewall/proxy blocking

### HTTP 403 Forbidden
```
httpx.HTTPStatusError: Client error '403 Forbidden'
```

**Cause**: RockAuto is blocking the request (bot detection).

**Solutions**:
1. **Check Headers**: Ensure all browser headers are properly set
2. **Session Cookies**: Verify cookies are being maintained
3. **Rate Limiting**: Add delays between requests
4. **User Agent**: Try different/updated browser user agents

## 🔄 Session Management

### Session Expires During Operation
```
Exception: Authentication required for accessing saved addresses
```

**Cause**: Session cookie expired during long-running operations.

**Solutions**:
```python
# Check authentication before each operation
async def safe_operation(client):
    if not client.is_authenticated:
        print("Session expired, need to re-login")
        return False

    # Proceed with operation
    return await client.get_saved_addresses()

# Or implement auto-retry with re-login
async def auto_retry_operation(client, operation):
    try:
        return await operation()
    except Exception as e:
        if "authentication required" in str(e).lower():
            # Try to re-login and retry once
            await client.login(email, password)
            return await operation()
        raise e
```

## 📊 Data Issues

### Empty Results
```python
makes = await client.get_makes()
print(makes.count)  # Returns 0
```

**Debug Steps**:
1. **Check Response**: Verify RockAuto is returning data
2. **Network Issues**: Test with browser to confirm site is working
3. **Parsing Problems**: Check if HTML structure changed
4. **Rate Limiting**: May be getting blocked responses

### Parsing Errors
```
Exception: Failed to parse vehicle engines
```

**Causes**:
- RockAuto changed their HTML structure
- Unexpected data format
- Missing expected elements

**Debug Approach**:
```python
# Enable debug logging to see raw responses
import logging
logging.basicConfig(level=logging.DEBUG)

# Check the raw response
response = await client.session.get("https://www.rockauto.com/en/partsearch/")
print(response.text[:500])  # First 500 chars
```

## ⚡ Performance Issues

### Slow Response Times
```python
# Operations taking > 5 seconds
```

**Optimizations**:
1. **Use Concurrency**: Batch operations with `asyncio.gather()`
2. **Cache Results**: Store frequently accessed data
3. **Reduce Requests**: Combine operations where possible
4. **Check Network**: Verify connection speed

**Example Concurrent Operations**:
```python
# Instead of sequential
makes = await client.get_makes()
manufacturers = await client.get_manufacturers()

# Use parallel
makes, manufacturers = await asyncio.gather(
    client.get_makes(),
    client.get_manufacturers()
)
```

## 🛠️ Development Issues

### Import Errors in Tests
```
ImportError: attempted relative import with no known parent package
```

**Solution**: Always run tests from project root with proper PYTHONPATH:
```bash
cd /path/to/rockauto-project
PYTHONPATH=src python tests/test_file.py
```

### Async Context Issues
```
RuntimeError: Cannot call async function from sync context
```

**Solution**: Always use `asyncio.run()` or proper async context:
```python
# ❌ Wrong
client = RockAutoClient()
makes = await client.get_makes()  # Error!

# ✅ Correct
async def main():
    async with RockAutoClient() as client:
        makes = await client.get_makes()

asyncio.run(main())
```

## 🔍 Debugging Tools

### Enable Detailed Logging
```python
import logging
import httpx

# Enable HTTP request logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("httpx")
logger.setLevel(logging.DEBUG)
```

### Inspect Session State
```python
# Check authentication status
status = client.get_authentication_status()
print(f"Authenticated: {status['is_authenticated']}")
print(f"User: {status['user_email']}")
print(f"Cookies: {len(client.cookies)} cookies")

# Check session cookies
for name, value in client.cookies.items():
    print(f"Cookie: {name} = {value[:20]}...")
```

### Test Individual Components
```python
# Test just the base HTTP functionality
async def test_basic_connection():
    async with RockAutoClient() as client:
        response = await client.session.get("https://www.rockauto.com/")
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
```

## 📞 Getting Help

### Before Reporting Issues

1. **Check This Guide**: Review all relevant sections above
2. **Test with Browser**: Verify RockAuto site works normally
3. **Run Diagnostic Tests**: Use the test commands in CLAUDE.md
4. **Collect Debug Info**: Save error messages, logs, and code snippets

### Useful Debug Information

When reporting issues, include:
- Python version and OS
- Complete error message and stack trace
- Code snippet that reproduces the issue
- Test credentials status (working/not working)
- Network environment (proxy, firewall, etc.)

### Test Commands for Diagnosis

```bash
# Basic connectivity
PYTHONPATH=src python -c "
import asyncio
from rockauto_api import RockAutoClient

async def test():
    async with RockAutoClient() as client:
        makes = await client.get_makes()
        print(f'Success: {makes.count} makes')

asyncio.run(test())
"

# Authentication test
PYTHONPATH=src python tests/test_authenticated_debug.py

# Full feature test
PYTHONPATH=src python tests/test_unauthenticated_features.py
```

---

**🔧 Most issues are authentication or network-related. Start with the simple tests above!**