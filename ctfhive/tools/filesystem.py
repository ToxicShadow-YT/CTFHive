from __future__ import annotations

from pathlib import Path


def safe_file_args(root: Path, relative_path: str) -> list[str]:
    path = (root / relative_path).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise ValueError("tool requires a regular file inside the challenge workspace")
    return [str(path)]
