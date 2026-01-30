"""Tests for the GitHub reporter module."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from hardwarextractor.core.github_reporter import (
    GitHubReporter,
    get_github_reporter,
    send_feedback_report,
)


class TestGitHubReporter:
    """Tests for GitHubReporter class."""

    def test_init(self):
        """Test GitHubReporter initialization."""
        reporter = GitHubReporter()
        assert reporter.REPO_OWNER == "NAZCAMEDIA"
        assert reporter.REPO_NAME == "hardwarextractor"
        assert reporter.MIN_INTERVAL_SECONDS == 60
        assert reporter._last_report_time is None

    def test_api_url(self):
        """Test API URL is correctly formed."""
        reporter = GitHubReporter()
        expected = "https://api.github.com/repos/NAZCAMEDIA/hardwarextractor/issues"
        assert reporter.API_URL == expected

    def test_get_token_from_env(self):
        """Test token is retrieved from environment variable."""
        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token_123"}):
            token = reporter._get_token()
        assert token == "test_token_123"

    def test_get_token_prefers_env(self):
        """Test environment variable takes precedence over embedded token."""
        reporter = GitHubReporter()
        reporter._TOKEN_PARTS = ["ghp_", "embedded"]
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "env_token"}):
            token = reporter._get_token()
        assert token == "env_token"

    def test_get_token_fallback_to_embedded(self):
        """Test fallback to embedded token when env not set."""
        reporter = GitHubReporter()
        reporter._TOKEN_PARTS = ["ghp_", "test", "parts"]
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("HXTRACTOR_GITHUB_TOKEN", None)
            token = reporter._get_token()
        assert token == "ghp_testparts"

    def test_get_token_returns_none_when_not_configured(self):
        """Test returns None when no token configured."""
        reporter = GitHubReporter()
        reporter._TOKEN_PARTS = []
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("HXTRACTOR_GITHUB_TOKEN", None)
            token = reporter._get_token()
        assert token is None

    def test_can_report_no_token(self):
        """Test can_report returns False when no token."""
        reporter = GitHubReporter()
        reporter._TOKEN_PARTS = []
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("HXTRACTOR_GITHUB_TOKEN", None)
            can_send, reason = reporter.can_report()
        assert can_send is False
        assert "Token" in reason

    def test_can_report_with_token(self):
        """Test can_report returns True when token available."""
        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            can_send, reason = reporter.can_report()
        assert can_send is True
        assert reason == ""

    def test_can_report_rate_limited(self):
        """Test can_report returns False when rate limited."""
        reporter = GitHubReporter()
        reporter._last_report_time = datetime.now()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            can_send, reason = reporter.can_report()
        assert can_send is False
        assert "Espera" in reason

    def test_can_report_after_rate_limit_expires(self):
        """Test can_report returns True after rate limit expires."""
        reporter = GitHubReporter()
        reporter._last_report_time = datetime.now() - timedelta(seconds=120)
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            can_send, reason = reporter.can_report()
        assert can_send is True

    def test_create_issue_no_token(self):
        """Test create_issue returns error when no token."""
        reporter = GitHubReporter()
        reporter._TOKEN_PARTS = []
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("HXTRACTOR_GITHUB_TOKEN", None)
            result = reporter.create_issue("Test", "Body")
        assert result["status"] == "error"
        assert "Token" in result["message"]

    def test_create_issue_rate_limited(self):
        """Test create_issue returns error when rate limited."""
        reporter = GitHubReporter()
        reporter._last_report_time = datetime.now()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test", "Body")
        assert result["status"] == "error"
        assert "Espera" in result["message"]

    @patch("requests.post")
    def test_create_issue_success(self, mock_post):
        """Test create_issue succeeds."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/NAZCAMEDIA/hardwarextractor/issues/123",
        }
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test Issue", "Test body", ["bug"])

        assert result["status"] == "success"
        assert result["issue_number"] == 123
        assert "issues/123" in result["issue_url"]

    @patch("requests.post")
    def test_create_issue_updates_last_report_time(self, mock_post):
        """Test create_issue updates last_report_time on success."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 1, "html_url": "http://test"}
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        assert reporter._last_report_time is None

        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            reporter.create_issue("Test", "Body")

        assert reporter._last_report_time is not None

    @patch("requests.post")
    def test_create_issue_unauthorized(self, mock_post):
        """Test create_issue handles 401 error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "bad_token"}):
            result = reporter.create_issue("Test", "Body")

        assert result["status"] == "error"
        assert "inválido" in result["message"]

    @patch("requests.post")
    def test_create_issue_forbidden(self, mock_post):
        """Test create_issue handles 403 error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test", "Body")

        assert result["status"] == "error"
        assert "permisos" in result["message"]

    @patch("requests.post")
    def test_create_issue_validation_error(self, mock_post):
        """Test create_issue handles 422 error."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Validation failed"
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test", "Body")

        assert result["status"] == "error"
        assert "inválidos" in result["message"]

    @patch("requests.post")
    def test_create_issue_timeout(self, mock_post):
        """Test create_issue handles timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test", "Body")

        assert result["status"] == "error"
        assert "Timeout" in result["message"]

    @patch("requests.post")
    def test_create_issue_connection_error(self, mock_post):
        """Test create_issue handles connection error."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            result = reporter.create_issue("Test", "Body")

        assert result["status"] == "error"
        assert "conexión" in result["message"]

    @patch("requests.post")
    def test_create_issue_includes_labels(self, mock_post):
        """Test create_issue includes labels in request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 1, "html_url": "http://test"}
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "test_token"}):
            reporter.create_issue("Test", "Body", ["bug", "beta"])

        # Check that labels were in the payload
        call_kwargs = mock_post.call_args[1]
        assert "labels" in call_kwargs["json"]
        assert call_kwargs["json"]["labels"] == ["bug", "beta"]

    @patch("requests.post")
    def test_create_issue_headers(self, mock_post):
        """Test create_issue sends correct headers."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 1, "html_url": "http://test"}
        mock_post.return_value = mock_response

        reporter = GitHubReporter()
        with patch.dict(os.environ, {"HXTRACTOR_GITHUB_TOKEN": "my_token"}):
            reporter.create_issue("Test", "Body")

        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["Authorization"] == "token my_token"
        assert "github" in headers["Accept"]
        assert "HardwareXtractor" in headers["User-Agent"]


class TestGetGitHubReporter:
    """Tests for get_github_reporter function."""

    def test_returns_same_instance(self):
        """Test get_github_reporter returns singleton."""
        import hardwarextractor.core.github_reporter as gr
        gr._reporter = None

        reporter1 = get_github_reporter()
        reporter2 = get_github_reporter()
        assert reporter1 is reporter2

    def test_creates_instance_on_first_call(self):
        """Test instance is created on first call."""
        import hardwarextractor.core.github_reporter as gr
        gr._reporter = None

        reporter = get_github_reporter()
        assert isinstance(reporter, GitHubReporter)


class TestSendFeedbackReport:
    """Tests for send_feedback_report convenience function."""

    @patch("hardwarextractor.core.github_reporter.get_github_reporter")
    def test_calls_create_issue(self, mock_get_reporter):
        """Test send_feedback_report calls create_issue."""
        mock_reporter = MagicMock()
        mock_reporter.create_issue.return_value = {"status": "success"}
        mock_get_reporter.return_value = mock_reporter

        result = send_feedback_report("Title", "Body", ["label"])

        mock_reporter.create_issue.assert_called_once_with("Title", "Body", ["label"])
        assert result["status"] == "success"

    @patch("hardwarextractor.core.github_reporter.get_github_reporter")
    def test_handles_none_labels(self, mock_get_reporter):
        """Test send_feedback_report handles None labels."""
        mock_reporter = MagicMock()
        mock_reporter.create_issue.return_value = {"status": "success"}
        mock_get_reporter.return_value = mock_reporter

        send_feedback_report("Title", "Body")

        mock_reporter.create_issue.assert_called_once_with("Title", "Body", None)
