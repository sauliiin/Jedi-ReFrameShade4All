import re
from pathlib import Path
from typing import Optional

from .base_service import BaseService
from .constants import LOSSLESS_DLL_FILENAME


class SteamService(BaseService):
    def _steam_roots(self):
        seen = set()
        for candidate in (
            self.user_home / ".local/share/Steam",
            self.user_home / ".steam/steam",
            self.user_home / ".steam/root",
            self.user_home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
        ):
            yield from self._unique_existing_root(candidate, seen)

    def _steam_library_roots(self):
        seen = set()
        for root in self._steam_roots():
            yield from self._unique_existing_root(root, seen)
            for library_file in (
                root / "steamapps/libraryfolders.vdf",
                root / "config/libraryfolders.vdf",
            ):
                try:
                    content = library_file.read_text(encoding="utf-8")
                except OSError:
                    continue
                for raw_path in re.findall(r'(?m)^\s*"path"\s+"((?:\\.|[^"])*)"', content):
                    path = raw_path.replace(r'\"', '"').replace(r'\\', '\\')
                    yield from self._unique_existing_root(Path(path), seen)

    @staticmethod
    def _unique_existing_root(path: Path, seen: set[str]):
        if not path.exists():
            return
        try:
            resolved = str(path.resolve())
        except OSError:
            resolved = str(path)
        if resolved not in seen:
            seen.add(resolved)
            yield path

    def _lossless_scaling_path(self) -> Optional[Path]:
        return next((
            path
            for root in self._steam_library_roots()
            if (path := root / "steamapps/common/Lossless Scaling").is_dir()
        ), None)

    def find_lossless_dll(self) -> Optional[str]:
        directory = self._lossless_scaling_path()
        path = directory / LOSSLESS_DLL_FILENAME if directory else None
        return str(path) if path and path.is_file() else None

