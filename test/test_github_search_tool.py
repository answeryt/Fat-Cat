# -*- coding: utf-8 -*-
"""Unit tests for the github_search tool in tools_bridge."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load tools_bridge directly to avoid importing the full Executor_agent chain
_spec = importlib.util.spec_from_file_location(
    "stage4_agent.tools_bridge",
    PROJECT_ROOT / "stage4_agent" / "tools_bridge.py",
)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["stage4_agent.tools_bridge"] = _module
_spec.loader.exec_module(_module)  # type: ignore[union-attr]

ToolsBridge = _module.ToolsBridge
github_search = _module.github_search


def _make_bridge() -> ToolsBridge:
    return ToolsBridge()


def _fake_response(payload: dict) -> MagicMock:
    """Return a mock urllib response that yields *payload* as JSON."""
    body = json.dumps(payload).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestGithubSearch(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = _make_bridge()

    @patch("urllib.request.urlopen")
    def test_successful_search_returns_results(self, mock_urlopen):
        payload = {
            "total_count": 2,
            "items": [
                {
                    "full_name": "org/repo-a",
                    "html_url": "https://github.com/org/repo-a",
                    "description": "Agent orchestration framework",
                    "stargazers_count": 1500,
                    "forks_count": 200,
                    "updated_at": "2025-01-15T10:00:00Z",
                    "language": "Python",
                    "topics": ["agent", "workflow"],
                },
                {
                    "full_name": "org/repo-b",
                    "html_url": "https://github.com/org/repo-b",
                    "description": "Multi-agent task runner",
                    "stargazers_count": 800,
                    "forks_count": 90,
                    "updated_at": "2024-12-01T08:00:00Z",
                    "language": "TypeScript",
                    "topics": [],
                },
            ],
        }
        mock_urlopen.return_value = _fake_response(payload)

        result = github_search(self.bridge, query="agent orchestration workflow")

        self.assertTrue(result.success)
        self.assertIn("org/repo-a", result.output)
        self.assertIn("https://github.com/org/repo-a", result.output)
        self.assertIn("Agent orchestration framework", result.output)
        self.assertIn("1500", result.output)
        self.assertIn("org/repo-b", result.output)

    @patch("urllib.request.urlopen")
    def test_zero_results_returns_helpful_message(self, mock_urlopen):
        payload = {"total_count": 0, "items": []}
        mock_urlopen.return_value = _fake_response(payload)

        result = github_search(self.bridge, query="xyzzy-nonexistent-term-123456")

        self.assertTrue(result.success)
        self.assertIn("Zero Results", result.output)

    @patch("urllib.request.urlopen")
    def test_http_error_returns_failure(self, mock_urlopen):
        error = urllib.error.HTTPError(
            url="https://api.github.com/search/repositories",
            code=403,
            msg="Forbidden",
            hdrs=MagicMock(),  # type: ignore[arg-type]
            fp=BytesIO(b'{"message":"rate limit exceeded"}'),
        )
        mock_urlopen.side_effect = error

        result = github_search(self.bridge, query="agent")

        self.assertFalse(result.success)
        self.assertIn("403", result.error or "")

    @patch("urllib.request.urlopen")
    def test_max_results_capped_at_30(self, mock_urlopen):
        payload = {"total_count": 0, "items": []}
        mock_urlopen.return_value = _fake_response(payload)

        github_search(self.bridge, query="agent", max_results=999)

        called_url = mock_urlopen.call_args[0][0].full_url
        self.assertIn("per_page=30", called_url)

    @patch("urllib.request.urlopen")
    def test_invalid_sort_falls_back_to_stars(self, mock_urlopen):
        payload = {"total_count": 0, "items": []}
        mock_urlopen.return_value = _fake_response(payload)

        github_search(self.bridge, query="agent", sort="invalid_sort")

        called_url = mock_urlopen.call_args[0][0].full_url
        self.assertIn("sort=stars", called_url)

    @patch("urllib.request.urlopen")
    def test_github_token_is_used_when_set(self, mock_urlopen):
        payload = {"total_count": 0, "items": []}
        mock_urlopen.return_value = _fake_response(payload)

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token-abc"}):
            github_search(self.bridge, query="agent")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer test-token-abc")

    @patch("urllib.request.urlopen")
    def test_tool_registered_in_registry(self, _mock_urlopen):
        from stage4_agent.tools_bridge import registry

        self.assertIn("github_search", registry.list_tools())


if __name__ == "__main__":
    unittest.main()
