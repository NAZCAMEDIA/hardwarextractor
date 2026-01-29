"""Tests for core/logger.py - Logging system."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging


class TestLoggerSetup:
    """Test logger setup and configuration."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        from hardwarextractor.core.logger import get_logger

        logger = get_logger("test_module")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert "hxtractor.test_module" in logger.name

    def test_get_logger_same_module_returns_same_logger(self):
        """Test that same module name returns same logger."""
        from hardwarextractor.core.logger import get_logger

        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")
        assert logger1 is logger2

    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns root logger."""
        from hardwarextractor.core.logger import setup_logging

        logger = setup_logging()
        assert logger is not None
        assert isinstance(logger, logging.Logger)


class TestProcessLogger:
    """Test ProcessLogger context manager."""

    def test_process_logger_creation(self):
        """Test ProcessLogger can be created."""
        from hardwarextractor.core.logger import ProcessLogger

        plog = ProcessLogger("test_process", url="https://test.com")
        assert plog.process_name == "test_process"
        assert plog.context == {"url": "https://test.com"}
        assert len(plog.process_id) == 10

    def test_process_logger_context_manager(self):
        """Test ProcessLogger as context manager."""
        from hardwarextractor.core.logger import ProcessLogger

        with ProcessLogger("test_context", param="value") as plog:
            assert plog.start_time is not None
            plog.debug("Test debug message")
            plog.info("Test info message")
            plog.warning("Test warning")
            plog.error("Test error")
            plog.data("test_data", {"key": "value"})

    def test_process_logger_methods(self):
        """Test ProcessLogger logging methods."""
        from hardwarextractor.core.logger import ProcessLogger
        from datetime import datetime

        plog = ProcessLogger("method_test")
        plog.start_time = datetime.now()

        # These should not raise
        msg_with_kwargs = plog._format_msg("test message", extra_param="value")
        msg_without_kwargs = plog._format_msg("test message without kwargs")

        assert "test message" in msg_with_kwargs
        assert "extra_param=value" in msg_with_kwargs
        assert "test message without kwargs" in msg_without_kwargs


class TestConvenienceFunctions:
    """Test convenience logging functions."""

    def test_log_debug(self):
        """Test log_debug function."""
        from hardwarextractor.core.logger import log_debug
        # Should not raise
        log_debug("Test debug message", module="test")

    def test_log_info(self):
        """Test log_info function."""
        from hardwarextractor.core.logger import log_info
        log_info("Test info message", module="test")

    def test_log_warning(self):
        """Test log_warning function."""
        from hardwarextractor.core.logger import log_warning
        log_warning("Test warning message", module="test")

    def test_log_error(self):
        """Test log_error function."""
        from hardwarextractor.core.logger import log_error
        log_error("Test error message", module="test")

    def test_log_with_default_module(self):
        """Test logging with default module."""
        from hardwarextractor.core.logger import log_info
        log_info("Test with default module")


class TestLoggerConstants:
    """Test logger constants and configuration."""

    def test_log_dir_exists(self):
        """Test that LOG_DIR constant is defined."""
        from hardwarextractor.core.logger import LOG_DIR
        assert LOG_DIR is not None
        assert isinstance(LOG_DIR, Path)

    def test_log_file_defined(self):
        """Test that LOG_FILE is defined."""
        from hardwarextractor.core.logger import LOG_FILE
        assert LOG_FILE is not None

    def test_format_constants(self):
        """Test format constants are defined."""
        from hardwarextractor.core.logger import FILE_FORMAT, DATE_FORMAT
        assert FILE_FORMAT is not None
        assert DATE_FORMAT is not None
        assert "%Y" in DATE_FORMAT
