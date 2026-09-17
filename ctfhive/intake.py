from __future__ import annotations

import hashlib
import mimetypes
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class FileRecord:
    path: str
    relative_path: str
    size: int
    sha256: str
    mime: str
    file_type: str


@dataclass(frozen=True)
class Challenge:
    name: str
    root: Path
    files: tuple[FileRecord, ...]
    description: str = ""


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_type(path: Path) -> str:
    try:
        result = shutil.which("file")
        if result:
            import subprocess
            completed = subprocess.run([result, "--brief", "--mime-type", str(path)], capture_output=True, text=True, timeout=5)
            if completed.returncode == 0 and completed.stdout.strip():
                return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def ingest(source: str | Path, workspace_root: Path) -> Challenge:
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    name = source_path.stem if source_path.is_file() else source_path.name
    root = (workspace_root / name).resolve()
    workspace_root.resolve().mkdir(parents=True, exist_ok=True)
    if root == workspace_root.resolve() or workspace_root.resolve() not in root.parents:
        raise ValueError("challenge workspace must remain below configured workspace root")
    if root.exists():
        shutil.rmtree(root)
    if source_path.is_file():
        root.mkdir(parents=True)
        shutil.copy2(source_path, root / source_path.name)
    else:
        shutil.copytree(source_path, root)
    records: list[FileRecord] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        file_type = _file_type(path)
        records.append(FileRecord(str(path), path.relative_to(root).as_posix(), path.stat().st_size, _hash_file(path), file_type, file_type))
    return Challenge(name, root, tuple(records))


def enumerate_files(challenge: Challenge) -> list[FileRecord]:
    return list(challenge.files)
