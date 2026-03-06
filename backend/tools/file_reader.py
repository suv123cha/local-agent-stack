"""
tools/file_reader.py
====================
File-reader tool.

Reads plain-text, markdown, JSON, CSV, and Python files from the
local filesystem (or a configurable uploads directory).

Security note: paths are sandboxed to ALLOWED_DIR.
"""

import csv
import io
import json
import logging
import os

log = logging.getLogger(__name__)

# Only allow reading from this directory
ALLOWED_DIR = os.getenv("FILE_READER_DIR", "/tmp/agent_files")
MAX_CHARS = int(os.getenv("FILE_READER_MAX_CHARS", 8000))

_TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".html", ".yaml", ".yml", ".toml"}


def _safe_path(filename: str) -> str:
    """Resolve path and ensure it stays inside ALLOWED_DIR."""
    safe = os.path.realpath(os.path.join(ALLOWED_DIR, filename))
    if not safe.startswith(os.path.realpath(ALLOWED_DIR)):
        raise PermissionError(f"Path traversal detected: {filename!r}")
    return safe


def read_file(filename: str) -> str:
    """
    Read *filename* from the allowed directory and return its contents
    as a string truncated to MAX_CHARS.
    """
    log.info("File reader: %s", filename)
    try:
        path = _safe_path(filename)
    except PermissionError as exc:
        return f"Error: {exc}"

    if not os.path.exists(path):
        return f"Error: File '{filename}' not found in the uploads directory."

    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".json":
            return _read_json(path)
        if ext == ".csv":
            return _read_csv(path)
        if ext in _TEXT_EXTENSIONS or ext == "":
            return _read_text(path)
        return f"Error: Unsupported file type '{ext}'."
    except Exception as exc:
        log.exception("File read failed: %s", exc)
        return f"Error reading file: {exc}"


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        content = fh.read(MAX_CHARS)
    truncated = len(content) == MAX_CHARS
    suffix = "\n[... content truncated ...]" if truncated else ""
    return content + suffix


def _read_json(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    text = json.dumps(data, indent=2)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n[... truncated ...]"
    return text


def _read_csv(path: str) -> str:
    rows: list[list[str]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for i, row in enumerate(reader):
            if i > 200:
                rows.append(["[... rows truncated ...]"])
                break
            rows.append(row)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue()
