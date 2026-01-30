"""Tests for the feedback system."""

from __future__ import annotations

import platform
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from hardwarextractor._version import __version__
from hardwarextractor.core.feedback import (
    FeedbackCollector,
    SearchContext,
    get_feedback_collector,
)


class TestSearchContext:
    """Tests for SearchContext dataclass."""

    def test_create_search_context(self):
        """Test creating a SearchContext with required fields."""
        ctx = SearchContext(
            input_text="RTX 4090",
            component_type="GPU",
            result="success",
        )
        assert ctx.input_text == "RTX 4090"
        assert ctx.component_type == "GPU"
        assert ctx.result == "success"
        assert ctx.error_message is None
        assert isinstance(ctx.timestamp, datetime)
        assert ctx.log_entries == []

    def test_create_search_context_with_error(self):
        """Test creating a SearchContext with error message."""
        ctx = SearchContext(
            input_text="unknown model",
            component_type="",
            result="error",
            error_message="Component not found",
        )
        assert ctx.result == "error"
        assert ctx.error_message == "Component not found"

    def test_create_search_context_with_logs(self):
        """Test creating a SearchContext with log entries."""
        logs = ["Normalizing input...", "Classifying component..."]
        ctx = SearchContext(
            input_text="i9-14900K",
            component_type="CPU",
            result="success",
            log_entries=logs,
        )
        assert ctx.log_entries == logs
        assert len(ctx.log_entries) == 2


class TestFeedbackCollector:
    """Tests for FeedbackCollector class."""

    def test_init(self):
        """Test FeedbackCollector initialization."""
        collector = FeedbackCollector()
        assert collector.search_count == 0
        assert collector.last_search is None
        assert collector.VERSION == __version__
        assert collector.REMINDER_INTERVAL == 5

    def test_capture_search(self):
        """Test capturing a search context."""
        collector = FeedbackCollector()
        collector.capture_search(
            input_text="RTX 4090",
            component_type="GPU",
            result="success",
        )
        assert collector.search_count == 1
        assert collector.last_search is not None
        assert collector.last_search.input_text == "RTX 4090"
        assert collector.last_search.component_type == "GPU"
        assert collector.last_search.result == "success"

    def test_capture_multiple_searches(self):
        """Test capturing multiple searches increments counter."""
        collector = FeedbackCollector()
        for i in range(3):
            collector.capture_search(
                input_text=f"component_{i}",
                component_type="CPU",
                result="success",
            )
        assert collector.search_count == 3
        assert collector.last_search.input_text == "component_2"

    def test_capture_search_with_error(self):
        """Test capturing a failed search."""
        collector = FeedbackCollector()
        collector.capture_search(
            input_text="invalid",
            component_type="",
            result="error",
            error_message="Timeout on corsair.com",
        )
        assert collector.last_search.result == "error"
        assert collector.last_search.error_message == "Timeout on corsair.com"

    def test_should_show_reminder_false_initially(self):
        """Test reminder not shown initially."""
        collector = FeedbackCollector()
        assert collector.should_show_reminder() is False

    def test_should_show_reminder_at_interval(self):
        """Test reminder shown at interval."""
        collector = FeedbackCollector()
        for i in range(5):
            collector.capture_search("test", "CPU", "success")
        assert collector.should_show_reminder() is True

    def test_should_show_reminder_only_at_multiples(self):
        """Test reminder only shown at multiples of interval."""
        collector = FeedbackCollector()
        results = []
        for i in range(12):
            collector.capture_search("test", "CPU", "success")
            results.append(collector.should_show_reminder())
        # Should be True at 5 and 10 (indices 4 and 9)
        assert results[4] is True  # After 5 searches
        assert results[9] is True  # After 10 searches
        assert results[0] is False
        assert results[3] is False
        assert results[6] is False

    def test_generate_report_empty_when_no_search(self):
        """Test generate_report returns empty dict when no search."""
        collector = FeedbackCollector()
        report = collector.generate_report()
        assert report == {}

    def test_generate_report_structure(self):
        """Test generate_report returns correct structure."""
        collector = FeedbackCollector()
        collector.capture_search(
            input_text="RTX 4090",
            component_type="GPU",
            result="no_results",
        )
        report = collector.generate_report()
        assert "title" in report
        assert "body" in report
        assert "labels" in report
        assert report["labels"] == ["beta-feedback", "auto-generated"]

    def test_generate_report_title_format(self):
        """Test generate_report title format."""
        collector = FeedbackCollector()
        collector.capture_search(
            input_text="RTX 4090",
            component_type="GPU",
            result="no_results",
        )
        report = collector.generate_report()
        assert "[Feedback Beta]" in report["title"]
        assert "GPU" in report["title"]
        assert "RTX 4090" in report["title"]

    def test_generate_report_title_truncates_long_input(self):
        """Test title truncates long input text."""
        collector = FeedbackCollector()
        long_input = "A" * 50
        collector.capture_search(
            input_text=long_input,
            component_type="CPU",
            result="error",
        )
        report = collector.generate_report()
        assert "..." in report["title"]
        assert len(report["title"]) < 100

    def test_generate_report_body_contains_system_info(self):
        """Test report body contains system information."""
        collector = FeedbackCollector()
        collector.capture_search("test", "CPU", "success")
        report = collector.generate_report()
        body = report["body"]
        assert "Información del sistema" in body
        assert "Versión:" in body
        assert "OS:" in body
        assert "Python:" in body

    def test_generate_report_body_contains_search_info(self):
        """Test report body contains search information."""
        collector = FeedbackCollector()
        collector.capture_search(
            input_text="i9-14900K",
            component_type="CPU",
            result="success",
        )
        report = collector.generate_report()
        body = report["body"]
        assert "i9-14900K" in body
        assert "CPU" in body
        assert "Éxito" in body

    def test_generate_report_with_user_comment(self):
        """Test report body includes user comment."""
        collector = FeedbackCollector()
        collector.capture_search("test", "RAM", "no_results")
        report = collector.generate_report(user_comment="The search didn't find my RAM model")
        body = report["body"]
        assert "Descripción del usuario" in body
        assert "The search didn't find my RAM model" in body

    def test_generate_report_without_user_comment(self):
        """Test report body without user comment section when empty."""
        collector = FeedbackCollector()
        collector.capture_search("test", "RAM", "success")
        report = collector.generate_report(user_comment="")
        body = report["body"]
        assert "Descripción del usuario" not in body

    def test_generate_report_result_mapping(self):
        """Test result strings are mapped correctly."""
        collector = FeedbackCollector()

        collector.capture_search("test", "CPU", "success")
        report = collector.generate_report()
        assert "Éxito" in report["body"]

        collector.capture_search("test", "CPU", "no_results")
        report = collector.generate_report()
        assert "No se encontraron resultados" in report["body"]

        collector.capture_search("test", "CPU", "error", error_message="Network timeout")
        report = collector.generate_report()
        assert "Error: Network timeout" in report["body"]

    def test_reset(self):
        """Test reset clears state."""
        collector = FeedbackCollector()
        collector.capture_search("test", "CPU", "success")
        collector.capture_search("test2", "GPU", "success")
        assert collector.search_count == 2
        assert collector.last_search is not None

        collector.reset()
        assert collector.search_count == 0
        assert collector.last_search is None

    @patch("hardwarextractor.core.feedback.LOG_FILE")
    def test_get_recent_log_entries_file_not_exists(self, mock_log_file):
        """Test getting log entries when file doesn't exist."""
        mock_log_file.exists.return_value = False
        collector = FeedbackCollector()
        entries = collector._get_recent_log_entries()
        assert entries == []

    @patch("builtins.open")
    @patch("hardwarextractor.core.feedback.LOG_FILE")
    def test_get_recent_log_entries_reads_file(self, mock_log_file, mock_open):
        """Test getting log entries reads from file."""
        mock_log_file.exists.return_value = True
        mock_open.return_value.__enter__.return_value.readlines.return_value = [
            "line1\n",
            "line2\n",
            "line3\n",
        ]
        collector = FeedbackCollector()
        entries = collector._get_recent_log_entries(max_lines=2)
        assert len(entries) == 2
        assert entries == ["line2", "line3"]


class TestGetFeedbackCollector:
    """Tests for get_feedback_collector function."""

    def test_returns_same_instance(self):
        """Test get_feedback_collector returns singleton."""
        # Reset the global
        import hardwarextractor.core.feedback as fb
        fb._collector = None

        collector1 = get_feedback_collector()
        collector2 = get_feedback_collector()
        assert collector1 is collector2

    def test_creates_instance_on_first_call(self):
        """Test instance is created on first call."""
        import hardwarextractor.core.feedback as fb
        fb._collector = None

        collector = get_feedback_collector()
        assert isinstance(collector, FeedbackCollector)
