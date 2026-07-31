"""Local filesystem report storage."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from ax_storage.keys import object_key


class LocalReportStorage:
    """Store report trees on local disk under a configurable root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        target = (self.root / key).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError(f"Invalid storage key: {key!r}")
        return target

    def upload_tree(self, local_dir: Path, key_prefix: str) -> str:
        src = local_dir.resolve()
        if not src.is_dir():
            raise FileNotFoundError(f"Report directory not found: {local_dir}")

        dest = self._path(key_prefix)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return key_prefix.rstrip("/")

    def exists(self, key_prefix: str, relative: str) -> bool:
        return self._path(object_key(key_prefix, relative)).is_file()

    def read_text(self, key_prefix: str, relative: str) -> str:
        path = self._path(object_key(key_prefix, relative))
        if not path.is_file():
            raise FileNotFoundError(relative)
        return path.read_text(encoding="utf-8")

    def presigned_url(self, key_prefix: str, relative: str, *, expires: int) -> str | None:
        return None

    def presigned_url_expires_at(self, expires: int) -> datetime | None:
        return None

    def supports_signed_urls(self) -> bool:
        return False

    def delete_tree(self, key_prefix: str) -> None:
        path = self._path(key_prefix)
        if path.exists():
            shutil.rmtree(path)
