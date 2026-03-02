"""Tests for the EventsLogHandler and EventsLogPanel."""

import logging
import tkinter as tk

import pytest

from ui.events_log import EventsLogHandler, EventsLogPanel


@pytest.fixture
def root():
    """Create and destroy a Tk root window for each test."""
    root = tk.Tk()
    root.withdraw()  # Hide the window during tests
    yield root
    root.destroy()


@pytest.fixture
def panel(root):
    """Create an EventsLogPanel attached to the root window."""
    return EventsLogPanel(root)


@pytest.fixture
def handler():
    """Create a fresh EventsLogHandler."""
    return EventsLogHandler(level=logging.INFO)


class TestEventsLogHandler:
    def test_buffers_records_before_panel_attached(self, handler):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="buffered message", args=(), exc_info=None,
        )
        handler.emit(record)
        assert len(handler._buffer) == 1

    def test_flush_buffer_on_attach(self, handler, panel, root):
        """Records emitted before attach should be flushed to the panel."""
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="pre-attach", args=(), exc_info=None,
        )
        handler.emit(record)
        assert len(handler._buffer) == 1

        handler.attach_panel(panel)
        # Process pending after() calls
        root.update_idletasks()
        root.update()

        assert len(handler._buffer) == 0
        text_content = panel._text.get("1.0", tk.END).strip()
        assert "pre-attach" in text_content

    def test_emit_after_attach(self, handler, panel, root):
        """Records emitted after attach should appear in the panel."""
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.attach_panel(panel)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="live message", args=(), exc_info=None,
        )
        handler.emit(record)
        root.update_idletasks()
        root.update()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert "live message" in text_content

    def test_filters_below_level(self, handler, panel, root):
        """DEBUG records should not pass through the INFO-level handler."""
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.attach_panel(panel)

        # Create a logger and add the handler
        test_logger = logging.getLogger("test_filter")
        test_logger.setLevel(logging.DEBUG)
        test_logger.addHandler(handler)

        test_logger.debug("debug message should not appear")
        root.update_idletasks()
        root.update()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert text_content == ""

        # Remove handler to avoid interference with other tests
        test_logger.removeHandler(handler)

    def test_buffer_max_size(self):
        """Buffer should respect max_buffer size."""
        handler = EventsLogHandler(level=logging.INFO, max_buffer=5)
        for i in range(10):
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg=f"msg {i}", args=(), exc_info=None,
            )
            handler.emit(record)
        assert len(handler._buffer) == 5
        # Oldest messages should have been dropped
        messages = [handler.format(r) for r in handler._buffer]
        assert "msg 5" in messages[0]


class TestEventsLogPanel:
    def test_append_message(self, panel, root):
        panel.append_message("Hello world")
        root.update_idletasks()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert text_content == "Hello world"
        assert panel._line_count == 1

    def test_multiple_messages(self, panel, root):
        panel.append_message("First")
        panel.append_message("Second")
        root.update_idletasks()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert "First" in text_content
        assert "Second" in text_content
        assert panel._line_count == 2

    def test_warning_tag(self, panel, root):
        panel.append_message("Warning!", logging.WARNING)
        root.update_idletasks()

        # Check that the WARNING tag is applied
        tags = panel._text.tag_names("1.0")
        assert "WARNING" in tags

    def test_error_tag(self, panel, root):
        panel.append_message("Error!", logging.ERROR)
        root.update_idletasks()

        tags = panel._text.tag_names("1.0")
        assert "ERROR" in tags

    def test_clear(self, panel, root):
        panel.append_message("To be cleared")
        panel.clear()
        root.update_idletasks()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert text_content == ""
        assert panel._line_count == 0

    def test_max_lines_trim(self, panel, root):
        """Lines beyond MAX_LINES should be trimmed from the top."""
        panel.MAX_LINES = 10
        for i in range(15):
            panel.append_message(f"line {i}")
        root.update_idletasks()

        text_content = panel._text.get("1.0", tk.END).strip()
        assert panel._line_count == 10
        # First 5 lines should have been trimmed
        assert "line 0" not in text_content
        assert "line 14" in text_content

    def test_text_is_read_only(self, panel, root):
        """Text widget should be in DISABLED state between appends."""
        assert str(panel._text.cget("state")) == tk.DISABLED
