"""Shared CLI UI helpers — Console, OutputMode, and process exit."""

import re
import sys


class Console:
    """Simple console replacement without rich."""

    _RICH_TAG = re.compile(r'\[/?[a-zA-Z_ ]*\]')

    def _strip_markup(self, message: str) -> str:
        """Remove rich markup tags from message."""
        return self._RICH_TAG.sub('', str(message))

    def print(self, message="", end=None):
        print(self._strip_markup(message), end=end)

    def success(self, message):
        print(self._strip_markup(message))

    def error(self, message):
        print(self._strip_markup(message))

    def warning(self, message):
        print(self._strip_markup(message))

    def info(self, message):
        print(self._strip_markup(message))

    def dim(self, message):
        print(self._strip_markup(message))


class OutputMode:
    """Controls output format (JSON vs human-readable).

    Replaces a bare module-level global so tests can reset state cleanly.
    """

    def __init__(self) -> None:
        self.json_output: bool = False


console = Console()
_output_mode = OutputMode()


def _exit(code: int = 1) -> None:
    """Exit the process. Returns without exiting when sys.exit is mocked in tests."""
    sys.exit(code)
    return
