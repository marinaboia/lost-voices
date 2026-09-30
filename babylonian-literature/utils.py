"""Shared utilities for babylonian-literature scripts."""

import os
from pathlib import Path


def load_env() -> None:
    """
    Load key=value pairs from a .env file into os.environ.
    Searches from this file's directory upward (up to the repo root).
    Existing environment variables are never overwritten.
    """
    search = Path(__file__).parent
    for _ in range(4):
        candidate = search / ".env"
        if candidate.exists():
            with open(candidate) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
            return
        search = search.parent
