import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Add the project root and backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from core.agent import BugExorcistAgent
from core.ollama_provider import OllamaProvider

async def test_ollama_retry_logic():
    """
    Test that the self-healing loop works correctly when using Ollama as the primary provider.
    """
    print("\n--- Testing Ollama Self-Healing Loop ---")
    
    # Mock environment variables
    with patch.dict(os.environ, {
        "PRIMARY_AGENT": "ollama",
        "OLLAMA_MODEL": "llama3",
        "OLLAMA_BASE_URL": "http://localhost:11434"
    }):
        # Mock Sandbox class to avoid Docker initialization errors
        # Note: mocking 'app.sandbox.Sandbox' because that's how it's imported in agent.py
        with patch('app.sandbox.Sandbox') as MockSandbox:
            mock_sandbox_instance = MockSandbox.return_value
            mock_sandbox_instance.run_code = MagicMock()
            mock_sandbox_instance.run_code.side_effect = [
                "Error: NameError: name 'fail' is not defined", # Verification 1
                "success\n" # Verification 2
            ]

            # Mock OllamaProvider.analyze_error to simulate a failure then a success
            with patch('core.ollama_provider.OllamaProvider.analyze_error') as mock_analyze:
                # First attempt: returns a fix that will "fail" verification
                # Second attempt: returns a fix that will "pass" verification
                mock_analyze.side_effect = [
                    {
                        "ai_agent": "ollama/llama3",
                        "root_cause": "Attempt 1 root cause",
                        "fixed_code": "print('fail')",
                        "explanation": "Attempt 1 explanation",
                        "confidence": 0.5,
                        "timestamp": "2026-02-03T20:00:00"
                    },
                    {
                        "ai_agent": "ollama/llama3",
                        "root_cause": "Attempt 2 root cause",
                        "fixed_code": "print('success')",
                        "explanation": "Attempt 2 explanation",
                        "confidence": 0.9,
                        "timestamp": "2026-02-03T20:05:00"
                    }
                ]
                
                # Initialize agent
                agent = BugExorcistAgent(bug_id="test-ollama-retry")
                # Ensure the agent uses our mocked sandbox instance
                agent.sandbox = mock_sandbox_instance
                
                print(f"Primary Agent: {agent.primary_agent_type}")
                
                # Run the self-healing loop
                result = await agent.analyze_and_fix_with_retry(
                    error_message="Original Error",
                    code_snippet="print('bug')",
                    max_attempts=3
                )
                
                # Assertions
                print(f"Success: {result['success']}")
                print(f"Total Attempts: {result['total_attempts']}")
                
                assert result['success'] is True
                assert result['total_attempts'] == 2
                assert "success" in result['final_fix']['fixed_code']
                
                print("✅ Self-healing loop with Ollama verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_ollama_retry_logic())
