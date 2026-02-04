import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root and backend to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

from app.sandbox import Sandbox

class TestSandboxLanguages(unittest.TestCase):
    def setUp(self):
        with patch('docker.from_env') as mock_docker:
            self.mock_client = MagicMock()
            mock_docker.return_value = self.mock_client
            self.sandbox = Sandbox()

    def test_language_mappings(self):
        """Verify that all requested languages map to the correct shell commands."""
        test_cases = [
            ("python", "python3 -c \"import sys; exec(sys.stdin.read())\""),
            ("javascript", "node -e \"$(cat)\""),
            ("nodejs", "node -e \"$(cat)\""),
            ("go", "cat > main.go && go run main.go"),
            ("go-test", "go test ./..."),
            ("rust", "cat > main.rs && rustc main.rs -o main && ./main"),
            ("cargo-test", "cargo test"),
            ("npm-test", "npm test"),
        ]

        for lang, expected_cmd in test_cases:
            with self.subTest(lang=lang):
                self.sandbox.run_code("test_code", language=lang)
                args, kwargs = self.mock_client.containers.run.call_args
                self.assertEqual(kwargs['command'], expected_cmd, f"Failed mapping for {lang}")

    def test_default_fallback(self):
        """Verify fallback to python for unknown languages."""
        self.sandbox.run_code("test_code", language="unknown-lang")
        args, kwargs = self.mock_client.containers.run.call_args
        self.assertEqual(kwargs['command'], "python3 -c \"import sys; exec(sys.stdin.read())\"")

if __name__ == "__main__":
    unittest.main()
