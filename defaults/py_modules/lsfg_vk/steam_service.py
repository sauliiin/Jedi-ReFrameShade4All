import re
import zlib
from pathlib import Path
from typing import Dict, Optional, Tuple

from .base_service import BaseService
from .constants import (
    LOSSLESS_DLL_FILENAME,
    STEAM_LOSSLESS_SCALING_APP_ID,
    STEAM_LOSSLESS_SCALING_BRANCH,
)


class SteamService(BaseService):
    DEFAULT_BRANCH = "public"
    MANIFEST_FILENAME = f"appmanifest_{STEAM_LOSSLESS_SCALING_APP_ID}.acf"
    # Valve compatibility tools, runtimes, Steamworks redistributables, and LSFG.
    GAME_SELECTOR_EXCLUDED_APPIDS = {
        "858280",   # Proton 3.7
        "961940",   # Proton 3.16
        "1054830",  # Proton 4.2
        "1113280",  # Proton 4.11
        "1245040",  # Proton 5.0
        "1420170",  # Proton 5.13
        "1493710",  # Proton Experimental
        "1580130",  # Proton 6.3
        "1887720",  # Proton 7
        "2180100",  # Proton Hotfix
        "228980",   # Steamworks Common Redistributables
        "2348590",  # Proton 8
        "2805730",  # Proton 9
        "3029110",  # Lepton
        "3127680",  # fex
        "3658110",  # Proton 10
        "4183110",  # Steam Linux Runtime 4.0
        "4185400",  # Steam Linux Runtime 4.0 for arm64
        "4427310",  # Proton Experimental (ARM64)
        "4628710",  # Proton 11 / Proton Next
        "4628740",  # Proton 11 (ARM64)
        "4690330",  # Legacy Steam Runtime
        "993090",   # Lossless Scaling
        "1070560",  # Steam Linux Runtime 1.0
        "1391110",  # Steam Linux Runtime 2.0
        "1628350",  # Steam Linux Runtime 3.0
    }

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

    @staticmethod
    def _read_shortcuts(data: bytes) -> Dict[str, object]:
        def read_string(offset: int) -> Tuple[str, int]:
            end = data.index(b"\0", offset)
            return data[offset:end].decode("utf-8", errors="replace"), end + 1

        def read_object(offset: int = 0) -> Tuple[Dict[str, object], int]:
            values = {}
            while offset < len(data):
                value_type, offset = data[offset], offset + 1
                if value_type == 8:
                    return values, offset
                key, offset = read_string(offset)
                if value_type == 0:
                    value, offset = read_object(offset)
                elif value_type == 1:
                    value, offset = read_string(offset)
                elif value_type in (2, 7):
                    width = 4 if value_type == 2 else 8
                    if offset + width > len(data):
                        raise ValueError("truncated binary VDF integer")
                    value = int.from_bytes(data[offset:offset + width], "little", signed=True)
                    offset += width
                else:
                    raise ValueError(f"unsupported binary VDF type {value_type}")
                values[key] = value
            # Shortcut tools do not always write the closing markers; keep
            # every entry read so far instead of dropping the whole file.
            return values, offset

        values, _ = read_object()
        return values

    @staticmethod
    def shortcut_appid(executable: str, name: str) -> int:
        """AppID Steam derives for a shortcut that does not store one."""
        return (zlib.crc32((executable + name).encode("utf-8")) & 0xFFFFFFFF) | 0x80000000

    @classmethod
    def _shortcut_game(cls, shortcut: object) -> Optional[Dict[str, object]]:
        if not isinstance(shortcut, dict):
            return None
        # Steam writes AppName/Exe, while shortcut tools often use lowercase keys.
        fields = {str(key).lower(): value for key, value in shortcut.items()}
        name = fields.get("appname")
        if not isinstance(name, str) or not name.strip():
            return None
        name = name.strip()
        executable = fields.get("exe")
        executable = executable.strip() if isinstance(executable, str) else ""
        appid = fields.get("appid")
        if not isinstance(appid, int) or appid == 0:
            if not executable:
                return None
            appid = cls.shortcut_appid(executable, name)
        game = {
            "appid": str(appid & 0xFFFFFFFF),
            "name": name,
            "nonSteam": True,
        }
        if executable.strip('"') in {"flatpak", "/usr/bin/flatpak"}:
            game["isFlatpakShortcut"] = True
        return game

    def _shortcut_games(self):
        games = {}
        for root in self._steam_roots():
            for path in sorted((root / "userdata").glob("*/config/shortcuts.vdf")):
                try:
                    root_values = self._read_shortcuts(path.read_bytes())
                    shortcuts = root_values.get("shortcuts") or root_values.get("Shortcuts") or {}
                except (OSError, ValueError) as error:
                    self.log.warning(f"Could not read non-Steam shortcuts from {path}: {error}")
                    continue
                if not isinstance(shortcuts, dict):
                    continue
                for shortcut in shortcuts.values():
                    game = self._shortcut_game(shortcut)
                    if game and game["appid"] not in self.GAME_SELECTOR_EXCLUDED_APPIDS:
                        games.setdefault(game["appid"], game)
        return list(games.values())

    def _lossless_scaling_path(self) -> Optional[Path]:
        return next((
            path
            for root in self._steam_library_roots()
            if (path := root / "steamapps/common/Lossless Scaling").is_dir()
        ), None)

    def _manifest_path(self) -> Optional[Path]:
        return next((
            path
            for root in self._steam_library_roots()
            if (path := root / "steamapps" / self.MANIFEST_FILENAME).is_file()
        ), None)

    @staticmethod
    def _section_bounds(content: str, section_name: str) -> Optional[Tuple[int, int, str]]:
        section = re.search(
            rf'(?m)^(?P<indent>[ \t]*)"{re.escape(section_name)}"[ \t\r\n]*\{{',
            content,
        )
        if section is None:
            return None
        depth = 1
        in_string = False
        escaped = False
        for index in range(section.end(), len(content)):
            character = content[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return section.end(), index, section.group("indent")
        return None

    @classmethod
    def _section_value(cls, content: str, section_name: str, key: str) -> Optional[str]:
        bounds = cls._section_bounds(content, section_name)
        if bounds is None:
            return None
        start, end, _ = bounds
        pattern = re.compile(r'(?m)^[ \t]*"(?P<key>[^"]+)"[ \t]+"(?P<value>(?:\\.|[^"\\])*)"')
        return next((
            match.group("value")
            for match in pattern.finditer(content, start, end)
            if match.group("key") == key
        ), None)

    @classmethod
    def _branch_or_default(cls, branch: Optional[str]) -> str:
        return branch or cls.DEFAULT_BRANCH

    def _status_fields(self, manifest_path: Path, content: str) -> Dict[str, object]:
        selected = self._branch_or_default(self._section_value(content, "UserConfig", "BetaKey"))
        current = self._branch_or_default(
            self._section_value(content, "MountedConfig", "BetaKey")
            or self._section_value(content, "UserConfig", "BetaKey")
        )
        # MAKO reads Lossless.dll, which the public and lsfg-vk branches both
        # ship. Only a branch without it needs switching.
        needs_switch = self.find_lossless_dll() is None
        return {
            "installed": True,
            "manifest_path": str(manifest_path),
            "selected_branch": selected,
            "current_branch": current,
            "target_branch": STEAM_LOSSLESS_SCALING_BRANCH,
            "needs_switch": needs_switch,
            "restart_required": False,
        }

    @staticmethod
    def _missing_branch_fields() -> Dict[str, object]:
        return {
            "installed": False,
            "manifest_path": None,
            "selected_branch": None,
            "current_branch": None,
            "target_branch": STEAM_LOSSLESS_SCALING_BRANCH,
            "needs_switch": False,
            "restart_required": False,
        }

    def find_lossless_dll(self) -> Optional[str]:
        directory = self._lossless_scaling_path()
        path = directory / LOSSLESS_DLL_FILENAME if directory else None
        return str(path) if path and path.is_file() else None

    def get_branch_status(self) -> Dict[str, object]:
        try:
            if self._lossless_scaling_path() is None:
                return self._success_response(
                    dict,
                    "Lossless Scaling is not installed through Steam",
                    **self._missing_branch_fields(),
                )
            manifest = self._manifest_path()
            if manifest is None:
                fields = self._missing_branch_fields()
                fields.update(installed=True, needs_switch=self.find_lossless_dll() is None)
                return self._success_response(
                    dict,
                    "Lossless Scaling is installed but its Steam branch could not be determined",
                    **fields,
                )
            fields = self._status_fields(manifest, manifest.read_text(encoding="utf-8"))
            message = (
                f"Lossless.dll found on the {fields['selected_branch']} Steam branch"
                if not fields["needs_switch"]
                else "Lossless.dll was not found; select None in Lossless Scaling's Steam Properties > Game Versions & Betas"
            )
            return self._success_response(dict, message, **fields)
        except Exception as error:
            return self._error_response(dict, str(error), **self._missing_branch_fields())

    def get_installed_games(self) -> Dict[str, object]:
        try:
            games: Dict[str, Dict[str, object]] = {}
            for root in self._steam_library_roots():
                for manifest in (root / "steamapps").glob("appmanifest_*.acf"):
                    match = re.fullmatch(r"appmanifest_(\d+)\.acf", manifest.name)
                    if not match:
                        continue
                    try:
                        content = manifest.read_text(encoding="utf-8")
                    except OSError:
                        continue
                    appid = match.group(1)
                    if appid in self.GAME_SELECTOR_EXCLUDED_APPIDS:
                        continue
                    games[appid] = {
                        "appid": appid,
                        "name": self._section_value(content, "AppState", "name") or f"App {appid}",
                        "nonSteam": False,
                    }
            for game in self._shortcut_games():
                games.setdefault(str(game["appid"]), game)
            return self._success_response(
                dict,
                games=sorted(games.values(), key=lambda game: str(game["name"]).lower()),
            )
        except Exception as error:
            return self._error_response(dict, str(error), games=[])
