import json
import subprocess
import tarfile
import tempfile
import traceback
from pathlib import Path, PurePosixPath

from .base_service import BaseService
from .config_schema import ConfigurationManager, ProfileData, UnsupportedConfigurationVersion
from .constants import (
    ARCHIVE_INSTALLER,
    INSTALLER_FILENAME,
    INSTALLER_STATE,
    LAYER_MANIFEST,
    LAYER_MANIFEST_X86,
    LIB_FILENAME,
    OWNERSHIP_FILENAME,
)
from .runtime_service import RuntimeService
from .steam_service import SteamService
from .types import InstallationCheckResponse, InstallationResponse, UninstallationResponse


class InstallationService(BaseService):
    INSTALLER_TIMEOUT_SECONDS = 180

    def __init__(
        self,
        logger=None,
        runtime_service: RuntimeService = None,
        steam_service: SteamService = None,
    ):
        super().__init__(logger)
        self.runtime_service = runtime_service or RuntimeService(logger=self.log)
        self.steam_service = steam_service or SteamService(logger=self.log)
        self.ownership_path = self.config_dir / OWNERSHIP_FILENAME
        self.installer_state_path = self.install_prefix / INSTALLER_STATE
        self.installed_installer_path = self.local_bin_dir / INSTALLER_FILENAME

    def _renderer_files(self) -> tuple[Path, ...]:
        return (
            self.launcher_path,
            self.cli_path,
            self.local_lib_dir / LIB_FILENAME,
            self.install_prefix / "lib32" / LIB_FILENAME,
            self.install_prefix / LAYER_MANIFEST,
            self.install_prefix / LAYER_MANIFEST_X86,
        )

    def _renderer_installed(self) -> bool:
        return all(path.is_file() for path in self._renderer_files())

    def install(self, archive_path: Path) -> InstallationResponse:
        """Install (or update to) the renderer in archive_path, a MAKO Renderer linux .tar.xz."""
        try:
            if not archive_path.exists():
                raise FileNotFoundError(f"MAKO Renderer archive not found at {archive_path}")
            self._ensure_directories()
            profile_data = self._prepare_config()
            installed_by_plugin = self._installed_by_plugin()
            if installed_by_plugin is None:
                # Only an installation created here is removed on uninstall;
                # a Renderer shared with MAKO Decky or a standalone setup stays.
                installed_by_plugin = not (
                    self.installer_state_path.exists() or self._renderer_installed()
                )
            self._install_renderer(archive_path)
            content = ConfigurationManager.generate_toml_content_multi_profile(profile_data)
            self.runtime_service.validate_config_content(content)
            self._write_file(self.config_file_path, content, 0o644)
            self._write_file(
                self.ownership_path,
                json.dumps({"version": 1, "installed_renderer": installed_by_plugin}) + "\n",
            )
            return self._success_response(
                InstallationResponse,
                "MAKO Renderer installed successfully",
            )
        except Exception as error:
            self.log.error(f"Error installing MAKO Renderer: {error}")
            return self._error_response(InstallationResponse, str(error))

    @staticmethod
    def _safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
        members = []
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe path in renderer archive: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsupported entry in renderer archive: {member.name}")
            members.append(member)
        return members

    def _install_renderer(self, archive_path: Path) -> None:
        with tempfile.TemporaryDirectory(prefix="jedi-lsfg-mako-") as staging:
            with tarfile.open(archive_path, "r:*") as archive:
                members = self._safe_members(archive)
                if hasattr(tarfile, "data_filter"):
                    archive.extractall(staging, members=members, filter="data")
                else:
                    archive.extractall(staging, members=members)
            installer = Path(staging) / ARCHIVE_INSTALLER
            if not installer.is_file():
                raise OSError(f"Renderer archive is missing '{ARCHIVE_INSTALLER}'")
            self._run_installer(installer, "--install")
        if not self._renderer_installed():
            missing = [str(path) for path in self._renderer_files() if not path.is_file()]
            raise OSError("MAKO Renderer installation is incomplete: " + ", ".join(missing))

    def _run_installer(self, installer: Path, *arguments: str) -> None:
        environment = self._host_environment()
        for name in ("DISPLAY", "WAYLAND_DISPLAY"):
            environment.pop(name, None)
        environment.update(
            MAKO_INSTALL_PREFIX=str(self.install_prefix),
            MAKO_INSTALLER_ASSUME_YES="1",
            MAKO_INSTALLER_NO_LAUNCH="1",
        )
        result = subprocess.run(
            ["bash", str(installer), *arguments],
            cwd=str(self.user_home),
            env=environment,
            capture_output=True,
            text=True,
            timeout=self.INSTALLER_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode != 0:
            output = (result.stderr or result.stdout or "").strip()
            raise OSError(output or f"MAKO installer exited with status {result.returncode}")

    def _installed_by_plugin(self):
        try:
            data = json.loads(self.ownership_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        value = data.get("installed_renderer") if isinstance(data, dict) else None
        return value if isinstance(value, bool) else None

    def _default_config(self) -> ProfileData:
        defaults = ConfigurationManager.get_defaults()
        return ProfileData(
            profiles={},
            global_config={"dll": defaults["dll"], "no_fp16": defaults["no_fp16"]},
        )

    def _prepare_config(self) -> ProfileData:
        try:
            profile_data = (
                ConfigurationManager.parse_toml_content_multi_profile(
                    self.config_file_path.read_text(encoding="utf-8")
                )
                if self.config_file_path.exists()
                else self._default_config()
            )
        except UnsupportedConfigurationVersion as error:
            if not ConfigurationManager.is_discardable_legacy_version(error.version):
                raise
            self._remove_if_exists(self.config_file_path)
            self.log.warning(
                f"Removed legacy configuration version {error.version!r} during installation"
            )
            profile_data = self._default_config()
        except ValueError:
            profile_data = self._default_config()
        self._resolve_dll_path(profile_data)
        defaults = ConfigurationManager.get_defaults()
        for name, profile in profile_data["profiles"].items():
            profile_data["profiles"][name] = ConfigurationManager.validate_config(
                {**defaults, **profile, **profile_data["global_config"]}
            )
        return profile_data

    def _resolve_dll_path(self, profile_data: ProfileData) -> bool:
        current_path = str(profile_data["global_config"].get("dll") or "")
        if current_path and Path(current_path).is_file():
            return False
        dll_path = self.steam_service.find_lossless_dll()
        if dll_path and current_path != dll_path:
            profile_data["global_config"]["dll"] = dll_path
            return True
        return False

    def refresh_config(self) -> None:
        """Rewrite conf.toml when the derived policy or Lossless.dll path changed.

        MAKO reads the file directly, so a profile saved by an older version
        keeps its old policy (and any target now below the minimum) until it
        is rendered again.
        """
        if not self._renderer_installed() or not self.config_file_path.is_file():
            return
        try:
            current = self.config_file_path.read_text(encoding="utf-8")
            profile_data = ConfigurationManager.parse_toml_content_multi_profile(current)
            dll_path = self.steam_service.find_lossless_dll()
            if dll_path:
                profile_data["global_config"]["dll"] = dll_path
            content = ConfigurationManager.generate_toml_content_multi_profile(profile_data)
            if content == current:
                return
            self.runtime_service.validate_config_content(content)
            self._write_file(self.config_file_path, content, 0o644)
            self.log.info("Refreshed MAKO configuration")
        except Exception as error:
            self.log.warning(f"Could not refresh MAKO configuration: {error}")

    def check_installation(self) -> InstallationCheckResponse:
        try:
            installed = self._renderer_installed() and self.config_file_path.is_file()
            self.refresh_config()
            lossless_scaling = self.runtime_service.check_lossless_scaling()
            return {
                "installed": installed,
                "lossless_scaling_installed": bool(lossless_scaling["installed"]),
                "lossless_scaling_status": str(lossless_scaling["status"]),
                "error": None,
            }
        except Exception as error:
            return {
                "installed": False,
                "lossless_scaling_installed": False,
                "lossless_scaling_status": str(error),
                "error": str(error),
            }

    def uninstall(self) -> UninstallationResponse:
        try:
            removed = []
            if (
                self._installed_by_plugin()
                and self.installer_state_path.is_file()
                and self.installed_installer_path.is_file()
            ):
                self._run_installer(self.installed_installer_path, "--uninstall")
                removed.append("MAKO Renderer")
            for path in (self.config_file_path, self.ownership_path):
                if self._remove_if_exists(path):
                    removed.append(str(path))
            try:
                self.config_dir.rmdir()
            except OSError:
                pass
            if not removed:
                return self._success_response(
                    UninstallationResponse,
                    "No plugin files found to remove",
                    removed_files=None,
                )
            return self._success_response(
                UninstallationResponse,
                f"Uninstalled successfully. Removed {len(removed)} items.",
                removed_files=removed,
            )
        except Exception as error:
            return self._error_response(
                UninstallationResponse,
                str(error),
                removed_files=None,
            )

    def cleanup_on_uninstall(self) -> bool:
        try:
            result = self.uninstall()
            if not result.get("success"):
                self.log.error(f"Error cleaning up files during uninstall: {result.get('error')}")
                return False
            return True
        except Exception as error:
            self.log.error(f"Error cleaning up files during uninstall: {error}")
            self.log.error(traceback.format_exc())
            return False
