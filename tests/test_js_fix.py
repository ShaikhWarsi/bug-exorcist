import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root and backend to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

from core.agent import BugExorcistAgent

async def test_javascript_bug_fix():
    """
    Test that the agent can handle a JavaScript bug fix workflow.
    """
    print("Running JavaScript bug fix test...")
    bug_id = "test-js-bug"
    js_code = """
function add(a, b) {
    return a + b;
}
console.log(add(5, "5")); // Intentional bug: should be numbers
    """
    error_message = "TypeError: add expects numbers but got string"
    
    # Mock AI response
    mock_ai_response = """
**Root Cause Analysis:**
The `add` function is performing string concatenation instead of numeric addition because one of the arguments is a string.

**Fixed Code:**
```javascript
function add(a, b) {
    return Number(a) + Number(b);
}
console.log(add(5, 5));
```

**Explanation:**
I updated the function to explicitly cast inputs to numbers and fixed the call site to use numeric literals.
    """
    
    # Configure mock provider
    mock_provider = MagicMock()
    mock_provider.ainvoke = AsyncMock()
    
    mock_response = MagicMock()
    mock_response.content = mock_ai_response
    mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 20}
    mock_provider.ainvoke.return_value = mock_response
    # Mock model_name for reporting
    mock_provider.model_name = "gpt-4o-mock"
    
    # Patch _init_provider to return our mock
    with patch.object(BugExorcistAgent, '_init_provider', return_value=mock_provider):
        # Mock Sandbox
        with patch('app.sandbox.Sandbox') as mock_sandbox_class:
            mock_sandbox = MagicMock()
            mock_sandbox_class.return_value = mock_sandbox
            mock_sandbox.run_code.return_value = "10" # Successful output
            
            agent = BugExorcistAgent(bug_id=bug_id)
            # Ensure primary provider is set
            agent.primary_provider = mock_provider
            
            # Execute workflow
            result = await agent.analyze_and_fix_with_retry(
                error_message=error_message,
                code_snippet=js_code,
                language="javascript"
            )
            
            # Verifications
            print("Verifying results...")
            assert result['success'] is True
            assert "Number(a)" in result['final_fix']['fixed_code']
            print("Fix content check: PASS")
            
            # Verify sandbox was called with javascript language
            mock_sandbox.run_code.assert_called_with(
                result['final_fix']['fixed_code'],
                language="javascript"
            )
            print("Sandbox language parameter check: PASS")
            
            # Verify AI was called with JS context
            args, kwargs = mock_provider.ainvoke.call_args
            prompt = args[0][1].content
            assert "**Language:** javascript" in prompt
            assert "```javascript" in prompt
            print("AI prompt context check: PASS")
            
    print("\nALL JS FIX TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_javascript_bug_fix())
