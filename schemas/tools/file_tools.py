import json
import os
from pathlib import Path

from langchain.tools import ToolRuntime, tool

MAX_READ_BYTES = 200_000
MAX_LIST_ENTRIES = 1000


def _workspace_root() -> Path:
    return Path(os.getenv("WORKSPACE_ROOT", str(Path.home()))).expanduser().resolve()


def _resolve(path: str) -> Path:
    root = _workspace_root()
    candidate = Path(path).expanduser()
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()

    if target != root and root not in target.parents:
        raise ValueError(
            f"Path '{target}' is outside the workspace root '{root}'. "
            "Set the WORKSPACE_ROOT environment variable to allow other locations."
        )

    return target


def _notify(runtime: ToolRuntime, message: str) -> None:
    writer = getattr(runtime, "stream_writer", None)
    if writer:
        writer({"message": message})


def _ok(**data) -> str:
    return json.dumps({"status": "success", **data})


def _err(message: str) -> str:
    return json.dumps({"status": "error", "message": message})


def _read_text(target: Path) -> str:
    return target.open("r", encoding="utf-8", newline="").read()


def _write_text(target: Path, text: str) -> None:
    target.open("w", encoding="utf-8", newline="").write(text)


@tool
def read_file(path: str, runtime: ToolRuntime) -> str:
    """Read a text file from disk.

    Args:
        path: File path (absolute, or relative to the workspace root).
    """
    try:
        target = _resolve(path)
    except ValueError as e:
        return _err(str(e))

    if not target.exists():
        return _err(f"File not found: {target}")
    if not target.is_file():
        return _err(f"Not a file: {target}")

    _notify(runtime, f"Reading file: {target.name}")

    data = target.read_bytes()
    truncated = len(data) > MAX_READ_BYTES
    content = data[:MAX_READ_BYTES].decode("utf-8", errors="replace")

    return _ok(
        output_file_path=str(target),
        path=str(target),
        bytes=len(data),
        truncated=truncated,
        content=content,
    )


@tool
def write_file(path: str, content: str, runtime: ToolRuntime) -> str:
    """Create a new text file or overwrite an existing one.

    Args:
        path: File path (absolute, or relative to the workspace root).
        content: Full text content to write to the file.
    """
    try:
        target = _resolve(path)
    except ValueError as e:
        return _err(str(e))

    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)

    _notify(
        runtime,
        f"{'Overwriting' if existed else 'Creating'} file: {target.name}",
    )

    _write_text(target, content)

    return _ok(
        output_file_path=str(target),
        path=str(target),
        bytes=len(content.encode("utf-8")),
        created=not existed,
        message=f"{'Overwrote' if existed else 'Created'} {target}",
    )


@tool
def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    runtime: ToolRuntime,
    replace_all: bool = False,
) -> str:
    """Edit a text file by replacing an exact string.

    Args:
        path: File path (absolute, or relative to the workspace root).
        old_string: Exact text to find in the file.
        new_string: Text to replace it with.
        replace_all: Replace every occurrence. By default the replacement only
            happens if old_string is unique in the file.
    """
    try:
        target = _resolve(path)
    except ValueError as e:
        return _err(str(e))

    if not target.exists():
        return _err(f"File not found: {target}")
    if not target.is_file():
        return _err(f"Not a file: {target}")

    text = _read_text(target)
    occurrences = text.count(old_string)

    if occurrences == 0:
        return _err(f"old_string was not found in {target}")

    if occurrences > 1 and not replace_all:
        return _err(
            f"old_string occurs {occurrences} times in {target}. "
            "Provide more surrounding context to make it unique, or pass replace_all=true."
        )

    _notify(runtime, f"Editing file: {target.name}")

    updated = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
    _write_text(target, updated)

    return _ok(
        output_file_path=str(target),
        path=str(target),
        replacements=occurrences if replace_all else 1,
        message=f"Updated {target}",
    )


@tool
def list_files(
    runtime: ToolRuntime,
    directory: str = ".",
    pattern: str = "*",
    recursive: bool = False,
) -> str:
    """List files and folders inside a directory.

    Args:
        directory: Directory to list (absolute, or relative to the workspace root).
        pattern: Glob pattern to filter entries (e.g. "*.py").
        recursive: Search sub-directories as well.
    """
    try:
        target = _resolve(directory)
    except ValueError as e:
        return _err(str(e))

    if not target.exists():
        return _err(f"Directory not found: {target}")
    if not target.is_dir():
        return _err(f"Not a directory: {target}")

    _notify(runtime, f"Listing: {target}")

    iterator = target.rglob(pattern) if recursive else target.glob(pattern)

    entries = []
    for item in iterator:
        try:
            stat = item.stat()
        except OSError:
            continue

        entries.append(
            {
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
            }
        )

        if len(entries) >= MAX_LIST_ENTRIES:
            break

    entries.sort(key=lambda entry: entry["path"])

    return _ok(directory=str(target), count=len(entries), entries=entries)
