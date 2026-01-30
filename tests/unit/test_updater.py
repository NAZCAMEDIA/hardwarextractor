"""Tests for the auto-updater module."""

from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from hardwarextractor.core.updater import (
    parse_version,
    get_latest_version,
    is_newer_version,
    get_installer,
    do_update,
    check_and_update,
)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_simple_version(self):
        """Test parsing a simple version string."""
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_parse_two_part_version(self):
        """Test parsing a two-part version."""
        assert parse_version("1.2") == (1, 2)

    def test_parse_single_number(self):
        """Test parsing a single number version."""
        assert parse_version("5") == (5,)

    def test_parse_invalid_version(self):
        """Test parsing invalid version returns zeros."""
        assert parse_version("invalid") == (0, 0, 0)

    def test_parse_none(self):
        """Test parsing None returns zeros."""
        assert parse_version(None) == (0, 0, 0)

    def test_parse_empty_string(self):
        """Test parsing empty string returns zeros."""
        assert parse_version("") == (0, 0, 0)


class TestIsNewerVersion:
    """Tests for is_newer_version function."""

    def test_newer_major(self):
        """Test newer major version is detected."""
        assert is_newer_version("2.0.0", "1.0.0") is True

    def test_newer_minor(self):
        """Test newer minor version is detected."""
        assert is_newer_version("1.1.0", "1.0.0") is True

    def test_newer_patch(self):
        """Test newer patch version is detected."""
        assert is_newer_version("1.0.1", "1.0.0") is True

    def test_same_version(self):
        """Test same version is not newer."""
        assert is_newer_version("1.0.0", "1.0.0") is False

    def test_older_version(self):
        """Test older version is not newer."""
        assert is_newer_version("0.9.0", "1.0.0") is False


class TestGetLatestVersion:
    """Tests for get_latest_version function."""

    @patch("requests.get")
    def test_get_latest_version_success(self, mock_get):
        """Test fetching latest version from PyPI."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {"version": "1.2.3"}
        }
        mock_get.return_value = mock_response

        version = get_latest_version()
        assert version == "1.2.3"

    @patch("requests.get")
    def test_get_latest_version_http_error(self, mock_get):
        """Test handling HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        version = get_latest_version()
        assert version is None

    @patch("requests.get")
    def test_get_latest_version_connection_error(self, mock_get):
        """Test handling connection error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()

        version = get_latest_version()
        assert version is None

    @patch("requests.get")
    def test_get_latest_version_timeout(self, mock_get):
        """Test handling timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        version = get_latest_version()
        assert version is None


class TestGetInstaller:
    """Tests for get_installer function."""

    def test_detect_pip(self):
        """Test detecting pip installation."""
        with patch.object(sys, 'prefix', '/usr/local'):
            installer = get_installer()
        assert installer == "pip"

    def test_detect_pipx(self):
        """Test detecting pipx installation."""
        with patch.object(sys, 'prefix', '/home/user/.local/pipx/venvs/app'):
            installer = get_installer()
        assert installer == "pipx"


class TestDoUpdate:
    """Tests for do_update function."""

    @patch("subprocess.run")
    def test_do_update_pip_success(self, mock_run):
        """Test successful pip update."""
        mock_run.return_value = MagicMock(returncode=0)

        result = do_update("pip")
        assert result is True

    @patch("subprocess.run")
    def test_do_update_pipx_success(self, mock_run):
        """Test successful pipx update."""
        mock_run.return_value = MagicMock(returncode=0)

        result = do_update("pipx")
        assert result is True
        mock_run.assert_called_once()
        assert "pipx" in mock_run.call_args[0][0]

    @patch("subprocess.run")
    def test_do_update_failure(self, mock_run):
        """Test failed update."""
        mock_run.return_value = MagicMock(returncode=1)

        result = do_update("pip")
        assert result is False

    @patch("subprocess.run")
    def test_do_update_timeout(self, mock_run):
        """Test update timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("pip", 60)

        result = do_update("pip")
        assert result is False

    @patch("subprocess.run")
    def test_do_update_file_not_found(self, mock_run):
        """Test pipx not found."""
        mock_run.side_effect = FileNotFoundError()

        result = do_update("pipx")
        assert result is False


class TestCheckAndUpdate:
    """Tests for check_and_update function."""

    @patch("hardwarextractor.core.updater.get_latest_version")
    def test_check_no_version_available(self, mock_get_latest):
        """Test when PyPI is unreachable."""
        mock_get_latest.return_value = None

        result = check_and_update(silent=True)
        assert result is None

    @patch("hardwarextractor.core.updater.get_latest_version")
    @patch("hardwarextractor.core.updater.__version__", "1.0.0")
    def test_check_no_update_needed(self, mock_get_latest):
        """Test when already on latest version."""
        mock_get_latest.return_value = "1.0.0"

        result = check_and_update(silent=True)
        assert result is None

    @patch("hardwarextractor.core.updater.do_update")
    @patch("hardwarextractor.core.updater.get_installer")
    @patch("hardwarextractor.core.updater.get_latest_version")
    @patch("hardwarextractor.core.updater.__version__", "1.0.0")
    def test_check_update_success(self, mock_get_latest, mock_get_installer, mock_do_update):
        """Test successful update."""
        mock_get_latest.return_value = "2.0.0"
        mock_get_installer.return_value = "pip"
        mock_do_update.return_value = True

        result = check_and_update(silent=True)
        assert result == "2.0.0"

    @patch("hardwarextractor.core.updater.do_update")
    @patch("hardwarextractor.core.updater.get_installer")
    @patch("hardwarextractor.core.updater.get_latest_version")
    @patch("hardwarextractor.core.updater.__version__", "1.0.0")
    def test_check_update_failure(self, mock_get_latest, mock_get_installer, mock_do_update):
        """Test failed update."""
        mock_get_latest.return_value = "2.0.0"
        mock_get_installer.return_value = "pip"
        mock_do_update.return_value = False

        result = check_and_update(silent=True)
        assert result is None
