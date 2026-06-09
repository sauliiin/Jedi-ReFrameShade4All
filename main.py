import decky
import os
import subprocess
import json
import shutil
import re
import filecmp
import hashlib
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OPTISCALER_ARCHIVE_ASSET = {
    "name": "Optiscaler_0.9.2a-final.20260517._Reup.7z",
    "sha256": "6426a16085f6128c810e0de58947029664439afd0567b6a286c0e3ef784a92a1",
    "version": "0.9.2a-final.20260517._Reup",
}

FSR4_INT8_ASSET = {
    "name": "amd_fidelityfx_upscaler_dx12.dll",
    "sha256": "c7720bc16bede334f59a1a32cd22edbcbbb159685ed5240e61350a5fb0bc8a94",
    "version": "4.0.2c",
}

OPTIPATCHER_ASSET = {
    "name": "OptiPatcher_rolling.asi",
    "sha256": "88b9e1be3559737cd205fdf5f2c8550cf1923fb1def4c603e5bf03c3e84131b1",
    "version": "rolling",
}

FSR4_UPSCALER_FILENAME = "amd_fidelityfx_upscaler_dx12.dll"
INSTALL_MANIFEST_FILENAME = "install-manifest.json"
VERSION_FILENAME = "version.txt"
DEFAULT_FSR4_VARIANT = "rdna23-int8"

FSR4_VARIANTS = {
    "rdna23-int8": {
        "label": "Steam Deck / RDNA2-3 optimized",
        "dir_name": "fsr4-rdna2-3",
        "sha256": "c7720bc16bede334f59a1a32cd22edbcbbb159685ed5240e61350a5fb0bc8a94",
        "source_asset_name": FSR4_INT8_ASSET["name"],
        "source_version": FSR4_INT8_ASSET["version"],
        "uses_archive_native": False,
    },
    "rdna4-native": {
        "label": "Native bundle / RDNA4",
        "dir_name": "fsr4-rdna4",
        "sha256": "ec7ed3ca674e288240e6f04b986342aece47454c41d9b0959449e82e22bd7f6d",
        "source_asset_name": OPTISCALER_ARCHIVE_ASSET["name"],
        "source_version": OPTISCALER_ARCHIVE_ASSET["version"],
        "uses_archive_native": True,
    },
}
FSR4_VARIANT_BY_SHA256 = {
    variant["sha256"].lower(): variant_id
    for variant_id, variant in FSR4_VARIANTS.items()
    if variant.get("sha256")
}

# OptiScaler auto-update: fetch the newest release archive from GitHub, falling back
# to the bundled, hash-verified OPTISCALER_ARCHIVE_ASSET when offline/unavailable.
OPTISCALER_LATEST_RELEASE_API = "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest"
OPTISCALER_RELEASES_API = "https://api.github.com/repos/optiscaler/OptiScaler/releases"
OPTISCALER_ASSET_NAME_RE = re.compile(r"OptiScaler.*\.7z$|Optiscaler.*\.7z$", re.IGNORECASE)
OPTISCALER_DOWNLOAD_TIMEOUT = 45
OPTISCALER_LATEST_CACHE_SECONDS = 900

PROXY_DLL_BACKUPS = [
    "dxgi.dll",
    "winmm.dll",
    "dbghelp.dll",
    "version.dll",
    "wininet.dll",
    "winhttp.dll",
    "OptiScaler.asi",
]

VALID_DLL_NAMES = set(PROXY_DLL_BACKUPS)

INJECTOR_FILENAMES = [
    *PROXY_DLL_BACKUPS,
    "nvngx.dll",
    "_nvngx.dll",
    "nvngx-wrapper.dll",
    "dlss-enabler.dll",
    "OptiScaler.dll",
]

PATCH_CLEANUP_FILES = [
    *INJECTOR_FILENAMES,
    "nvapi64.dll",
    "nvapi64.dll.b",
    "nvngx.ini",
    "dlss-enabler-upscaler.dll",
    "fakenvapi.log",
    "OptiScaler.log",
    "dlssg_to_fsr3.log",
    "dlssg_to_fsr3_amd_is_better-3.0.dll",
]

PATCH_FINGERPRINT_FILES = [
    "FRAMEGEN_PATCH",
    "OptiScaler.ini",
    "fakenvapi.dll",
    "fakenvapi.ini",
    "dlssg_to_fsr3_amd_is_better.dll",
    "D3D12_Optiscaler",
]

ORIGINAL_DLL_BACKUPS = [
    "d3dcompiler_47.dll",
    "amd_fidelityfx_dx12.dll",
    "amd_fidelityfx_framegeneration_dx12.dll",
    FSR4_UPSCALER_FILENAME,
    "amd_fidelityfx_vk.dll",
]

RESTORABLE_BACKUP_FILES = [
    *PROXY_DLL_BACKUPS,
    *ORIGINAL_DLL_BACKUPS,
]

SUPPORT_FILES = [
    "libxess.dll",
    "libxess_dx11.dll",
    "libxess_fg.dll",
    "libxell.dll",
    "amd_fidelityfx_dx12.dll",
    "amd_fidelityfx_framegeneration_dx12.dll",
    "amd_fidelityfx_vk.dll",
    "dlssg_to_fsr3_amd_is_better.dll",
    "fakenvapi.dll",
    "fakenvapi.ini",
]

MARKER_FILENAME = "FRAMEGEN_PATCH"

BAD_EXE_SUBSTRINGS = [
    "crashreport",
    "crashreportclient",
    "eac",
    "easyanticheat",
    "beclient",
    "eosbootstrap",
    "benchmark",
    "uninstall",
    "setup",
    "launcher",
    "updater",
    "bootstrap",
    "_redist",
    "prereq",
]

LEGACY_FILES = [
    "dlssg_to_fsr3.ini",
    "dlssg_to_fsr3.log",
    "nvapi64.dll",
    "nvapi64.dll.b",
    "fakenvapi.log",
    "dlss-enabler.dll",
    "dlss-enabler-upscaler.dll",
    "dlss-enabler.log",
    "nvngx.ini",
    "nvngx-wrapper.dll",
    "_nvngx.dll",
    "dlssg_to_fsr3_amd_is_better-3.0.dll",
    "OptiScaler.asi",
    "OptiScaler.ini",
    "OptiScaler.log",
]


# --- extra imports required by the ReShade backend ---
import ssl
import glob
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


# ===== OptiScaler / Frame Generation backend =====
class _OptiScalerMixin:
    _latest_optiscaler_release_cache = None

    def _create_renamed_copies(self, source_file, renames_dir):
        """Create renamed copies of the OptiScaler.dll file"""
        try:
            renames_dir.mkdir(exist_ok=True)
            
            rename_files = [
                "dxgi.dll",
                "winmm.dll",
                "dbghelp.dll",
                "version.dll",
                "wininet.dll",
                "winhttp.dll",
                "OptiScaler.asi"
            ]
            
            if source_file.exists():
                for rename_file in rename_files:
                    dest_file = renames_dir / rename_file
                    shutil.copy2(source_file, dest_file)
                    decky.logger.info(f"Created renamed copy: {dest_file}")
                return True
            else:
                decky.logger.error(f"Source file {source_file} does not exist")
                return False
                
        except Exception as e:
            decky.logger.error(f"Failed to create renamed copies: {e}")
            return False
    
    def _copy_launcher_scripts(self, assets_dir, extract_path):
        """Copy launcher scripts from assets directory"""
        try:
            # Copy fgmod script
            fgmod_script_src = assets_dir / "fgmod.sh"
            fgmod_script_dest = extract_path / "fgmod"
            if fgmod_script_src.exists():
                shutil.copy2(fgmod_script_src, fgmod_script_dest)
                fgmod_script_dest.chmod(0o755)
                decky.logger.info(f"Copied fgmod script to {fgmod_script_dest}")
            
            # Copy uninstaller script
            uninstaller_src = assets_dir / "fgmod-uninstaller.sh"
            uninstaller_dest = extract_path / "fgmod-uninstaller.sh"
            if uninstaller_src.exists():
                shutil.copy2(uninstaller_src, uninstaller_dest)
                uninstaller_dest.chmod(0o755)
                decky.logger.info(f"Copied uninstaller script to {uninstaller_dest}")

            # Copy optiscaler config updater script
            optiscaler_config_updater_src = assets_dir / "update-optiscaler-config.py"
            optiscaler_config_updater_dest = extract_path / "update-optiscaler-config.py"
            if optiscaler_config_updater_src.exists():
                shutil.copy2(optiscaler_config_updater_src, optiscaler_config_updater_dest)
                optiscaler_config_updater_dest.chmod(0o755)
                decky.logger.info(f"Copied update-optiscaler-config.py script to {optiscaler_config_updater_dest}")
                
            return True
        except Exception as e:
            decky.logger.error(f"Failed to copy launcher scripts: {e}")
            return False
    
    def _files_match(self, file_a: Path, file_b: Path) -> bool:
        try:
            return file_a.exists() and file_b.exists() and filecmp.cmp(file_a, file_b, shallow=False)
        except Exception:
            return False

    def _is_bundled_proxy_copy(self, file_path: Path, fgmod_path: Path) -> bool:
        bundled_copy = fgmod_path / "renames" / file_path.name
        return self._files_match(file_path, bundled_copy)

    def _has_patch_fingerprint(self, directory: Path) -> bool:
        return any((directory / filename).exists() for filename in PATCH_FINGERPRINT_FILES)

    def _backup_preexisting_proxy_files(self, directory: Path, fgmod_path: Path) -> list[str]:
        backed_up: list[str] = []
        already_patched = self._has_patch_fingerprint(directory)
        for filename in PROXY_DLL_BACKUPS:
            source = directory / filename
            backup = directory / f"{filename}.b"
            if not source.exists() or backup.exists():
                continue
            if already_patched or self._is_bundled_proxy_copy(source, fgmod_path):
                continue
            shutil.move(source, backup)
            backed_up.append(filename)
        return backed_up

    def _file_sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _read_json_file(self, path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_json_file(self, path: Path, payload: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _extract_archive(self, archive_path: Path, output_dir: Path, members: list[str] | None = None) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        extract_cmd = [
            "7z",
            "x",
            "-y",
            "-o" + str(output_dir),
            str(archive_path),
        ]
        if members:
            extract_cmd.extend(members)

        clean_env = os.environ.copy()
        clean_env["LD_LIBRARY_PATH"] = ""
        result = subprocess.run(
            extract_cmd,
            capture_output=True,
            text=True,
            check=False,
            env=clean_env,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or f"Failed to extract {archive_path.name}")

    def _verify_bundled_asset(self, path: Path, expected_sha256: str, description: str) -> str:
        actual_sha256 = self._file_sha256(path)
        if actual_sha256.lower() != expected_sha256.lower():
            raise RuntimeError(
                f"{description} hash mismatch: expected {expected_sha256}, got {actual_sha256}"
            )
        return actual_sha256

    def _install_manifest_path(self, fgmod_path: Path) -> Path:
        return fgmod_path / INSTALL_MANIFEST_FILENAME

    def _load_install_manifest(self, fgmod_path: Path) -> dict:
        return self._read_json_file(self._install_manifest_path(fgmod_path))

    def _normalize_fsr4_variant(self, fsr4_variant: str | None) -> str:
        variant = str(fsr4_variant or "").strip()
        if variant in FSR4_VARIANTS:
            return variant
        return DEFAULT_FSR4_VARIANT

    def _selected_fsr4_variant(self, fgmod_path: Path, requested_variant: str | None = None) -> str:
        normalized_requested = str(requested_variant or "").strip()
        if normalized_requested in FSR4_VARIANTS:
            return normalized_requested
        manifest = self._load_install_manifest(fgmod_path)
        manifest_variant = str(manifest.get("selected_default_variant") or "").strip()
        if manifest_variant in FSR4_VARIANTS:
            return manifest_variant
        return DEFAULT_FSR4_VARIANT

    def _fsr4_variant_info(self, fsr4_variant: str | None) -> dict:
        return FSR4_VARIANTS[self._normalize_fsr4_variant(fsr4_variant)]

    def _fsr4_variant_path(self, fgmod_path: Path, fsr4_variant: str | None) -> Path:
        variant_id = self._normalize_fsr4_variant(fsr4_variant)
        return fgmod_path / FSR4_VARIANTS[variant_id]["dir_name"] / FSR4_UPSCALER_FILENAME

    def _activate_default_fsr4_variant(self, fgmod_path: Path, fsr4_variant: str | None) -> str:
        variant_id = self._normalize_fsr4_variant(fsr4_variant)
        variant_path = self._fsr4_variant_path(fgmod_path, variant_id)
        if not variant_path.exists():
            raise FileNotFoundError(f"Prepared FSR4 variant missing: {variant_path}")
        shutil.copy2(variant_path, fgmod_path / FSR4_UPSCALER_FILENAME)
        return variant_id

    def _detect_fsr4_variant(self, upscaler_sha256: str | None) -> str | None:
        if not upscaler_sha256:
            return None
        return FSR4_VARIANT_BY_SHA256.get(str(upscaler_sha256).lower())

    def _fgmod_version(self, fgmod_path: Path) -> str | None:
        manifest = self._load_install_manifest(fgmod_path)
        optiscaler = manifest.get("optiscaler") if isinstance(manifest, dict) else None
        if isinstance(optiscaler, dict) and optiscaler.get("version"):
            return str(optiscaler.get("version"))
        version_file = fgmod_path / VERSION_FILENAME
        try:
            if version_file.exists():
                return version_file.read_text(encoding="utf-8").strip() or None
        except Exception:
            return None
        return None

    def _managed_support_candidate_paths(self, fgmod_path: Path, filename: str) -> list[Path]:
        candidates: list[Path] = []
        if filename == FSR4_UPSCALER_FILENAME:
            candidates.append(fgmod_path / FSR4_UPSCALER_FILENAME)
            for variant_id in FSR4_VARIANTS:
                candidates.append(self._fsr4_variant_path(fgmod_path, variant_id))
        else:
            candidates.append(fgmod_path / filename)
        unique: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate)
            if key not in seen:
                unique.append(candidate)
                seen.add(key)
        return unique

    def _is_managed_support_file(self, path: Path, fgmod_path: Path) -> bool:
        if not path.exists():
            return False
        for candidate in self._managed_support_candidate_paths(fgmod_path, path.name):
            if self._files_match(path, candidate):
                return True
        return False

    def _migrate_optiscaler_ini(self, ini_file):
        """Migrate pre-v0.9-final OptiScaler.ini: replace FGType with FGInput + FGOutput.

        v0.9-final split the single FGType key into separate FGInput and FGOutput keys.
        Games already patched with an older build will have FGType=<value> in their
        per-game INI but no FGInput/FGOutput entries, causing the new DLL to silently
        fall back to nofg.  This migration runs at patch-time and at every fgmod.sh
        launch so users never have to manually touch their INI.
        """
        try:
            if not ini_file.exists():
                return False

            with open(ini_file, 'r') as f:
                content = f.read()

            fg_type_match = re.search(r'^FGType\s*=\s*(\S+)', content, re.MULTILINE)
            if not fg_type_match:
                return True  # Nothing to migrate

            fg_value = fg_type_match.group(1)

            if re.search(r'^FGInput\s*=', content, re.MULTILINE):
                # FGInput already present (INI already in v0.9-final format);
                # just remove the now-unknown FGType line.
                content = re.sub(r'^FGType\s*=\s*\S+\n?', '', content, flags=re.MULTILINE)
                decky.logger.info(f"Removed stale FGType from {ini_file} (FGInput already present)")
            else:
                # Replace the single FGType=X line with FGInput=X then FGOutput=X
                content = re.sub(
                    r'^FGType\s*=\s*\S+',
                    f'FGInput={fg_value}\nFGOutput={fg_value}',
                    content,
                    flags=re.MULTILINE
                )
                decky.logger.info(f"Migrated FGType={fg_value} → FGInput={fg_value}, FGOutput={fg_value} in {ini_file}")

            with open(ini_file, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            decky.logger.error(f"Failed to migrate OptiScaler.ini: {e}")
            return False

    def _disable_hq_font_auto(self, ini_file):
        """Disable the new HQ font auto mode to avoid missing font assertions on Wine/Proton."""
        try:
            if not ini_file.exists():
                decky.logger.warning(f"OptiScaler.ini not found at {ini_file}")
                return False

            with open(ini_file, 'r') as f:
                content = f.read()

            updated_content = re.sub(r'UseHQFont\s*=\s*auto', 'UseHQFont=false', content)
            if updated_content != content:
                with open(ini_file, 'w') as f:
                    f.write(updated_content)
                decky.logger.info("Set UseHQFont=false to avoid missing font assertions")

            return True
        except Exception as e:
            decky.logger.error(f"Failed to update HQ font setting in OptiScaler.ini: {e}")
            return False

    def _modify_optiscaler_ini(self, ini_file):
        """Modify OptiScaler.ini to set FG defaults, ASI plugin settings, and safe font defaults."""
        try:
            if ini_file.exists():
                with open(ini_file, 'r') as f:
                    content = f.read()
                
                # Replace FGInput=auto with FGInput=nukems (final v0.9+ split FGType into FGInput/FGOutput)
                updated_content = re.sub(r'FGInput\s*=\s*auto', 'FGInput=nukems', content)

                # Replace FGOutput=auto with FGOutput=nukems
                updated_content = re.sub(r'FGOutput\s*=\s*auto', 'FGOutput=nukems', updated_content)
                
                # Replace Fsr4Update=auto with Fsr4Update=true
                updated_content = re.sub(r'Fsr4Update\s*=\s*auto', 'Fsr4Update=true', updated_content)
                
                # Replace LoadAsiPlugins=auto with LoadAsiPlugins=true
                updated_content = re.sub(r'LoadAsiPlugins\s*=\s*auto', 'LoadAsiPlugins=true', updated_content)
                
                # Replace Path=auto with Path=plugins
                updated_content = re.sub(r'Path\s*=\s*auto', 'Path=plugins', updated_content)

                # Disable new HQ font auto mode to avoid missing font assertions on Proton
                updated_content = re.sub(r'UseHQFont\s*=\s*auto', 'UseHQFont=false', updated_content)
                
                with open(ini_file, 'w') as f:
                    f.write(updated_content)
                
                decky.logger.info("Modified OptiScaler.ini to set FGInput=nukems, FGOutput=nukems, Fsr4Update=true, LoadAsiPlugins=true, Path=plugins, UseHQFont=false")
                return True
            else:
                decky.logger.warning(f"OptiScaler.ini not found at {ini_file}")
                return False
        except Exception as e:
            decky.logger.error(f"Failed to modify OptiScaler.ini: {e}")
            return False

    # ── OptiScaler auto-update (GitHub Releases) ──────────────────────────────

    def _request_text(self, url):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Decky-Framegen",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=OPTISCALER_DOWNLOAD_TIMEOUT) as response:
                return response.read().decode("utf-8")
        except Exception as urllib_error:
            decky.logger.warning(f"urllib request failed for {url}: {urllib_error}")

        fallback_commands = [
            [
                "curl",
                "-fsSL",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "User-Agent: Decky-Framegen",
                url,
            ],
            [
                "wget",
                "-qO-",
                "--header=Accept: application/vnd.github+json",
                "--header=User-Agent: Decky-Framegen",
                url,
            ],
        ]
        errors = []
        for command in fallback_commands:
            if not shutil.which(command[0]):
                errors.append(f"{command[0]} not installed")
                continue
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout:
                return result.stdout
            errors.append(f"{command[0]} failed: {result.stderr.strip() or result.returncode}")

        raise RuntimeError("; ".join(errors))

    def _request_json(self, url):
        return json.loads(self._request_text(url))

    def _download_file(self, url, destination):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Decky-Framegen"},
        )
        try:
            with urllib.request.urlopen(request, timeout=OPTISCALER_DOWNLOAD_TIMEOUT) as response:
                with open(destination, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)
                return
        except Exception as urllib_error:
            decky.logger.warning(f"urllib download failed for {url}: {urllib_error}")

        fallback_commands = [
            ["curl", "-fL", "-o", str(destination), url],
            ["wget", "-O", str(destination), url],
        ]
        errors = []
        for command in fallback_commands:
            if not shutil.which(command[0]):
                errors.append(f"{command[0]} not installed")
                continue
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode == 0 and destination.exists() and destination.stat().st_size > 0:
                return
            errors.append(f"{command[0]} failed: {result.stderr.strip() or result.returncode}")

        raise RuntimeError("; ".join(errors))

    def _select_optiscaler_release_asset(self, release):
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            if OPTISCALER_ASSET_NAME_RE.search(name) and "BUNDLE" not in name.upper():
                download_url = asset.get("browser_download_url")
                if download_url:
                    return asset
        return None

    def _include_optiscaler_prereleases(self):
        include_prereleases = os.environ.get(
            "DECKY_OPTISCALER_INCLUDE_PRERELEASES", "false"
        ).lower() in ("1", "true", "yes")
        return include_prereleases

    def _optiscaler_release_metadata(self, release):
        asset = self._select_optiscaler_release_asset(release)
        if not asset:
            return None
        return {
            "version": release.get("tag_name") or asset["name"].replace(".7z", ""),
            "release_url": release.get("html_url"),
            "asset_name": asset["name"],
            "download_url": asset["browser_download_url"],
        }

    def _get_latest_optiscaler_release(self, use_cache=True):
        """Return metadata for the newest usable OptiScaler release archive."""
        include_prereleases = self._include_optiscaler_prereleases()
        cache_key = "with-prereleases" if include_prereleases else "stable"
        now = datetime.now(timezone.utc).timestamp()

        if use_cache and self._latest_optiscaler_release_cache:
            cached_key, cached_at, cached_release = self._latest_optiscaler_release_cache
            if cached_key == cache_key and now - cached_at < OPTISCALER_LATEST_CACHE_SECONDS:
                return cached_release

        if not include_prereleases:
            try:
                latest_release = self._request_json(OPTISCALER_LATEST_RELEASE_API)
                if not isinstance(latest_release, dict):
                    raise RuntimeError("Unexpected GitHub latest release response")
                release_metadata = self._optiscaler_release_metadata(latest_release)
                if release_metadata:
                    self._latest_optiscaler_release_cache = (cache_key, now, release_metadata)
                    return release_metadata
                decky.logger.warning(
                    f"No OptiScaler .7z asset found in latest release {latest_release.get('tag_name')}"
                )
            except Exception as e:
                decky.logger.warning(f"GitHub latest release endpoint failed: {e}")

        releases = self._request_json(OPTISCALER_RELEASES_API)
        if not isinstance(releases, list):
            raise RuntimeError("Unexpected GitHub releases response")

        for release in releases:
            if release.get("draft"):
                continue
            if release.get("prerelease") and not include_prereleases:
                continue

            release_metadata = self._optiscaler_release_metadata(release)
            if not release_metadata:
                decky.logger.warning(
                    f"No OptiScaler .7z asset found in release {release.get('tag_name')}"
                )
                continue

            self._latest_optiscaler_release_cache = (cache_key, now, release_metadata)
            return release_metadata

        raise RuntimeError("No suitable OptiScaler release archive found")

    def _download_latest_optiscaler_archive(self, download_dir):
        """Download the newest OptiScaler release archive from GitHub Releases.

        By default this skips prereleases, matching GitHub's stable "latest release"
        behavior. Set DECKY_OPTISCALER_INCLUDE_PRERELEASES=true to allow prereleases.
        """
        release = self._get_latest_optiscaler_release(use_cache=False)
        archive_path = download_dir / release["asset_name"]
        decky.logger.info(
            f"Downloading OptiScaler {release['version']} from {release['download_url']}"
        )
        self._download_file(release["download_url"], archive_path)
        return {
            "path": archive_path,
            "version": release["version"],
            "release_url": release.get("release_url"),
        }

    async def extract_static_optiscaler(self, selected_default_variant: str = DEFAULT_FSR4_VARIANT) -> dict:
        """Prepare the shared ~/fgmod bundle with both FSR4 runtime variants."""
        try:
            decky.logger.info("Starting extract_static_optiscaler method")

            bin_path = Path(decky.DECKY_PLUGIN_DIR) / "bin"
            extract_path = Path(decky.HOME) / "fgmod"
            assets_dir = Path(decky.DECKY_PLUGIN_DIR) / "assets"
            selected_default_variant = self._normalize_fsr4_variant(selected_default_variant)

            if not bin_path.exists():
                return {"status": "error", "message": f"Bin directory not found: {bin_path}"}

            # The INT8 (Steam Deck / RDNA2-3) upscaler and OptiPatcher always come from the
            # bundled, hash-verified binaries -- they are independent of the OptiScaler archive.
            fsr4_int8_src = bin_path / FSR4_INT8_ASSET["name"]
            optipatcher_src = bin_path / OPTIPATCHER_ASSET["name"]
            for required_path, asset in [
                (fsr4_int8_src, FSR4_INT8_ASSET),
                (optipatcher_src, OPTIPATCHER_ASSET),
            ]:
                if not required_path.exists():
                    return {
                        "status": "error",
                        "message": f"Required bundled asset missing: {asset['name']}",
                    }
                self._verify_bundled_asset(required_path, asset["sha256"], asset["name"])

            # ── Stage A: obtain the base OptiScaler archive ───────────────────────
            # Prefer the newest release published on GitHub (auto-update). Fall back to
            # the bundled, pinned 0.9.2a-final archive when the download is unavailable
            # or offline. Stage B below always layers the plugin optimizations on top.
            bundled_archive = bin_path / OPTISCALER_ARCHIVE_ASSET["name"]
            optiscaler_version = OPTISCALER_ARCHIVE_ASSET["version"]
            archive_is_pinned = True
            optiscaler_archive = None
            temp_download_dir = None

            # Auto-update is OPT-IN. The bundled "_Reup" archive is curated to include the
            # full Frame Generation stack (fakenvapi, dlssg_to_fsr3, libxess, FSR/XeSS DLLs).
            # The official optiscaler/OptiScaler release archive does NOT ship those extra
            # components, so downloading it leaves ~/fgmod incomplete and check_fgmod_path
            # reports "not installed". Default to the complete bundled archive.
            auto_update = os.environ.get(
                "DECKY_OPTISCALER_AUTO_UPDATE", "false"
            ).lower() in ("1", "true", "yes")

            if auto_update:
                try:
                    temp_download_dir = tempfile.TemporaryDirectory()
                    release_metadata = self._download_latest_optiscaler_archive(
                        Path(temp_download_dir.name)
                    )
                    optiscaler_archive = release_metadata["path"]
                    optiscaler_version = release_metadata["version"]
                    archive_is_pinned = False
                    decky.logger.info(
                        f"Using latest OptiScaler archive from GitHub: {optiscaler_archive.name} "
                        f"({optiscaler_version})"
                    )
                except Exception as download_error:
                    decky.logger.warning(
                        f"OptiScaler auto-update failed, falling back to bundled archive: {download_error}"
                    )
                    if temp_download_dir is not None:
                        temp_download_dir.cleanup()
                        temp_download_dir = None

            if optiscaler_archive is None:
                if not bundled_archive.exists():
                    return {
                        "status": "error",
                        "message": (
                            "OptiScaler archive unavailable "
                            f"(download failed and bundled missing: {bundled_archive.name})"
                        ),
                    }
                self._verify_bundled_asset(
                    bundled_archive,
                    OPTISCALER_ARCHIVE_ASSET["sha256"],
                    OPTISCALER_ARCHIVE_ASSET["name"],
                )
                optiscaler_archive = bundled_archive
                optiscaler_version = OPTISCALER_ARCHIVE_ASSET["version"]
                archive_is_pinned = True

            try:
                if extract_path.exists():
                    shutil.rmtree(extract_path)
                extract_path.mkdir(parents=True, exist_ok=True)

                self._extract_archive(optiscaler_archive, extract_path)
            finally:
                # The archive is only needed during extraction; release the download now.
                if temp_download_dir is not None:
                    temp_download_dir.cleanup()
                    temp_download_dir = None

            source_file = extract_path / "OptiScaler.dll"
            renames_dir = extract_path / "renames"
            if not self._create_renamed_copies(source_file, renames_dir):
                return {"status": "error", "message": "Failed to prepare renamed OptiScaler proxies."}

            if not self._copy_launcher_scripts(assets_dir, extract_path):
                return {"status": "error", "message": "Failed to copy launcher scripts."}

            plugins_dir = extract_path / "plugins"
            plugins_dir.mkdir(parents=True, exist_ok=True)
            optipatcher_dst = plugins_dir / "OptiPatcher.asi"
            shutil.copy2(optipatcher_src, optipatcher_dst)
            optipatcher_sha256 = self._verify_bundled_asset(
                optipatcher_dst,
                OPTIPATCHER_ASSET["sha256"],
                "Prepared OptiPatcher plugin",
            )

            ini_file = extract_path / "OptiScaler.ini"
            self._modify_optiscaler_ini(ini_file)

            rdna4_dir = extract_path / FSR4_VARIANTS["rdna4-native"]["dir_name"]
            rdna4_dir.mkdir(parents=True, exist_ok=True)
            rdna4_upscaler = rdna4_dir / FSR4_UPSCALER_FILENAME
            native_upscaler_root = extract_path / FSR4_UPSCALER_FILENAME

            if native_upscaler_root.exists():
                if archive_is_pinned:
                    # Pinned bundle: enforce the known-good RDNA4-native hash.
                    native_upscaler_sha256 = self._verify_bundled_asset(
                        native_upscaler_root,
                        FSR4_VARIANTS["rdna4-native"]["sha256"],
                        "Archive-native FSR4 upscaler",
                    )
                else:
                    # Downloaded build: hash is unknown, record it but do not assert.
                    native_upscaler_sha256 = self._file_sha256(native_upscaler_root)
                    decky.logger.warning(
                        "RDNA4-native FSR4 variant integrity not verified (downloaded build): "
                        f"sha256={native_upscaler_sha256}"
                    )
                shutil.copy2(native_upscaler_root, rdna4_upscaler)
            else:
                # Some OptiScaler archives may not ship the native upscaler; keep the
                # rdna4-native slot populated (with the INT8 DLL) so check_fgmod_path passes.
                decky.logger.warning(
                    "Archive-native FSR4 upscaler missing; using INT8 DLL for rdna4-native slot."
                )
                shutil.copy2(fsr4_int8_src, rdna4_upscaler)
                native_upscaler_sha256 = self._file_sha256(rdna4_upscaler)

            rdna23_dir = extract_path / FSR4_VARIANTS["rdna23-int8"]["dir_name"]
            rdna23_dir.mkdir(parents=True, exist_ok=True)
            self._verify_bundled_asset(
                fsr4_int8_src,
                FSR4_VARIANTS["rdna23-int8"]["sha256"],
                "Bundled rdna23-int8 FSR4 upscaler",
            )
            shutil.copy2(fsr4_int8_src, rdna23_dir / FSR4_UPSCALER_FILENAME)
            self._verify_bundled_asset(
                rdna23_dir / FSR4_UPSCALER_FILENAME,
                FSR4_VARIANTS["rdna23-int8"]["sha256"],
                "Prepared rdna23-int8 FSR4 upscaler",
            )

            selected_default_variant = self._activate_default_fsr4_variant(extract_path, selected_default_variant)
            active_upscaler_sha256 = self._file_sha256(extract_path / FSR4_UPSCALER_FILENAME)

            version_file = extract_path / VERSION_FILENAME
            version_file.write_text(optiscaler_version, encoding="utf-8")

            install_manifest = {
                "schema_version": 1,
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "optiscaler": {
                    "asset_name": optiscaler_archive.name,
                    "version": optiscaler_version,
                    "sha256": OPTISCALER_ARCHIVE_ASSET["sha256"] if archive_is_pinned else None,
                    "source": "bundled" if archive_is_pinned else "github-latest",
                    "native_upscaler_sha256": native_upscaler_sha256,
                },
                "optipatcher": {
                    "asset_name": OPTIPATCHER_ASSET["name"],
                    "version": OPTIPATCHER_ASSET["version"],
                    "sha256": optipatcher_sha256,
                    "target_path": str(optipatcher_dst.relative_to(extract_path)),
                },
                "fsr4_variants": {
                    variant_id: {
                        "label": variant["label"],
                        "dir_name": variant["dir_name"],
                        "path": str((Path(variant["dir_name"]) / FSR4_UPSCALER_FILENAME).as_posix()),
                        "sha256": variant["sha256"],
                        "source_asset_name": variant["source_asset_name"],
                        "source_version": variant["source_version"],
                        "uses_archive_native": bool(variant["uses_archive_native"]),
                    }
                    for variant_id, variant in FSR4_VARIANTS.items()
                },
                "selected_default_variant": selected_default_variant,
                "active_root_upscaler": {
                    "path": FSR4_UPSCALER_FILENAME,
                    "sha256": active_upscaler_sha256,
                    "variant": selected_default_variant,
                },
            }
            self._write_json_file(self._install_manifest_path(extract_path), install_manifest)

            return {
                "status": "success",
                "message": f"Successfully extracted OptiScaler {optiscaler_version} to ~/fgmod",
                "version": optiscaler_version,
                "selected_default_variant": selected_default_variant,
                "selected_default_variant_label": FSR4_VARIANTS[selected_default_variant]["label"],
            }
        except Exception as e:
            decky.logger.error(f"Extract failed with exception: {str(e)}")
            import traceback
            decky.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": f"Extract failed: {str(e)}"}

    async def run_uninstall_fgmod(self) -> dict:
        try:
            # Remove fgmod directory
            fgmod_path = Path(decky.HOME) / "fgmod"
            
            if fgmod_path.exists():
                shutil.rmtree(fgmod_path)
                decky.logger.info(f"Removed directory: {fgmod_path}")
                return {
                    "status": "success", 
                    "output": "Successfully removed fgmod directory"
                }
            else:
                return {
                    "status": "success", 
                    "output": "No fgmod directory found to remove"
                }
            
        except Exception as e:
            decky.logger.error(f"Uninstall error: {str(e)}")
            return {
                "status": "error", 
                "message": f"Uninstall failed: {str(e)}", 
                "output": str(e)
            }

    async def set_default_fsr4_variant(self, selected_default_variant: str = DEFAULT_FSR4_VARIANT) -> dict:
        try:
            fgmod_path = Path(decky.HOME) / "fgmod"
            if not fgmod_path.exists():
                return {"status": "error", "message": "OptiScaler bundle not installed. Run Install first."}

            selected_default_variant = self._normalize_fsr4_variant(selected_default_variant)
            manifest = self._load_install_manifest(fgmod_path)
            if not manifest:
                return {"status": "error", "message": "Install manifest missing. Reinstall OptiScaler."}

            selected_default_variant = self._activate_default_fsr4_variant(fgmod_path, selected_default_variant)
            active_upscaler_sha256 = self._file_sha256(fgmod_path / FSR4_UPSCALER_FILENAME)
            manifest["selected_default_variant"] = selected_default_variant
            manifest["active_root_upscaler"] = {
                "path": FSR4_UPSCALER_FILENAME,
                "sha256": active_upscaler_sha256,
                "variant": selected_default_variant,
            }
            manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_json_file(self._install_manifest_path(fgmod_path), manifest)
            return {
                "status": "success",
                "output": f"Default FSR4 runtime switched to {FSR4_VARIANTS[selected_default_variant]['label']}.",
                "version": self._fgmod_version(fgmod_path),
                "selected_default_variant": selected_default_variant,
                "selected_default_variant_label": FSR4_VARIANTS[selected_default_variant]["label"],
            }
        except Exception as e:
            decky.logger.error(f"Failed to switch default FSR4 runtime: {e}")
            return {"status": "error", "message": f"Failed to switch default FSR4 runtime: {e}"}

    async def run_install_fgmod(self, selected_default_variant: str = DEFAULT_FSR4_VARIANT) -> dict:
        try:
            decky.logger.info("Starting OptiScaler installation from static bundle")
            selected_default_variant = self._normalize_fsr4_variant(selected_default_variant)

            extract_result = await self.extract_static_optiscaler(selected_default_variant)
            if extract_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"OptiScaler extraction failed: {extract_result.get('message', 'Unknown error')}"
                }

            return {
                "status": "success",
                "output": (
                    "Successfully installed OptiScaler "
                    f"{extract_result.get('version', OPTISCALER_ARCHIVE_ASSET['version'])} "
                    f"with {extract_result.get('selected_default_variant_label', FSR4_VARIANTS[selected_default_variant]['label'])}."
                ),
                "version": extract_result.get("version", OPTISCALER_ARCHIVE_ASSET["version"]),
                "selected_default_variant": extract_result.get("selected_default_variant", selected_default_variant),
                "selected_default_variant_label": extract_result.get(
                    "selected_default_variant_label",
                    FSR4_VARIANTS[selected_default_variant]["label"],
                ),
            }

        except Exception as e:
            decky.logger.error(f"Unexpected error during installation: {str(e)}")
            return {
                "status": "error",
                "message": f"Installation failed: {str(e)}"
            }

    async def check_fgmod_path(self) -> dict:
        path = Path(decky.HOME) / "fgmod"
        required_files = [
            "OptiScaler.dll",
            "OptiScaler.ini",
            "dlssg_to_fsr3_amd_is_better.dll",
            "fakenvapi.dll",
            "fakenvapi.ini",
            "amd_fidelityfx_dx12.dll",
            "amd_fidelityfx_framegeneration_dx12.dll",
            FSR4_UPSCALER_FILENAME,
            "amd_fidelityfx_vk.dll",
            "libxess.dll",
            "libxess_dx11.dll",
            "libxess_fg.dll",
            "libxell.dll",
            "fgmod",
            "fgmod-uninstaller.sh",
            "update-optiscaler-config.py",
            INSTALL_MANIFEST_FILENAME,
        ]

        if not path.exists():
            return {"exists": False}

        for file_name in required_files:
            if not path.joinpath(file_name).exists():
                return {"exists": False}

        plugins_dir = path / "plugins"
        if not plugins_dir.exists() or not (plugins_dir / "OptiPatcher.asi").exists():
            return {"exists": False}

        for variant in FSR4_VARIANTS.values():
            variant_path = path / variant["dir_name"] / FSR4_UPSCALER_FILENAME
            if not variant_path.exists():
                return {"exists": False}

        manifest = self._load_install_manifest(path)
        selected_variant = self._selected_fsr4_variant(path)
        return {
            "exists": True,
            "version": self._fgmod_version(path),
            "selected_fsr4_variant": selected_variant,
            "selected_fsr4_variant_label": FSR4_VARIANTS[selected_variant]["label"],
            "install_manifest_present": bool(manifest),
        }

    def _resolve_target_directory(self, directory: str) -> Path:
        decky.logger.info(f"Resolving target directory: {directory}")
        target = Path(directory).expanduser()
        if not target.exists():
            raise FileNotFoundError(f"Target directory does not exist: {directory}")
        if not target.is_dir():
            raise NotADirectoryError(f"Target path is not a directory: {directory}")
        if not os.access(target, os.W_OK | os.X_OK):
            raise PermissionError(f"Insufficient permissions for {directory}")
        decky.logger.info(f"Resolved directory {directory} to absolute path {target}")
        return target

    def _manual_patch_directory_impl(
        self,
        directory: Path,
        dll_name: str = "dxgi.dll",
        fsr4_variant: str | None = None,
        allow_managed_support_cleanup: bool = False,
    ) -> dict:
        fgmod_path = Path(decky.HOME) / "fgmod"
        if not fgmod_path.exists():
            return {
                "status": "error",
                "message": "OptiScaler bundle not installed. Run Install first.",
            }

        optiscaler_dll = fgmod_path / "OptiScaler.dll"
        if not optiscaler_dll.exists():
            return {
                "status": "error",
                "message": "OptiScaler.dll not found in ~/fgmod. Reinstall OptiScaler.",
            }

        preserve_ini = True
        selected_variant = self._selected_fsr4_variant(fgmod_path, fsr4_variant)
        selected_variant_info = FSR4_VARIANTS[selected_variant]
        selected_upscaler_src = self._fsr4_variant_path(fgmod_path, selected_variant)
        if not selected_upscaler_src.exists():
            selected_upscaler_src = fgmod_path / FSR4_UPSCALER_FILENAME
        if not selected_upscaler_src.exists():
            return {
                "status": "error",
                "message": f"FSR4 upscaler variant not found for {selected_variant}. Reinstall OptiScaler.",
            }
        optiscaler_version = self._fgmod_version(fgmod_path)
        selected_upscaler_sha256 = self._file_sha256(selected_upscaler_src)

        try:
            decky.logger.info(
                f"Manual patch started for {directory} with FSR4 variant {selected_variant} ({selected_variant_info['label']})"
            )

            backed_up_proxies = self._backup_preexisting_proxy_files(directory, fgmod_path)
            decky.logger.info(
                f"Backed up pre-existing proxy files: {backed_up_proxies}"
                if backed_up_proxies
                else "No pre-existing proxy files required backup"
            )

            removed_patch_files = []
            for filename in dict.fromkeys(PATCH_CLEANUP_FILES):
                path = directory / filename
                if path.exists():
                    path.unlink()
                    removed_patch_files.append(filename)
            decky.logger.info(
                f"Removed stale patch files: {removed_patch_files}"
                if removed_patch_files
                else "No stale patch files found to remove"
            )

            backed_up_originals = []
            removed_managed_support = []
            for dll in ORIGINAL_DLL_BACKUPS:
                source = directory / dll
                backup = directory / f"{dll}.b"
                if not source.exists() or backup.exists():
                    continue
                if allow_managed_support_cleanup and self._is_managed_support_file(source, fgmod_path):
                    source.unlink()
                    removed_managed_support.append(dll)
                    continue
                shutil.move(source, backup)
                backed_up_originals.append(dll)
            if removed_managed_support:
                decky.logger.info(f"Removed managed support files before repatch: {removed_managed_support}")
            decky.logger.info(
                f"Backed up original game DLLs: {backed_up_originals}"
                if backed_up_originals
                else "No original game DLLs required backup"
            )

            renamed = fgmod_path / "renames" / dll_name
            destination_dll = directory / dll_name
            source_for_copy = renamed if renamed.exists() else optiscaler_dll
            shutil.copy2(source_for_copy, destination_dll)
            decky.logger.info(f"Copied injector DLL from {source_for_copy} to {destination_dll}")

            target_ini = directory / "OptiScaler.ini"
            source_ini = fgmod_path / "OptiScaler.ini"
            if preserve_ini and target_ini.exists():
                decky.logger.info(f"Preserving existing OptiScaler.ini at {target_ini}")
            elif source_ini.exists():
                shutil.copy2(source_ini, target_ini)
                decky.logger.info(f"Copied OptiScaler.ini from {source_ini} to {target_ini}")
            else:
                decky.logger.warning("No OptiScaler.ini found to copy")

            if target_ini.exists():
                self._migrate_optiscaler_ini(target_ini)
                self._disable_hq_font_auto(target_ini)

            plugins_src = fgmod_path / "plugins"
            plugins_dest = directory / "plugins"
            if plugins_src.exists():
                shutil.copytree(plugins_src, plugins_dest, dirs_exist_ok=True)
                decky.logger.info(f"Synced plugins directory from {plugins_src} to {plugins_dest}")
            else:
                decky.logger.warning("Plugins directory missing in fgmod bundle")

            d3d12_src = fgmod_path / "D3D12_Optiscaler"
            d3d12_dest = directory / "D3D12_Optiscaler"
            if d3d12_src.exists():
                shutil.copytree(d3d12_src, d3d12_dest, dirs_exist_ok=True)
                decky.logger.info(f"Copied D3D12_Optiscaler directory to {d3d12_dest}")
            else:
                decky.logger.warning("D3D12_Optiscaler directory missing in fgmod bundle")

            copied_support = []
            missing_support = []
            for filename in SUPPORT_FILES:
                source = fgmod_path / filename
                dest = directory / filename
                if source.exists():
                    shutil.copy2(source, dest)
                    copied_support.append(filename)
                else:
                    missing_support.append(filename)

            upscaler_dest = directory / FSR4_UPSCALER_FILENAME
            shutil.copy2(selected_upscaler_src, upscaler_dest)
            copied_support.append(FSR4_UPSCALER_FILENAME)

            if copied_support:
                decky.logger.info(f"Copied support files: {copied_support}")
            if missing_support:
                decky.logger.warning(f"Support files missing from fgmod bundle: {missing_support}")

            decky.logger.info(f"Manual patch complete for {directory}")
            return {
                "status": "success",
                "message": (
                    f"OptiScaler files copied to {directory} using "
                    f"{selected_variant_info['label']}"
                ),
                "fsr4_variant": selected_variant,
                "fsr4_variant_label": selected_variant_info["label"],
                "fsr4_upscaler_sha256": selected_upscaler_sha256,
                "optiscaler_version": optiscaler_version,
            }

        except PermissionError as exc:
            decky.logger.error(f"Manual patch permission error: {exc}")
            return {
                "status": "error",
                "message": f"Permission error while patching: {exc}",
            }
        except Exception as exc:
            decky.logger.error(f"Manual patch failed: {exc}")
            return {
                "status": "error",
                "message": f"Manual patch failed: {exc}",
            }

    def _manual_unpatch_directory_impl(self, directory: Path) -> dict:
        try:
            decky.logger.info(f"Manual unpatch started for {directory}")

            removed_files = []
            for filename in set(INJECTOR_FILENAMES + SUPPORT_FILES + [FSR4_UPSCALER_FILENAME]):
                path = directory / filename
                if path.exists():
                    path.unlink()
                    removed_files.append(filename)
            decky.logger.info(f"Removed injector/support files: {removed_files}" if removed_files else "No injector/support files found to remove")

            legacy_removed = []
            for legacy in LEGACY_FILES:
                path = directory / legacy
                if path.exists():
                    try:
                        path.unlink()
                    except IsADirectoryError:
                        shutil.rmtree(path, ignore_errors=True)
                    legacy_removed.append(legacy)
            decky.logger.info(f"Removed legacy artifacts: {legacy_removed}" if legacy_removed else "No legacy artifacts present")

            plugins_dir = directory / "plugins"
            if plugins_dir.exists():
                shutil.rmtree(plugins_dir, ignore_errors=True)
                decky.logger.info(f"Removed plugins directory at {plugins_dir}")

            d3d12_dir = directory / "D3D12_Optiscaler"
            if d3d12_dir.exists():
                shutil.rmtree(d3d12_dir, ignore_errors=True)
                decky.logger.info(f"Removed D3D12_Optiscaler directory from {d3d12_dir}")

            restored_backups = []
            for dll in dict.fromkeys(RESTORABLE_BACKUP_FILES):
                backup = directory / f"{dll}.b"
                original = directory / dll
                if backup.exists():
                    if original.exists():
                        original.unlink()
                    shutil.move(backup, original)
                    restored_backups.append(dll)
            decky.logger.info(f"Restored backups: {restored_backups}" if restored_backups else "No backups found to restore")

            uninstaller = directory / "fgmod-uninstaller.sh"
            if uninstaller.exists():
                uninstaller.unlink()
                decky.logger.info(f"Removed fgmod uninstaller at {uninstaller}")

            decky.logger.info(f"Manual unpatch complete for {directory}")
            return {
                "status": "success",
                "message": f"OptiScaler files removed from {directory}",
            }

        except PermissionError as exc:
            decky.logger.error(f"Manual unpatch permission error: {exc}")
            return {
                "status": "error",
                "message": f"Permission error while unpatching: {exc}",
            }
        except Exception as exc:
            decky.logger.error(f"Manual unpatch failed: {exc}")
            return {
                "status": "error",
                "message": f"Manual unpatch failed: {exc}",
            }

    # ── Steam library discovery ───────────────────────────────────────────────

    def _home_path(self) -> Path:
        try:
            return Path(decky.HOME)
        except TypeError:
            return Path(str(decky.HOME))

    def _steam_root_candidates(self) -> list[Path]:
        home = self._home_path()
        candidates = [
            home / ".local" / "share" / "Steam",
            home / ".steam" / "steam",
            home / ".steam" / "root",
            home / ".var" / "app" / "com.valvesoftware.Steam" / "home" / ".local" / "share" / "Steam",
            home / ".var" / "app" / "com.valvesoftware.Steam" / "home" / ".steam" / "steam",
        ]
        unique: list[Path] = []
        seen: set[str] = set()
        for c in candidates:
            key = str(c)
            if key not in seen:
                unique.append(c)
                seen.add(key)
        return unique

    def _steam_library_paths(self) -> list[Path]:
        library_paths: list[Path] = []
        seen: set[str] = set()
        for steam_root in self._steam_root_candidates():
            if steam_root.exists():
                key = str(steam_root)
                if key not in seen:
                    library_paths.append(steam_root)
                    seen.add(key)
            library_file = steam_root / "steamapps" / "libraryfolders.vdf"
            if not library_file.exists():
                continue
            try:
                with open(library_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if '"path"' not in line:
                            continue
                        path = line.split('"path"', 1)[1].strip().strip('"').replace("\\\\", "/")
                        candidate = Path(path)
                        key = str(candidate)
                        if key not in seen:
                            library_paths.append(candidate)
                            seen.add(key)
            except Exception as exc:
                decky.logger.error(f"[Framegen] failed to parse libraryfolders: {library_file}: {exc}")
        return library_paths

    def _find_installed_games(self, appid: str | None = None) -> list[dict]:
        games: list[dict] = []
        for library_path in self._steam_library_paths():
            steamapps_path = library_path / "steamapps"
            if not steamapps_path.exists():
                continue
            for appmanifest in steamapps_path.glob("appmanifest_*.acf"):
                game_info: dict = {"appid": "", "name": "", "library_path": str(library_path), "install_path": ""}
                install_dir = ""
                try:
                    with open(appmanifest, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            if '"appid"' in line:
                                game_info["appid"] = line.split('"appid"', 1)[1].strip().strip('"')
                            elif '"name"' in line:
                                game_info["name"] = line.split('"name"', 1)[1].strip().strip('"')
                            elif '"installdir"' in line:
                                install_dir = line.split('"installdir"', 1)[1].strip().strip('"')
                except Exception as exc:
                    decky.logger.error(f"[Framegen] skipping manifest {appmanifest}: {exc}")
                    continue
                if not game_info["appid"] or not game_info["name"]:
                    continue
                if "Proton" in game_info["name"] or "Steam Linux Runtime" in game_info["name"]:
                    continue
                install_path = steamapps_path / "common" / install_dir if install_dir else Path()
                game_info["install_path"] = str(install_path)
                if appid is None or str(game_info["appid"]) == str(appid):
                    games.append(game_info)
        deduped: dict[str, dict] = {}
        for game in games:
            deduped[str(game["appid"])] = game
        return sorted(deduped.values(), key=lambda g: g["name"].lower())

    def _game_record(self, appid: str) -> dict | None:
        matches = self._find_installed_games(appid)
        return matches[0] if matches else None

    # ── Patch target auto-detection ───────────────────────────────────────────

    def _normalized_path_string(self, value: str) -> str:
        normalized = value.lower().replace("\\", "/")
        normalized = normalized.replace("z:/", "/")
        normalized = normalized.replace("//", "/")
        return normalized

    def _candidate_executables(self, install_root: Path) -> list[Path]:
        if not install_root.exists():
            return []
        candidates: list[Path] = []
        try:
            for exe in install_root.rglob("*.exe"):
                if exe.is_file():
                    candidates.append(exe)
        except Exception as exc:
            decky.logger.error(f"[Framegen] exe scan failed for {install_root}: {exc}")
        return candidates

    def _exe_score(self, exe: Path, install_root: Path, game_name: str) -> int:
        normalized = self._normalized_path_string(str(exe))
        name = exe.name.lower()
        score = 0
        if normalized.endswith("-win64-shipping.exe"):
            score += 300
        if "shipping.exe" in name:
            score += 220
        if "/binaries/win64/" in normalized:
            score += 200
        if "/win64/" in normalized:
            score += 80
        if exe.parent == install_root:
            score += 20
        sanitized_game = re.sub(r"[^a-z0-9]", "", game_name.lower())
        sanitized_name = re.sub(r"[^a-z0-9]", "", exe.stem.lower())
        sanitized_root = re.sub(r"[^a-z0-9]", "", install_root.name.lower())
        if sanitized_game and sanitized_game in sanitized_name:
            score += 120
        if sanitized_root and sanitized_root in sanitized_name:
            score += 90
        for bad in BAD_EXE_SUBSTRINGS:
            if bad in normalized:
                score -= 200
        score -= len(exe.parts)
        return score

    def _best_running_executable(self, candidates: list[Path]) -> Path | None:
        if not candidates:
            return None
        try:
            result = subprocess.run(["ps", "-eo", "args="], capture_output=True, text=True, check=False)
            process_lines = result.stdout.splitlines()
        except Exception as exc:
            decky.logger.error(f"[Framegen] running exe scan failed: {exc}")
            return None
        normalized_candidates = [(exe, self._normalized_path_string(str(exe))) for exe in candidates]
        matches: list[tuple[int, Path]] = []
        for line in process_lines:
            normalized_line = self._normalized_path_string(line)
            for exe, normalized_exe in normalized_candidates:
                if normalized_exe in normalized_line:
                    matches.append((len(normalized_exe), exe))
        if not matches:
            return None
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    def _guess_patch_target(self, game_info: dict) -> tuple[Path, Path | None]:
        install_root = Path(game_info["install_path"])
        candidates = self._candidate_executables(install_root)
        if not candidates:
            return install_root, None
        running_exe = self._best_running_executable(candidates)
        if running_exe:
            return running_exe.parent, running_exe
        best = max(candidates, key=lambda exe: self._exe_score(exe, install_root, game_info["name"]))
        return best.parent, best

    def _is_game_running(self, game_info: dict) -> bool:
        install_root = Path(game_info["install_path"])
        candidates = self._candidate_executables(install_root)
        return self._best_running_executable(candidates) is not None

    # ── Marker file tracking ──────────────────────────────────────────────────

    def _find_marker(self, install_root: Path) -> Path | None:
        if not install_root.exists():
            return None
        try:
            for marker in install_root.rglob(MARKER_FILENAME):
                if marker.is_file():
                    return marker
        except Exception:
            pass
        return None

    def _read_marker(self, marker_path: Path) -> dict:
        try:
            with open(marker_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_marker(
        self,
        marker_path: Path,
        *,
        appid: str,
        game_name: str,
        dll_name: str,
        target_dir: Path,
        original_launch_options: str,
        backed_up_files: list[str],
        optiscaler_version: str | None = None,
        fsr4_variant: str | None = None,
        fsr4_upscaler_sha256: str | None = None,
    ) -> None:
        normalized_variant = self._normalize_fsr4_variant(fsr4_variant)
        variant_info = FSR4_VARIANTS[normalized_variant]
        payload = {
            "appid": str(appid),
            "game_name": game_name,
            "dll_name": dll_name,
            "target_dir": str(target_dir),
            "original_launch_options": original_launch_options,
            "backed_up_files": backed_up_files,
            "optiscaler_version": optiscaler_version,
            "fsr4_variant": normalized_variant,
            "fsr4_variant_label": variant_info["label"],
            "fsr4_upscaler_sha256": fsr4_upscaler_sha256,
            "managed_files": [
                {
                    "path": str(target_dir / FSR4_UPSCALER_FILENAME),
                    "sha256": fsr4_upscaler_sha256,
                    "kind": "fsr4-upscaler",
                    "variant": normalized_variant,
                }
            ],
            "patched_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_json_file(marker_path, payload)

    # ── Launch options helpers ────────────────────────────────────────────────

    def _build_managed_launch_options(self, dll_name: str) -> str:
        if dll_name == "OptiScaler.asi":
            return "SteamDeck=0 %command%"
        base = dll_name.replace(".dll", "")
        return f"WINEDLLOVERRIDES={base}=n,b SteamDeck=0 %command%"

    def _is_managed_launch_options(self, opts: str) -> bool:
        if not opts or not opts.strip():
            return False
        normalized = " ".join(opts.strip().split())
        for dll_name in VALID_DLL_NAMES:
            if dll_name == "OptiScaler.asi":
                continue
            base = dll_name.replace(".dll", "")
            if f"WINEDLLOVERRIDES={base}=n,b" in normalized:
                return True
        if "fgmod/fgmod" in normalized:
            return True
        return False

    async def list_installed_games(self) -> dict:
        try:
            games = []
            for game in self._find_installed_games():
                install_root = Path(game["install_path"])
                games.append({
                    "appid": str(game["appid"]),
                    "name": game["name"],
                    "install_found": install_root.exists(),
                })
            return {"status": "success", "games": games}
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}

    async def get_path_defaults(self) -> dict:
        try:
            home_path = Path(decky.HOME)
        except TypeError:
            home_path = Path(str(decky.HOME))

        steam_common = home_path / ".local" / "share" / "Steam" / "steamapps" / "common"

        return {
            "home": str(home_path),
            "steam_common": str(steam_common),
        }

    async def log_error(self, error: str) -> None:
        decky.logger.error(f"FRONTEND: {error}")

    async def manual_patch_directory(
        self,
        directory: str,
        dll_name: str = "dxgi.dll",
        fsr4_variant: str = DEFAULT_FSR4_VARIANT,
    ) -> dict:
        if dll_name not in VALID_DLL_NAMES:
            return {"status": "error", "message": f"Invalid proxy DLL name: {dll_name}"}
        try:
            target_dir = self._resolve_target_directory(directory)
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
            decky.logger.error(f"Manual patch validation failed: {exc}")
            return {"status": "error", "message": str(exc)}

        allow_managed_support_cleanup = (target_dir / MARKER_FILENAME).exists()
        return self._manual_patch_directory_impl(
            target_dir,
            dll_name,
            fsr4_variant,
            allow_managed_support_cleanup=allow_managed_support_cleanup,
        )

    async def manual_unpatch_directory(self, directory: str) -> dict:
        try:
            target_dir = self._resolve_target_directory(directory)
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
            decky.logger.error(f"Manual unpatch validation failed: {exc}")
            return {"status": "error", "message": str(exc)}

        return self._manual_unpatch_directory_impl(target_dir)

    # ── AppID-based patch / unpatch / status ───────────────────────────────────────

    async def get_game_status(self, appid: str) -> dict:
        try:
            game_info = self._game_record(str(appid))
            if not game_info:
                return {
                    "status": "success",
                    "appid": str(appid),
                    "install_found": False,
                    "patched": False,
                    "dll_name": None,
                    "target_dir": None,
                    "fsr4_variant": None,
                    "fsr4_variant_label": None,
                    "message": "Game not found in Steam library.",
                }
            install_root = Path(game_info["install_path"])
            if not install_root.exists():
                return {
                    "status": "success",
                    "appid": str(appid),
                    "name": game_info["name"],
                    "install_found": False,
                    "patched": False,
                    "dll_name": None,
                    "target_dir": None,
                    "fsr4_variant": None,
                    "fsr4_variant_label": None,
                    "message": "Game install directory not found.",
                }
            marker = self._find_marker(install_root)
            if not marker:
                return {
                    "status": "success",
                    "appid": str(appid),
                    "name": game_info["name"],
                    "install_found": True,
                    "patched": False,
                    "dll_name": None,
                    "target_dir": None,
                    "fsr4_variant": None,
                    "fsr4_variant_label": None,
                    "message": "Not patched.",
                }
            metadata = self._read_marker(marker)
            dll_name = metadata.get("dll_name", "dxgi.dll")
            target_dir = Path(metadata.get("target_dir", str(marker.parent)))
            dll_present = (target_dir / dll_name).exists()
            upscaler_path = target_dir / FSR4_UPSCALER_FILENAME
            upscaler_sha256 = self._file_sha256(upscaler_path) if upscaler_path.exists() else None
            detected_variant = self._detect_fsr4_variant(upscaler_sha256)
            stored_variant = str(metadata.get("fsr4_variant") or "").strip() or None
            effective_variant = detected_variant or (stored_variant if stored_variant in FSR4_VARIANTS else None)
            effective_label = FSR4_VARIANTS[effective_variant]["label"] if effective_variant else None
            return {
                "status": "success",
                "appid": str(appid),
                "name": game_info["name"],
                "install_found": True,
                "patched": dll_present,
                "dll_name": dll_name,
                "target_dir": str(target_dir),
                "patched_at": metadata.get("patched_at"),
                "optiscaler_version": metadata.get("optiscaler_version"),
                "fsr4_variant": effective_variant,
                "fsr4_variant_label": effective_label,
                "fsr4_upscaler_sha256": upscaler_sha256,
                "message": (
                    f"Patched using {dll_name}" + (f" with {effective_label}." if effective_label else ".")
                    if dll_present
                    else f"Marker found but {dll_name} is missing. Reinstall recommended."
                ),
            }
        except Exception as exc:
            decky.logger.error(f"[Framegen] get_game_status failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    async def patch_game(
        self,
        appid: str,
        dll_name: str = "dxgi.dll",
        current_launch_options: str = "",
        fsr4_variant: str = DEFAULT_FSR4_VARIANT,
    ) -> dict:
        try:
            if dll_name not in VALID_DLL_NAMES:
                return {"status": "error", "message": f"Invalid proxy DLL name: {dll_name}"}
            game_info = self._game_record(str(appid))
            if not game_info:
                return {"status": "error", "message": "Game not found in Steam library."}
            install_root = Path(game_info["install_path"])
            if not install_root.exists():
                return {"status": "error", "message": "Game install directory does not exist."}
            if self._is_game_running(game_info):
                return {"status": "error", "message": "Close the game before patching."}
            fgmod_path = Path(decky.HOME) / "fgmod"
            if not fgmod_path.exists():
                return {"status": "error", "message": "OptiScaler bundle not installed. Run Install first."}

            # Preserve true original launch options across re-patches
            original_launch_options = current_launch_options or ""
            existing_marker = self._find_marker(install_root)
            existing_marker_metadata = self._read_marker(existing_marker) if existing_marker else {}
            existing_marker_target_dir = Path(
                existing_marker_metadata.get("target_dir", str(existing_marker.parent))
            ) if existing_marker else None
            if existing_marker:
                stored_opts = str(existing_marker_metadata.get("original_launch_options") or "")
                if stored_opts and not self._is_managed_launch_options(stored_opts):
                    original_launch_options = stored_opts
            if self._is_managed_launch_options(original_launch_options):
                original_launch_options = ""

            # Auto-detect the right directory to patch
            target_dir, target_exe = self._guess_patch_target(game_info)
            decky.logger.info(f"[Framegen] patch_game: appid={appid} dll={dll_name} target={target_dir} exe={target_exe}")

            allow_managed_support_cleanup = bool(
                existing_marker and existing_marker_target_dir == target_dir
            ) or (target_dir / MARKER_FILENAME).exists()
            result = self._manual_patch_directory_impl(
                target_dir,
                dll_name,
                fsr4_variant,
                allow_managed_support_cleanup=allow_managed_support_cleanup,
            )
            if result["status"] != "success":
                return result

            backed_up = [dll for dll in dict.fromkeys(RESTORABLE_BACKUP_FILES) if (target_dir / f"{dll}.b").exists()]
            marker_path = target_dir / MARKER_FILENAME
            self._write_marker(
                marker_path,
                appid=str(appid),
                game_name=game_info["name"],
                dll_name=dll_name,
                target_dir=target_dir,
                original_launch_options=original_launch_options,
                backed_up_files=backed_up,
                optiscaler_version=result.get("optiscaler_version"),
                fsr4_variant=result.get("fsr4_variant"),
                fsr4_upscaler_sha256=result.get("fsr4_upscaler_sha256"),
            )

            if existing_marker and existing_marker != marker_path:
                try:
                    existing_marker.unlink()
                except Exception:
                    pass

            managed_launch_options = self._build_managed_launch_options(dll_name)
            decky.logger.info(f"[Framegen] patch_game success: appid={appid} launch_options={managed_launch_options}")
            return {
                "status": "success",
                "appid": str(appid),
                "name": game_info["name"],
                "dll_name": dll_name,
                "target_dir": str(target_dir),
                "launch_options": managed_launch_options,
                "original_launch_options": original_launch_options,
                "optiscaler_version": result.get("optiscaler_version"),
                "fsr4_variant": result.get("fsr4_variant"),
                "fsr4_variant_label": result.get("fsr4_variant_label"),
                "fsr4_upscaler_sha256": result.get("fsr4_upscaler_sha256"),
                "message": (
                    f"Patched {game_info['name']} using {dll_name} "
                    f"with {result.get('fsr4_variant_label', FSR4_VARIANTS[self._normalize_fsr4_variant(fsr4_variant)]['label'])}."
                ),
            }
        except Exception as exc:
            decky.logger.error(f"[Framegen] patch_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    async def unpatch_game(self, appid: str) -> dict:
        try:
            game_info = self._game_record(str(appid))
            if not game_info:
                return {"status": "error", "message": "Game not found in Steam library."}
            install_root = Path(game_info["install_path"])
            if not install_root.exists():
                return {
                    "status": "success",
                    "appid": str(appid),
                    "name": game_info["name"],
                    "launch_options": "",
                    "message": "Game install directory does not exist.",
                }
            if self._is_game_running(game_info):
                return {"status": "error", "message": "Close the game before unpatching."}
            marker = self._find_marker(install_root)
            if not marker:
                return {
                    "status": "success",
                    "appid": str(appid),
                    "name": game_info["name"],
                    "launch_options": "",
                    "message": "No Framegen patch found for this game.",
                }
            metadata = self._read_marker(marker)
            target_dir = Path(metadata.get("target_dir", str(marker.parent)))
            original_launch_options = str(metadata.get("original_launch_options") or "")
            self._manual_unpatch_directory_impl(target_dir)
            try:
                marker.unlink()
            except FileNotFoundError:
                pass
            decky.logger.info(f"[Framegen] unpatch_game success: appid={appid} target={target_dir}")
            return {
                "status": "success",
                "appid": str(appid),
                "name": game_info["name"],
                "launch_options": original_launch_options,
                "message": f"Unpatched {game_info['name']}.",
            }
        except Exception as exc:
            decky.logger.error(f"[Framegen] unpatch_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}



# ===== ReShade backend (from LetMeReShadeAll) =====
class _ReShadeMixin:
    def __init__(self):
        self.environment = {
            'XDG_DATA_HOME': os.path.expandvars('$HOME/.local/share'),
            'UPDATE_RESHADE': '1',
            'MERGE_SHADERS': '1',
            'VULKAN_SUPPORT': '0',
            'GLOBAL_INI': 'ReShade.ini',
            'DELETE_RESHADE_FILES': '0',
            'FORCE_RESHADE_UPDATE_CHECK': '0',
            'RESHADE_ADDON_SUPPORT': '0',
            'AUTOHDR_ENABLED': '0'
        }
        # Main paths for ReShade
        self.main_path = os.path.join(self.environment['XDG_DATA_HOME'], 'reshade')
        
        # Cache for executable paths
        self.executable_cache = {}
        self.reshade_release_cache = {}
        
        # Create necessary directories
        os.makedirs(self.main_path, exist_ok=True)

    def _get_assets_dir(self) -> Path:
        """Get the assets directory, checking both possible locations"""
        plugin_dir = Path(decky.DECKY_PLUGIN_DIR)
        
        # Check defaults/assets first (development)
        defaults_assets = plugin_dir / "defaults" / "assets"
        if defaults_assets.exists():
            decky.logger.info(f"Using assets from: {defaults_assets}")
            return defaults_assets
            
        # Check assets (decky store installation)
        assets = plugin_dir / "assets"
        if assets.exists():
            decky.logger.info(f"Using assets from: {assets}")
            return assets
            
        # Fallback to defaults/assets even if it doesn't exist (for error reporting)
        decky.logger.warning(f"Neither {defaults_assets} nor {assets} exists, defaulting to {defaults_assets}")
        return defaults_assets

    def _get_plugin_root_dir(self) -> Path:
        return Path(decky.DECKY_PLUGIN_DIR)

    def _get_bin_dir(self) -> Path:
        return self._get_plugin_root_dir() / "bin"

    def _sha256_file(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _load_remote_binary_manifest(self) -> list[dict]:
        package_json_path = self._get_plugin_root_dir() / "package.json"
        with open(package_json_path, "r", encoding="utf-8") as package_file:
            package_data = json.load(package_file)
        return package_data.get("remote_binary", [])

    def _download_remote_binary(self, entry: dict, destination: Path) -> None:
        temp_destination = destination.with_suffix(destination.suffix + ".part")
        try:
            request = Request(
                entry["url"],
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                    "Accept": "*/*"
                }
            )
            errors = []

            try:
                with urlopen(request, timeout=60) as response, open(temp_destination, "wb") as output_file:
                    shutil.copyfileobj(response, output_file)
            except Exception as error:
                errors.append(f"urlopen: {error}")
                try:
                    insecure_context = ssl._create_unverified_context()
                    with urlopen(request, timeout=60, context=insecure_context) as response, open(temp_destination, "wb") as output_file:
                        shutil.copyfileobj(response, output_file)
                except Exception as insecure_error:
                    errors.append(f"urlopen_unverified: {insecure_error}")
                    curl_commands = (
                        ["curl", "-fsSL", "--retry", "2", "--connect-timeout", "20", "--compressed", "--http1.1", entry["url"], "-o", str(temp_destination)],
                        ["curl", "-k", "-fsSL", "--retry", "2", "--connect-timeout", "20", "--compressed", "--http1.1", entry["url"], "-o", str(temp_destination)]
                    )

                    download_succeeded = False
                    for command in curl_commands:
                        process = subprocess.run(
                            command,
                            capture_output=True,
                            text=True,
                            timeout=90,
                            env=os.environ.copy()
                        )
                        if process.returncode == 0 and temp_destination.exists():
                            download_succeeded = True
                            break
                        errors.append(process.stderr.strip() or "curl download failed")

                    if not download_succeeded:
                        raise RuntimeError(f"Failed to download {entry['name']}: {' | '.join(errors)}")

            expected_hash = entry.get("sha256hash")
            if expected_hash:
                actual_hash = self._sha256_file(temp_destination)
                if actual_hash.lower() != expected_hash.lower():
                    raise RuntimeError(
                        f"Hash mismatch for {entry['name']}: expected {expected_hash}, got {actual_hash}"
                    )

            temp_destination.replace(destination)
        finally:
            if temp_destination.exists():
                temp_destination.unlink(missing_ok=True)

    def _ensure_runtime_binaries(self, required_names: list[str] | None = None) -> Path:
        bin_dir = self._get_bin_dir()
        bin_dir.mkdir(parents=True, exist_ok=True)

        manifest_entries = self._load_remote_binary_manifest()
        if required_names is not None:
            required_name_set = set(required_names)
            manifest_entries = [entry for entry in manifest_entries if entry.get("name") in required_name_set]

        for entry in manifest_entries:
            destination = bin_dir / entry["name"]
            expected_hash = entry.get("sha256hash")

            if destination.exists() and expected_hash:
                try:
                    actual_hash = self._sha256_file(destination)
                    if actual_hash.lower() == expected_hash.lower():
                        continue
                    decky.logger.warning(f"Existing binary hash mismatch for {entry['name']}, re-downloading")
                except Exception as error:
                    decky.logger.warning(f"Could not verify {entry['name']}: {error}")
                destination.unlink(missing_ok=True)
            elif destination.exists():
                continue

            decky.logger.info(f"Downloading runtime binary: {entry['name']}")
            self._download_remote_binary(entry, destination)

        return bin_dir

    async def parse_steam_logs_for_executable(self, appid: str) -> dict:
        """Parse Steam console logs to find the exact executable path Steam uses"""
        try:
            decky.logger.info(f"Parsing Steam logs for App ID: {appid}")
            
            # Check cache first
            cache_key = f"steam_log_{appid}"
            if cache_key in self.executable_cache:
                cached_result = self.executable_cache[cache_key]
                # Check if cache is less than 1 hour old
                if time.time() - cached_result.get('timestamp', 0) < 3600:
                    decky.logger.info(f"Using cached result for {appid}")
                    return cached_result
            
            # Steam log file locations
            log_files = [
                "/home/deck/.steam/steam/logs/console-linux.txt",
                "/home/deck/.steam/steam/logs/console_log.txt", 
                "/home/deck/.steam/steam/logs/console_log.previous.txt"
            ]
            
            executable_path = None
            launch_command = None
            
            for log_file in log_files:
                if not os.path.exists(log_file):
                    continue
                    
                decky.logger.info(f"Checking log file: {log_file}")
                
                try:
                    # Read the log file (check last 10000 lines for performance)
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        # Check recent lines first (Steam logs can be large)
                        recent_lines = lines[-10000:] if len(lines) > 10000 else lines
                        
                    # Look for game launch patterns
                    for line in recent_lines:
                        # Pattern 1: Direct executable in launch command
                        # Example: AppId=501300 -- ... '/path/to/game.exe'
                        if f"AppId={appid}" in line and ".exe" in line:
                            # Extract the executable path
                            exe_match = re.search(r"'([^']*\.exe)'", line)
                            if exe_match:
                                potential_exe = exe_match.group(1)
                                # Verify this is a real path and not a temp file
                                if "/steamapps/common/" in potential_exe and os.path.exists(potential_exe):
                                    executable_path = potential_exe
                                    launch_command = line.strip()
                                    decky.logger.info(f"Found executable from logs: {executable_path}")
                                    break
                        
                        # Pattern 2: Game process added/updated logs
                        # Example: Game process added : AppID 501300 "command with exe path"
                        if f"AppID {appid}" in line and (".exe" in line or "Game process" in line):
                            exe_match = re.search(r"'([^']*\.exe)'", line)
                            if not exe_match:
                                # Try different quote patterns
                                exe_match = re.search(r'"([^"]*\.exe)"', line)
                            if exe_match:
                                potential_exe = exe_match.group(1)
                                if "/steamapps/common/" in potential_exe and os.path.exists(potential_exe):
                                    executable_path = potential_exe
                                    launch_command = line.strip()
                                    decky.logger.info(f"Found executable from process log: {executable_path}")
                                    break
                    
                    if executable_path:
                        break
                        
                except Exception as e:
                    decky.logger.error(f"Error reading log file {log_file}: {str(e)}")
                    continue
            
            if executable_path:
                # Cache the result
                result = {
                    "status": "success",
                    "method": "steam_logs",
                    "executable_path": executable_path,
                    "directory_path": os.path.dirname(executable_path),
                    "filename": os.path.basename(executable_path),
                    "launch_command": launch_command,
                    "timestamp": time.time()
                }
                self.executable_cache[cache_key] = result
                
                return result
            else:
                decky.logger.info(f"No executable found in logs for App ID: {appid}")
                return {
                    "status": "not_found",
                    "method": "steam_logs", 
                    "message": "No executable path found in Steam logs"
                }
                
        except Exception as e:
            decky.logger.error(f"Error parsing Steam logs: {str(e)}")
            return {
                "status": "error",
                "method": "steam_logs",
                "message": str(e)
            }

    async def find_game_executable_enhanced(self, appid: str) -> dict:
        """Enhanced executable detection with simplified Linux game detection"""
        try:
            decky.logger.info(f"Enhanced detection with simplified Linux check for App ID: {appid}")
            
            # Get the base game path using existing method
            try:
                steam_root = Path(decky.HOME) / ".steam" / "steam"
                library_file = steam_root / "steamapps" / "libraryfolders.vdf"

                if not library_file.exists():
                    return {"status": "error", "message": "Steam library file not found"}

                library_paths = []
                with open(library_file, "r", encoding="utf-8") as file:
                    for line in file:
                        if '"path"' in line:
                            path = line.split('"path"')[1].strip().strip('"').replace("\\\\", "/")
                            library_paths.append(path)

                base_game_path = None
                game_name = None
                for library_path in library_paths:
                    manifest_path = Path(library_path) / "steamapps" / f"appmanifest_{appid}.acf"
                    if manifest_path.exists():
                        with open(manifest_path, "r", encoding="utf-8") as manifest:
                            manifest_content = manifest.read()
                            for line in manifest_content.split('\n'):
                                if '"installdir"' in line:
                                    install_dir = line.split('"installdir"')[1].strip().strip('"')
                                    base_game_path = str(Path(library_path) / "steamapps" / "common" / install_dir)
                                    game_name = install_dir
                                elif '"name"' in line:
                                    game_title = line.split('"name"')[1].strip().strip('"')
                                    if not game_name:
                                        game_name = game_title
                        break

                if not base_game_path:
                    return {"status": "error", "message": f"Could not find installation directory for AppID: {appid}"}
                    
                decky.logger.info(f"Base game path: {base_game_path}")
                decky.logger.info(f"Game name from Steam: {game_name}")
                
                # Check appmanifest for Linux indicators
                manifest_has_linux = False
                for library_path in library_paths:
                    manifest_path = Path(library_path) / "steamapps" / f"appmanifest_{appid}.acf"
                    if manifest_path.exists():
                        with open(manifest_path, "r", encoding="utf-8") as manifest:
                            manifest_content = manifest.read().lower()
                            if "linux" in manifest_content:
                                manifest_has_linux = True
                                decky.logger.info("Found 'linux' in appmanifest")
                                break
                
            except Exception as e:
                return {"status": "error", "message": str(e)}
            
            game_path_obj = Path(base_game_path)
            if not game_path_obj.exists():
                return {"status": "error", "message": f"Game path not found: {base_game_path}"}
            
            # Simplified Linux detection - only check for key indicators
            linux_indicators = {
                'so_files': [],
                'sh_files': []
            }
            
            all_executables = []
            
            decky.logger.info(f"Scanning directory tree for executables and Linux indicators: {base_game_path}")
            
            # Single directory traversal
            for root, dirs, files in os.walk(base_game_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_obj = Path(file_path)
                    rel_path = os.path.relpath(file_path, base_game_path)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        continue
                    
                    # Check for Windows executables
                    if file.lower().endswith('.exe'):
                        all_executables.append({
                            "path": file_path,
                            "directory_path": os.path.dirname(file_path),
                            "relative_path": rel_path,
                            "filename": file,
                            "size": file_size,
                            "size_mb": round(file_size / (1024 * 1024), 1),
                            "type": "windows_exe"
                        })
                        decky.logger.debug(f"Found Windows exe: {file} ({rel_path}) - {round(file_size / (1024 * 1024), 1)}MB")
                    
                    # Simplified Linux detection - only .so and .sh files
                    file_lower = file.lower()
                    
                    # Check for .so files
                    if file_lower.endswith('.so') or '.so.' in file_lower:
                        linux_indicators['so_files'].append(rel_path)
                        decky.logger.debug(f"Found .so file: {rel_path}")
                    
                    # Check for .sh files
                    elif file_lower.endswith('.sh'):
                        linux_indicators['sh_files'].append(rel_path)
                        decky.logger.debug(f"Found .sh file: {rel_path}")
            
            # Filter out utility executables from Windows list
            main_windows_executables = []
            for exe in all_executables:
                if exe["type"] == "windows_exe":
                    exe_name = exe["filename"].lower()
                    if not any(skip in exe_name for skip in ["unins", "redist", "vcredist", "directx", "setup", "install"]):
                        main_windows_executables.append(exe)
            
            # Simplified Linux game determination
            is_linux_game = False
            linux_confidence = "low"
            linux_reasons = []
            
            # Check for Linux indicators
            so_file_count = len(linux_indicators['so_files'])
            sh_file_count = len(linux_indicators['sh_files'])
            
            if manifest_has_linux:
                is_linux_game = True
                linux_confidence = "high"
                linux_reasons.append("Steam manifest contains 'linux'")
            
            if so_file_count >= 5:  # Multiple .so files is a strong indicator
                is_linux_game = True
                if linux_confidence != "high":
                    linux_confidence = "medium"
                linux_reasons.append(f"Found {so_file_count} shared library (.so) files")
            
            if sh_file_count >= 2:  # Multiple shell scripts
                is_linux_game = True
                if linux_confidence == "low":
                    linux_confidence = "medium"
                linux_reasons.append(f"Found {sh_file_count} shell script (.sh) files")
            
            # If no Windows executables and Linux indicators present
            if not main_windows_executables and (so_file_count > 0 or sh_file_count > 0):
                is_linux_game = True
                if linux_confidence == "low":
                    linux_confidence = "medium"
                linux_reasons.append("No Windows executables found, Linux files present")
            
            # If it's determined to be a Linux game, return early with warning
            if is_linux_game and linux_confidence in ["high", "medium"]:
                return {
                    "status": "linux_game_detected",
                    "method": "enhanced_detection_with_simplified_linux_check",
                    "is_linux_game": True,
                    "linux_confidence": linux_confidence,
                    "linux_reasons": linux_reasons,
                    "linux_indicators": linux_indicators,
                    "windows_executables_found": len(main_windows_executables),
                    "message": "Linux version detected - ReShade requires Windows version through Proton",
                    "details": {
                        "game_path": base_game_path,
                        "total_files_scanned": len(all_executables),
                        "windows_exe_count": len(main_windows_executables),
                        "so_files_count": so_file_count,
                        "sh_files_count": sh_file_count
                    },
                    "scan_summary": {
                        "total_files_scanned": len(all_executables),
                        "windows_executables": len(all_executables),
                        "main_windows_executables": len(main_windows_executables),
                        "so_files": so_file_count,
                        "sh_files": sh_file_count,
                        "linux_indicators_found": so_file_count + sh_file_count
                    }
                }
            
            # Continue with Windows executable analysis if not a Linux game
            if not main_windows_executables:
                return {
                    "status": "error",
                    "method": "enhanced_detection_with_simplified_linux_check",
                    "is_linux_game": is_linux_game,
                    "linux_confidence": linux_confidence,
                    "message": f"No suitable Windows executables found in game directory: {base_game_path}",
                    "details": {
                        "total_executables_found": len(all_executables),
                        "windows_exe_count": len(all_executables),
                        "main_windows_exe_count": len(main_windows_executables),
                        "so_files_count": so_file_count,
                        "sh_files_count": sh_file_count
                    },
                    "scan_summary": {
                        "total_files_scanned": len(all_executables),
                        "windows_executables": len(all_executables),
                        "main_windows_executables": len(main_windows_executables),
                        "so_files": so_file_count,
                        "sh_files": sh_file_count,
                        "linux_indicators_found": so_file_count + sh_file_count
                    }
                }
            
            decky.logger.info(f"Found {len(main_windows_executables)} Windows executables for scoring")
            
            # ENHANCED SCORING for Windows executables (keeping existing logic)
            def score_executable(exe_info):
                score = 50
                filename = exe_info["filename"].lower()
                filename_no_ext = os.path.splitext(filename)[0]
                rel_path = exe_info["relative_path"].lower()
                size_mb = exe_info["size_mb"]
                
                decky.logger.debug(f"Scoring {filename} at {rel_path}")
                
                # Enhanced game name matching with multiple normalization approaches
                clean_game_name = re.sub(r'[^a-z0-9]', '', game_name.lower()) if game_name else ""
                clean_filename = re.sub(r'[^a-z0-9]', '', filename_no_ext)
                
                # Split into words for more flexible matching
                game_name_words = re.findall(r'[a-z0-9]+', game_name.lower()) if game_name else []
                filename_words = re.findall(r'[a-z0-9]+', filename_no_ext)
                
                # Calculate various types of matches
                name_match_score = 0
                
                # Exact matches (highest priority)
                if clean_filename == clean_game_name:
                    name_match_score += 60
                    decky.logger.debug(f"  Exact name match: +60 (normalized names match exactly)")
                
                # Substantial partial matches (high priority)
                elif clean_game_name and (clean_game_name in clean_filename or clean_filename in clean_game_name):
                    # Calculate how much of the string matches
                    match_ratio = max(
                        len(clean_game_name) / len(clean_filename) if len(clean_filename) > 0 else 0,
                        len(clean_filename) / len(clean_game_name) if len(clean_game_name) > 0 else 0
                    )
                    # Scale the score based on how much of the string matches (max 45 points)
                    partial_score = min(45, int(match_ratio * 45))
                    name_match_score += partial_score
                    decky.logger.debug(f"  Partial name match: +{partial_score} (ratio: {match_ratio:.2f})")
                
                # Word-level matches (medium priority)
                else:
                    # Find matching words between game name and filename
                    matching_words = set(game_name_words).intersection(set(filename_words))
                    
                    if matching_words:
                        # Calculate match percentage relative to the source words
                        match_percentage = len(matching_words) / len(game_name_words) if game_name_words else 0
                        word_score = len(matching_words) * 8 * (1 + match_percentage)  # Scale based on percentage match
                        name_match_score += min(40, round(word_score))  # Cap at 40 points
                        decky.logger.debug(f"  Word match: +{min(40, round(word_score))} ({matching_words})")
                
                # Common game executable names bonus
                if any(common in filename_no_ext.lower() for common in ["game", "main", "client", "app", "play"]):
                    common_bonus = 15
                    name_match_score += common_bonus
                    decky.logger.debug(f"  Common game exe name: +{common_bonus}")
                
                # Add the name match score to the total score
                score += name_match_score
                
                # Size-based scoring (reduced weights)
                size_score = 0
                if size_mb > 50:      # Large games
                    size_score = 10  # Reduced from 35
                elif size_mb > 20:    # Medium games  
                    size_score = 8   # Reduced from 25
                elif size_mb > 5:     # Small games
                    size_score = 5   # Reduced from 15
                elif size_mb > 1:     # Small but not tiny
                    size_score = 2   # Reduced from 5
                elif size_mb < 0.5:   # Very small files (likely utilities)
                    size_score = -20  # Keep this penalty to avoid tiny utility executables
                
                score += size_score
                decky.logger.debug(f"  Size score: +{size_score} ({size_mb} MB)")
                
                # Path-based scoring (more moderate)
                path_score = 0
                if "binaries/win64" in rel_path or "binaries\\win64" in rel_path:    # Unreal Engine pattern
                    path_score += 15  # Reduced from 25
                elif "bin" in rel_path:             # Common bin directory
                    path_score += 10  # Reduced from 15
                elif "game" in rel_path:            # Game subdirectory
                    path_score += 8   # Reduced from 10
                elif rel_path.count("/") == 0 and rel_path.count("\\") == 0:  # Root directory
                    path_score += 5   # Reduced from 8
                
                score += path_score
                decky.logger.debug(f"  Path score: +{path_score}")
                
                # Special patterns from real data (more moderate)
                special_score = 0
                if "shipping" in filename:          # Unreal shipping builds
                    special_score += 15  # Reduced from 20
                elif "win64" in filename:           # 64-bit indicator
                    special_score += 5   # Reduced from 8
                elif "launcher" in filename:        # Launchers (lower score but don't exclude)
                    special_score -= 25  # Increased penalty from 15
                
                score += special_score
                if special_score != 0:
                    decky.logger.debug(f"  Special pattern score: {special_score}")
                
                # Moderate penalty for deep nesting
                path_depth = rel_path.count("/") + rel_path.count("\\")
                if path_depth > 4:  # Increased threshold
                    depth_penalty = (path_depth - 4) * 3
                    score -= depth_penalty
                    decky.logger.debug(f"  Deep nesting penalty: -{depth_penalty}")
                
                # Cap score between 0 and 100
                score = max(0, min(100, score))
                
                # Round to 1 decimal place for cleaner display
                score = round(score, 1)
                
                decky.logger.debug(f"  Final score for {filename}: {score} (name match: {name_match_score})")
                return score
            
            # Score all Windows executables
            scored_executables = []
            for exe_info in main_windows_executables:
                score = score_executable(exe_info)
                if score > 0:
                    scored_executables.append({
                        **exe_info,
                        "score": score
                    })
                else:
                    decky.logger.debug(f"Filtered out {exe_info['filename']} with score {score}")
            
            if not scored_executables:
                return {
                    "status": "error",
                    "method": "enhanced_detection_with_simplified_linux_check",
                    "is_linux_game": is_linux_game,
                    "message": "No suitable Windows executables found after scoring",
                    "scan_summary": {
                        "total_files_scanned": len(all_executables),
                        "windows_executables": len(all_executables),
                        "main_windows_executables": len(main_windows_executables),
                        "so_files": so_file_count,
                        "sh_files": sh_file_count,
                        "linux_indicators_found": so_file_count + sh_file_count
                    }
                }
            
            # Sort and get top results
            scored_executables.sort(key=lambda x: x["score"], reverse=True)
            top_executables = scored_executables[:5]
            best_executable = top_executables[0]
            
            decky.logger.info(f"Top executable: {best_executable['filename']} (score: {best_executable['score']})")
            
            return {
                "status": "success",
                "method": "enhanced_detection_with_simplified_linux_check",
                "executable_path": best_executable["path"],
                "directory_path": best_executable["directory_path"],
                "filename": best_executable["filename"],
                "all_executables": top_executables,
                "confidence": "high" if best_executable["score"] > 70 else "medium",
                "is_linux_game": is_linux_game,
                "linux_confidence": linux_confidence,
                "linux_reasons": linux_reasons if linux_reasons else None,
                "scan_summary": {
                    "total_files_scanned": len(all_executables),
                    "windows_executables": len(all_executables),
                    "main_windows_executables": len(main_windows_executables),
                    "so_files": so_file_count,
                    "sh_files": sh_file_count,
                    "linux_indicators_found": so_file_count + sh_file_count
                }
            }
            
        except Exception as e:
            decky.logger.error(f"Enhanced detection error: {str(e)}")
            return {
                "status": "error",
                "method": "enhanced_detection_with_simplified_linux_check",
                "message": str(e)
            }

    async def find_game_executable_path(self, appid: str) -> dict:
        """
        Primary method that runs BOTH Steam logs and enhanced detection, returning both results
        """
        try:
            decky.logger.info(f"Finding executable path for App ID: {appid}")
            base_game_path = None

            try:
                base_game_path = self._get_steam_game_install_path(appid)
            except ValueError as error:
                decky.logger.warning(f"Could not resolve Steam game install path for picker: {error}")
            
            # Method 1: Steam console logs
            steam_logs_result = await self.parse_steam_logs_for_executable(appid)
            
            # Method 2: Enhanced detection (now includes Linux detection)
            enhanced_result = await self.find_game_executable_enhanced(appid)
            
            # Handle special case where enhanced detection found a Linux game
            if enhanced_result.get("status") == "linux_game_detected":
                # Return the Linux detection as the enhanced result
                return {
                    "status": "success", 
                    "steam_logs_result": steam_logs_result,
                    "enhanced_detection_result": enhanced_result,
                    "recommended_method": "enhanced_detection",  # Linux detection takes priority
                    "linux_game_warning": True,
                    "base_game_path": base_game_path
                }
            
            # Determine recommended method for Windows games
            recommended_method = "steam_logs"
            if steam_logs_result["status"] != "success":
                recommended_method = "enhanced_detection"
            
            return {
                "status": "success",
                "steam_logs_result": steam_logs_result,
                "enhanced_detection_result": enhanced_result,
                "recommended_method": recommended_method,
                "base_game_path": base_game_path
            }
            
        except Exception as e:
            decky.logger.error(f"Error in find_game_executable_path: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def find_heroic_game_executable_path(self, game_path: str, game_name: str) -> dict:
        """
        Find executable paths for a Heroic game, similar to Steam game detection
        """
        try:
            decky.logger.info(f"Finding executable path for Heroic game: {game_name} at {game_path}")
            
            # Check cache first
            cache_key = f"heroic_{game_path}_{game_name}"
            if cache_key in self.executable_cache:
                cached_result = self.executable_cache[cache_key]
                # Check if cache is less than 1 hour old
                if time.time() - cached_result.get('timestamp', 0) < 3600:
                    decky.logger.info(f"Using cached result for {game_name}")
                    return cached_result
            
            # Verify game path exists
            if not os.path.exists(game_path):
                return {"status": "error", "message": f"Game path not found: {game_path}"}
            
            game_path_obj = Path(game_path)
            
            # Find all executables in the game directory
            all_executables = []
            
            decky.logger.info(f"Walking directory tree starting from: {game_path}")
            for root, dirs, files in os.walk(game_path):
                for file in files:
                    if file.lower().endswith('.exe'):
                        exe_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(exe_path)
                            rel_path = os.path.relpath(exe_path, game_path)
                            
                            all_executables.append({
                                "path": exe_path,
                                "directory_path": os.path.dirname(exe_path),
                                "relative_path": rel_path,
                                "filename": file,
                                "size": file_size,
                                "size_mb": round(file_size / (1024 * 1024), 1)
                            })
                            decky.logger.debug(f"Found exe: {file} ({rel_path}) - {round(file_size / (1024 * 1024), 1)}MB")
                        except Exception as e:
                            decky.logger.warning(f"Error getting size for {exe_path}: {str(e)}")
                            continue
            
            if not all_executables:
                return {
                    "status": "error",
                    "method": "heroic_enhanced_detection",
                    "message": f"No executables found in game directory: {game_path}"
                }
            
            decky.logger.info(f"Found {len(all_executables)} total executables")
            
            # Enhanced filtering based on discovered patterns
            def score_executable(exe_info):
                score = 50  # Start with a base score
                filename = exe_info["filename"].lower()
                filename_no_ext = os.path.splitext(filename)[0]  # Remove extension
                rel_path = exe_info["relative_path"].lower()
                size_mb = exe_info["size_mb"]
                
                decky.logger.debug(f"Scoring {filename} at {rel_path}")
                
                # LESS aggressive utility filtering - only skip very obvious ones
                utility_keywords = ["unins", "setup", "vcredist", "directx", "redist"]
                if any(skip in filename for skip in utility_keywords):
                    decky.logger.debug(f"  Utility file detected: {filename}")
                    return 0
                
                # Enhanced game name matching with multiple normalization approaches
                # 1. Get directory name and clean game name
                dir_name = os.path.basename(game_path).lower()
                clean_game_name = game_name.lower()
                
                # 2. Clean up names by removing spaces, special chars, etc.
                clean_dir_name = re.sub(r'[^a-z0-9]', '', dir_name)
                norm_game_name = re.sub(r'[^a-z0-9]', '', clean_game_name)
                norm_filename = re.sub(r'[^a-z0-9]', '', filename_no_ext)
                
                # 3. Split into words for more flexible matching
                dir_words = re.findall(r'[a-z0-9]+', dir_name)
                game_name_words = re.findall(r'[a-z0-9]+', clean_game_name)
                filename_words = re.findall(r'[a-z0-9]+', filename_no_ext)
                
                # Log the normalized values for debugging
                decky.logger.debug(f"  Normalized names - Dir: '{clean_dir_name}', Game: '{norm_game_name}', File: '{norm_filename}'")
                
                # 4. Calculate various types of matches
                name_match_score = 0
                
                # Exact matches (highest priority)
                if norm_filename == norm_game_name or norm_filename == clean_dir_name:
                    name_match_score += 60
                    decky.logger.debug(f"  Exact name match: +60 (normalized names match exactly)")
                
                # Handle specific cases like "among us.exe" vs "amongus" folder
                elif (norm_filename.replace(" ", "") == norm_game_name or 
                    norm_game_name.replace(" ", "") == norm_filename or
                    norm_filename.replace(" ", "") == clean_dir_name or
                    clean_dir_name.replace(" ", "") == norm_filename):
                    name_match_score += 55
                    decky.logger.debug(f"  Space-normalized match: +55")
                
                # Substantial partial matches (high priority)
                elif (norm_game_name in norm_filename or norm_filename in norm_game_name or
                    clean_dir_name in norm_filename or norm_filename in clean_dir_name):
                    # Calculate how much of the string matches
                    match_ratio = max(
                        len(norm_game_name) / len(norm_filename) if len(norm_filename) > 0 else 0,
                        len(norm_filename) / len(norm_game_name) if len(norm_game_name) > 0 else 0,
                        len(clean_dir_name) / len(norm_filename) if len(norm_filename) > 0 else 0,
                        len(norm_filename) / len(clean_dir_name) if len(clean_dir_name) > 0 else 0
                    )
                    # Scale the score based on how much of the string matches (max 45 points)
                    partial_score = min(45, int(match_ratio * 45))
                    name_match_score += partial_score
                    decky.logger.debug(f"  Partial name match: +{partial_score} (ratio: {match_ratio:.2f})")
                    
                    # Extra case for when folder has additional characters (like "DREDGEmKMzX" vs "DREDGE.exe")
                    if (norm_filename in clean_dir_name and len(norm_filename) > 4 and
                        len(norm_filename) >= len(clean_dir_name) * 0.5):
                        extra_bonus = 15
                        name_match_score += extra_bonus
                        decky.logger.debug(f"  Extra partial match bonus: +{extra_bonus} (likely main game exe)")
                
                # Word-level matches (medium priority)
                else:
                    # Find matching words between game name/dir and filename
                    matching_game_words = set(game_name_words).intersection(set(filename_words))
                    matching_dir_words = set(dir_words).intersection(set(filename_words))
                    
                    # Use the best match (dir or game name)
                    best_matches = matching_game_words if len(matching_game_words) > len(matching_dir_words) else matching_dir_words
                    if best_matches:
                        # Calculate match percentage relative to the source words
                        match_percentage = len(best_matches) / len(game_name_words) if game_name_words else 0
                        word_score = len(best_matches) * 5.0 * (1 + match_percentage)  # Scale based on percentage match
                        name_match_score += min(40, round(word_score))  # Cap at 40 points
                        decky.logger.debug(f"  Word match: +{min(40, round(word_score))} ({best_matches})")
                
                # Common game executable names bonus
                if any(common in filename_no_ext.lower() for common in ["game", "main", "client", "app", "play"]):
                    common_bonus = 15
                    name_match_score += common_bonus
                    decky.logger.debug(f"  Common game exe name: +{common_bonus}")
                
                # Add the name match score to the total score
                score += name_match_score
                
                # Size-based scoring (reduced weights)
                size_score = 0
                if size_mb > 50:      # Large games
                    size_score = 10  # Reduced from 35
                elif size_mb > 20:    # Medium games  
                    size_score = 8   # Reduced from 25
                elif size_mb > 5:     # Small games
                    size_score = 5   # Reduced from 15
                elif size_mb > 1:     # Small but not tiny
                    size_score = 2   # Reduced from 5
                elif size_mb < 0.5:   # Very small files (likely utilities)
                    size_score = -10  # Reduced from 20
                
                score += size_score
                decky.logger.debug(f"  Size score: +{size_score} ({size_mb} MB)")
                
                # Path-based scoring
                path_score = 0
                if "binaries/win64" in rel_path or "binaries\\win64" in rel_path:    # Unreal Engine pattern
                    path_score += 15  # Reduced from 25
                elif "bin" in rel_path:             # Common bin directory
                    path_score += 10  # Reduced from 15
                elif "game" in rel_path:            # Game subdirectory
                    path_score += 8   # Reduced from 10
                elif rel_path.count("/") == 0 and rel_path.count("\\") == 0:  # Root directory
                    path_score += 5   # Reduced from 8
                
                score += path_score
                decky.logger.debug(f"  Path score: +{path_score}")
                
                # Special patterns scoring
                special_score = 0
                if "shipping" in filename:          # Unreal shipping builds
                    special_score += 15  # Reduced from 20
                elif "win64" in filename:           # 64-bit indicator
                    special_score += 5   # Reduced from 8
                elif "launcher" in filename:        # Launchers (lower score but don't exclude)
                    special_score -= 25  # Increased penalty from 15
                
                score += special_score
                if special_score != 0:
                    decky.logger.debug(f"  Special pattern score: {special_score}")
                
                # Moderate penalty for deep nesting
                path_depth = rel_path.count("/") + rel_path.count("\\")
                if path_depth > 4:  # Increased threshold
                    depth_penalty = (path_depth - 4) * 3
                    score -= depth_penalty
                    decky.logger.debug(f"  Deep nesting penalty: -{depth_penalty}")
                
                # Cap score between 0 and 100
                score = max(0, min(100, score))
                
                # Round to 1 decimal place for cleaner display
                score = round(score, 1)
                
                decky.logger.debug(f"  Final score for {filename}: {score} (name match: {name_match_score})")
                return score
            
            # Score all executables
            scored_executables = []
            for exe_info in all_executables:
                score = score_executable(exe_info)
                if score > 0:
                    scored_executables.append({
                        **exe_info,
                        "score": score
                    })
                else:
                    decky.logger.debug(f"Filtered out {exe_info['filename']} with score {score}")
            
            if not scored_executables:
                # If we filtered everything out, include everything with any positive score
                decky.logger.warning("All executables filtered out, using less restrictive filtering")
                for exe_info in all_executables:
                    score = score_executable(exe_info)
                    if score >= 0:
                        scored_executables.append({
                            **exe_info,
                            "score": score
                        })
            
            if not scored_executables:
                # Last resort: include everything
                decky.logger.warning("Still no executables, including all found")
                for exe_info in all_executables:
                    scored_executables.append({
                        **exe_info,
                        "score": score_executable(exe_info)
                    })
            
            # Sort by score (highest first) and take top 5
            scored_executables.sort(key=lambda x: x["score"], reverse=True)
            top_executables = scored_executables[:5]
            
            best_executable = top_executables[0]
            
            decky.logger.info(f"Total executables after filtering: {len(scored_executables)}")
            decky.logger.info(f"Top 5 executables:")
            for i, exe in enumerate(top_executables):
                decky.logger.info(f"  {i+1}. {exe['filename']} (score: {exe['score']}) at {exe['relative_path']}")
            
            result = {
                "status": "success",
                "heroic_enhanced_detection_result": {
                    "status": "success",
                    "method": "heroic_enhanced_detection",
                    "executable_path": best_executable["path"],
                    "directory_path": best_executable["directory_path"],
                    "filename": best_executable["filename"],
                    "all_executables": top_executables,
                    "confidence": "high" if best_executable["score"] > 70 else "medium"
                },
                "recommended_method": "heroic_enhanced_detection",
                "timestamp": time.time()
            }
            
            # Cache the result
            self.executable_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            decky.logger.error(f"Heroic executable detection error: {str(e)}")
            return {
                "status": "error",
                "method": "heroic_enhanced_detection",
                "message": str(e)
            }

    async def save_shader_preferences(self, selected_shaders: list) -> dict:
        """Save user's shader preferences to a file"""
        try:
            preferences_file = os.path.join(self.main_path, "user_preferences.json")
            
            # Load existing preferences to preserve other settings
            existing_preferences = {}
            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        existing_preferences = json.load(f)
                except:
                    pass  # If file is corrupted, start fresh
            
            # Update shader preferences while preserving other settings
            existing_preferences.update({
                "selected_shaders": selected_shaders,
                "last_updated": int(time.time()),
                "version": "1.1"
            })
            
            # Ensure directory exists
            os.makedirs(self.main_path, exist_ok=True)
            
            with open(preferences_file, 'w') as f:
                json.dump(existing_preferences, f, indent=2)
            
            decky.logger.info(f"Saved shader preferences: {selected_shaders}")
            return {"status": "success", "message": "Shader preferences saved successfully"}
            
        except Exception as e:
            decky.logger.error(f"Error saving shader preferences: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def load_shader_preferences(self) -> dict:
        """Load user's shader preferences from file"""
        try:
            preferences_file = os.path.join(self.main_path, "user_preferences.json")
            
            # Also check old file for migration
            old_preferences_file = os.path.join(self.main_path, "shader_preferences.json")
            
            preferences = None
            
            # Try to load from new file first
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r') as f:
                    preferences = json.load(f)
            # Migrate from old file if exists
            elif os.path.exists(old_preferences_file):
                with open(old_preferences_file, 'r') as f:
                    old_prefs = json.load(f)
                    # Migrate to new format
                    preferences = {
                        "selected_shaders": old_prefs.get("selected_shaders", []),
                        "last_updated": old_prefs.get("last_updated", int(time.time())),
                        "version": "1.1",
                        "autohdr_enabled": False  # Default for migrated preferences
                    }
                    # Save in new format and remove old file
                    with open(preferences_file, 'w') as f:
                        json.dump(preferences, f, indent=2)
                    try:
                        os.remove(old_preferences_file)
                    except:
                        pass
            
            if not preferences:
                return {"status": "success", "preferences": None, "message": "No preferences file found"}
            
            # Validate the preferences structure
            if "selected_shaders" not in preferences:
                return {"status": "error", "message": "Invalid preferences file format"}
            
            decky.logger.info(f"Loaded shader preferences: {preferences['selected_shaders']}")
            return {
                "status": "success", 
                "preferences": preferences,
                "selected_shaders": preferences["selected_shaders"]
            }
            
        except Exception as e:
            decky.logger.error(f"Error loading shader preferences: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def has_shader_preferences(self) -> dict:
        """Check if user has saved shader preferences"""
        try:
            preferences_file = os.path.join(self.main_path, "user_preferences.json")
            old_preferences_file = os.path.join(self.main_path, "shader_preferences.json")
            
            exists = os.path.exists(preferences_file) or os.path.exists(old_preferences_file)
            
            if exists:
                # Also load and return a summary
                result = await self.load_shader_preferences()
                if result["status"] == "success" and result["preferences"]:
                    shader_count = len(result["selected_shaders"])
                    return {
                        "status": "success",
                        "has_preferences": True,
                        "shader_count": shader_count,
                        "last_updated": result["preferences"].get("last_updated", 0)
                    }
            
            return {"status": "success", "has_preferences": False}
            
        except Exception as e:
            decky.logger.error(f"Error checking shader preferences: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def save_autohdr_preference(self, autohdr_enabled: bool) -> dict:
        """Save user's AutoHDR preference"""
        try:
            preferences_file = os.path.join(self.main_path, "user_preferences.json")
            
            # Load existing preferences to preserve other settings
            existing_preferences = {}
            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        existing_preferences = json.load(f)
                except:
                    pass  # If file is corrupted, start fresh
            
            # Update AutoHDR preference while preserving other settings
            existing_preferences.update({
                "autohdr_enabled": autohdr_enabled,
                "last_updated": int(time.time()),
                "version": "1.1"
            })
            
            # Ensure selected_shaders exists if it doesn't
            if "selected_shaders" not in existing_preferences:
                existing_preferences["selected_shaders"] = []
            
            # Ensure directory exists
            os.makedirs(self.main_path, exist_ok=True)
            
            with open(preferences_file, 'w') as f:
                json.dump(existing_preferences, f, indent=2)
            
            decky.logger.info(f"Saved AutoHDR preference: {autohdr_enabled}")
            return {"status": "success", "message": "AutoHDR preference saved successfully"}
            
        except Exception as e:
            decky.logger.error(f"Error saving AutoHDR preference: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def load_autohdr_preference(self) -> dict:
        """Load user's AutoHDR preference"""
        try:
            preferences_file = os.path.join(self.main_path, "user_preferences.json")
            
            if not os.path.exists(preferences_file):
                return {"status": "success", "autohdr_enabled": False, "message": "No preferences file found"}
            
            with open(preferences_file, 'r') as f:
                preferences = json.load(f)
            
            autohdr_enabled = preferences.get("autohdr_enabled", False)
            
            decky.logger.info(f"Loaded AutoHDR preference: {autohdr_enabled}")
            return {
                "status": "success", 
                "autohdr_enabled": autohdr_enabled
            }
            
        except Exception as e:
            decky.logger.error(f"Error loading AutoHDR preference: {str(e)}")
            return {"status": "error", "message": str(e), "autohdr_enabled": False}

    async def save_installed_configuration(self, with_addon: bool, version: str, with_autohdr: bool, selected_shaders: list) -> dict:
        """Save the configuration that was actually installed"""
        try:
            config_file = os.path.join(self.main_path, "installed_config.json")
            
            installed_config = {
                "with_addon": with_addon,
                "version": version,
                "with_autohdr": with_autohdr,
                "selected_shaders": selected_shaders or [],
                "installed_at": int(time.time())
            }
            
            os.makedirs(self.main_path, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(installed_config, f, indent=2)
            
            decky.logger.info(f"Saved installed configuration: {installed_config}")
            return {"status": "success"}
            
        except Exception as e:
            decky.logger.error(f"Error saving installed configuration: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def load_installed_configuration(self) -> dict:
        """Load the configuration that was actually installed"""
        try:
            config_file = os.path.join(self.main_path, "installed_config.json")
            
            if not os.path.exists(config_file):
                return {"status": "success", "config": None}
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            return {"status": "success", "config": config}
            
        except Exception as e:
            decky.logger.error(f"Error loading installed configuration: {str(e)}")
            return {"status": "error", "message": str(e), "config": None}

    async def clear_installed_configuration(self) -> dict:
        """Clear the installed configuration (called on uninstall)"""
        try:
            config_file = os.path.join(self.main_path, "installed_config.json")
            
            if os.path.exists(config_file):
                os.remove(config_file)
            
            return {"status": "success"}
            
        except Exception as e:
            decky.logger.error(f"Error clearing installed configuration: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_available_shaders(self) -> dict:
        """Get list of available shader packages for selection"""
        try:
            shader_binary_names = [
                "reshade_shaders.tar.gz",
                "sweetfx_shaders.tar.gz",
                "martymc_shaders.tar.gz",
                "astrayfx_shaders.tar.gz",
                "prod80_shaders.tar.gz",
                "retroarch_shaders.tar.gz"
            ]
            bin_path = self._ensure_runtime_binaries(shader_binary_names)

            # Define available shader packages with descriptions
            shader_packages = [
                {
                    "id": "reshade_shaders",
                    "name": "ReShade Community Shaders",
                    "description": "Official ReShade community shader collection",
                    "file": "reshade_shaders.tar.gz",
                    "size_mb": "~15MB",
                    "enabled": True
                },
                {
                    "id": "sweetfx_shaders", 
                    "name": "SweetFX Shaders",
                    "description": "Popular SweetFX shader effects collection",
                    "file": "sweetfx_shaders.tar.gz",
                    "size_mb": "~8MB",
                    "enabled": True
                },
                {
                    "id": "martymc_shaders",
                    "name": "MartyMcFly's RT Shaders",
                    "description": "High-quality ray tracing and lighting effects",
                    "file": "martymc_shaders.tar.gz", 
                    "size_mb": "~12MB",
                    "enabled": True
                },
                {
                    "id": "astrayfx_shaders",
                    "name": "AstrayFX Shaders",
                    "description": "Performance-focused shader collection",
                    "file": "astrayfx_shaders.tar.gz",
                    "size_mb": "~5MB", 
                    "enabled": True
                },
                {
                    "id": "prod80_shaders",
                    "name": "Prod80's Shaders",
                    "description": "Professional color grading and enhancement shaders",
                    "file": "prod80_shaders.tar.gz",
                    "size_mb": "~6MB",
                    "enabled": True
                },
                {
                    "id": "retroarch_shaders",
                    "name": "RetroArch Shaders",
                    "description": "Retro gaming and CRT emulation effects",
                    "file": "retroarch_shaders.tar.gz",
                    "size_mb": "~10MB",
                    "enabled": True
                }
            ]

            # Check which shader packages actually exist
            available_shaders = []
            for shader in shader_packages:
                shader_file = bin_path / shader["file"]
                if shader_file.exists():
                    # Get actual file size
                    file_size = shader_file.stat().st_size
                    size_mb = round(file_size / (1024 * 1024), 1)
                    shader["size_mb"] = f"{size_mb}MB"
                    available_shaders.append(shader)
                else:
                    decky.logger.warning(f"Shader package not found: {shader_file}")

            return {
                "status": "success",
                "shaders": available_shaders,
                "total_count": len(available_shaders)
            }

        except Exception as e:
            decky.logger.error(f"Error getting available shaders: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def detect_steam_deck_model(self) -> dict:
        """Detect Steam Deck model (OLED vs LCD) using board name"""
        try:
            decky.logger.info("Detecting Steam Deck model...")
            
            # First check if we can read system info at all
            is_steam_deck = False
            product_name = ""
            
            try:
                with open('/sys/devices/virtual/dmi/id/product_name', 'r') as f:
                    product_name = f.read().strip()
                decky.logger.info(f"DMI Product name: '{product_name}'")
                
                # More flexible Steam Deck detection
                if any(term in product_name.lower() for term in ["steam deck", "steamdeck", "jupiter", "galileo"]):
                    is_steam_deck = True
                    decky.logger.info("Confirmed this is a Steam Deck")
                else:
                    decky.logger.warning(f"Product name '{product_name}' doesn't indicate Steam Deck")
            except (FileNotFoundError, PermissionError) as e:
                decky.logger.warning(f"Could not read DMI product name: {e}")
            
            # If we can't confirm it's a Steam Deck through product name, 
            # let's assume it is and try board detection anyway
            if not is_steam_deck:
                decky.logger.info("Could not confirm Steam Deck via product name, proceeding with board detection")
            
            # Check board name - most reliable method for Steam Deck OLED vs LCD
            board_name = ""
            try:
                with open('/sys/devices/virtual/dmi/id/board_name', 'r') as f:
                    board_name = f.read().strip()
                decky.logger.info(f"DMI Board name: '{board_name}'")
                
                # Check for OLED (Galileo)
                if "Galileo" in board_name:
                    decky.logger.info("Detected Steam Deck OLED (Galileo)")
                    return {
                        "status": "success",
                        "model": "OLED",
                        "is_oled": True
                    }
                # Check for LCD (Jupiter)
                elif "Jupiter" in board_name:
                    decky.logger.info("Detected Steam Deck LCD (Jupiter)")
                    return {
                        "status": "success",
                        "model": "LCD",
                        "is_oled": False
                    }
                else:
                    decky.logger.warning(f"Unknown board name: '{board_name}'")
                    
                    # If we confirmed it's a Steam Deck but unknown board, default to LCD
                    if is_steam_deck:
                        decky.logger.info("Confirmed Steam Deck but unknown board, defaulting to LCD")
                        return {
                            "status": "success",
                            "model": "LCD",
                            "is_oled": False
                        }
                    
            except (FileNotFoundError, PermissionError) as e:
                decky.logger.warning(f"Could not read DMI board name: {e}")
            
            # Additional fallback checks for Steam Deck detection
            try:
                # Check system manufacturer
                with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as f:
                    vendor = f.read().strip()
                decky.logger.info(f"System vendor: '{vendor}'")
                
                if "Valve" in vendor:
                    is_steam_deck = True
                    decky.logger.info("Confirmed Steam Deck via vendor")
            except (FileNotFoundError, PermissionError) as e:
                decky.logger.debug(f"Could not read sys_vendor: {e}")
            
            # Final decision logic
            if is_steam_deck:
                # We know it's a Steam Deck but couldn't determine the model
                decky.logger.info("Confirmed Steam Deck, but model detection failed - defaulting to LCD")
                return {
                    "status": "success",
                    "model": "LCD", 
                    "is_oled": False
                }
            else:
                # We couldn't confirm this is a Steam Deck
                decky.logger.info("Could not confirm this is a Steam Deck")
                return {
                    "status": "success",
                    "model": "Not Steam Deck",
                    "is_oled": False
                }
                
        except Exception as e:
            decky.logger.error(f"Error detecting Steam Deck model: {str(e)}")
            return {
                "status": "error", 
                "message": str(e),
                "model": "Unknown",
                "is_oled": False
            }

    def _parse_version_tuple(self, version: str) -> tuple[int, ...]:
        if not version or not re.fullmatch(r"\d+(?:\.\d+)+", version):
            return ()
        return tuple(int(part) for part in version.split('.'))

    def _validate_selected_windows_executable_path(self, selected_executable_path: str) -> tuple[bool, str]:
        normalized_path = os.path.abspath(os.path.expanduser(selected_executable_path or ""))

        if not normalized_path:
            return False, "No executable path was provided."

        if not normalized_path.lower().endswith(".exe"):
            return False, "Please choose a Windows executable (.exe)."

        if not os.path.exists(normalized_path):
            return False, f"Selected executable was not found: {normalized_path}"

        if not os.path.isfile(normalized_path):
            return False, f"Selected path is not a file: {normalized_path}"

        return True, normalized_path

    def _fetch_reshade_page(self, base_url: str) -> str:
        request = Request(
            base_url,
            headers={
                "User-Agent": "LetMeReShadeAll/0.8",
                "Accept": "text/html,application/xhtml+xml"
            }
        )

        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", "ignore")

    def _fetch_reshade_page_unverified(self, base_url: str) -> str:
        request = Request(
            base_url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml"
            }
        )

        insecure_context = ssl._create_unverified_context()
        with urlopen(request, timeout=20, context=insecure_context) as response:
            return response.read().decode("utf-8", "ignore")

    def _fetch_reshade_page_with_curl(self, base_url: str) -> str:
        curl_commands = (
            ["curl", "-fsSL", "--retry", "2", "--connect-timeout", "15", "--compressed", "--http1.1", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", base_url],
            ["curl", "-k", "-fsSL", "--retry", "2", "--connect-timeout", "15", "--compressed", "--http1.1", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", base_url]
        )

        last_error = None
        for command in curl_commands:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                env=os.environ.copy()
            )

            if process.returncode == 0 and process.stdout:
                return process.stdout

            last_error = process.stderr.strip() or f"curl failed for {base_url}"

        raise RuntimeError(last_error or f"curl failed for {base_url}")

    def _extract_reshade_release_candidates(self, html: str, base_url: str, with_addon: bool) -> dict:
        candidates_by_version = {}
        link_pattern = re.compile(
            r"(?:https?://[^\"'\\s>]+)?/downloads/ReShade_Setup_([0-9][0-9.]*[0-9])(_Addon)?\.exe",
            re.IGNORECASE
        )
        text_patterns = (
            re.compile(r"Version\s+([0-9][0-9.]*[0-9])\s+was\s+released", re.IGNORECASE),
            re.compile(r"Download\s+ReShade\s+([0-9][0-9.]*[0-9])(?:\s+with\s+full\s+add-on\s+support)?", re.IGNORECASE)
        )

        for version, addon_suffix in link_pattern.findall(html):
            is_addon_release = bool(addon_suffix)
            if is_addon_release != with_addon:
                continue

            download_path = f"/downloads/ReShade_Setup_{version}{addon_suffix}.exe"
            candidates_by_version[version] = {
                "version": version,
                "download_url": urljoin(base_url, download_path)
            }

        if candidates_by_version:
            return candidates_by_version

        for pattern in text_patterns:
            matches = pattern.findall(html)
            if not matches:
                continue

            for version in matches:
                download_suffix = "_Addon" if with_addon else ""
                download_path = f"/downloads/ReShade_Setup_{version}{download_suffix}.exe"
                candidates_by_version[version] = {
                    "version": version,
                    "download_url": urljoin(base_url, download_path)
                }

        return candidates_by_version

    def _resolve_latest_reshade_release(self, with_addon: bool) -> dict:
        cache_key = "addon" if with_addon else "standard"
        cached_release = self.reshade_release_cache.get(cache_key)
        if cached_release and time.time() - cached_release.get("timestamp", 0) < 14400:
            return cached_release

        candidates_by_version = {}
        base_urls = ("https://reshade.me", "https://static.reshade.me")
        fetchers = (
            self._fetch_reshade_page,
            self._fetch_reshade_page_with_curl,
            self._fetch_reshade_page_unverified
        )
        fetch_errors = []

        for base_url in base_urls:
            for fetcher in fetchers:
                try:
                    html = fetcher(base_url)
                except (HTTPError, URLError, TimeoutError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    fetch_errors.append(f"{base_url} via {fetcher.__name__}: {error}")
                    decky.logger.warning(f"Failed to fetch ReShade page from {base_url} via {fetcher.__name__}: {error}")
                    continue

                page_candidates = self._extract_reshade_release_candidates(html, base_url, with_addon)
                if page_candidates:
                    candidates_by_version.update(page_candidates)

                if candidates_by_version:
                    break

            if candidates_by_version:
                break

        if not candidates_by_version:
            error_details = " | ".join(fetch_errors[-6:]) if fetch_errors else "No fetch attempts returned content."
            raise RuntimeError(f"Unable to resolve the latest ReShade release from the official website. {error_details}")

        best_release = max(
            candidates_by_version.values(),
            key=lambda release: self._parse_version_tuple(release["version"])
        )
        best_release["timestamp"] = time.time()
        self.reshade_release_cache[cache_key] = best_release
        return best_release

    def _read_installed_reshade_version_info(self) -> dict:
        marker_file = Path(self.main_path) / ".installed"
        addon_marker = Path(self.main_path) / ".installed_addon"
        version_file = Path(self.main_path) / "reshade" / "LVERS"

        version_info = {
            "exists": marker_file.exists() or addon_marker.exists(),
            "version": "unknown",
            "addon": addon_marker.exists()
        }

        if not version_info["exists"]:
            return version_info

        if not version_file.exists():
            return version_info

        try:
            version_content = version_file.read_text(encoding="utf-8").strip()
            if version_content:
                normalized_version = version_content
                if normalized_version.lower().endswith("_addon"):
                    normalized_version = normalized_version[:-6]
                    version_info["addon"] = True
                version_info["version"] = normalized_version
        except Exception as error:
            decky.logger.error(f"Error reading version info: {str(error)}")

        return version_info

    def _is_update_available(self, installed_version: str, latest_version: str) -> bool:
        installed_tuple = self._parse_version_tuple(installed_version)
        latest_tuple = self._parse_version_tuple(latest_version)

        if not installed_tuple or not latest_tuple:
            return installed_version != latest_version

        return installed_tuple < latest_tuple

    async def check_reshade_path(self) -> dict:
        version_info = self._read_installed_reshade_version_info()

        return {
            "exists": version_info["exists"],
            "is_addon": version_info["addon"],
            "version_info": {
                "version": version_info["version"],
                "addon": version_info["addon"]
            }
        }

    async def get_reshade_update_status(self, with_addon: bool = False) -> dict:
        try:
            latest_release = self._resolve_latest_reshade_release(with_addon)
            installed_info = self._read_installed_reshade_version_info()
            installed_version = installed_info["version"] if installed_info["exists"] else None

            return {
                "status": "success",
                "installed_version": installed_version,
                "latest_version": latest_release["version"],
                "update_available": bool(
                    installed_info["exists"] and
                    self._is_update_available(installed_version or "", latest_release["version"])
                )
            }
        except Exception as error:
            decky.logger.error(f"Error resolving ReShade update status: {str(error)}")
            return {
                "status": "error",
                "message": str(error)
            }

    async def validate_windows_executable_path(self, selected_executable_path: str) -> dict:
        try:
            is_valid, result = self._validate_selected_windows_executable_path(selected_executable_path)
            if not is_valid:
                return {
                    "status": "error",
                    "valid": False,
                    "message": result
                }

            return {
                "status": "success",
                "valid": True,
                "normalized_path": result
            }
        except Exception as error:
            decky.logger.error(f"Error validating executable path: {str(error)}")
            return {
                "status": "error",
                "valid": False,
                "message": str(error)
            }

    async def browse_filesystem_for_executable(self, current_path: str = "", show_hidden: bool = True) -> dict:
        try:
            normalized_path = os.path.abspath(os.path.expanduser(current_path or "/home/deck"))

            if not os.path.exists(normalized_path):
                return {
                    "status": "error",
                    "message": f"Path not found: {normalized_path}"
                }

            if not os.path.isdir(normalized_path):
                normalized_path = os.path.dirname(normalized_path)

            entries = []
            with os.scandir(normalized_path) as directory_entries:
                for entry in directory_entries:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=True)
                        is_file = entry.is_file(follow_symlinks=True)
                    except OSError:
                        continue

                    is_hidden = entry.name.startswith(".")
                    if is_hidden and not show_hidden:
                        continue

                    if not is_dir and not (is_file and entry.name.lower().endswith(".exe")):
                        continue

                    entries.append({
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": is_dir,
                        "is_file": is_file,
                        "is_hidden": is_hidden,
                        "is_symlink": entry.is_symlink()
                    })

            entries.sort(key=lambda item: (0 if item["is_dir"] else 1, item["name"].lower()))

            if normalized_path == os.path.sep:
                parent_path = None
            else:
                parent_path = os.path.dirname(normalized_path.rstrip(os.path.sep)) or os.path.sep

            return {
                "status": "success",
                "current_path": normalized_path,
                "parent_path": parent_path,
                "entries": entries
            }
        except Exception as error:
            decky.logger.error(f"Error browsing filesystem for executable selection: {str(error)}")
            return {
                "status": "error",
                "message": str(error)
            }

    async def get_sd_card_mount_path(self) -> dict:
        try:
            search_roots = ["/run/media", "/media"]
            candidate_paths = []
            ignored_names = {"deck", "root", "media"}

            for root in search_roots:
                if not os.path.isdir(root):
                    continue

                with os.scandir(root) as root_entries:
                    for entry in root_entries:
                        if not entry.is_dir(follow_symlinks=True):
                            continue

                        if (
                            entry.name.lower() not in ignored_names and
                            os.access(entry.path, os.R_OK | os.X_OK) and
                            os.path.ismount(entry.path)
                        ):
                            candidate_paths.append(entry.path)
                            continue

                        if entry.name.lower() in ignored_names:
                            nested_dirs = []
                            try:
                                with os.scandir(entry.path) as nested_entries:
                                    nested_dirs = [
                                        nested.path
                                        for nested in nested_entries
                                        if nested.is_dir(follow_symlinks=True)
                                        and os.access(nested.path, os.R_OK | os.X_OK)
                                        and os.path.ismount(nested.path)
                                    ]
                            except OSError:
                                nested_dirs = []

                            if nested_dirs:
                                candidate_paths.extend(nested_dirs)

            unique_candidates = []
            for path in candidate_paths:
                if path not in unique_candidates:
                    unique_candidates.append(path)

            preferred_candidates = sorted(
                [
                    path for path in unique_candidates
                    if os.path.basename(path).lower() not in ignored_names
                ],
                key=lambda path: (path.count(os.path.sep), path.lower())
            )

            resolved_path = preferred_candidates[0] if preferred_candidates else (
                unique_candidates[0] if unique_candidates else "/run/media"
            )

            return {
                "status": "success",
                "path": resolved_path,
                "available": bool(unique_candidates)
            }
        except Exception as error:
            decky.logger.error(f"Error resolving SD card mount path: {str(error)}")
            return {
                "status": "error",
                "path": "/run/media",
                "available": False,
                "message": str(error)
            }

    async def run_install_reshade(self, with_addon: bool = False, with_autohdr: bool = False, selected_shaders: list = None) -> dict:
        try:
            assets_dir = self._get_assets_dir()
            script_path = assets_dir / "reshade-install.sh"
            latest_release = self._resolve_latest_reshade_release(with_addon)
            self._ensure_runtime_binaries()

            if not script_path.exists():
                decky.logger.error(f"Install script not found: {script_path}")
                return {"status": "error", "message": "Install script not found"}

            # Create a new environment dictionary for this installation
            install_env = self.environment.copy()
            
            # Explicitly set environment needed by the installer.
            install_env['RESHADE_ADDON_SUPPORT'] = '1' if with_addon else '0'
            install_env['AUTOHDR_ENABLED'] = '1' if with_autohdr else '0'
            install_env['RESHADE_RESOLVED_VERSION'] = latest_release["version"]
            install_env['RESHADE_DOWNLOAD_URL'] = latest_release["download_url"]
            
            # Set selected shaders (if provided)
            if selected_shaders is not None:
                # Convert selected shaders list to comma-separated string
                selected_shader_ids = ','.join(selected_shaders) if selected_shaders else ''
                install_env['SELECTED_SHADERS'] = selected_shader_ids
                decky.logger.info(f"Selected shader packages: {selected_shader_ids}")
            else:
                # Install all shaders (default behavior)
                install_env['SELECTED_SHADERS'] = 'all'
            
            # Add other necessary environment variables
            install_env.update({
                'LD_LIBRARY_PATH': '/usr/lib',
                'XDG_DATA_HOME': os.path.expandvars('$HOME/.local/share')
            })

            install_description = f"Installing ReShade {latest_release['version']}"
            if with_addon:
                install_description += " with addon support"
            if with_autohdr:
                install_description += " and AutoHDR components"
            if selected_shaders and selected_shaders != ['all']:
                install_description += f" with {len(selected_shaders)} shader packages"
            
            decky.logger.info(install_description)
            decky.logger.info(f"Environment: {install_env}")

            # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
            clean_env = {**os.environ, **install_env}
            clean_env["LD_LIBRARY_PATH"] = ""
            
            process = subprocess.run(
                ["/bin/bash", str(script_path)],
                cwd=str(assets_dir),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=600
            )

            decky.logger.info(f"Install output:\n{process.stdout}")
            if process.stderr:
                decky.logger.error(f"Install errors:\n{process.stderr}")

            if process.returncode != 0:
                return {"status": "error", "message": process.stderr}

            # Create appropriate installation marker
            if with_addon:
                marker_file = Path(self.main_path) / ".installed_addon"
                # Remove non-addon marker if it exists
                normal_marker = Path(self.main_path) / ".installed"
                if normal_marker.exists():
                    normal_marker.unlink()
            else:
                marker_file = Path(self.main_path) / ".installed"
                # Remove addon marker if it exists
                addon_marker = Path(self.main_path) / ".installed_addon"
                if addon_marker.exists():
                    addon_marker.unlink()

            marker_file.touch()

            # Save the installed configuration
            await self.save_installed_configuration(with_addon, latest_release["version"], with_autohdr, selected_shaders)

            # Clear executable cache since new installation might affect detection
            self.executable_cache.clear()

            # Create success message
            version_display = f"ReShade {latest_release['version']}"
            if with_addon:
                version_display += ' (with Addon Support)'
            if with_autohdr:
                version_display += ' and AutoHDR components'
            if selected_shaders and selected_shaders != ['all']:
                version_display += f' with {len(selected_shaders)} shader packages'
            
            return {"status": "success", "output": f"{version_display} installed successfully!"}
        except Exception as e:
            decky.logger.error(f"Install error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def run_uninstall_reshade(self) -> dict:
        try:
            assets_dir = self._get_assets_dir()
            script_path = assets_dir / "reshade-uninstall.sh"
            
            if not script_path.exists():
                return {"status": "error", "message": "Uninstall script not found"}

            # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
            clean_env = {**os.environ, **self.environment}
            clean_env["LD_LIBRARY_PATH"] = ""
            
            process = subprocess.run(
                ["/bin/bash", str(script_path)],
                cwd=str(assets_dir),
                env=clean_env,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                return {"status": "error", "message": process.stderr}

            # Remove installation markers
            marker_file = Path(self.main_path) / ".installed"
            addon_marker = Path(self.main_path) / ".installed_addon"
            if marker_file.exists():
                marker_file.unlink()
            if addon_marker.exists():
                addon_marker.unlink()

            # Clear installed configuration and cache
            await self.clear_installed_configuration()
            self.executable_cache.clear()
                
            return {"status": "success", "output": "ReShade uninstalled"}
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}

    async def manage_game_reshade(self, appid: str, action: str, dll_override: str = "dxgi", vulkan_mode: str = "", selected_executable_path: str = "") -> dict:
        try:
            assets_dir = self._get_assets_dir()
            script_path = assets_dir / "reshade-game-manager.sh"

            validated_executable_path = ""
            if selected_executable_path:
                is_valid, validation_result = self._validate_selected_windows_executable_path(selected_executable_path)
                if not is_valid:
                    return {"status": "error", "message": validation_result}
                validated_executable_path = validation_result

            # Track if user selected a specific executable path
            using_user_selected_path = bool(validated_executable_path)
            
            try:
                # Use selected executable path if provided, otherwise use detection
                if using_user_selected_path:
                    game_path = os.path.dirname(validated_executable_path)
                    decky.logger.info(f"Using user-selected executable path: {validated_executable_path}")
                    decky.logger.info(f"Installing ReShade to directory: {game_path}")
                elif action == "install":
                    # Get the base game installation path (not executable-specific directory)
                    game_path = self._find_game_path(appid)
                    decky.logger.info(f"Using base game path for Bash detection: {game_path}")
                else:
                    # For uninstall, we still need to find where ReShade was installed
                    # Try to use our detection first, then fall back to base path
                    try:
                        exe_result = await self.find_game_executable_path(appid)
                        if (exe_result["status"] == "success" and 
                            exe_result.get("steam_logs_result", {}).get("status") == "success"):
                            game_path = os.path.dirname(exe_result["steam_logs_result"]["executable_path"])
                            decky.logger.info(f"Using detected executable directory for uninstall: {game_path}")
                        elif (exe_result["status"] == "success" and 
                              exe_result.get("enhanced_detection_result", {}).get("status") == "success"):
                            game_path = os.path.dirname(exe_result["enhanced_detection_result"]["executable_path"])
                            decky.logger.info(f"Using enhanced detection directory for uninstall: {game_path}")
                        else:
                            game_path = self._find_game_path(appid)
                            decky.logger.info(f"Using base game path for uninstall: {game_path}")
                    except:
                        game_path = self._find_game_path(appid)
                        decky.logger.info(f"Using base game path for uninstall (fallback): {game_path}")
                
                decky.logger.info(f"Final game path: {game_path}")
            except ValueError as e:
                return {"status": "error", "message": str(e)}

            # Build command - if user selected a specific path, don't pass appid to prevent bash script from overriding
            cmd = ["/bin/bash", str(script_path), action, game_path, dll_override]
            if vulkan_mode:
                cmd.extend([vulkan_mode, os.path.expanduser(f"~/.local/share/Steam/steamapps/compatdata/{appid}"), appid])
            else:
                # For non-Vulkan mode, add empty placeholders for vulkan_mode and wineprefix
                if using_user_selected_path:
                    # Don't pass appid when using user-selected path to prevent bash script from overriding
                    cmd.extend(["", "", ""])
                    decky.logger.info("Not passing App ID to bash script to prevent path override")
                else:
                    # Pass appid for automatic detection
                    cmd.extend(["", "", appid])
            
            decky.logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
            clean_env = {**os.environ, **self.environment}
            clean_env["LD_LIBRARY_PATH"] = ""
            
            process = subprocess.run(
                cmd,
                cwd=str(assets_dir),
                env=clean_env,
                capture_output=True,
                text=True
            )
            
            decky.logger.info(f"Script output: {process.stdout}")
            if process.stderr:
                decky.logger.error(f"Script errors: {process.stderr}")
            
            if process.returncode != 0:
                return {"status": "error", "message": process.stderr}
                
            return {"status": "success", "output": process.stdout}
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}

    async def find_heroic_games(self) -> dict:
        """Find games installed through Heroic Launcher using the config file"""
        try:
            # Read the Heroic config file to get the default install path
            heroic_config_path = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/store/config.json")
            
            if not os.path.exists(heroic_config_path):
                return {"status": "error", "message": "Heroic config file not found"}
                
            with open(heroic_config_path, 'r', encoding='utf-8') as f:
                heroic_config = json.load(f)
            
            # Get the install path from config
            default_install_path = heroic_config.get("settings", {}).get("defaultInstallPath")
            if not default_install_path:
                default_install_path = os.path.expanduser("~/Games/Heroic")  # Fallback
            
            decky.logger.info(f"Heroic games install path: {default_install_path}")
            
            # Get the list of recent games for quick reference
            recent_games = heroic_config.get("games", {}).get("recent", [])
            recent_games_map = {game.get("title"): game.get("appName") for game in recent_games if game.get("title") and game.get("appName")}
            
            # Find all game directories in the install path
            games = []
            if os.path.exists(default_install_path):
                for game_dir in os.listdir(default_install_path):
                    game_path = os.path.join(default_install_path, game_dir)
                    if os.path.isdir(game_path) and game_dir.lower() not in ["prefixes", "temp", "legendary", "gog", "state", "logs"]:
                        # This is likely a game directory
                        game_info = {
                            "name": game_dir,
                            "path": game_path
                        }
                        
                        # Check if this game is in the recent games list
                        if game_dir in recent_games_map:
                            game_info["app_id"] = recent_games_map[game_dir]
                        
                        # Try to find a better name from appinfo.json if it exists
                        appinfo_paths = [
                            os.path.join(game_path, "appinfo.json"),
                            os.path.join(game_path, ".egstore", "appinfo.json")
                        ]
                        
                        for appinfo_path in appinfo_paths:
                            if os.path.exists(appinfo_path):
                                try:
                                    with open(appinfo_path, 'r', encoding='utf-8') as f:
                                        appinfo = json.load(f)
                                        if "DisplayName" in appinfo:
                                            game_info["name"] = appinfo["DisplayName"]
                                        elif "AppName" in appinfo:
                                            game_info["name"] = appinfo["AppName"]
                                        if "AppId" in appinfo:
                                            game_info["app_id"] = str(appinfo["AppId"])
                                        break
                                except Exception as e:
                                    decky.logger.error(f"Error reading appinfo.json for {game_dir}: {str(e)}")
                        
                        # Find and cache the config file information if available
                        if "app_id" in game_info:
                            # Check if there's a direct config file match
                            games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
                            for config_file in os.listdir(games_config_dir):
                                if config_file.endswith(".json"):
                                    config_file_path = os.path.join(games_config_dir, config_file)
                                    try:
                                        with open(config_file_path, 'r', encoding='utf-8') as f:
                                            config_data = json.load(f)
                                            # Check if app_id is a key in this config file
                                            if game_info["app_id"] in config_data:
                                                game_info["config_file"] = config_file
                                                game_info["config_key"] = game_info["app_id"]
                                                break
                                    except Exception as e:
                                        decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
                        
                        games.append(game_info)
            
            # Sort games alphabetically by name
            games.sort(key=lambda g: g["name"].lower())
            
            return {"status": "success", "games": games}
        except Exception as e:
            decky.logger.error(f"Error finding Heroic games: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def find_heroic_game_config(self, game_path: str, game_name: str) -> dict:
        """
        Find the config file and key for a Heroic game using the config.json file
        """
        try:
            decky.logger.info(f"Finding config for Heroic game: {game_name} at {game_path}")
            
            # Normalize game name for more flexible matching
            normalized_game_name = game_name.lower().replace(" ", "").replace("-", "").replace("_", "")
            normalized_game_path = os.path.normpath(game_path)
            base_folder_name = os.path.basename(normalized_game_path).lower()
            
            decky.logger.info(f"Normalized game name: {normalized_game_name}")
            decky.logger.info(f"Base folder name: {base_folder_name}")
            
            # First, try to read the Heroic config file
            heroic_config_path = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/store/config.json")
            if os.path.exists(heroic_config_path):
                with open(heroic_config_path, 'r', encoding='utf-8') as f:
                    heroic_config = json.load(f)
                
                # Get the list of recent games
                recent_games = heroic_config.get("games", {}).get("recent", [])
                
                # Look for a match by title with flexible matching
                for game in recent_games:
                    game_title = game.get("title", "")
                    normalized_title = game_title.lower().replace(" ", "").replace("-", "").replace("_", "")
                    
                    # Try multiple matching approaches
                    if (game.get("title") == game_name or  # Exact match
                        normalized_title == normalized_game_name or  # Normalized match
                        normalized_game_name in normalized_title or  # Normalized game name is in title
                        normalized_title in normalized_game_name or  # Normalized title is in game name
                        base_folder_name.startswith(normalized_title) or  # Folder starts with title
                        normalized_title.startswith(base_folder_name)):  # Title starts with folder
                        
                        app_name = game.get("appName")
                        if app_name:
                            decky.logger.info(f"Found appName in config.json for '{game_title}': {app_name}")
                            
                            # Now look for this appName in the GamesConfig directory
                            games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
                            for config_file in os.listdir(games_config_dir):
                                if not config_file.endswith(".json"):
                                    continue
                                    
                                config_file_path = os.path.join(games_config_dir, config_file)
                                try:
                                    with open(config_file_path, 'r', encoding='utf-8') as f:
                                        config_data = json.load(f)
                                        
                                        if app_name in config_data:
                                            decky.logger.info(f"Found config file: {config_file}, key: {app_name}")
                                            return {
                                                "status": "success",
                                                "config_file": config_file,
                                                "config_key": app_name
                                            }
                                except Exception as e:
                                    decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
                
                # If direct matching failed, try checking winePrefix paths in all config files
                decky.logger.info("Trying to match using winePrefix paths...")
                games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
                
                for config_file in os.listdir(games_config_dir):
                    if not config_file.endswith(".json"):
                        continue
                        
                    config_file_path = os.path.join(games_config_dir, config_file)
                    try:
                        with open(config_file_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            
                            # Check each game config
                            for app_key, app_config in config_data.items():
                                # Check winePrefix path
                                wine_prefix = app_config.get("winePrefix", "")
                                if wine_prefix:
                                    # Get both last part and parent part of path for more chances to match
                                    prefix_parts = wine_prefix.rstrip('/').split('/')
                                    last_part = prefix_parts[-1].lower()
                                    parent_part = prefix_parts[-2].lower() if len(prefix_parts) > 1 else ""
                                    
                                    # Normalize for matching
                                    last_part_norm = last_part.replace(" ", "").replace("-", "").replace("_", "")
                                    parent_part_norm = parent_part.replace(" ", "").replace("-", "").replace("_", "")
                                    
                                    # Enhanced matching for Wine prefix components
                                    if (last_part.lower() == game_name.lower() or
                                        last_part_norm == normalized_game_name or
                                        normalized_game_name in last_part_norm or
                                        last_part_norm in normalized_game_name or
                                        base_folder_name.startswith(last_part_norm) or
                                        last_part_norm.startswith(base_folder_name) or
                                        # Also check parent directory if it's not a common prefix folder
                                        (parent_part and parent_part not in ["prefixes", "wine", "pfx"] and (
                                            parent_part.lower() == game_name.lower() or
                                            parent_part_norm == normalized_game_name or
                                            normalized_game_name in parent_part_norm or
                                            parent_part_norm in normalized_game_name or
                                            base_folder_name.startswith(parent_part_norm) or
                                            parent_part_norm.startswith(base_folder_name)))):
                                        
                                        match_type = "last_part" if (last_part.lower() == game_name.lower() or 
                                                                    last_part_norm == normalized_game_name or
                                                                    normalized_game_name in last_part_norm or
                                                                    last_part_norm in normalized_game_name) else "parent_part"
                                        
                                        decky.logger.info(f"Found match via winePrefix {match_type}: {wine_prefix}")
                                        decky.logger.info(f"Config file: {config_file}, key: {app_key}")
                                        return {
                                            "status": "success",
                                            "config_file": config_file,
                                            "config_key": app_key
                                        }
                    except Exception as e:
                        decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
            
            # Improved executable name matching
            decky.logger.info("Trying enhanced matching using executable names...")
            
            # Find the executable directory
            exe_dir = self._find_heroic_game_executable_directory(game_path)
            if not exe_dir:
                exe_dir = game_path
                
            # Find executable files - get all to increase chances of a match
            exe_files = []
            try:
                for file in os.listdir(exe_dir):
                    if file.lower().endswith(".exe") and not any(skip in file.lower() for skip in 
                                                            ["unins", "launcher", "crash", "setup", "config", "redist"]):
                        exe_files.append(file)
                        
                # Try additional subdirectories if no EXEs found in main directory
                if not exe_files:
                    for subdir in ["bin", "binaries", "game", "win64", "x64"]:
                        subdir_path = os.path.join(exe_dir, subdir)
                        if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
                            for file in os.listdir(subdir_path):
                                if file.lower().endswith(".exe") and not any(skip in file.lower() for skip in 
                                                                        ["unins", "launcher", "crash", "setup", "config", "redist"]):
                                    exe_files.append(file)
                                    decky.logger.info(f"Found exe in subdirectory {subdir}: {file}")
            except Exception as e:
                decky.logger.error(f"Error listing executable directory: {str(e)}")
                
            if exe_files:
                # Use all executable names for matching, not just the first one
                games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
                
                for exe_file in exe_files:
                    # Get name without .exe extension
                    exe_name = os.path.splitext(exe_file)[0].lower()
                    exe_name_norm = exe_name.replace(" ", "").replace("-", "").replace("_", "")
                    
                    decky.logger.info(f"Trying to match using executable: {exe_name}")
                    
                    # Check all config files for matches
                    for config_file in os.listdir(games_config_dir):
                        if not config_file.endswith(".json"):
                            continue
                            
                        config_file_path = os.path.join(games_config_dir, config_file)
                        try:
                            with open(config_file_path, 'r', encoding='utf-8') as f:
                                config_data = json.load(f)
                                
                                # Check all games in this config
                                for app_key, app_config in config_data.items():
                                    # Get game info and any other relevant fields that might contain the game name
                                    game_info = app_config.get("game", {})
                                    config_title = game_info.get("title", "").lower()
                                    config_title_norm = config_title.replace(" ", "").replace("-", "").replace("_", "")
                                    
                                    # Also check the app config directly for game name
                                    app_title = app_config.get("title", "").lower()
                                    app_title_norm = app_title.replace(" ", "").replace("-", "").replace("_", "")
                                    
                                    # Enhanced matching for executable names
                                    if (exe_name == config_title.lower() or
                                        exe_name_norm == config_title_norm or
                                        exe_name == app_title.lower() or
                                        exe_name_norm == app_title_norm or
                                        exe_name_norm in config_title_norm or
                                        exe_name_norm in app_title_norm or
                                        config_title_norm in exe_name_norm or
                                        app_title_norm in exe_name_norm):
                                        
                                        match_source = "game_info" if exe_name_norm in config_title_norm else "app_config"
                                        match_type = "exact" if (exe_name == config_title.lower() or exe_name == app_title.lower()) else "partial"
                                        
                                        decky.logger.info(f"Found match via executable name: {exe_name} matches '{config_title or app_title}' ({match_type} match from {match_source})")
                                        decky.logger.info(f"Config file: {config_file}, key: {app_key}")
                                        return {
                                            "status": "success",
                                            "config_file": config_file,
                                            "config_key": app_key
                                        }
                        except Exception as e:
                            decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
                        
            # Check install path as before
            decky.logger.info("Trying to match using install path...")
            games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
            for config_file in os.listdir(games_config_dir):
                if not config_file.endswith(".json"):
                    continue
                    
                config_file_path = os.path.join(games_config_dir, config_file)
                try:
                    with open(config_file_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        
                        # Check all games in this config
                        for app_key, app_config in config_data.items():
                            install_path = app_config.get("installPath", "")
                            if install_path:
                                normalized_install_path = os.path.normpath(install_path)
                                install_folder = os.path.basename(normalized_install_path).lower()
                                install_folder_norm = install_folder.replace(" ", "").replace("-", "").replace("_", "")
                                
                                # Enhanced matching for install paths
                                if (normalized_install_path == normalized_game_path or
                                    install_folder == base_folder_name or
                                    (normalized_game_name in install_folder_norm) or
                                    (install_folder_norm in normalized_game_name) or
                                    base_folder_name.startswith(install_folder_norm) or
                                    install_folder_norm.startswith(base_folder_name)):
                                    
                                    decky.logger.info(f"Found match via install path: {install_path}")
                                    decky.logger.info(f"Config file: {config_file}, key: {app_key}")
                                    return {
                                        "status": "success",
                                        "config_file": config_file,
                                        "config_key": app_key
                                    }
                except Exception as e:
                    decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
            
            # NEW FALLBACK: Check store-specific installed.json files if all other methods fail
            decky.logger.info("Trying to find game in store-specific installed.json files...")
            
            # Define paths to different store installed.json files
            installed_json_paths = {
                "epic": os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/legendaryConfig/legendary/installed.json"),
                "gog": os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/gog_store/installed.json"),
                "amazon": os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/nile_config/nile/installed.json")
            }
            
            # Check each store's installed.json file
            for store, json_path in installed_json_paths.items():
                if not os.path.exists(json_path):
                    decky.logger.debug(f"{store.upper()} installed.json not found: {json_path}")
                    continue
                    
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        installed_data = json.load(f)
                    
                    decky.logger.info(f"Checking {store.upper()} installed.json file")
                    
                    # Handle Epic Games format (object with app IDs as keys)
                    if store == "epic":
                        for app_id, game_info in installed_data.items():
                            title = game_info.get("title", "").lower()
                            title_norm = title.replace(" ", "").replace("-", "").replace("_", "")
                            install_path = os.path.normpath(game_info.get("install_path", ""))
                            executable = game_info.get("executable", "").lower()
                            executable_name = os.path.splitext(executable)[0].lower() if executable else ""
                            
                            # Comprehensive matching
                            if (title.lower() == game_name.lower() or
                                title_norm == normalized_game_name or
                                normalized_game_name in title_norm or
                                title_norm in normalized_game_name or
                                install_path == normalized_game_path or
                                os.path.basename(install_path).lower() == base_folder_name or
                                (executable_name and (
                                    executable_name == normalized_game_name or
                                    normalized_game_name in executable_name or
                                    executable_name in normalized_game_name
                                ))):
                                
                                app_name = game_info.get("app_name", app_id)
                                if app_name:
                                    decky.logger.info(f"Found match in Epic installed.json: {app_name} for {title}")
                                    
                                    # Now search for this app_name in GamesConfig directory
                                    config_result = self._find_config_for_app_name(app_name)
                                    if config_result["status"] == "success":
                                        return config_result
                    
                    # Handle GOG format (installed array)
                    elif store == "gog":
                        installed_array = installed_data.get("installed", [])
                        for game_info in installed_array:
                            install_path = os.path.normpath(game_info.get("install_path", ""))
                            app_name = game_info.get("appName")
                            
                            # Match based on install path
                            if (install_path == normalized_game_path or
                                os.path.basename(install_path).lower() == base_folder_name):
                                
                                if app_name:
                                    decky.logger.info(f"Found match in GOG installed.json: {app_name}")
                                    
                                    # Search for this app_name in config files
                                    config_result = self._find_config_for_app_name(app_name)
                                    if config_result["status"] == "success":
                                        return config_result
                    
                    # Handle Amazon format (likely similar to others)
                    elif store == "amazon":
                        # Implementation would depend on exact structure
                        # This is a placeholder assuming similar structure to other stores
                        if isinstance(installed_data, dict) and "installed" in installed_data:
                            # Array format like GOG
                            for game_info in installed_data.get("installed", []):
                                app_name = game_info.get("appName") or game_info.get("app_name")
                                install_path = os.path.normpath(game_info.get("install_path", ""))
                                
                                if (install_path == normalized_game_path or
                                    os.path.basename(install_path).lower() == base_folder_name):
                                    
                                    if app_name:
                                        decky.logger.info(f"Found match in Amazon installed.json: {app_name}")
                                        
                                        # Search for this app_name in config files
                                        config_result = self._find_config_for_app_name(app_name)
                                        if config_result["status"] == "success":
                                            return config_result
                        else:
                            # Object format like Epic
                            for app_id, game_info in installed_data.items():
                                app_name = game_info.get("appName") or game_info.get("app_name")
                                install_path = os.path.normpath(game_info.get("install_path", ""))
                                
                                if (install_path == normalized_game_path or
                                    os.path.basename(install_path).lower() == base_folder_name):
                                    
                                    if app_name:
                                        decky.logger.info(f"Found match in Amazon installed.json: {app_name}")
                                        
                                        # Search for this app_name in config files
                                        config_result = self._find_config_for_app_name(app_name)
                                        if config_result["status"] == "success":
                                            return config_result
                        
                except Exception as e:
                    decky.logger.error(f"Error reading {store} installed.json: {str(e)}")
            
            # If we still couldn't find a match, look for appinfo.json
            return {"status": "error", "message": f"Could not find config for game: {game_name}"}
        except Exception as e:
            decky.logger.error(f"Error finding Heroic game config: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _find_config_for_app_name(self, app_name: str) -> dict:
        """Find config file containing the specified app_name as a key"""
        games_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
        
        for config_file in os.listdir(games_config_dir):
            if not config_file.endswith(".json"):
                continue
                
            config_file_path = os.path.join(games_config_dir, config_file)
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                    if app_name in config_data:
                        decky.logger.info(f"Found config file for {app_name}: {config_file}")
                        return {
                            "status": "success",
                            "config_file": config_file,
                            "config_key": app_name
                        }
            except Exception as e:
                decky.logger.error(f"Error reading config file {config_file}: {str(e)}")
        
        return {"status": "error", "message": f"No config file found for app name: {app_name}"}

    async def update_heroic_config(self, config_file: str, config_key: str, dll_override: str) -> dict:
        """Update Heroic game configuration with WINEDLLOVERRIDES for ReShade"""
        try:
            config_path = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig/")
            config_file_path = os.path.join(config_path, config_file)
            
            if not os.path.exists(config_file_path):
                return {"status": "error", "message": f"Config file not found: {config_file}"}
                
            # Read the config file
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            if config_key not in config_data:
                return {"status": "error", "message": f"Game config key '{config_key}' not found in config file"}
                
            # Check if environmentOptions exists (note: it's "environmentOptions" in newer versions, not "enviromentOptions")
            env_key = "environmentOptions" if "environmentOptions" in config_data[config_key] else "enviromentOptions"
            
            if env_key not in config_data[config_key]:
                config_data[config_key][env_key] = []
            
            # Handle WINEDLLOVERRIDES
            # Remove any existing WINEDLLOVERRIDES
            config_data[config_key][env_key] = [
                env for env in config_data[config_key][env_key] 
                if env.get("key") != "WINEDLLOVERRIDES"
            ]
            
            # Add new WINEDLLOVERRIDES if not removing
            if dll_override != "remove":
                config_data[config_key][env_key].append({
                    "key": "WINEDLLOVERRIDES",
                    "value": f"d3dcompiler_47=n;{dll_override}=n,b"
                })
            
            # Write back the updated config
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
                
            return {"status": "success", "output": f"Updated Heroic config with {dll_override} override."}
        except Exception as e:
            decky.logger.error(f"Error updating Heroic config: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def install_reshade_for_heroic_game(self, game_path: str, dll_override: str = "d3d9", selected_executable_path: str = "") -> dict:
        """Install ReShade for a selected Windows executable path by copying files and configuring ReShade.ini"""
        try:
            decky.logger.info(f"Installing ReShade for selected game path: {game_path}")
            
            # Verify ReShade is installed
            marker_file = Path(self.main_path) / ".installed"
            addon_marker = Path(self.main_path) / ".installed_addon"
            if not marker_file.exists() and not addon_marker.exists():
                return {"status": "error", "message": "ReShade is not installed. Please install ReShade first."}
            
            # Verify game path exists
            if not os.path.exists(game_path):
                return {"status": "error", "message": f"Game path not found: {game_path}"}
            
            validated_executable_path = ""
            if selected_executable_path:
                is_valid, validation_result = self._validate_selected_windows_executable_path(selected_executable_path)
                if not is_valid:
                    return {"status": "error", "message": validation_result}
                validated_executable_path = validation_result

            # Determine the target directory for ReShade installation
            if validated_executable_path:
                # Use the directory of the selected executable
                exe_dir = os.path.dirname(validated_executable_path)
                decky.logger.info(f"Using user-selected executable directory: {exe_dir}")
            else:
                # Find the actual executable directory using smart detection
                exe_dir = self._find_heroic_game_executable_directory(game_path)
                if not exe_dir:
                    decky.logger.warning(f"Could not find executable directory, using provided path: {game_path}")
                    exe_dir = game_path
                else:
                    decky.logger.info(f"Found executable directory: {exe_dir}")
            
            # Find architecture by checking for .exe files
            arch = "64"  # Default to 64-bit
            exe_found = False
            
            for file in os.listdir(exe_dir):
                if file.lower().endswith(".exe"):
                    # Skip known utility executables
                    if any(skip in file.lower() for skip in ["unins", "launcher", "crash", "setup", "config", "redist"]):
                        continue
                        
                    exe_found = True
                    exe_path = os.path.join(exe_dir, file)
                    try:
                        # Check if 32-bit or 64-bit using the 'file' command
                        # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
                        clean_env = os.environ.copy()
                        clean_env["LD_LIBRARY_PATH"] = ""
                        
                        process = subprocess.run(
                            ["file", exe_path],
                            capture_output=True,
                            text=True,
                            env=clean_env
                        )
                        
                        if "PE32 executable" in process.stdout and "PE32+" not in process.stdout:
                            arch = "32"
                            decky.logger.info(f"Found 32-bit executable: {exe_path}")
                            break
                        elif "PE32+ executable" in process.stdout or "x86-64" in process.stdout:
                            decky.logger.info(f"Found 64-bit executable: {exe_path}")
                    except Exception as e:
                        decky.logger.error(f"Error checking EXE architecture: {str(e)}")
            
            decky.logger.info(f"Using architecture: {arch}-bit")
            
            # Source paths for DLLs
            reshade_dll_src = os.path.join(self.main_path, "reshade/latest", f"ReShade{arch}.dll")
            d3dcompiler_src = os.path.join(self.main_path, "reshade", f"d3dcompiler_47.dll.{arch}")
            
            if not os.path.exists(reshade_dll_src) or not os.path.exists(d3dcompiler_src):
                return {"status": "error", "message": "ReShade DLL files not found. Please reinstall ReShade."}
                
            # Destination paths
            reshade_dll_dst = os.path.join(exe_dir, f"{dll_override}.dll")
            d3dcompiler_dst = os.path.join(exe_dir, "d3dcompiler_47.dll")
            
            # Copy files instead of creating symlinks
            shutil.copy2(reshade_dll_src, reshade_dll_dst)
            shutil.copy2(d3dcompiler_src, d3dcompiler_dst)
            
            # Set proper permissions for DLL files (read/write for all)
            os.chmod(reshade_dll_dst, 0o666)
            os.chmod(d3dcompiler_dst, 0o666)
            
            # Copy shader directory if exists
            if os.path.exists(os.path.join(self.main_path, "ReShade_shaders")):
                shaders_dst = os.path.join(exe_dir, "ReShade_shaders")
                # Check if it already exists
                if os.path.exists(shaders_dst):
                    # Remove old link/directory
                    if os.path.islink(shaders_dst):
                        os.unlink(shaders_dst)
                    else:
                        shutil.rmtree(shaders_dst)
                # Create the directory and copy files
                shutil.copytree(os.path.join(self.main_path, "ReShade_shaders"), shaders_dst)
            
            # Fix ReShade.ini to use local paths instead of system paths
            reshade_ini_src = os.path.join(self.main_path, "ReShade.ini")
            reshade_ini_dst = os.path.join(exe_dir, "ReShade.ini")
            
            if os.path.exists(reshade_ini_src):
                # Read the original file
                with open(reshade_ini_src, 'r', encoding='utf-8') as f:
                    ini_content = f.read()
                    
                # Update paths to use local directories instead of system paths
                # This is critical for Wine/Proton compatibility
                
                # First, detect if we're using merged shaders
                merged_path = False
                if "ReShade_shaders\\Merged\\Shaders" in ini_content or "ReShade_shaders/Merged/Shaders" in ini_content:
                    merged_path = True
                    
                # Replace system paths with relative game paths (convert to Windows format for Wine)
                if merged_path:
                    # For merged shader setup
                    ini_content = re.sub(r'EffectSearchPaths=.*', r'EffectSearchPaths=.\\ReShade_shaders\\Merged\\Shaders', ini_content)
                    ini_content = re.sub(r'TextureSearchPaths=.*', r'TextureSearchPaths=.\\ReShade_shaders\\Merged\\Textures', ini_content)
                else:
                    # For individual shader repositories
                    ini_content = re.sub(r'EffectSearchPaths=.*', r'EffectSearchPaths=.\\ReShade_shaders', ini_content)
                    ini_content = re.sub(r'TextureSearchPaths=.*', r'TextureSearchPaths=.\\ReShade_shaders', ini_content)
                    
                # Update the PresetPath to use the local directory
                ini_content = re.sub(r'PresetPath=.*', r'PresetPath=.', ini_content)
                
                # Write the modified ini file with proper permissions
                with open(reshade_ini_dst, 'w', encoding='utf-8') as f:
                    f.write(ini_content)
                
                # Set proper permissions for ReShade.ini (read/write for all)
                os.chmod(reshade_ini_dst, 0o666)
                
            else:
                # If no ReShade.ini exists, create a basic one
                with open(reshade_ini_dst, 'w', encoding='utf-8') as f:
                    f.write("""[GENERAL]
EffectSearchPaths=.\\ReShade_shaders
TextureSearchPaths=.\\ReShade_shaders
PresetPath=.
PerformanceMode=0
PreprocessorDefinitions=
Effects=
Techniques=

[INPUT]
KeyOverlay=36
KeyNextPreset=0
KeyPreviousPreset=0
""")
                # Set proper permissions (read/write for all)
                os.chmod(reshade_ini_dst, 0o666)
            
            # Handle ReShadePreset.ini - preserve existing user settings
            reshade_preset_dst = os.path.join(exe_dir, "ReShadePreset.ini")
            
            # Only create the file if it doesn't already exist (preserve existing user settings)
            if not os.path.exists(reshade_preset_dst):
                game_name = os.path.basename(game_path)
                with open(reshade_preset_dst, 'w', encoding='utf-8') as f:
                    f.write(f"""# ReShade Preset Configuration for {game_name}
# This file will be automatically populated when you save presets in ReShade
# Press HOME key in-game to open ReShade overlay
# Go to Settings -> General -> "Reload all shaders" if shaders don't appear

# Example preset configuration:
# [Preset1]
# Techniques=SMAA,Clarity,LumaSharpen
# PreprocessorDefinitions=

# Uncomment and modify the lines below to create a default preset:
# [Default]
# Techniques=
# PreprocessorDefinitions=
""")
                
                # Set proper permissions for ReShadePreset.ini (read/write for all)
                os.chmod(reshade_preset_dst, 0o666)
                decky.logger.info("Created new ReShadePreset.ini with proper permissions")
            else:
                # File exists, just ensure it has proper permissions
                os.chmod(reshade_preset_dst, 0o666)
                decky.logger.info("ReShadePreset.ini already exists, updated permissions only")
            
            # Create a README file to help users with the configuration
            readme_path = os.path.join(exe_dir, "ReShade_README.txt")
            
            # Check if AutoHDR was actually installed
            autohdr_installed = os.path.exists(os.path.join(exe_dir, f"AutoHDR.addon{arch}"))
            autohdr_compatible = dll_override.lower() in ['dxgi', 'd3d11', 'd3d12']
            
            if autohdr_installed:
                autohdr_status = f"- AutoHDR.addon{arch}: AutoHDR addon (DirectX 10/11/12 compatible)"
            elif autohdr_compatible:
                autohdr_status = f"- AutoHDR.addon{arch}: Not installed (AutoHDR addon file missing)"
            else:
                autohdr_status = f"- AutoHDR.addon{arch}: Not compatible with {dll_override} (requires DirectX 10/11/12)"
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"""ReShade for {os.path.basename(game_path)}
------------------------------------
Installed with LetMeReShadeAll

DLL Override: {dll_override}
Architecture: {arch}-bit
Executable Directory: {exe_dir}
{f'Selected Executable: {os.path.basename(validated_executable_path)}' if validated_executable_path else 'Auto-detected executable location'}

Press HOME key in-game to open the ReShade overlay.

If shaders are not visible:
1. Open the ReShade overlay with HOME key
2. Go to Settings tab
3. Check paths for "Effect Search Paths" and "Texture Search Paths"
4. They should point to the ReShade_shaders folder in this game directory
5. If not, update them to: ".\\ReShade_shaders"

Shader preset files (.ini) will be saved in this game directory.

Files created:
- ReShade.ini: Main ReShade configuration
- ReShadePreset.ini: Preset configurations (auto-populated when you save presets)
- {dll_override}.dll: ReShade DLL
- d3dcompiler_47.dll: DirectX shader compiler
- ReShade_shaders/: Shader files directory
{autohdr_status}

AutoHDR Compatibility:
- Compatible APIs: DXGI, D3D11, D3D12 (DirectX 10/11/12)
- Incompatible APIs: D3D9, D3D8, OpenGL32, DDraw, DInput8
- Current API: {dll_override} {'(✅ AutoHDR Compatible)' if autohdr_compatible else '(❌ AutoHDR Incompatible)'}

Note: If ReShadePreset.ini already existed, your previous settings were preserved.
""")
            
            # Set proper permissions for README (read/write for all)
            os.chmod(readme_path, 0o666)
            
            # Copy AutoHDR addon files if available AND compatible with the selected API
            autohdr_compatible = dll_override.lower() in ['dxgi', 'd3d11', 'd3d12']
            
            if autohdr_compatible:
                autohdr_addon_path = os.path.join(self.main_path, "AutoHDR_addons", f"AutoHDR.addon{arch}")
                if os.path.exists(autohdr_addon_path):
                    autohdr_dst = os.path.join(exe_dir, f"AutoHDR.addon{arch}")
                    try:
                        shutil.copy2(autohdr_addon_path, autohdr_dst)
                        os.chmod(autohdr_dst, 0o666)
                        decky.logger.info(f"AutoHDR addon copied successfully for {arch}-bit architecture (API: {dll_override})")
                    except Exception as e:
                        decky.logger.warning(f"Failed to copy AutoHDR addon: {str(e)}")
                else:
                    decky.logger.info(f"AutoHDR addon file not found: {autohdr_addon_path}")
            else:
                decky.logger.info(f"Skipping AutoHDR addon installation for API: {dll_override} (requires DirectX 10/11/12)")
                # Remove any existing AutoHDR addon files if they exist from previous installations
                for addon_arch in ['32', '64']:
                    existing_addon = os.path.join(exe_dir, f"AutoHDR.addon{addon_arch}")
                    if os.path.exists(existing_addon):
                        decky.logger.info(f"Removing existing AutoHDR addon (incompatible with {dll_override})")
                        os.remove(existing_addon)
                
            return {"status": "success", "output": f"ReShade installed successfully using {dll_override} override."}
        except Exception as e:
            decky.logger.error(f"Error installing ReShade for selected executable path: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _find_game_executable_directory(self, path: Path, game_name: str) -> tuple[Path, float]:
        """
        Unified function to find the game executable directory with smart detection
        
        Args:
            path: Base path to search for game executables
            game_name: Name of the game for matching
            
        Returns:
            tuple[Path, float]: The best executable directory and its score
        """
        try:
            if not path.exists() or not path.is_dir():
                return path, 0
                
            # Extract words from game name for better matching
            game_words = set(re.findall(r'\w+', game_name.lower()))
            # Clean game name (remove spaces, special chars)
            clean_game_name = re.sub(r'[^a-z0-9]', '', game_name.lower())
            
            decky.logger.info(f"Looking for executables for game: {game_name}")
            decky.logger.info(f"Game words for matching: {game_words}")
            
            def analyze_directory_content(dir_path: Path) -> float:
                """Score a directory based on its content"""
                if not dir_path.exists() or not dir_path.is_dir():
                    return 0
                    
                score = 0
                file_types = {'exe': 0, 'dll': 0, 'config': 0, 'asset': 0, 'setup': 0, 'redist': 0}
                
                try:
                    # Count file types
                    for file in dir_path.iterdir():
                        if file.is_file():
                            ext = file.suffix.lower()
                            
                            # Game binary files
                            if ext == '.exe':
                                file_types['exe'] += 1
                            elif ext == '.dll':
                                file_types['dll'] += 1
                                
                            # Game config and data files
                            elif ext in ['.ini', '.cfg', '.xml', '.json', '.txt']:
                                file_types['config'] += 1
                                
                            # Game asset files
                            elif ext in ['.pak', '.dat', '.bsa', '.ba2', '.dds', '.tga', '.png', '.jpg']:
                                file_types['asset'] += 1
                                
                            # Setup and redistributable files (negative indicators)
                            elif ext in ['.msi', '.cab', '.msm']:
                                file_types['setup'] += 1
                            
                            # Check file names for redistributable indicators
                            file_name = file.name.lower()
                            if any(term in file_name for term in ['redist', 'vcredist', 'directx', 'setup', 'install']):
                                file_types['redist'] += 1
                    
                    # Score based on file types
                    # Game directories usually have more DLLs and game-related files
                    score += file_types['dll'] * 0.5  # DLLs are good indicators
                    score += file_types['config'] * 0.3  # Config files are somewhat good indicators
                    score += file_types['asset'] * 0.4  # Asset files are good indicators
                    
                    # Too many EXEs might indicate a utility directory
                    if file_types['exe'] > 5:
                        score -= (file_types['exe'] - 5) * 0.2
                    
                    # Setup files are negative indicators
                    score -= file_types['setup'] * 1.0
                    score -= file_types['redist'] * 1.0
                    
                    # Check directory name - look for similarity to game name
                    dir_name = dir_path.name.lower()
                    clean_dir_name = re.sub(r'[^a-z0-9]', '', dir_name)
                    
                    # Increase score for directories that match game name
                    if clean_dir_name == clean_game_name:
                        score += 3  # Exact match
                    elif clean_game_name in clean_dir_name or clean_dir_name in clean_game_name:
                        score += 2  # Partial match
                    elif dir_name in ['bin', 'bin64', 'bin32', 'binaries', 'game', 'main']:
                        score += 2  # Common game directories
                    elif any(term in dir_name for term in ['redist', 'setup', 'support', 'tools', 'eadm']):
                        score -= 2  # Negative indicators
                    
                    # Analyze subdirectory names
                    subdirs = [d for d in dir_path.iterdir() if d.is_dir()]
                    subdir_names = [d.name.lower() for d in subdirs]
                    
                    # Game directories often have these subdirectories
                    game_subdir_indicators = ['data', 'config', 'save', 'content', 'assets', 'levels']
                    for indicator in game_subdir_indicators:
                        if any(indicator in name for name in subdir_names):
                            score += 0.5
                    
                    # Round to 1 decimal place
                    score = round(score, 1)
                    decky.logger.debug(f"Directory content score for {dir_path}: {score}")
                    return score
                    
                except (PermissionError, OSError) as e:
                    decky.logger.debug(f"Error analyzing directory {dir_path}: {e}")
                    return 0
            
            def score_executable(exe_path: Path) -> float:
                """Score an executable based on how likely it is to be the main game executable"""
                if not exe_path.is_file():
                    return 0
                    
                name = exe_path.stem.lower()
                score = 0
                
                # Skip utility executables
                if any(skip in name for skip in ["unins", "launcher", "crash", "setup", "config", "redist", "install"]):
                    return 0
                    
                decky.logger.debug(f"Scoring executable: {name}")
                
                # Enhanced name matching for specific cases
                clean_exe_name = re.sub(r'[^a-z0-9]', '', name)
                
                # Check exact match (normalized)
                if clean_exe_name == clean_game_name:
                    exact_match_score = 30
                    decky.logger.debug(f"  Exact normalized match: +{exact_match_score}")
                    score += exact_match_score
                
                # Handle special cases like "among us.exe" vs "amongus"
                elif name.replace(" ", "") == game_name.lower() or game_name.lower().replace(" ", "") == name:
                    special_match_score = 25
                    decky.logger.debug(f"  Special space-normalized match: +{special_match_score}")
                    score += special_match_score
                
                # Check partial matches
                elif clean_game_name in clean_exe_name or clean_exe_name in clean_game_name:
                    # Calculate how much of the string matches
                    match_ratio = max(
                        len(clean_game_name) / len(clean_exe_name) if len(clean_exe_name) > 0 else 0,
                        len(clean_exe_name) / len(clean_game_name) if len(clean_game_name) > 0 else 0
                    )
                    # Scale the score (max 20 points)
                    partial_score = min(20, int(match_ratio * 20))
                    score += partial_score
                    decky.logger.debug(f"  Partial name match: +{partial_score} (ratio: {match_ratio:.2f})")
                
                # Word-based matching
                else:
                    # Name matching with game name
                    name_words = set(re.findall(r'\w+', name))
                    
                    # Calculate word match score based on intersection
                    matching_words = game_words.intersection(name_words)
                    
                    # If there are matching words, they're worth MUCH more if they're a larger percentage of the game name
                    if matching_words:
                        match_percentage = len(matching_words) / len(game_words) if game_words else 0
                        word_score = len(matching_words) * 5.0 * (1 + match_percentage)  # Increased from 1.5 to 5.0
                        word_score = min(15, round(word_score, 1))  # Cap at 15 and round
                        decky.logger.debug(f"  Name match score: +{word_score} (words: {matching_words})")
                        score += word_score
                
                # Bonus for common game executable names (increased)
                if name.lower() in ["game", "start", "play", "client", "app"]:
                    common_name_score = 5.0  # Increased from 0.5 to 5.0
                    decky.logger.debug(f"  Common name bonus: +{common_name_score} ({name})")
                    score += common_name_score
                
                try:
                    # File size is still a factor, but MUCH less important than name matching
                    size = exe_path.stat().st_size
                    size_mb = size / (1024 * 1024)
                    
                    # Reduced logarithmic scoring for size - much lower weight
                    if size_mb > 0:
                        import math
                        size_score = min(0.5, math.log10(size_mb) / 6)  # Significantly reduced weight for size
                        size_score = round(size_score, 1)  # Round to 1 decimal
                        decky.logger.debug(f"  Size score: +{size_score} ({size_mb:.2f} MB)")
                        score += size_score
                    
                    # Smaller penalty for extremely small executables
                    if size_mb < 0.5:  # Less than 500KB
                        size_penalty = 0.5  # Reduced from 1
                        decky.logger.debug(f"  Small size penalty: -{size_penalty}")
                        score -= size_penalty
                except Exception as e:
                    decky.logger.debug(f"  Error checking file size: {e}")
                
                # If the name contains "launcher" or "setup", reduce score significantly
                if "launcher" in name.lower() or "setup" in name.lower():
                    launcher_penalty = 10  # Increased from 3 to 10
                    decky.logger.debug(f"  Launcher/setup penalty: -{launcher_penalty}")
                    score -= launcher_penalty
                
                # Round score to 1 decimal place
                score = round(score, 1)
                
                decky.logger.debug(f"  Final executable score: {score}")
                return score
            
            def find_best_exe_dir(path: Path, max_depth=3, current_depth=0) -> tuple[Path, float]:
                """Recursively find the best executable directory"""
                if not path.exists() or not path.is_dir():
                    return None, 0
                    
                best_exe_dir = None
                best_score = -1
                
                try:
                    # First check for executables in this directory
                    exes_in_dir = []
                    for exe in path.glob("*.exe"):
                        exe_score = score_executable(exe)
                        if exe_score > 0:
                            exes_in_dir.append((exe, exe_score))
                    
                    # Get directory content score
                    dir_content_score = analyze_directory_content(path)
                    
                    # Sort executables by score (highest first)
                    exes_in_dir.sort(key=lambda x: x[1], reverse=True)
                    
                    # Calculate combined score for this directory
                    if exes_in_dir:
                        best_exe_score = exes_in_dir[0][1]
                        combined_score = best_exe_score + dir_content_score
                        decky.logger.debug(f"Directory {path} - Best exe: {exes_in_dir[0][0].name} (score: {best_exe_score:.1f}), Dir content: {dir_content_score:.1f}, Combined: {combined_score:.1f}")
                        
                        if combined_score > best_score:
                            best_score = combined_score
                            best_exe_dir = path
                    else:
                        # If no executables, just use the directory content score
                        if dir_content_score > best_score:
                            best_score = dir_content_score
                            best_exe_dir = path
                    
                    # If we haven't found a good match and have depth remaining, check subdirectories
                    if (best_score < 4 or current_depth == 0) and current_depth < max_depth:
                        for subdir in path.iterdir():
                            if subdir.is_dir():
                                sub_exe_dir, sub_score = find_best_exe_dir(subdir, max_depth, current_depth + 1)
                                if sub_score > best_score:
                                    best_score = sub_score
                                    best_exe_dir = sub_exe_dir
                
                except (PermissionError, OSError) as e:
                    decky.logger.debug(f"Error accessing directory {path}: {e}")
                
                # Round final score to 1 decimal
                best_score = round(best_score, 1)
                
                return best_exe_dir, best_score
                
            # Find the best executable directory
            best_dir, score = find_best_exe_dir(path)
            
            return best_dir, score
            
        except Exception as e:
            decky.logger.error(f"Error in _find_game_executable_directory: {str(e)}")
            return path, 0

    def _find_heroic_game_executable_directory(self, game_path: str) -> str:
        """Find the directory containing the game's main executable using smart detection"""
        try:
            game_path = Path(game_path)
            if not game_path.exists() or not game_path.is_dir():
                return None
                
            # Get name of the game directory for smarter exe matching
            game_name = game_path.name.lower().replace("_", " ").replace("-", " ")
            
            decky.logger.info(f"Finding executable directory for Heroic game: {game_name}")
            
            # Use the unified game executable detection function
            best_dir, score = self._find_game_executable_directory(game_path, game_name)
            
            if best_dir and score > 0:
                decky.logger.info(f"Found game executable directory: {best_dir} (score: {score:.2f})")
                return str(best_dir)
            
            # If we couldn't find anything, check some common subdirectories
            common_dirs = ["bin", "bin32", "bin64", "binaries", "game", "win64", "win32", "x64", "x86"]
            for common in common_dirs:
                test_path = game_path / common
                if test_path.exists() and test_path.is_dir():
                    exes = list(test_path.glob("*.exe"))
                    if exes:
                        decky.logger.info(f"Using common executable directory: {test_path}")
                        return str(test_path)
            
            # If we still didn't find anything, just use the original path
            decky.logger.info(f"No suitable executable directory found, using original path: {game_path}")
            return str(game_path)
        
        except Exception as e:
            decky.logger.error(f"Error finding game executable directory: {str(e)}")
            return None

    def _get_steam_game_install_path(self, appid: str) -> str:
        steam_root = Path(decky.HOME) / ".steam" / "steam"
        library_file = steam_root / "steamapps" / "libraryfolders.vdf"

        if not library_file.exists():
            raise ValueError(f"Steam library file not found: {library_file}")

        library_paths = []
        with open(library_file, "r", encoding="utf-8") as file:
            for line in file:
                if '"path"' in line:
                    path = line.split('"path"')[1].strip().strip('"').replace("\\\\", "/")
                    library_paths.append(path)

        for library_path in library_paths:
            manifest_path = Path(library_path) / "steamapps" / f"appmanifest_{appid}.acf"
            if manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as manifest:
                    for line in manifest:
                        if '"installdir"' in line:
                            install_dir = line.split('"installdir"')[1].strip().strip('"')
                            base_path = Path(library_path) / "steamapps" / "common" / install_dir
                            return str(base_path)

        raise ValueError(f"Could not find installation directory for AppID: {appid}")

    def _find_game_path(self, appid: str) -> str:
        base_path = Path(self._get_steam_game_install_path(appid))
        game_name = base_path.name.lower().replace("_", " ").replace("-", " ")

        decky.logger.info(f"Finding executable directory for Steam game: {game_name}")

        best_dir, score = self._find_game_executable_directory(base_path, game_name)

        if best_dir and score > 0:
            decky.logger.info(f"Found game executable directory: {best_dir} (score: {score:.2f})")
            return str(best_dir)

        common_dirs = ["bin", "bin32", "bin64", "binaries", "game", "win64", "win32", "x64", "x86"]
        for common in common_dirs:
            test_path = base_path / common
            if test_path.exists() and test_path.is_dir():
                exes = list(test_path.glob("*.exe"))
                if exes:
                    decky.logger.info(f"Using common executable directory: {test_path}")
                    return str(test_path)

        decky.logger.info(f"No suitable executable directory found, using base path: {base_path}")
        return str(base_path)

    async def uninstall_reshade_for_heroic_game(self, game_path: str) -> dict:
        """Uninstall ReShade from a selected executable path while preserving user presets"""
        try:
            decky.logger.info(f"Uninstalling ReShade from selected game path: {game_path}")
            
            # Find the executable directory
            exe_dir = self._find_heroic_game_executable_directory(game_path)
            if not exe_dir:
                decky.logger.warning(f"Could not find executable directory, using provided path: {game_path}")
                exe_dir = game_path
            
            # Remove ReShade files (excluding ReShadePreset.ini to preserve user settings)
            reshade_files = [
                "d3d8.dll", "d3d9.dll", "d3d10.dll", "d3d11.dll", "d3d12.dll", 
                "dxgi.dll", "opengl32.dll", "dinput8.dll", "ddraw.dll",
                "d3dcompiler_47.dll", "ReShade.ini", "ReShade_README.txt",
                "AutoHDR.addon32", "AutoHDR.addon64"
                # Note: ReShadePreset.ini is intentionally excluded to preserve user settings
            ]
            
            for file in reshade_files:
                file_path = os.path.join(exe_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    decky.logger.info(f"Removed {file_path}")
            
            # Remove ReShade_shaders directory if it exists
            shaders_path = os.path.join(exe_dir, "ReShade_shaders")
            if os.path.exists(shaders_path):
                if os.path.islink(shaders_path):
                    os.unlink(shaders_path)
                else:
                    shutil.rmtree(shaders_path)
                decky.logger.info(f"Removed {shaders_path}")
            
            # Check if ReShadePreset.ini exists and inform user it's preserved
            preset_path = os.path.join(exe_dir, "ReShadePreset.ini")
            if os.path.exists(preset_path):
                decky.logger.info(f"ReShadePreset.ini preserved at {preset_path}")
                return {"status": "success", "output": "ReShade uninstalled successfully.\nYour shader presets (ReShadePreset.ini) have been preserved for future use."}
            else:
                return {"status": "success", "output": "ReShade uninstalled successfully."}
                
        except Exception as e:
            decky.logger.error(f"Error uninstalling ReShade: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def detect_heroic_game_api(self, game_path: str) -> dict:
        """Detect the best API/DLL override for a Heroic game"""
        try:
            decky.logger.info(f"Detecting API for Heroic game at: {game_path}")
            
            # Verify game path exists
            if not os.path.exists(game_path):
                return {"status": "error", "message": f"Game path not found: {game_path}"}
            
            # Default API is dxgi (DirectX 10/11/12)
            detected_api = "dxgi"
            arch = "64"  # Default to 64-bit
            
            # Find all executable files
            exe_files = []
            for root, _, files in os.walk(game_path):
                for file in files:
                    if file.lower().endswith(".exe"):
                        # Skip known utility executables
                        if any(skip in file.lower() for skip in ["unins", "launcher", "crash", "setup", "config", "redist"]):
                            continue
                        
                        exe_path = os.path.join(root, file)
                        file_size = os.path.getsize(exe_path)
                        
                        # Larger files are more likely to be the main executable
                        if file_size > 1024 * 1024:  # Files larger than 1MB
                            exe_files.append((exe_path, file_size))
            
            # Sort by file size (descending)
            exe_files.sort(key=lambda x: x[1], reverse=True)
            
            # Process the largest executable files first
            for exe_path, _ in exe_files[:3]:  # Check the top 3 largest executables
                decky.logger.info(f"Analyzing executable: {exe_path}")
                
                # Check architecture
                try:
                    # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
                    clean_env = os.environ.copy()
                    clean_env["LD_LIBRARY_PATH"] = ""
                    
                    process = subprocess.run(
                        ["file", exe_path],
                        capture_output=True,
                        text=True,
                        env=clean_env
                    )
                    
                    if "PE32 executable" in process.stdout and "PE32+" not in process.stdout:
                        arch = "32"
                        decky.logger.info(f"Detected 32-bit executable: {exe_path}")
                    elif "PE32+ executable" in process.stdout or "x86-64" in process.stdout:
                        arch = "64"
                        decky.logger.info(f"Detected 64-bit executable: {exe_path}")
                except Exception as e:
                    decky.logger.error(f"Error checking architecture: {str(e)}")
                
                # Look for DLL files in the same directory to determine API
                exe_dir = os.path.dirname(exe_path)
                
                # Check for specific DLLs to determine API
                if os.path.exists(os.path.join(exe_dir, "d3d9.dll")):
                    detected_api = "d3d9"
                    decky.logger.info(f"Detected D3D9 API from d3d9.dll")
                    break
                elif os.path.exists(os.path.join(exe_dir, "d3d11.dll")):
                    detected_api = "d3d11"
                    decky.logger.info(f"Detected D3D11 API from d3d11.dll")
                    break
                elif os.path.exists(os.path.join(exe_dir, "d3d8.dll")):
                    detected_api = "d3d8"
                    decky.logger.info(f"Detected D3D8 API from d3d8.dll")
                    break
                elif os.path.exists(os.path.join(exe_dir, "opengl32.dll")):
                    detected_api = "opengl32"
                    decky.logger.info(f"Detected OpenGL API from opengl32.dll")
                    break
                elif os.path.exists(os.path.join(exe_dir, "dxgi.dll")):
                    detected_api = "dxgi"
                    decky.logger.info(f"Detected DXGI API from dxgi.dll")
                    break
                
                # If no DLLs found, try to analyze the executable for imports
                try:
                    # Check imports using objdump (if available)
                    # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
                    clean_env = os.environ.copy()
                    clean_env["LD_LIBRARY_PATH"] = ""
                    
                    process = subprocess.run(
                        ["objdump", "-p", exe_path],
                        capture_output=True,
                        text=True,
                        env=clean_env
                    )
                    
                    output = process.stdout.lower()
                    
                    # Check for DLL imports
                    if "d3d9.dll" in output:
                        detected_api = "d3d9"
                        decky.logger.info(f"Detected D3D9 API from imports")
                        break
                    elif "d3d11.dll" in output:
                        detected_api = "d3d11"
                        decky.logger.info(f"Detected D3D11 API from imports")
                        break
                    elif "d3d8.dll" in output:
                        detected_api = "d3d8"
                        decky.logger.info(f"Detected D3D8 API from imports")
                        break
                    elif "opengl32.dll" in output:
                        detected_api = "opengl32"
                        decky.logger.info(f"Detected OpenGL API from imports")
                        break
                    elif "dxgi.dll" in output:
                        detected_api = "dxgi"
                        decky.logger.info(f"Detected DXGI API from imports")
                        break
                except Exception as e:
                    decky.logger.error(f"Error analyzing imports: {str(e)}")
            
            # For 32-bit executables, default to d3d9 if not detected
            if arch == "32" and detected_api == "dxgi":
                detected_api = "d3d9"
                decky.logger.info(f"Falling back to D3D9 for 32-bit executable")
                
            decky.logger.info(f"Final detection - API: {detected_api}, Architecture: {arch}")
            
            return {
                "status": "success", 
                "api": detected_api,
                "architecture": arch
            }
        except Exception as e:
            decky.logger.error(f"Error detecting API for Heroic game: {str(e)}")
            return {"status": "error", "message": str(e)}



# ===== Unified plugin =====
class Plugin(_OptiScalerMixin, _ReShadeMixin):
    # Coexistence policy ("fixed + auto-merge"): ReShade owns the graphics proxy slot
    # (default dxgi); OptiScaler/Framegen is forced onto a non-graphics proxy so the two
    # never fight over the same file. Users can override per game via set_slots_manual.
    OPTISCALER_COEXIST_SLOT = "winmm.dll"
    GRAPHICS_PROXY_SLOTS = {
        "dxgi.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll", "d3d8.dll", "ddraw.dll", "opengl32.dll",
    }
    RESHADE_SLOT_CANDIDATES = (
        "dxgi.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll", "d3d8.dll", "ddraw.dll", "opengl32.dll", "dinput8.dll",
    )

    async def _main(self):
        decky.logger.info("Jedi ReFrameShade4All loaded")

    async def _unload(self):
        decky.logger.info("Jedi ReFrameShade4All unloaded")

    # ── coexistence helpers ──────────────────────────────────────────────────
    def _dir_has_reshade(self, directory) -> bool:
        if not directory:
            return False
        directory = Path(directory)
        return (directory / "ReShade.ini").exists() or (directory / "reshade-shaders").exists()

    def _dir_has_optiscaler(self, directory) -> bool:
        if not directory:
            return False
        directory = Path(directory)
        return (directory / MARKER_FILENAME).exists() or (directory / "OptiScaler.ini").exists()

    def _detect_reshade_slot(self, directory) -> str:
        directory = Path(directory) if directory else None
        if directory:
            for slot in self.RESHADE_SLOT_CANDIDATES:
                # skip the slot OptiScaler is using to avoid mis-detection
                if slot == self.OPTISCALER_COEXIST_SLOT:
                    continue
                if (directory / slot).exists():
                    return slot
        return "dxgi.dll"

    def _coexist_optiscaler_slot(self, directory, requested) -> str:
        """Keep OptiScaler off ReShade's graphics slot when both are present."""
        if self._dir_has_reshade(directory) and (not requested or requested in self.GRAPHICS_PROXY_SLOTS):
            return self.OPTISCALER_COEXIST_SLOT
        return requested or self.OPTISCALER_COEXIST_SLOT

    def _merge_launch_options(self, slots, include_d3dcompiler: bool) -> str:
        parts = []
        if include_d3dcompiler:
            parts.append("d3dcompiler_47=n")
        seen = set()
        for slot in slots:
            base = str(slot).replace(".dll", "")
            if base and base not in seen:
                parts.append(f"{base}=n,b")
                seen.add(base)
        return f'WINEDLLOVERRIDES="{";".join(parts)}" SteamDeck=0 %command%'

    # ── Framegen patch override: avoid ReShade's slot + merge launch options ──
    async def patch_game(self, appid, dll_name="winmm.dll", current_launch_options="", fsr4_variant=DEFAULT_FSR4_VARIANT):
        game = self._game_record(str(appid))
        if game:
            try:
                target_dir, _ = self._guess_patch_target(game)
                dll_name = self._coexist_optiscaler_slot(target_dir, dll_name)
            except Exception as exc:
                decky.logger.warning(f"[JediReFrameShade] slot resolution failed: {exc}")
        result = await super().patch_game(str(appid), dll_name, current_launch_options, fsr4_variant)
        try:
            if result.get("status") == "success" and result.get("target_dir"):
                td = Path(result["target_dir"])
                if self._dir_has_reshade(td):
                    reshade_slot = self._detect_reshade_slot(td)
                    result["launch_options"] = self._merge_launch_options(
                        [reshade_slot, dll_name], include_d3dcompiler=True
                    )
                    result["coexist_with_reshade"] = True
                    result["reshade_slot"] = reshade_slot
        except Exception as exc:
            decky.logger.warning(f"[JediReFrameShade] launch-option merge failed: {exc}")
        return result

    async def set_slots_manual(self, appid, optiscaler_slot="winmm.dll", fsr4_variant=DEFAULT_FSR4_VARIANT, current_launch_options=""):
        """Re-patch Framegen with an explicit proxy slot chosen by the user (manual override)."""
        if optiscaler_slot not in VALID_DLL_NAMES:
            return {"status": "error", "message": f"Invalid proxy slot: {optiscaler_slot}"}
        result = await super().patch_game(str(appid), optiscaler_slot, current_launch_options, fsr4_variant)
        try:
            if result.get("status") == "success" and result.get("target_dir"):
                td = Path(result["target_dir"])
                if self._dir_has_reshade(td):
                    reshade_slot = self._detect_reshade_slot(td)
                    result["launch_options"] = self._merge_launch_options(
                        [reshade_slot, optiscaler_slot], include_d3dcompiler=True
                    )
                    result["coexist_with_reshade"] = True
        except Exception as exc:
            decky.logger.warning(f"[JediReFrameShade] manual merge failed: {exc}")
        return result

    async def get_combined_game_status(self, appid) -> dict:
        opti = await self.get_game_status(str(appid))
        directory = None
        if opti.get("target_dir"):
            directory = Path(opti["target_dir"])
        else:
            game = self._game_record(str(appid))
            if game:
                try:
                    directory, _ = self._guess_patch_target(game)
                except Exception:
                    directory = None
        reshade_present = self._dir_has_reshade(directory)
        return {
            "status": "success",
            "appid": str(appid),
            "name": opti.get("name"),
            "optiscaler_patched": bool(opti.get("patched")),
            "optiscaler_slot": opti.get("dll_name"),
            "optiscaler_variant_label": opti.get("fsr4_variant_label"),
            "reshade_present": reshade_present,
            "reshade_slot": self._detect_reshade_slot(directory) if reshade_present else None,
            "both_active": bool(opti.get("patched")) and reshade_present,
            "target_dir": str(directory) if directory else None,
        }

    # ── OptiScaler version/update status (mirrors get_reshade_update_status) ──
    async def get_optiscaler_update_status(self) -> dict:
        fgmod_path = Path(decky.HOME) / "fgmod"
        installed = self._fgmod_version(fgmod_path) if fgmod_path.exists() else None
        try:
            latest_meta = self._get_latest_optiscaler_release()
            latest = latest_meta.get("version") if isinstance(latest_meta, dict) else None
        except Exception as exc:
            return {
                "status": "success",
                "installed_version": installed,
                "latest_version": None,
                "update_available": False,
                "message": f"Could not reach GitHub: {exc}",
            }
        update_available = bool(
            installed and latest
            and str(latest) not in str(installed)
            and str(installed) not in str(latest)
        )
        return {
            "status": "success",
            "installed_version": installed,
            "latest_version": latest,
            "update_available": update_available,
        }

    # ── One-button "Patch All": install engines if needed + patch both mods ───
    async def get_engines_status(self) -> dict:
        fg = await self.check_fgmod_path()
        try:
            rs = await self.check_reshade_path()
        except Exception:
            rs = {"exists": False}
        return {
            "status": "success",
            "optiscaler_installed": bool(fg.get("exists")),
            "optiscaler_version": fg.get("version"),
            "reshade_installed": bool(rs.get("exists")),
            "reshade_version": (rs.get("version_info") or {}).get("version") if isinstance(rs.get("version_info"), dict) else None,
        }

    async def patch_all_game(
        self,
        appid,
        fsr4_variant=DEFAULT_FSR4_VARIANT,
        with_reshade_addon=True,
        current_launch_options="",
    ) -> dict:
        """Install OptiScaler + ReShade engines if missing, then patch the chosen Steam
        game with BOTH (ReShade on dxgi, Frame Generation on winmm) in one shot."""
        try:
            game = self._game_record(str(appid))
            if not game:
                return {"status": "error", "message": "Game not found in Steam library."}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before patching."}

            steps = []

            # 1) ensure OptiScaler engine
            fg = await self.check_fgmod_path()
            if not fg.get("exists"):
                r = await self.run_install_fgmod(fsr4_variant)
                if r.get("status") != "success":
                    return {"status": "error", "message": f"OptiScaler install failed: {r.get('message') or r.get('output')}"}
                steps.append("installed OptiScaler")

            # 2) ensure ReShade engine
            try:
                rs = await self.check_reshade_path()
            except Exception:
                rs = {"exists": False}
            if not rs.get("exists"):
                r = await self.run_install_reshade(bool(with_reshade_addon), False, None)
                if r.get("status") != "success":
                    return {"status": "error", "message": f"ReShade install failed: {r.get('message') or r.get('output')}"}
                steps.append("installed ReShade")

            # 3) resolve a single target directory/exe so both mods land together
            target_dir, target_exe = self._guess_patch_target(game)

            # 4) patch Frame Generation FIRST (winmm). This MUST run before ReShade:
            #    OptiScaler's proxy-DLL cleanup backs up every proxy slot (incl. dxgi), so
            #    if ReShade's dxgi.dll were already there it would be moved to dxgi.dll.b
            #    and ReShade would never load. winmm is not touched by ReShade afterwards.
            pr = await self.patch_game(str(appid), "winmm.dll", current_launch_options, fsr4_variant)
            if pr.get("status") != "success":
                return {"status": "error", "message": f"Frame Generation patch failed: {pr.get('message')}"}
            steps.append("patched Frame Generation (winmm)")

            # 5) patch ReShade (graphics slot dxgi) AFTER Frame Generation.
            if target_exe:
                rr = await self.manage_game_reshade(str(appid), "install", "dxgi", "", str(target_exe))
            else:
                rr = await self.manage_game_reshade(str(appid), "install", "dxgi")
            if rr.get("status") != "success":
                return {"status": "error", "message": f"ReShade patch failed (Frame Generation was applied): {rr.get('message') or rr.get('output')}"}
            steps.append("patched ReShade (dxgi)")

            # Both mods are now in the folder → always hand back the merged overrides.
            launch_options = self._merge_launch_options(["dxgi.dll", "winmm.dll"], True)
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "target_dir": pr.get("target_dir") or (str(target_dir) if target_dir else None),
                "launch_options": launch_options,
                "message": f"Patched {game['name']}: Frame Generation (winmm) + ReShade (dxgi). " + ", ".join(steps) + ".",
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] patch_all_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    async def unpatch_all_game(self, appid) -> dict:
        """Remove both mods from the chosen Steam game and restore launch options."""
        try:
            game = self._game_record(str(appid))
            if not game:
                return {"status": "error", "message": "Game not found in Steam library."}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before removing."}

            target_dir, target_exe = self._guess_patch_target(game)
            try:
                if target_exe:
                    await self.manage_game_reshade(str(appid), "uninstall", "dxgi", "", str(target_exe))
                else:
                    await self.manage_game_reshade(str(appid), "uninstall", "dxgi")
            except Exception as exc:
                decky.logger.warning(f"[JediReFrameShade] ReShade uninstall warning: {exc}")

            res = await self.unpatch_game(str(appid))
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "launch_options": res.get("launch_options", ""),
                "message": f"Removed ReShade + Frame Generation from {game['name']}.",
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] unpatch_all_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

