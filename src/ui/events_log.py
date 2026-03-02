"""Events log UI panel and logging handler.

Provides a scrollable text panel that displays INFO+ log messages in the GUI,
giving users real-time feedback about generator activity. Log messages are
still written to the file handler as before.
"""

import logging
import tkinter as tk
from tkinter import ttk
from collections import deque


class EventsLogHandler(logging.Handler):
    """Custom logging handler that forwards log records to the EventsLogPanel.

    Thread-safe: uses tkinter's after() to schedule UI updates on the main thread.
    Records are buffered if the panel is not yet attached.
    """

    def __init__(self, level=logging.INFO, max_buffer: int = 200):
        super().__init__(level)
        self._panel = None
        self._buffer: deque[logging.LogRecord] = deque(maxlen=max_buffer)

    def attach_panel(self, panel: "EventsLogPanel"):
        """Attach a panel and flush any buffered records to it."""
        self._panel = panel
        for record in self._buffer:
            self._schedule_append(record)
        self._buffer.clear()

    def emit(self, record: logging.LogRecord):
        if self._panel is None:
            self._buffer.append(record)
            return
        self._schedule_append(record)

    def _schedule_append(self, record: logging.LogRecord):
        """Schedule a UI append on the main thread."""
        try:
            msg = self.format(record)
            self._panel.winfo_toplevel().after(0, self._panel.append_message, msg, record.levelno)
        except Exception:
            self.handleError(record)


class EventsLogPanel(ttk.LabelFrame):
    """A scrollable text panel that displays event log messages."""

    # Reasonable max lines to prevent unbounded memory growth
    MAX_LINES = 500

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Events Log", **kwargs)

        # Text widget with vertical scrollbar
        self._scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self._text = tk.Text(
            self,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=12,
            width=60,
            yscrollcommand=self._scrollbar.set,
            font=("TkDefaultFont", 9),
            borderwidth=0,
            padx=4,
            pady=2,
        )
        self._scrollbar.config(command=self._text.yview)

        # Layout
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag styles for different log levels
        self._text.tag_configure("WARNING", foreground="#CC7A00")
        self._text.tag_configure("ERROR", foreground="#CC0000")
        self._text.tag_configure("CRITICAL", foreground="#CC0000", underline=True)

        self._line_count = 0

    def append_message(self, message: str, level: int = logging.INFO):
        """Append a formatted log message to the text widget.

        Args:
            message: The pre-formatted log message string.
            level: The logging level (used for colour tagging).
        """
        tag = None
        if level >= logging.CRITICAL:
            tag = "CRITICAL"
        elif level >= logging.ERROR:
            tag = "ERROR"
        elif level >= logging.WARNING:
            tag = "WARNING"

        self._text.configure(state=tk.NORMAL)
        if self._line_count > 0:
            self._text.insert(tk.END, "\n")
        self._text.insert(tk.END, message, (tag,) if tag else ())
        self._line_count += 1

        # Trim oldest lines if we exceed the limit
        if self._line_count > self.MAX_LINES:
            excess = self._line_count - self.MAX_LINES
            self._text.delete("1.0", f"{excess + 1}.0")
            self._line_count = self.MAX_LINES

        self._text.configure(state=tk.DISABLED)
        self._text.see(tk.END)

    def clear(self):
        """Clear all messages from the log panel."""
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)
        self._line_count = 0
