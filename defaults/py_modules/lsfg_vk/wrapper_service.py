from __future__ import annotations

import json
import re
import shlex
import threading
from typing import Any, Dict, Optional, Tuple

from .base_service import BaseService
from .configuration import ConfigurationService
from .constants import COMPETING_LSFG_DISABLE_ENVS, WRAPPER_FILENAME


class WrapperService(BaseService):
    FORMAT_VERSION = 1
    MARKER = "# jedi-lsfg-wrapper-format: 1"
    WRAPPER_TOKEN = f"~/{WRAPPER_FILENAME}"
    # dxvkFrameRate, disableGamescopeWsi, disableHdr and disableVkbasalt are
    # kept for state compatibility only: the plugin never caps real frames, and
    # mako-launch always owns Gamescope WSI, HDR exposure and vkBasalt.
    STATE_FIELDS = (
        "dxvkFrameRate",
        "disableGamescopeWsi",
        "disableHdr",
        "disableSteamdeckMode",
        "disableVkbasalt",
        "enableZink",
    )
    BOOLEAN_FIELDS = STATE_FIELDS[1:]
    MANAGED_ENV_KEYS = (
        "MAKO_CONFIG",
        "MAKO_ENV",
        "MAKO_PROFILE",
        "MAKO_PROFILE_FALLBACK",
        "MESA_LOADER_DRIVER_OVERRIDE",
        "__GLX_VENDOR_LIBRARY_NAME",
        "GALLIUM_DRIVER",
    )

    def __init__(self, logger=None):
        super().__init__(logger)
        self.sidecar_path = self.config_dir / "workarounds.json"
        self.wrapper_path = self.user_home / WRAPPER_FILENAME
        self._lock = threading.RLock()

    @classmethod
    def default_state(cls) -> Dict[str, Any]:
        return {
            "dxvkFrameRate": 0,
            "disableGamescopeWsi": True,
            "disableHdr": True,
            "disableSteamdeckMode": False,
            "disableVkbasalt": False,
            "enableZink": False,
        }

    @staticmethod
    def _valid_appid(appid: Any) -> str:
        value = str(appid)
        if not re.fullmatch(r"[1-9][0-9]*", value):
            raise ValueError("Invalid Steam App ID")
        return value

    @classmethod
    def _validate_state(cls, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Workaround state must be an object")
        missing = [field for field in cls.STATE_FIELDS if field not in raw]
        if missing:
            raise ValueError("Workaround state is missing: " + ", ".join(missing))
        state = {field: raw[field] for field in cls.STATE_FIELDS}
        frame_rate = state["dxvkFrameRate"]
        if isinstance(frame_rate, bool) or not isinstance(frame_rate, int) or not 0 <= frame_rate <= 60:
            raise ValueError("Base FPS Cap must be an integer from 0 to 60")
        for field in cls.BOOLEAN_FIELDS:
            if type(state[field]) is not bool:
                raise ValueError(f"{field} must be a boolean")
        return state

    @classmethod
    def _validate_entry(cls, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Workaround AppID entry must be an object")
        entry = {
            "state": cls._validate_state(raw.get("state")),
            "command_token_added": raw.get("command_token_added", False),
            "non_steam": raw.get("non_steam", False),
        }
        if type(entry["command_token_added"]) is not bool:
            raise ValueError("command_token_added must be a boolean")
        if type(entry["non_steam"]) is not bool:
            raise ValueError("non_steam must be a boolean")
        return entry

    @classmethod
    def _validate_document(cls, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict) or raw.get("version") != cls.FORMAT_VERSION:
            raise ValueError("Unsupported workaround state version")
        apps = raw.get("apps")
        if not isinstance(apps, dict):
            raise ValueError("Workaround state apps must be an object")
        validated_apps: Dict[str, Any] = {}
        for appid, entry in apps.items():
            normalized = cls._valid_appid(appid)
            if normalized != str(appid):
                raise ValueError("Workaround AppIDs must not contain leading zeroes")
            validated_apps[normalized] = cls._validate_entry(entry)
        return {"version": cls.FORMAT_VERSION, "apps": validated_apps}

    def _empty_document(self) -> Dict[str, Any]:
        return {"version": self.FORMAT_VERSION, "apps": {}}

    def _read_document(self) -> Tuple[Dict[str, Any], bool, Optional[str]]:
        if not self.sidecar_path.exists():
            return self._empty_document(), False, None
        if self.sidecar_path.is_symlink() or not self.sidecar_path.is_file():
            raise RuntimeError("Workaround state path is not a regular file")
        try:
            content = self.sidecar_path.read_text(encoding="utf-8")
            raw = json.loads(content)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not read workaround state: {error}") from error
        return self._validate_document(raw), True, content

    def _wrapper_marker(self) -> bool:
        if self.wrapper_path.is_symlink() or not self.wrapper_path.exists():
            return False
        if not self.wrapper_path.is_file():
            raise RuntimeError("Launch wrapper path is not a regular file")
        try:
            prefix = "\n".join(self.wrapper_path.read_text(encoding="utf-8").splitlines()[:8])
        except OSError as error:
            raise RuntimeError(f"Could not read launch wrapper: {error}") from error
        return self.MARKER in prefix

    def _assert_wrapper_owned_or_absent(self) -> bool:
        if not self.wrapper_path.exists() and not self.wrapper_path.is_symlink():
            return False
        if self.wrapper_path.is_symlink() or not self._wrapper_marker():
            raise RuntimeError(f"Refusing to replace unowned wrapper at {self.wrapper_path}")
        return True

    @staticmethod
    def _shell(value: str) -> str:
        return shlex.quote(value)

    def _state_lines(self, appid: str, state: Dict[str, Any]) -> list[str]:
        lines = ["    unset " + " ".join(self.MANAGED_ENV_KEYS)]
        lines.extend([
            '    SteamAppId="$appid"',
            "    export SteamAppId",
            f"    MAKO_CONFIG={self._shell(str(self.config_file_path))}",
            "    export MAKO_CONFIG",
            f"    MAKO_PROFILE={self._shell(ConfigurationService.game_profile_name(appid))}",
            "    export MAKO_PROFILE",
        ])
        # A second frame generation layer on the same swapchain breaks MAKO.
        for name in COMPETING_LSFG_DISABLE_ENVS:
            lines.extend([f"    {name}=1", f"    export {name}"])
        lines.append("    use_mako=1")
        if state["disableSteamdeckMode"]:
            lines.extend(["    SteamDeck=0", "    export SteamDeck"])
        if state["enableZink"]:
            lines.extend([
                "    __GLX_VENDOR_LIBRARY_NAME=mesa",
                "    export __GLX_VENDOR_LIBRARY_NAME",
                "    MESA_LOADER_DRIVER_OVERRIDE=zink",
                "    export MESA_LOADER_DRIVER_OVERRIDE",
                "    GALLIUM_DRIVER=zink",
                "    export GALLIUM_DRIVER",
            ])
        return lines

    @staticmethod
    def _game_ids(appid: str) -> list[str]:
        """Values Steam may export for an AppID.

        A shortcut's 64-bit GameID keeps its AppID in the upper half and the
        shortcut type in the lower half; some launch paths, and UMU, export
        only that form.
        """
        value = int(appid)
        return [appid, str((value << 32) | 0x02000000)] if value & 0x80000000 else [appid]

    def _render_wrapper(self, document: Dict[str, Any]) -> str:
        launcher = self._shell(str(self.launcher_path))
        appids = sorted(document["apps"], key=lambda value: int(value))
        lines = [
            "#!/bin/sh",
            self.MARKER,
            "",
            "appid=",
            "use_mako=",
            # Steam does not fill these the same way for every launch path, so
            # take the first one that names an enabled game.
            'for candidate in "${SteamAppId-}" "${SteamGameId-}" "${STEAM_COMPAT_APP_ID-}" "${UMU_STEAM_GAME_ID-}"; do',
            '  case "$candidate" in',
        ]
        for appid in appids:
            lines.append(f"    {'|'.join(self._game_ids(appid))}) appid={appid} ;;")
        lines.extend([
            "  esac",
            '  if [ -n "$appid" ]; then break; fi',
            "done",
            'case "$appid" in',
        ])
        for appid in appids:
            lines.append(f"  {appid})")
            lines.extend(self._state_lines(appid, document["apps"][appid]["state"]))
            lines.append("    ;;")
        lines.extend([
            "esac",
            "# A missing Renderer must never stop the game from starting.",
            f'if [ -n "$use_mako" ] && [ -x {launcher} ]; then',
            f'  exec {launcher} "$@"',
            "fi",
            'exec "$@"',
            "",
        ])
        return "\n".join(lines)

    def _write_document(self, document: Dict[str, Any]) -> None:
        self._write_file(
            self.sidecar_path,
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            0o644,
        )

    def _write_pair(self, document: Dict[str, Any]) -> None:
        old_sidecar_exists = self.sidecar_path.exists()
        old_sidecar = self.sidecar_path.read_text(encoding="utf-8") if old_sidecar_exists else None
        old_wrapper_exists = self.wrapper_path.exists() or self.wrapper_path.is_symlink()
        old_wrapper = self.wrapper_path.read_text(encoding="utf-8") if old_wrapper_exists and not self.wrapper_path.is_symlink() else None
        try:
            self._write_document(document)
            self._write_file(self.wrapper_path, self._render_wrapper(document), 0o755)
        except Exception:
            try:
                if old_sidecar_exists and old_sidecar is not None:
                    self._write_file(self.sidecar_path, old_sidecar, 0o644)
                elif self.sidecar_path.exists():
                    self.sidecar_path.unlink()
                if old_wrapper_exists and old_wrapper is not None:
                    self._write_file(self.wrapper_path, old_wrapper, 0o755)
                elif not old_wrapper_exists and self.wrapper_path.exists():
                    self.wrapper_path.unlink()
            except Exception as rollback_error:
                self.log.error(f"Could not roll back workaround wrapper update: {rollback_error}")
            raise

    def _response(self, document: Dict[str, Any], appid: str = "") -> Dict[str, Any]:
        entry = document["apps"].get(appid)
        return {
            "success": True,
            "message": "",
            "error": None,
            "appid": appid or None,
            "state": dict(entry["state"]) if entry else None,
            "wrapper_path": self.WRAPPER_TOKEN,
            "wrapper_owned": self._wrapper_marker() if document["apps"] else False,
            "command_token_added": entry.get("command_token_added", False) if entry else False,
            "non_steam": entry.get("non_steam", False) if entry else False,
        }

    def get(self, appid: str) -> Dict[str, Any]:
        try:
            normalized = self._valid_appid(appid)
            with self._lock:
                document, _, _ = self._read_document()
                self._assert_wrapper_owned_or_absent()
                return self._response(document, normalized)
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "appid": str(appid),
                "state": None,
                "wrapper_path": self.WRAPPER_TOKEN,
                "wrapper_owned": False,
                "non_steam": False,
            }

    def set(
        self,
        appid: str,
        state: Dict[str, Any],
        command_token_added: bool = False,
        non_steam: bool = False,
    ) -> Dict[str, Any]:
        try:
            normalized = self._valid_appid(appid)
            validated_state = self._validate_state(state)
            if type(command_token_added) is not bool:
                raise ValueError("command_token_added must be a boolean")
            if type(non_steam) is not bool:
                raise ValueError("non_steam must be a boolean")
            with self._lock:
                self._assert_wrapper_owned_or_absent()
                document, _, _ = self._read_document()
                document["apps"][normalized] = {
                    "state": validated_state,
                    "command_token_added": command_token_added,
                    "non_steam": non_steam,
                }
                self._write_pair(document)
                return self._response(document, normalized)
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "appid": str(appid),
                "state": None,
                "wrapper_path": self.WRAPPER_TOKEN,
                "wrapper_owned": False,
                "non_steam": False,
            }

    def remove(self, appid: str) -> Dict[str, Any]:
        try:
            normalized = self._valid_appid(appid)
            with self._lock:
                document, _, _ = self._read_document()
                self._assert_wrapper_owned_or_absent()
                if normalized not in document["apps"]:
                    return self._response(document, normalized)
                document["apps"].pop(normalized, None)
                self._write_pair(document)
                return self._response(document, normalized)
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "appid": str(appid),
                "state": None,
                "wrapper_path": self.WRAPPER_TOKEN,
                "wrapper_owned": False,
                "non_steam": False,
            }

    def repair(self) -> Dict[str, Any]:
        try:
            with self._lock:
                document, _, _ = self._read_document()
                self._assert_wrapper_owned_or_absent()
                if not document["apps"]:
                    return self._response(document)
                self._write_file(self.wrapper_path, self._render_wrapper(document), 0o755)
                return self._response(document)
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "wrapper_path": self.WRAPPER_TOKEN,
                "wrapper_owned": False,
            }

    def list_apps(self) -> Dict[str, Any]:
        try:
            with self._lock:
                document, _, _ = self._read_document()
                self._assert_wrapper_owned_or_absent()
                apps = [
                    {
                        "appid": appid,
                        "non_steam": entry.get("non_steam", False),
                        "command_token_added": entry.get("command_token_added", False),
                    }
                    for appid, entry in document["apps"].items()
                ]
                return {
                    "success": True,
                    "message": "",
                    "error": None,
                    "apps": apps,
                    "wrapper_path": self.WRAPPER_TOKEN,
                }
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "apps": [],
                "wrapper_path": self.WRAPPER_TOKEN,
            }

    def purge(self) -> Dict[str, Any]:
        """Remove the plugin-owned wrapper and its sidecar during uninstall.

        This is deliberately separate from ``remove``: normal profile removal
        leaves a safe passthrough wrapper for the remaining profiles, while an
        uninstall should remove the wrapper entirely.  Both files are
        validated before anything is removed so a user's replacement wrapper
        or damaged state is left untouched.
        """
        removed = []
        try:
            with self._lock:
                _document, sidecar_exists, _ = self._read_document()
                wrapper_owned = self._assert_wrapper_owned_or_absent()
                if wrapper_owned:
                    self.wrapper_path.unlink()
                    removed.append(str(self.wrapper_path))
                if sidecar_exists:
                    self.sidecar_path.unlink()
                    removed.append(str(self.sidecar_path))
            return {
                "success": True,
                "message": "Removed workaround state",
                "error": None,
                "removed_files": removed,
            }
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "removed_files": removed or None,
            }

    def neutralize(self) -> Dict[str, Any]:
        """Leave an owned passthrough wrapper for Decky-level uninstall.

        Decky can remove this plugin without giving the frontend a chance to
        clean Steam launch options first.  Keeping a dependency-free wrapper
        prevents those options from turning into a broken executable path.
        """
        try:
            with self._lock:
                _document, sidecar_exists, _ = self._read_document()
                self._assert_wrapper_owned_or_absent()
                self._write_file(
                    self.wrapper_path,
                    "#!/bin/sh\n"
                    f"{self.MARKER}\n"
                    "# Safe passthrough retained for existing Steam launch options.\n"
                    "exec \"$@\"\n",
                    0o755,
                )
                if sidecar_exists:
                    self.sidecar_path.unlink()
            return {
                "success": True,
                "message": "Replaced launch wrapper with a safe passthrough",
                "error": None,
                "removed_files": [str(self.sidecar_path)] if sidecar_exists else [],
            }
        except Exception as error:
            return {
                "success": False,
                "message": "",
                "error": str(error),
                "removed_files": None,
            }
