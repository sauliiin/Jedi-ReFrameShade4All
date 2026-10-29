import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar

import decky

from .constants import (
    CLI_FILENAME,
    CONFIG_DIR,
    CONFIG_FILENAME,
    LAUNCHER_FILENAME,
    LOCAL_BIN,
    LOCAL_LIB,
    LOCAL_PREFIX,
)

ResponseType = TypeVar("ResponseType", bound=Dict[str, Any])


class BaseService:
    def __init__(self, logger: Optional[Any] = None):
        self.log = decky.logger if logger is None else logger
        decky_user_home = getattr(decky, "DECKY_USER_HOME", None)
        self.user_home = Path(decky_user_home) if decky_user_home else Path.home()
        self.install_prefix = self.user_home / LOCAL_PREFIX
        self.local_bin_dir = self.user_home / LOCAL_BIN
        self.local_lib_dir = self.user_home / LOCAL_LIB
        self.launcher_path = self.local_bin_dir / LAUNCHER_FILENAME
        self.cli_path = self.local_bin_dir / CLI_FILENAME
        self.config_dir = self.user_home / CONFIG_DIR
        self.config_file_path = self.config_dir / CONFIG_FILENAME

    def _ensure_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _remove_if_exists(self, path: Path) -> bool:
        if not path.exists() and not path.is_symlink():
            return False
        path.unlink()
        self.log.info(f"Removed {path}")
        return True

    def _write_file(self, path: Path, content: str, mode: int = 0o644) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.chmod(mode)
            os.replace(temporary_path, path)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    def _host_environment(self) -> Dict[str, str]:
        """Environment for host tools, without Decky's bundled libraries."""
        environment = os.environ.copy()
        environment.pop("LD_LIBRARY_PATH", None)
        environment.update(
            HOME=str(self.user_home),
            XDG_CONFIG_HOME=str(self.user_home / ".config"),
        )
        path = [entry for entry in environment.get("PATH", "").split(":") if entry]
        for entry in ("/usr/bin", "/usr/local/bin", "/bin"):
            if entry not in path:
                path.insert(0, entry)
        environment["PATH"] = ":".join(path)
        return environment

    def _success_response(self, response_type: type, message: str = "", **kwargs) -> Any:
        response = {"success": True, "message": message, "error": None}
        response.update(kwargs)
        return response

    def _error_response(self, response_type: type, error: str, message: str = "", **kwargs) -> Any:
        response = {"success": False, "message": message, "error": error}
        response.update(kwargs)
        return response
