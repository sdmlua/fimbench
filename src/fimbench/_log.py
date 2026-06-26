"""
fimbench._log

Shared status logger so every subpackage emits output the same way:
    [HH:MM:SS] message
"""

from __future__ import annotations

from datetime import datetime


def log(msg):
    """Print a timestamped status line."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
