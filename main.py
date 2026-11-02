import decky
import asyncio
import contextvars
import functools
import os
import signal
import sys
import subprocess
import time
import zipfile
import json
import shutil
import re
import filecmp
import hashlib
import tempfile
import threading
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

OPTISCALER_ARCHIVE_ASSET = {
    "name": "Optiscaler_0.9.4-final.20260718._MM.7z",
    "sha256": "575cb4df866116093df75af607e37fd70e10f5163e0f23fd5c804142e80ef0ad",
    "version": "0.9.4-final.20260718",
}

FSR4_INT8_ASSET = {
    "name": "amd_fidelityfx_upscaler_dx12.dll",
    "sha256": "c7720bc16bede334f59a1a32cd22edbcbbb159685ed5240e61350a5fb0bc8a94",
    "version": "4.0.2c",
}

FSR4_VALVE_411_ASSET = {
    "name": "amdxcffx64_valve_2.3.0.2913.dll",
    "sha256": "4e7dc37aebea3a90e3d3cc43e24cb2b54176b2535315f20dbe63b3b7cfc56b1e",
    "version": "4.1.1-valve-2.3.0.2913",
}

# FSR 4.1.2 Lite (FSR4L-i8): AMD's driver FSR from Adrenalin 26.10.1, unmodified (AMD/WHQL signed). Both
# carry the INT8 Lite model (ffxProvider_FSR4Lite_Int8), the smaller INT8 model AMD made for APUs.
FSR4_LITE_412_ASSET = {
    "name": "amdxcffx64_4.1.2_2.4.0.4370.dll",
    "sha256": "c33a287f3048bf02311cae430b6a977500b94ca7b315cd7bff751e6b03e483e3",
    "version": "4.1.2-lite-2.4.0.4370",
}

FSR4_LITE_412_VK_ASSET = {
    "name": "amdvkffx64_4.1.2_2.4.0.4370.dll",
    "sha256": "80e761f7c8c0ec8ead7b321df01911baaf917defae51388d29eaecb1d6bc58bd",
    "version": "4.1.2-lite-2.4.0.4370",
}

# OptiScaler 10 built from optiscaler/OptiScaler master 2128299c: selects FSR 4.1.2 models (Fsr4Model=3 = INT8
# Lite) and keeps the AMD vendor id for amdxcffx64 while spoofing (8f2a943). Its FFX/XeSS libraries are the
# same files as 0.9.4's, so only the injector changes.
OPTISCALER_V10_ASSET = {
    "name": "OptiScaler_10.0.0-master.2128299c.dll",
    "sha256": "52b3045d6e0d5322f45368652c16185ca8c34a4fe5da0b0ab098818fb2f458a5",
    "version": "10.0.0-master.2128299c",
}

# OptiScaler 10 built from optiscaler/OptiScaler master de2626f: loads upscalers from custom/<name>/dlss even on
# GPUs it doesn't consider DLSS capable, which is how HelixSR 3.x's HLX DLSS (an NGX runtime) runs on AMD. Our patch
# (attached to its release) also takes driver DLLs in custom/<name>/ffx, which is how Valve's 4.1.1 sits next to 4.1.2.
OPTISCALER_HLX_ASSET = {
    "name": "OptiScaler_10.0.0-de2626f-jedi1.dll",
    "sha256": "ddddce19f5e60f1897573fbafb1eaa2703b58a6d172d470ce71a6731f533b95a",
    "version": "10.0.0-de2626f-jedi1",
}

OPTIPATCHER_ASSET = {
    "name": "OptiPatcher_rolling.asi",
    "sha256": "88b9e1be3559737cd205fdf5f2c8550cf1923fb1def4c603e5bf03c3e84131b1",
    "version": "rolling",
}

FSR4_UPSCALER_FILENAME = "amd_fidelityfx_upscaler_dx12.dll"
FSR4_DRIVER_OVERRIDE_FILENAME = "amdxcffx64.dll"
FSR4_VK_DRIVER_OVERRIDE_FILENAME = "amdvkffx64.dll"
INSTALL_MANIFEST_FILENAME = "install-manifest.json"
VERSION_FILENAME = "version.txt"
DEFAULT_FSR4_VARIANT = "rdna23-int8"

FSR4_VARIANTS = {
    "rdna23-int8": {
        "label": "4.0.2c / RDNA2-3 compatibility",
        "dir_name": "fsr4-rdna2-3",
        "sha256": "c7720bc16bede334f59a1a32cd22edbcbbb159685ed5240e61350a5fb0bc8a94",
        "source_asset_name": FSR4_INT8_ASSET["name"],
        "source_version": FSR4_INT8_ASSET["version"],
        "uses_archive_native": False,
        "extra_files": [],
    },
    "rdna2-valve-411-pre10": {
        "label": "4.1.1 Valve RDNA2 compatibility",
        "dir_name": "fsr4-rdna2-valve-411-pre10",
        "sha256": "d0dcccc74a43c44ba435b7a369b456e0970d8a4464e4bd683119b374f2c9fb46",
        "source_asset_name": OPTISCALER_ARCHIVE_ASSET["name"],
        "source_version": OPTISCALER_ARCHIVE_ASSET["version"],
        "uses_archive_native": True,
        "extra_files": [
            {
                "name": FSR4_DRIVER_OVERRIDE_FILENAME,
                "sha256": FSR4_VALVE_411_ASSET["sha256"],
                "source_asset_name": FSR4_VALVE_411_ASSET["name"],
                "source_version": FSR4_VALVE_411_ASSET["version"],
            },
        ],
    },
    "lite-412-i8": {
        "label": "4.1.2 Lite FSR4L-i8 / Steam Deck + APUs",
        "dir_name": "fsr4-lite-412-i8",
        "sha256": "d0dcccc74a43c44ba435b7a369b456e0970d8a4464e4bd683119b374f2c9fb46",
        "source_asset_name": OPTISCALER_ARCHIVE_ASSET["name"],
        "source_version": OPTISCALER_ARCHIVE_ASSET["version"],
        "uses_archive_native": True,
        "injector": {
            "name": "OptiScaler.dll",
            "sha256": OPTISCALER_V10_ASSET["sha256"],
            "source_asset_name": OPTISCALER_V10_ASSET["name"],
            "source_version": OPTISCALER_V10_ASSET["version"],
        },
        "extra_files": [
            {
                "name": FSR4_DRIVER_OVERRIDE_FILENAME,
                "sha256": FSR4_LITE_412_ASSET["sha256"],
                "source_asset_name": FSR4_LITE_412_ASSET["name"],
                "source_version": FSR4_LITE_412_ASSET["version"],
            },
            {
                "name": FSR4_VK_DRIVER_OVERRIDE_FILENAME,
                "sha256": FSR4_LITE_412_VK_ASSET["sha256"],
                "source_asset_name": FSR4_LITE_412_VK_ASSET["name"],
                "source_version": FSR4_LITE_412_VK_ASSET["version"],
            },
        ],
        # OptiScaler 10 keys: GPU treated as INT8 Lite, Lite model, FSR 4 as the DX12 upscaler. FGInput=nukems
        # is gone in 10 (it reads as no FG): the same Nukems DLSSG replacement is FGInput=NvngxFG.
        "config_overrides": {
            "FSR.Fsr4GpuSupport": "4",
            "FSR.Fsr4Model": "3",
            "FSR.UpscalerIndex": "0",
            "Upscalers.Dx12Upscaler": "ffx",
            "FrameGen.FGInput": "NvngxFG",
            "FrameGen.FGOutput": "auto",
            "FrameGen.FGNvngxReplacement": "Nukems",
        },
        # What a game gets back when it leaves this variant for an OptiScaler 0.9.4 one.
        "leave_config_overrides": {
            "FSR.Fsr4GpuSupport": "auto",
            "FSR.Fsr4Model": "auto",
            "FSR.UpscalerIndex": "auto",
            "Upscalers.Dx12Upscaler": "auto",
            "FrameGen.FGInput": "nukems",
            "FrameGen.FGOutput": "nukems",
            "FrameGen.FGNvngxReplacement": "auto",
        },
    },
    # HelixSR is not bundled: it is downloaded and built on the device (see _HelixSRMixin).
    # The game root keeps the INT8 FSR4 upscaler, which also stays selectable next to HelixSR.
    "helixsr": {
        "label": "HelixSR | DLSS Model E on AMD",
        "dir_name": "fsr4-rdna2-3",
        "sha256": FSR4_INT8_ASSET["sha256"],
        "source_asset_name": FSR4_INT8_ASSET["name"],
        "source_version": FSR4_INT8_ASSET["version"],
        "uses_archive_native": False,
        "extra_files": [],
        "helixsr": True,
    },
}
HELIXSR_VARIANT = "helixsr"
# 4.0.2c, 4.1.1, 4.1.2 Lite and HLX DLSS in one game, picked in OptiScaler's menu. The game gets the Lite runtime
# (FSR 4, from the Lite folder of the bundle) with the OptiScaler 10 build that loads custom upscalers
# (OPTISCALER_HLX_ASSET), 4.0.2c's upscaler as custom/FSR 4.0.2c/ffx, Valve's 4.1.1 driver DLL as custom/FSR 4.1.1/ffx
# and, when HelixSR 3.x is installed, HLX DLSS as custom/HLX DLSS/dlss.
COMBINED_VARIANT = "deck-all"
FSR4_VARIANTS[COMBINED_VARIANT] = {
    **FSR4_VARIANTS["lite-412-i8"],
    "label": "4.0.2c + 4.1.1 + 4.1.2 Lite + HLX DLSS",
    "combined": True,
}
CUSTOM_402C_NAME = "FSR 4.0.2c"
CUSTOM_411_NAME = "FSR 4.1.1"
CUSTOM_411_DLL = "amdxcffx64_valve.dll"   # OptiScaler keeps the AMD vendor id for DLLs named amdxcffx64*
CUSTOM_UPSCALER_MARKER = "jedi-custom.json"
# amdxc64.dll: only games patched before the old 4.1.1 Valve runtime was trimmed have it, and removing them still clears it.
VARIANT_EXTRA_FILENAMES = sorted(
    {
        "amdxc64.dll",
        *(
            extra_file["name"]
            for variant in FSR4_VARIANTS.values()
            for extra_file in variant.get("extra_files", [])
        ),
    }
)

OPTISCALER_DOWNLOAD_TIMEOUT = 45
# Seconds a helper command can run, generous for a Deck's SD card. Without a limit a stuck one holds every patch.
PROCESS_LIST_TIMEOUT = 10
REQUEST_FALLBACK_TIMEOUT = 60
GAME_SCRIPT_TIMEOUT = 120
DOWNLOAD_FALLBACK_TIMEOUT = 900
EXTRACT_TIMEOUT = 900
# Every game's OptiScaler.ini: the plugin pins OptiScaler's builds, so OptiScaler doesn't look for or announce updates.
OPTISCALER_BASE_CONFIG_OVERRIDES = {"Hotfix.CheckForUpdate": "false"}

# Plugin self-update: the newest release of this plugin on GitHub, installed by Decky's own installer.
PLUGIN_RELEASES_API = "https://api.github.com/repos/sauliiin/Jedi-ReFrameShade4All/releases?per_page=20"
PLUGIN_ZIP_RE = re.compile(r"^Jedi-ReFrameShade4All-(\d+(?:\.\d+)+)\.zip$")
PLUGIN_UPDATE_CACHE_SECONDS = 600

# HelixSR (https://github.com/lonewolf0622/HelixSR): NVIDIA's DLSS Model E network on AMD GPUs.
# Ported from DeckyHelixSRManager (https://github.com/PeroTuncay/DeckyHelixSRManager, The Unlicense).
# Releases ship no NVIDIA files: the latest release is downloaded and HelixSR's own setup builds
# the network into its DLL on this device. Only one (the newest) release is kept installed.
HELIXSR_RELEASES_API = "https://api.github.com/repos/lonewolf0622/HelixSR/releases?per_page=30"
HELIXSR_LATEST_CACHE_SECONDS = 900
HELIXSR_DIRNAME = "fgmod-helixsr"
HELIXSR_META_FILENAME = ".jedi-helixsr.json"
HELIXSR_GAME_SUBDIR = "HelixSR"
HELIXSR_GAME_MARKER = "jedi-helixsr.json"

# Proton-CachyOS takes an absolute file path in PROTON_FSR4_UPGRADE and copies that amdxcffx64.dll
# into the prefix's system32 instead of downloading one. The Lite DLL is kept here for it.
PROTON_FSR4_LITE_DIRNAME = "fgmod-proton-fsr4"

# Releases up to cachyos-11.0-20261015 predate that (protonfixes ef718b0): they take the path as a version
# name, find none and download 4.1.1. The plugin installs a copy of the newest release into
# compatibilitytools.d with protonfixes/upscalers.py patched to take the path.
PROTON_CACHYOS_RELEASES_API = "https://api.github.com/repos/CachyOS/proton-cachyos/releases?per_page=10"
PROTON_CACHYOS_ASSET_RE = re.compile(r"^(proton-cachyos-[A-Za-z0-9._-]+-x86_64)\.tar\.xz$")
PROTON_LITE_SUFFIX = "-jedi-fsr4lite"
# One internal name for every release, so an update replaces the copy in place: games set to it keep it and
# Steam keeps a single entry. Up to 1.1.23 the name carried the release (proton-cachyos-<release>-jedi-fsr4lite).
PROTON_LITE_TOOL_NAME = "proton-cachyos" + PROTON_LITE_SUFFIX
PROTON_LITE_RELEASE_FILE = ".jedi-proton-lite.json"
PROTON_LITE_MARKER = "# Jedi-ReFrameShade4All: local dll"
PROTON_LITE_UPSCALER_PATCHES = (
    (
        "def __get_dll_manifest(upscaler: str, version: str = 'default') -> dict:\n"
        "    dlls = __get_manifest()[upscaler]\n",
        "def __get_dll_manifest(upscaler: str, version: str = 'default') -> dict:\n"
        f"    {PROTON_LITE_MARKER}: an absolute file path as the version uses that file.\n"
        "    local = Path(version)\n"
        "    if local.is_absolute() and local.is_file():\n"
        "        with local.open('rb') as local_fd:\n"
        "            local_md5 = hashlib.md5(local_fd.read()).hexdigest().upper()\n"
        "        return {\n"
        "            'version': f'local-{local_md5}',\n"
        "            'download_url': str(local),\n"
        "            'file_description': upscaler,\n"
        "            'is_dev_file': False,\n"
        "            'is_bundle': False,\n"
        "            'md5_hash': local_md5,\n"
        "            'zip_md5_hash': local_md5,\n"
        "        }\n"
        "    dlls = __get_manifest()[upscaler]\n",
    ),
    (
        "def __download_extract_zip(item: dict, cache: Path, dst: Path) -> None:\n",
        "def __download_extract_zip(item: dict, cache: Path, dst: Path) -> None:\n"
        f"    {PROTON_LITE_MARKER}: copied as is.\n"
        "    if Path(item['download_url']).is_absolute():\n"
        "        dst.parent.mkdir(parents=True, exist_ok=True)\n"
        "        with Path(item['download_url']).open('rb') as src_fd, dst.open('wb') as dst_fd:\n"
        "            dst_fd.write(src_fd.read())\n"
        "        return\n",
    ),
    (
        "    if 'fsr4' in upscaler_replace:\n"
        "        pass\n",
        "    if 'fsr4' in upscaler_replace:\n"
        f"        {PROTON_LITE_MARKER}: turns FSR4_UPGRADE on, as newer releases do.\n"
        "        if Path(fsr4_version).is_absolute():\n"
        "            env.setdefault('FSR4_UPGRADE', '1')\n",
    ),
)
HELIXSR_DLL_FFX = "amd_fidelityfx_dx12.dll"   # up to 1.4 and from 1.7: an FSR 3.1 replacement
HELIXSR_DLL_NGX = "nvngx.dll"                 # 1.5/1.6 (withdrawn): a DLSS replacement, not supported here
HELIXSR_OUT_SUBDIR = "HelixSR-fsrfg"          # 2.0+: HelixSR's DLL (and what the setup builds) is in this folder
HELIXSR_DLL_HLX = "helixsr.dll"               # 3.0+: HLX DLSS, an NGX runtime (no FFX exports)
HELIXSR_HLX_SUBDIR = "HelixSR"                # 3.0+: the release folder that holds it
# 3.0+ in the game: OptiScaler (de2626f+) lists custom/<name>/dlss/<dll> as an upscaler named <name>
HELIXSR_HLX_NAME = "HLX DLSS"
HELIXSR_HLX_FG_KEYS = {   # OptiScaler 10 reads FGInput=nukems as no FG: the same Nukems FG, as the Lite runtime sets it
    ("FrameGen", "FGInput"): "NvngxFG",
    ("FrameGen", "FGOutput"): "auto",
    ("FrameGen", "FGNvngxReplacement"): "Nukems",
}
HELIXSR_DLSS_FILENAME = ".jedi-nvngx_dlss.dll"   # NVIDIA's DLSS DLL for the setup's --dlss, deleted after the build
HELIXSR_DLSS_URL = re.compile(r"""^DLSS_URL\s*=\s*['"](https://[^'"]+)['"]""", re.M)
HELIXSR_DLSS_SHA256 = re.compile(r"""^DLSS_SHA256\s*=\s*['"]([0-9a-fA-F]{64})['"]""", re.M)
# In the game, HelixSR gets names of its own (as HelixSR's own OptiScaler install did): a game that loads
# its amd_fidelityfx_*.dll first would otherwise make the loader hand that module back for HelixSR's path,
# and OptiScaler would only list the FSR4 upscaler.
HELIXSR_GAME_DLL = "helixsr.dll"                 # OptiScaler's FfxDx12Path
HELIXSR_GAME_SR_DLL = "helixsr_upscaler.dll"     # OptiScaler's FfxDx12SRPath
HELIXSR_GAME_OLD_NAMES = (FSR4_UPSCALER_FILENAME, HELIXSR_DLL_FFX)   # 1.1.11 used the FSR file names
HELIXSR_FSR4_COPY_NAME = "amd_fidelityfx_upscaler_dx12.amd.dll"
HELIXSR_FG_DLL = "amd_fidelityfx_framegeneration_dx12.dll"
HELIXSR_EMBED_MAGIC = b"HXSRNET1"
HELIXSR_SEPARATE_FILES = ("helixsr_weights.bin", "helixsr_kernels.pak")   # the network before 1.4.0
# Everything this plugin puts in (or HelixSR writes to) the game's HelixSR folder
HELIXSR_GAME_OWN_FILES = {
    HELIXSR_GAME_MARKER, HELIXSR_GAME_DLL, HELIXSR_GAME_SR_DLL, *HELIXSR_GAME_OLD_NAMES, HELIXSR_FSR4_COPY_NAME,
    HELIXSR_FG_DLL, "amd_fidelityfx_dx12.original.dll", "helixsr.ini", "helixsr.log", *HELIXSR_SEPARATE_FILES,
}
# Release folders not needed here: HelixSR Scaler (from 1.9.3 in HelixSR's zip, ~205 MB) is OptiScaler-based
# and only installed by HelixSR's own installer; the setup builds the network without it.
HELIXSR_SKIP_DIRS = ("helixsr-scaler/",)
HELIXSR_GAMES_MARKER = "# --- games ---"   # helixsr-setup.sh 1.7-1.8: HelixSR's own game installer follows
HELIXSR_BUILD_SCRIPT = ".jedi-helixsr-build.sh"
HELIXSR_PHASES = [  # (setup log pattern, progress %, label)
    (r"\[helixsr-setup\] system:", 1, "Checking the system"),
    (r"portable Python|python\.tar\.gz", 2, "Downloading Python + numpy (one time)"),
    (r"\[helixsr-setup\] python:", 5, "Preparing the shader compiler"),
    (r"dxc-win\.zip", 5, "Downloading the shader compiler (one time)"),
    (r"shader compiler:", 7, "Starting the build"),
    (r"downloading nvngx_dlss", 8, "Downloading NVIDIA's DLSS DLL"),
    (r"1/5 weights", 10, "Step 1/5: extracting weights"),
    (r"2/5 PTX", 14, "Step 2/5: extracting the network kernels"),
    (r"3/5 fragment tables", 18, "Step 3/5: fragment tables"),
    (r"4/5 kernel sources", 40, "Step 4/5: generating shader sources"),
    (r"5/5 shaders", 50, "Step 5/5: compiling shaders"),
    (r"building the network", 10, "Building the network"),
    (r"HelixSR is ready|now carries the network|done: the network is built", 100, "Finished"),
    (r"looking for games with DLSS", 100, "Finished"),
]
# 1.7+: "[helixsr-setup] [########------------]  42%  1:23  shaders 12/72"
HELIXSR_BUILD_PROGRESS = re.compile(r"\[[#-]{5,}\]\s+(\d+)%\s+\d+:\d\d\s+(.*?)\s*$")
HELIXSR_PROMPT_LINE = re.compile(r"\[Y/n|\[f/n|\[f/r/n")
HELIXSR_ERROR_PATTERN = re.compile(r"error|failed|traceback|no such file|not found|denied|mismatch|cannot|killed", re.I)

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
    FSR4_DRIVER_OVERRIDE_FILENAME,
    FSR4_VK_DRIVER_OVERRIDE_FILENAME,
    "amdxc64.dll",
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
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


# Long handlers run on their own thread, so the panel's other calls keep answering. One at a time, as they were on
# the event loop: they change the same game and engine files. A handler they call just runs in place.
_worker_scans = contextvars.ContextVar("jedi_worker_scans", default=None)
_worker_lock = threading.Lock()


def _worker(handler):
    @functools.wraps(handler)
    async def run(self, *args, **kwargs):
        if _worker_scans.get() is not None:
            return await handler(self, *args, **kwargs)

        def work():
            _worker_scans.set({})
            with _worker_lock:
                return asyncio.run(handler(self, *args, **kwargs))

        return await asyncio.to_thread(work)

    return run


def _scan_once(key, scan):
    """Inside one worker handler the game's record, its executables and the process list are read once."""
    scans = _worker_scans.get()
    if scans is None:
        return scan()
    if key not in scans:
        scans[key] = scan()
    return scans[key]


# ===== OptiScaler / Frame Generation backend =====
class _OptiScalerMixin:
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
            scripts = {
                "fgmod.sh": "fgmod",
                "fgmod-uninstaller.sh": "fgmod-uninstaller.sh",
                "update-optiscaler-config.py": "update-optiscaler-config.py",
            }
            missing = [name for name in scripts if not (assets_dir / name).is_file()]
            if missing:
                decky.logger.error(
                    f"Required OptiScaler helper scripts missing from {assets_dir}: {', '.join(missing)}"
                )
                return False

            for source_name, destination_name in scripts.items():
                destination = extract_path / destination_name
                shutil.copy2(assets_dir / source_name, destination)
                destination.chmod(0o755)

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

    def _is_reshade_link(self, path: Path) -> bool:
        """A link the ReShade side made into ~/.local/share/reshade (dangling or not): ReShade's, not OptiScaler's."""
        if not path.is_symlink():
            return False
        try:
            target = os.path.normpath(os.path.join(str(path.parent), os.readlink(path)))
        except OSError:
            return False
        return target.startswith(os.path.normpath(self.main_path) + os.sep)

    def _has_patch_fingerprint(self, directory: Path) -> bool:
        return any((directory / filename).exists() for filename in PATCH_FINGERPRINT_FILES)

    def _backup_preexisting_proxy_files(self, directory: Path, fgmod_path: Path) -> list[str]:
        backed_up: list[str] = []
        already_patched = self._has_patch_fingerprint(directory)
        for filename in PROXY_DLL_BACKUPS:
            source = directory / filename
            backup = directory / f"{filename}.b"
            if not source.exists() or backup.exists() or self._is_reshade_link(source):
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
        try:
            result = subprocess.run(
                extract_cmd,
                capture_output=True,
                text=True,
                check=False,
                env=clean_env,
                timeout=EXTRACT_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Extracting {archive_path.name} timed out.")
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or f"Failed to extract {archive_path.name}")

    def _replace_directory_atomically(self, prepared_path: Path, destination: Path) -> None:
        """Commit a prepared bundle without destroying a working install on failure."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        backup_path = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}-backup-", dir=str(destination.parent))
        )
        backup_path.rmdir()
        had_previous_install = destination.exists()

        if had_previous_install:
            destination.rename(backup_path)

        try:
            prepared_path.rename(destination)
        except Exception:
            if had_previous_install and backup_path.exists() and not destination.exists():
                backup_path.rename(destination)
            raise

        if backup_path.exists():
            try:
                shutil.rmtree(backup_path)
            except Exception as cleanup_error:
                decky.logger.warning(f"Could not remove old OptiScaler bundle: {cleanup_error}")

    def _missing_fgmod_files(self, path: Path) -> list[str]:
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
            "plugins/OptiPatcher.asi",
        ]
        required_files.extend(
            str(Path(variant["dir_name"]) / FSR4_UPSCALER_FILENAME)
            for variant in FSR4_VARIANTS.values()
        )
        for variant in FSR4_VARIANTS.values():
            injector = variant.get("injector")
            if isinstance(injector, dict):
                required_files.append(str(Path(variant["dir_name"]) / injector.get("name", "OptiScaler.dll")))
                required_files.append(str(Path(variant["dir_name"]) / "renames" / "dxgi.dll"))
            for extra_file in variant.get("extra_files", []):
                required_files.append(str(Path(variant["dir_name"]) / extra_file["name"]))
        return [relative_path for relative_path in required_files if not (path / relative_path).exists()]

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

    def _fsr4_variant_dir(self, fgmod_path: Path, fsr4_variant: str | None) -> Path:
        variant_id = self._normalize_fsr4_variant(fsr4_variant)
        return fgmod_path / FSR4_VARIANTS[variant_id]["dir_name"]

    def _fsr4_variant_path(self, fgmod_path: Path, fsr4_variant: str | None) -> Path:
        return self._fsr4_variant_dir(fgmod_path, fsr4_variant) / FSR4_UPSCALER_FILENAME

    def _fsr4_variant_extra_files(self, fsr4_variant: str | None) -> list[dict]:
        variant = self._fsr4_variant_info(fsr4_variant)
        return list(variant.get("extra_files") or [])

    def _fsr4_variant_extra_file_path(self, fgmod_path: Path, fsr4_variant: str | None, filename: str) -> Path:
        return self._fsr4_variant_dir(fgmod_path, fsr4_variant) / filename

    def _fsr4_variant_injector_info(self, fsr4_variant: str | None) -> dict | None:
        variant = self._fsr4_variant_info(fsr4_variant)
        injector = variant.get("injector")
        return injector if isinstance(injector, dict) else None

    def _fsr4_variant_injector_path(self, fgmod_path: Path, fsr4_variant: str | None) -> Path | None:
        injector = self._fsr4_variant_injector_info(fsr4_variant)
        if not injector:
            return None
        return self._fsr4_variant_dir(fgmod_path, fsr4_variant) / injector.get("name", "OptiScaler.dll")

    def _fsr4_variant_renamed_proxy_path(self, fgmod_path: Path, fsr4_variant: str | None, dll_name: str) -> Path | None:
        if not self._fsr4_variant_injector_info(fsr4_variant):
            return None
        return self._fsr4_variant_dir(fgmod_path, fsr4_variant) / "renames" / dll_name

    def _fsr4_variant_config_overrides(self, fsr4_variant: str | None) -> dict:
        variant = self._fsr4_variant_info(fsr4_variant)
        overrides = variant.get("config_overrides") or {}
        return {**OPTISCALER_BASE_CONFIG_OVERRIDES, **(overrides if isinstance(overrides, dict) else {})}

    def _split_ini_override_key(self, raw_key: str) -> tuple[str | None, str]:
        key = str(raw_key).strip()
        if "." in key:
            section, section_key = key.split(".", 1)
            section = section.strip()
            section_key = section_key.strip()
            if section and section_key:
                return section, section_key
        return None, key

    def _apply_optiscaler_ini_overrides(self, ini_file: Path, overrides: dict) -> bool:
        if not overrides:
            return True
        try:
            content = ini_file.read_text(encoding="utf-8", errors="replace")
            newline = "\r\n" if "\r\n" in content else "\n"
            lines = content.splitlines(keepends=True)
            section_pattern = re.compile(r"^\s*\[(?P<section>[^\]]+)\]\s*$")

            def ensure_trailing_newline() -> None:
                if lines and not lines[-1].endswith(("\n", "\r")):
                    lines[-1] += newline

            def upsert(section: str | None, key: str, value: str) -> None:
                replacement = f"{key}={value}"
                key_pattern = re.compile(rf"^(\s*{re.escape(key)}\s*)=.*$")

                if section is None:
                    for idx, line in enumerate(lines):
                        if key_pattern.match(line):
                            line_ending = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else newline)
                            lines[idx] = f"{replacement}{line_ending}"
                            return
                    ensure_trailing_newline()
                    lines.append(f"{replacement}{newline}")
                    return

                in_section = False
                insert_at = None
                for idx, line in enumerate(lines):
                    match = section_pattern.match(line.strip())
                    if match:
                        if in_section:
                            insert_at = idx
                            break
                        if match.group("section") == section:
                            in_section = True
                            continue
                    if in_section and key_pattern.match(line):
                        line_ending = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else newline)
                        lines[idx] = f"{replacement}{line_ending}"
                        return

                if in_section:
                    if insert_at is None:
                        ensure_trailing_newline()
                        insert_at = len(lines)
                    lines.insert(insert_at, f"{replacement}{newline}")
                    return

                ensure_trailing_newline()
                if lines and lines[-1].strip():
                    lines.append(newline)
                lines.append(f"[{section}]{newline}")
                lines.append(f"{replacement}{newline}")

            for raw_key, raw_value in overrides.items():
                section, key = self._split_ini_override_key(str(raw_key))
                value = str(raw_value).strip()
                if key:
                    upsert(section, key, value)

            ini_file.write_text("".join(lines), encoding="utf-8")
            return True
        except Exception as exc:
            decky.logger.error(f"Failed to apply OptiScaler.ini overrides to {ini_file}: {exc}")
            return False

    def _sync_variant_root_extra_files(self, fgmod_path: Path, fsr4_variant: str | None) -> None:
        selected_extra_files = {extra_file["name"]: extra_file for extra_file in self._fsr4_variant_extra_files(fsr4_variant)}
        for filename in VARIANT_EXTRA_FILENAMES:
            destination = fgmod_path / filename
            if filename not in selected_extra_files:
                if destination.exists() and self._is_managed_support_file(destination, fgmod_path):
                    destination.unlink()
                continue
            source_path = self._fsr4_variant_extra_file_path(fgmod_path, fsr4_variant, filename)
            if not source_path.exists():
                raise FileNotFoundError(f"Prepared FSR4 variant extra file missing: {source_path}")
            shutil.copy2(source_path, destination)

    def _activate_default_fsr4_variant(self, fgmod_path: Path, fsr4_variant: str | None) -> str:
        variant_id = self._normalize_fsr4_variant(fsr4_variant)
        variant_path = self._fsr4_variant_path(fgmod_path, variant_id)
        if not variant_path.exists():
            raise FileNotFoundError(f"Prepared FSR4 variant missing: {variant_path}")
        shutil.copy2(variant_path, fgmod_path / FSR4_UPSCALER_FILENAME)
        self._sync_variant_root_extra_files(fgmod_path, variant_id)
        return variant_id

    def _detect_fsr4_variant(self, directory: Path, upscaler_path: Path) -> str | None:
        # The combined runtime has the Lite runtime's files plus 4.0.2c's custom folder (and maybe HLX DLSS's).
        if (self._custom_402c_folder(directory) / CUSTOM_UPSCALER_MARKER).exists():
            return COMBINED_VARIANT
        # HelixSR lives in its own subfolder; the game root keeps the INT8 FSR4 upscaler.
        if ((directory / HELIXSR_GAME_SUBDIR / HELIXSR_GAME_MARKER).exists()
                or (self._helixsr_hlx_folder(directory) / HELIXSR_GAME_MARKER).exists()):
            return HELIXSR_VARIANT
        upscaler_sha256 = self._file_sha256(upscaler_path) if upscaler_path.exists() else None
        for variant_id, variant in FSR4_VARIANTS.items():
            if variant.get("helixsr"):
                continue
            extra_files = list(variant.get("extra_files") or [])
            if not extra_files:
                continue
            if not upscaler_sha256 or str(variant.get("sha256") or "").lower() != str(upscaler_sha256).lower():
                continue
            matched = True
            for extra_file in extra_files:
                file_path = directory / extra_file["name"]
                if not file_path.exists() or self._file_sha256(file_path).lower() != extra_file["sha256"].lower():
                    matched = False
                    break
            if matched:
                return variant_id
        if not upscaler_sha256:
            return None
        normalized_sha = str(upscaler_sha256).lower()
        for variant_id, variant in FSR4_VARIANTS.items():
            if variant.get("extra_files") or variant.get("helixsr"):
                continue
            if str(variant.get("sha256") or "").lower() == normalized_sha:
                return variant_id
        return None

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
        elif filename in VARIANT_EXTRA_FILENAMES:
            candidates.append(fgmod_path / filename)
            for variant_id in FSR4_VARIANTS:
                for extra_file in self._fsr4_variant_extra_files(variant_id):
                    if extra_file["name"] == filename:
                        candidates.append(self._fsr4_variant_extra_file_path(fgmod_path, variant_id, filename))
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

    def _repair_plugins_path_values(self, content: str) -> str:
        """Undo an old template bug: an unanchored Path=auto -> Path=plugins also turned OptiDllPath, NvapiPath,
        FfxDx12*Path, XeSSPath, TTFFontPath, ... into "plugins". Only the bare [Plugins] Path keeps it."""
        return re.sub(r'(?m)^(\s*)(\w+Path)(\s*=\s*)plugins[ \t]*$', r'\1\2\3auto', content)

    def _repair_optiscaler_ini_paths(self, ini_file) -> bool:
        try:
            content = Path(ini_file).read_text(encoding="utf-8", errors="replace")
            repaired = self._repair_plugins_path_values(content)
            if repaired != content:
                Path(ini_file).write_text(repaired, encoding="utf-8")
                decky.logger.info(f"Repaired library paths wrongly set to 'plugins' in {ini_file}")
            return True
        except Exception as exc:
            decky.logger.error(f"Failed to repair OptiScaler.ini paths in {ini_file}: {exc}")
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
                
                # Replace [Plugins] Path=auto with Path=plugins (only the bare "Path" key)
                updated_content = re.sub(r'(?m)^Path\s*=\s*auto', 'Path=plugins', updated_content)
                updated_content = self._repair_plugins_path_values(updated_content)

                # OptiScaler doesn't look for or announce updates: the plugin pins its builds
                updated_content = re.sub(r'CheckForUpdate\s*=\s*auto', 'CheckForUpdate=false', updated_content)

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

    # ── GitHub requests ───────────────────────────────────────────────────────

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
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=REQUEST_FALLBACK_TIMEOUT)
            except subprocess.TimeoutExpired:
                errors.append(f"{command[0]} timed out")
                continue
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
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=DOWNLOAD_FALLBACK_TIMEOUT)
            except subprocess.TimeoutExpired:
                errors.append(f"{command[0]} timed out")
                continue
            if result.returncode == 0 and destination.exists() and destination.stat().st_size > 0:
                return
            errors.append(f"{command[0]} failed: {result.stderr.strip() or result.returncode}")

        raise RuntimeError("; ".join(errors))

    async def extract_static_optiscaler(self, selected_default_variant: str = DEFAULT_FSR4_VARIANT) -> dict:
        """Prepare the shared ~/fgmod bundle with all bundled FSR4 runtime variants."""
        staging_path = None
        try:

            bin_path = Path(decky.DECKY_PLUGIN_DIR) / "bin"
            final_extract_path = Path(decky.HOME) / "fgmod"
            assets_dir = self._get_assets_dir()
            selected_default_variant = self._normalize_fsr4_variant(selected_default_variant)

            required_binary_names = [
                OPTISCALER_ARCHIVE_ASSET["name"],
                FSR4_INT8_ASSET["name"],
                FSR4_VALVE_411_ASSET["name"],
                FSR4_LITE_412_ASSET["name"],
                FSR4_LITE_412_VK_ASSET["name"],
                OPTISCALER_V10_ASSET["name"],
                OPTIPATCHER_ASSET["name"],
            ]
            try:
                self._ensure_runtime_binaries(required_binary_names)
            except Exception as binary_error:
                decky.logger.warning(f"Could not prepare runtime binaries: {binary_error}")

            if not bin_path.exists():
                return {"status": "error", "message": f"Bin directory not found: {bin_path}"}

            # The INT8 (Steam Deck / RDNA2-3) upscaler and OptiPatcher always come from the
            # bundled, hash-verified binaries -- they are independent of the OptiScaler archive.
            fsr4_int8_src = bin_path / FSR4_INT8_ASSET["name"]
            fsr4_valve_411_src = bin_path / FSR4_VALVE_411_ASSET["name"]
            fsr4_lite_412_src = bin_path / FSR4_LITE_412_ASSET["name"]
            fsr4_lite_412_vk_src = bin_path / FSR4_LITE_412_VK_ASSET["name"]
            optiscaler_v10_src = bin_path / OPTISCALER_V10_ASSET["name"]
            optipatcher_src = bin_path / OPTIPATCHER_ASSET["name"]
            for required_path, asset in [
                (fsr4_int8_src, FSR4_INT8_ASSET),
                (fsr4_valve_411_src, FSR4_VALVE_411_ASSET),
                (fsr4_lite_412_src, FSR4_LITE_412_ASSET),
                (fsr4_lite_412_vk_src, FSR4_LITE_412_VK_ASSET),
                (optiscaler_v10_src, OPTISCALER_V10_ASSET),
                (optipatcher_src, OPTIPATCHER_ASSET),
            ]:
                if not required_path.exists():
                    return {
                        "status": "error",
                        "message": f"Required bundled asset missing: {asset['name']}",
                    }
                self._verify_bundled_asset(required_path, asset["sha256"], asset["name"])

            # ── Stage A: obtain the base OptiScaler archive ───────────────────────
            bundled_archive = bin_path / OPTISCALER_ARCHIVE_ASSET["name"]
            if not bundled_archive.exists():
                return {
                    "status": "error",
                    "message": f"OptiScaler archive unavailable (bundled missing: {bundled_archive.name})",
                }
            self._verify_bundled_asset(
                bundled_archive,
                OPTISCALER_ARCHIVE_ASSET["sha256"],
                OPTISCALER_ARCHIVE_ASSET["name"],
            )
            optiscaler_archive = bundled_archive
            optiscaler_version = OPTISCALER_ARCHIVE_ASSET["version"]
            optiscaler_archive_sha256 = OPTISCALER_ARCHIVE_ASSET["sha256"]

            final_extract_path.parent.mkdir(parents=True, exist_ok=True)
            staging_path = Path(
                tempfile.mkdtemp(prefix=".fgmod-staging-", dir=str(final_extract_path.parent))
            )
            staging_path.chmod(0o755)
            extract_path = staging_path

            self._extract_archive(optiscaler_archive, extract_path)

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

            native_upscaler_root = extract_path / FSR4_UPSCALER_FILENAME
            native_upscaler_source = native_upscaler_root

            if native_upscaler_root.exists():
                # Pinned bundle: enforce the known-good archive-native hash.
                native_upscaler_sha256 = self._verify_bundled_asset(
                    native_upscaler_root,
                    FSR4_VARIANTS["lite-412-i8"]["sha256"],
                    "Archive-native FSR4 upscaler",
                )
            else:
                decky.logger.warning("Archive-native FSR4 upscaler missing; using the INT8 DLL.")
                native_upscaler_source = fsr4_int8_src
                native_upscaler_sha256 = self._file_sha256(fsr4_int8_src)

            rdna2_valve_dir = extract_path / FSR4_VARIANTS["rdna2-valve-411-pre10"]["dir_name"]
            rdna2_valve_dir.mkdir(parents=True, exist_ok=True)
            rdna2_valve_upscaler = rdna2_valve_dir / FSR4_UPSCALER_FILENAME
            shutil.copy2(native_upscaler_source, rdna2_valve_upscaler)
            self._verify_bundled_asset(
                rdna2_valve_upscaler,
                FSR4_VARIANTS["rdna2-valve-411-pre10"]["sha256"],
                "Prepared rdna2-valve-411-pre10 FSR4 upscaler",
            )
            self._verify_bundled_asset(
                fsr4_valve_411_src,
                FSR4_VALVE_411_ASSET["sha256"],
                "Bundled rdna2-valve-411-pre10 driver override",
            )
            rdna2_valve_driver = rdna2_valve_dir / FSR4_DRIVER_OVERRIDE_FILENAME
            shutil.copy2(fsr4_valve_411_src, rdna2_valve_driver)
            self._verify_bundled_asset(
                rdna2_valve_driver,
                FSR4_VALVE_411_ASSET["sha256"],
                "Prepared rdna2-valve-411-pre10 driver override",
            )
            lite_412_dir = extract_path / FSR4_VARIANTS["lite-412-i8"]["dir_name"]
            lite_412_dir.mkdir(parents=True, exist_ok=True)
            lite_412_upscaler = lite_412_dir / FSR4_UPSCALER_FILENAME
            shutil.copy2(native_upscaler_source, lite_412_upscaler)
            self._verify_bundled_asset(
                lite_412_upscaler,
                FSR4_VARIANTS["lite-412-i8"]["sha256"],
                "Prepared lite-412-i8 FSR4 upscaler",
            )
            for source, destination_name, asset in [
                (fsr4_lite_412_src, FSR4_DRIVER_OVERRIDE_FILENAME, FSR4_LITE_412_ASSET),
                (fsr4_lite_412_vk_src, FSR4_VK_DRIVER_OVERRIDE_FILENAME, FSR4_LITE_412_VK_ASSET),
                (optiscaler_v10_src, "OptiScaler.dll", OPTISCALER_V10_ASSET),
            ]:
                destination = lite_412_dir / destination_name
                shutil.copy2(source, destination)
                self._verify_bundled_asset(destination, asset["sha256"], f"Prepared lite-412-i8 {destination_name}")
            if not self._create_renamed_copies(lite_412_dir / "OptiScaler.dll", lite_412_dir / "renames"):
                return {"status": "error", "message": "Failed to prepare renamed OptiScaler 10 proxies."}

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
                    "sha256": optiscaler_archive_sha256,
                    "source": "bundled",
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
                        "injector": (
                            {
                                "name": variant["injector"]["name"],
                                "sha256": variant["injector"]["sha256"],
                                "source_asset_name": variant["injector"]["source_asset_name"],
                                "source_version": variant["injector"]["source_version"],
                                "path": str((Path(variant["dir_name"]) / variant["injector"]["name"]).as_posix()),
                            }
                            if isinstance(variant.get("injector"), dict)
                            else None
                        ),
                        "config_overrides": dict(variant.get("config_overrides") or {}),
                        "extra_files": [
                            {
                                "name": extra_file["name"],
                                "sha256": extra_file["sha256"],
                                "source_asset_name": extra_file["source_asset_name"],
                                "source_version": extra_file["source_version"],
                                "path": str((Path(variant["dir_name"]) / extra_file["name"]).as_posix()),
                            }
                            for extra_file in variant.get("extra_files", [])
                        ],
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

            missing_files = self._missing_fgmod_files(extract_path)
            if missing_files:
                raise RuntimeError(
                    "Prepared OptiScaler bundle is incomplete; missing: " + ", ".join(missing_files)
                )

            self._replace_directory_atomically(extract_path, final_extract_path)
            staging_path = None

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
        finally:
            if staging_path is not None and staging_path.exists():
                shutil.rmtree(staging_path, ignore_errors=True)

    @_worker
    async def run_uninstall_fgmod(self) -> dict:
        try:
            # Remove fgmod directory
            fgmod_path = Path(decky.HOME) / "fgmod"
            # half-done installs/updates leave staging and backup copies of the bundle next to it
            for leftover in fgmod_path.parent.glob(".fgmod-*"):
                if leftover.is_dir() and leftover.name.startswith((".fgmod-staging-", ".fgmod-backup-")):
                    shutil.rmtree(leftover, ignore_errors=True)

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

    @_worker
    async def run_install_fgmod(self, selected_default_variant: str = DEFAULT_FSR4_VARIANT) -> dict:
        try:
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
        if not path.exists():
            return {"exists": False}

        missing_files = self._missing_fgmod_files(path)
        if missing_files:
            return {"exists": False, "missing_files": missing_files}

        manifest = self._load_install_manifest(path)
        selected_variant = self._selected_fsr4_variant(path)
        return {
            "exists": True,
            "version": self._fgmod_version(path),
            "selected_fsr4_variant": selected_variant,
            "selected_fsr4_variant_label": FSR4_VARIANTS[selected_variant]["label"],
            "install_manifest_present": bool(manifest),
        }

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
        previous_marker_metadata = self._read_marker(directory / MARKER_FILENAME)
        previous_variant = str(previous_marker_metadata.get("fsr4_variant") or "").strip()
        selected_variant = self._selected_fsr4_variant(fgmod_path, fsr4_variant)
        selected_variant_info = FSR4_VARIANTS[selected_variant]
        selected_config_overrides = self._fsr4_variant_config_overrides(selected_variant)
        if previous_variant == "rdna2-valve-411-pre10" and selected_variant != previous_variant:
            selected_config_overrides.setdefault("FSR.Fsr4ForceModel", "auto")
            selected_config_overrides.setdefault("Plugins.LoadCustomAmdxc64OnRdna2", "false")
        if previous_variant in FSR4_VARIANTS and selected_variant != previous_variant:
            for key, value in (FSR4_VARIANTS[previous_variant].get("leave_config_overrides") or {}).items():
                selected_config_overrides.setdefault(key, value)
        selected_upscaler_src = self._fsr4_variant_path(fgmod_path, selected_variant)
        if not selected_upscaler_src.exists():
            selected_upscaler_src = fgmod_path / FSR4_UPSCALER_FILENAME
        if not selected_upscaler_src.exists():
            return {
                "status": "error",
                "message": f"FSR4 upscaler variant not found for {selected_variant}. Reinstall OptiScaler.",
            }
        selected_extra_files = self._fsr4_variant_extra_files(selected_variant)
        optiscaler_version = self._fgmod_version(fgmod_path)
        selected_upscaler_sha256 = self._file_sha256(selected_upscaler_src)
        use_helixsr = bool(selected_variant_info.get("helixsr"))
        if use_helixsr:
            try:
                self._helixsr_built_dll()
            except RuntimeError as exc:
                return {"status": "error", "message": str(exc)}

        try:
            backed_up_proxies = self._backup_preexisting_proxy_files(directory, fgmod_path)
            if backed_up_proxies:
                decky.logger.info(f"Backed up pre-existing proxy files: {backed_up_proxies}")

            removed_patch_files = []
            for filename in dict.fromkeys(PATCH_CLEANUP_FILES):
                path = directory / filename
                if path.exists() and not self._is_reshade_link(path):
                    path.unlink()
                    removed_patch_files.append(filename)
            if removed_patch_files:
                decky.logger.info(f"Removed stale patch files: {removed_patch_files}")

            backed_up_originals = []
            removed_managed_support = []
            for dll in ORIGINAL_DLL_BACKUPS:
                source = directory / dll
                backup = directory / f"{dll}.b"
                if not source.exists() or backup.exists() or self._is_reshade_link(source):
                    continue
                if allow_managed_support_cleanup and self._is_managed_support_file(source, fgmod_path):
                    source.unlink()
                    removed_managed_support.append(dll)
                    continue
                shutil.move(source, backup)
                backed_up_originals.append(dll)
            if removed_managed_support:
                decky.logger.info(f"Removed managed support files before repatch: {removed_managed_support}")
            if backed_up_originals:
                decky.logger.info(f"Backed up original game DLLs: {backed_up_originals}")

            variant_renamed = self._fsr4_variant_renamed_proxy_path(fgmod_path, selected_variant, dll_name)
            variant_injector = self._fsr4_variant_injector_path(fgmod_path, selected_variant)
            root_renamed = fgmod_path / "renames" / dll_name
            destination_dll = directory / dll_name
            if variant_renamed and variant_renamed.exists():
                source_for_copy = variant_renamed
            elif variant_injector and variant_injector.exists():
                source_for_copy = variant_injector
            elif root_renamed.exists():
                source_for_copy = root_renamed
            else:
                source_for_copy = optiscaler_dll
            if destination_dll.is_symlink():   # copying onto ReShade's link would overwrite ReShade's own DLL
                destination_dll.unlink()
            shutil.copy2(source_for_copy, destination_dll)

            target_ini = directory / "OptiScaler.ini"
            source_ini = fgmod_path / "OptiScaler.ini"
            if not (preserve_ini and target_ini.exists()):
                if source_ini.exists():
                    shutil.copy2(source_ini, target_ini)
                else:
                    decky.logger.warning("No OptiScaler.ini found to copy")

            if target_ini.exists():
                self._migrate_optiscaler_ini(target_ini)
                self._disable_hq_font_auto(target_ini)
                self._repair_optiscaler_ini_paths(target_ini)
                self._apply_optiscaler_ini_overrides(target_ini, selected_config_overrides)

            plugins_src = fgmod_path / "plugins"
            plugins_dest = directory / "plugins"
            if plugins_src.exists():
                shutil.copytree(plugins_src, plugins_dest, dirs_exist_ok=True)
            else:
                decky.logger.warning("Plugins directory missing in fgmod bundle")

            d3d12_src = fgmod_path / "D3D12_Optiscaler"
            d3d12_dest = directory / "D3D12_Optiscaler"
            if d3d12_src.exists():
                shutil.copytree(d3d12_src, d3d12_dest, dirs_exist_ok=True)
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

            for extra_file in selected_extra_files:
                source = self._fsr4_variant_extra_file_path(fgmod_path, selected_variant, extra_file["name"])
                dest = directory / extra_file["name"]
                if source.exists():
                    shutil.copy2(source, dest)
                    copied_support.append(extra_file["name"])
                else:
                    missing_support.append(extra_file["name"])

            if missing_support:
                decky.logger.warning(f"Support files missing from fgmod bundle: {missing_support}")

            helixsr_note = ""
            if not selected_variant_info.get("combined"):
                self._remove_custom_upscalers(directory)
            if use_helixsr:
                helixsr_note = f" {self._helixsr_apply_to_game(directory, destination_dll)}"
            elif selected_variant_info.get("combined"):
                helixsr_note = f" {self._apply_combined_upscalers(directory, fgmod_path, destination_dll)}"
                # HelixSR's restore and HLX DLSS's keys can touch this variant's own keys: FSR 4 stays selected.
                if target_ini.exists():
                    self._apply_optiscaler_ini_overrides(target_ini, self._fsr4_variant_config_overrides(selected_variant))
            elif self._helixsr_remove_from_game(directory, restore_ini=True):
                helixsr_note = " HelixSR removed; OptiScaler is back to FSR."
                # HelixSR's restore puts back keys still holding its values (Dx12Upscaler=ffx, UpscalerIndex=0),
                # which can be this variant's own values too.
                if target_ini.exists():
                    self._apply_optiscaler_ini_overrides(target_ini, self._fsr4_variant_config_overrides(selected_variant))

            return {
                "status": "success",
                "message": (
                    f"OptiScaler files copied to {directory} using "
                    f"{selected_variant_info['label']}.{helixsr_note}"
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

            removed_files = []
            for filename in set(INJECTOR_FILENAMES + SUPPORT_FILES + VARIANT_EXTRA_FILENAMES + [FSR4_UPSCALER_FILENAME]):
                path = directory / filename
                if path.exists() and not self._is_reshade_link(path):
                    path.unlink()
                    removed_files.append(filename)

            legacy_removed = []
            for legacy in LEGACY_FILES:
                path = directory / legacy
                if path.exists():
                    try:
                        path.unlink()
                    except IsADirectoryError:
                        shutil.rmtree(path, ignore_errors=True)
                    legacy_removed.append(legacy)

            plugins_dir = directory / "plugins"
            (plugins_dir / "OptiPatcher.asi").unlink(missing_ok=True)
            try:
                plugins_dir.rmdir()   # only when nothing else is in it
            except OSError:
                pass

            d3d12_dir = directory / "D3D12_Optiscaler"
            if d3d12_dir.exists():
                shutil.rmtree(d3d12_dir, ignore_errors=True)

            # OptiScaler.ini is removed above (LEGACY_FILES), so only HelixSR's folder goes.
            self._helixsr_remove_from_game(directory, restore_ini=False)
            self._remove_custom_upscalers(directory)

            restored_backups = []
            for dll in dict.fromkeys(RESTORABLE_BACKUP_FILES):
                backup = directory / f"{dll}.b"
                original = directory / dll
                if self._is_reshade_link(backup):   # set aside by an older patch: ReShade relinks itself
                    backup.unlink()
                    continue
                if backup.exists():
                    if original.exists():
                        original.unlink()
                    shutil.move(backup, original)
                    restored_backups.append(dll)
            if restored_backups:
                decky.logger.info(f"Restored backups: {restored_backups}")

            uninstaller = directory / "fgmod-uninstaller.sh"
            if uninstaller.exists():
                uninstaller.unlink()

            (directory / MARKER_FILENAME).unlink(missing_ok=True)

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
            for appmanifest in steamapps_path.glob(f"appmanifest_{appid}.acf" if appid else "appmanifest_*.acf"):
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
        if not appid or not games:
            for shortcut in self._find_non_steam_shortcuts():
                if appid is None or shortcut["appid"] == str(appid):
                    games.append(shortcut)
        deduped: dict[str, dict] = {}
        for game in games:
            deduped[str(game["appid"])] = game
        return sorted(deduped.values(), key=lambda g: g["name"].lower())

    # ── Non-Steam shortcuts (userdata/<id>/config/shortcuts.vdf) ─────────────

    def _parse_binary_vdf(self, data: bytes) -> dict:
        """Minimal parser for Steam's binary VDF (map / string / int32 nodes)."""
        pos = 0

        def read_cstring() -> str:
            nonlocal pos
            end = data.index(b"\x00", pos)
            value = data[pos:end].decode("utf-8", errors="replace")
            pos = end + 1
            return value

        def read_map() -> dict:
            nonlocal pos
            result: dict = {}
            while pos < len(data):
                node_type = data[pos]
                pos += 1
                if node_type == 0x08:
                    return result
                key = read_cstring()
                if node_type == 0x00:
                    result[key] = read_map()
                elif node_type == 0x01:
                    result[key] = read_cstring()
                elif node_type == 0x02:
                    result[key] = int.from_bytes(data[pos:pos + 4], "little", signed=False)
                    pos += 4
                elif node_type == 0x07:
                    result[key] = int.from_bytes(data[pos:pos + 8], "little", signed=False)
                    pos += 8
                else:
                    raise ValueError(f"Unsupported binary VDF node type 0x{node_type:02x} at {pos - 1}")
            return result

        return read_map()

    def _shortcuts_vdf_paths(self) -> list[Path]:
        paths: list[Path] = []
        seen: set[str] = set()
        for steam_root in self._steam_root_candidates():
            userdata = steam_root / "userdata"
            if not userdata.is_dir():
                continue
            for shortcuts_file in userdata.glob("*/config/shortcuts.vdf"):
                try:
                    key = str(shortcuts_file.resolve())
                except OSError:
                    key = str(shortcuts_file)
                if key not in seen and shortcuts_file.is_file():
                    paths.append(shortcuts_file)
                    seen.add(key)
        return paths

    def _is_unsafe_scan_root(self, root: Path) -> bool:
        """Roots too broad to scan recursively for .exe files (home, drive roots, ...)."""
        home = self._home_path()
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if len(resolved.parts) < 4 or resolved == home or resolved in home.parents:
            return True
        if resolved.parent == home and resolved.name.lower() in ("desktop", "downloads", "documents", "games"):
            return True
        try:
            return os.path.ismount(resolved)
        except OSError:
            return False

    def _find_non_steam_shortcuts(self) -> list[dict]:
        """Non-Steam shortcuts that launch a Windows .exe directly: patchable like a Steam game,
        with launch options set on the shortcut's appid. Shortcuts that start a launcher
        (Heroic, Lutris, ...) or a native Linux program are ignored: the game .exe is unknown.
        """
        shortcuts: list[dict] = []
        for shortcuts_file in self._shortcuts_vdf_paths():
            try:
                parsed = self._parse_binary_vdf(shortcuts_file.read_bytes())
            except Exception as exc:
                decky.logger.error(f"[Framegen] failed to parse {shortcuts_file}: {exc}")
                continue
            root = parsed.get("shortcuts") or parsed.get("Shortcuts") or {}
            if not isinstance(root, dict):
                continue
            for entry in root.values():
                if not isinstance(entry, dict):
                    continue
                fields = {str(k).lower(): v for k, v in entry.items()}
                name = str(fields.get("appname") or "").strip()
                exe_raw = str(fields.get("exe") or "").strip()
                if not name or not exe_raw:
                    continue
                appid_value = fields.get("appid")
                if isinstance(appid_value, int) and appid_value:
                    appid = appid_value & 0xFFFFFFFF
                else:
                    # Older Steam builds do not store the appid; derive it the same way Steam does.
                    appid = (zlib.crc32((exe_raw + name).encode("utf-8")) & 0xFFFFFFFF) | 0x80000000
                exe_path_str = exe_raw.strip('"')
                if not exe_path_str.lower().endswith(".exe"):
                    continue
                exe_path = Path(exe_path_str)
                if not exe_path.is_file():
                    continue
                shortcuts.append({
                    "appid": str(appid),
                    "name": name,
                    "library_path": "",
                    "install_path": str(exe_path.parent),
                    "non_steam": True,
                    "shortcut_exe": str(exe_path),
                })
        return shortcuts

    def _game_not_found_message(self, appid: str) -> str:
        return "Game not found in Steam library or non-Steam shortcuts."

    def _game_candidate_executables(self, game_info: dict) -> list[Path]:
        install_root = Path(game_info["install_path"])
        shortcut_exe = game_info.get("shortcut_exe")
        if shortcut_exe and self._is_unsafe_scan_root(install_root):
            exe = Path(shortcut_exe)
            return [exe] if exe.is_file() else []
        return _scan_once(("exes", str(install_root)), lambda: self._candidate_executables(install_root))

    def _game_record(self, appid: str) -> dict | None:
        matches = _scan_once(("game", str(appid)), lambda: self._find_installed_games(appid))
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
            process_lines = _scan_once("ps", lambda: subprocess.run(
                ["ps", "-eo", "args="], capture_output=True, text=True, check=False, timeout=PROCESS_LIST_TIMEOUT
            ).stdout.splitlines())
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
        candidates = self._game_candidate_executables(game_info)
        if not candidates:
            return install_root, None
        running_exe = self._best_running_executable(candidates)
        if running_exe:
            return running_exe.parent, running_exe
        best = max(candidates, key=lambda exe: self._exe_score(exe, install_root, game_info["name"]))
        return best.parent, best

    def _is_game_running(self, game_info: dict) -> bool:
        candidates = self._game_candidate_executables(game_info)
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
        return await asyncio.to_thread(self._list_installed_games)

    def _list_installed_games(self) -> dict:
        try:
            games = []
            for game in self._find_installed_games():
                install_root = Path(game["install_path"])
                games.append({
                    "appid": str(game["appid"]),
                    "name": game["name"],
                    "install_found": install_root.exists(),
                    "non_steam": bool(game.get("non_steam")),
                })
            games.sort(key=lambda g: g["name"].lower())
            return {"status": "success", "games": games}
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}

    async def log_error(self, error: str) -> None:
        decky.logger.error(f"FRONTEND: {error}")

    # ── AppID-based patch / unpatch / status ───────────────────────────────────────

    def _game_status(self, appid: str, game_info: dict | None) -> dict:
        try:
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
                    "message": self._game_not_found_message(str(appid)),
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
            detected_variant = self._detect_fsr4_variant(target_dir, target_dir / FSR4_UPSCALER_FILENAME)
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
        selected_executable_path: str = "",
    ) -> dict:
        try:
            if dll_name not in VALID_DLL_NAMES:
                return {"status": "error", "message": f"Invalid proxy DLL name: {dll_name}"}
            game_info = self._game_record(str(appid))
            if not game_info:
                return {"status": "error", "message": self._game_not_found_message(str(appid))}
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

            # Auto-detect the right directory to patch, unless the user selected
            # a specific executable from the ranked target list.
            if selected_executable_path:
                target_exe = Path(os.path.abspath(os.path.expanduser(selected_executable_path)))
                if not target_exe.is_file() or target_exe.suffix.lower() != ".exe":
                    return {"status": "error", "message": f"Invalid selected executable: {selected_executable_path}"}
                try:
                    target_exe.resolve().relative_to(install_root.resolve())
                except ValueError:
                    return {"status": "error", "message": "Selected executable is outside the Steam game install directory."}
                target_dir = target_exe.parent
            else:
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
        
        self.reshade_release_cache = {}
        
        # Create necessary directories
        os.makedirs(self.main_path, exist_ok=True)

    def _get_assets_dir(self) -> Path:
        """Get the assets directory, checking both possible locations"""
        plugin_dir = Path(decky.DECKY_PLUGIN_DIR)
        
        # Check defaults/assets first (development)
        defaults_assets = plugin_dir / "defaults" / "assets"
        if defaults_assets.exists():
            return defaults_assets
            
        # Check assets (decky store installation)
        assets = plugin_dir / "assets"
        if assets.exists():
            return assets
            
        # Fallback to defaults/assets even if it doesn't exist (for error reporting)
        decky.logger.warning(f"Neither {defaults_assets} nor {assets} exists, defaulting to {defaults_assets}")
        return defaults_assets

    def _get_plugin_root_dir(self) -> Path:
        return Path(decky.DECKY_PLUGIN_DIR)

    def _get_bin_dir(self) -> Path:
        return self._get_plugin_root_dir() / "bin"

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
                actual_hash = self._file_sha256(temp_destination)
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
                    actual_hash = self._file_sha256(destination)
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
                except (OSError, ValueError) as exc:  # If file is corrupted, start fresh
                    decky.logger.warning(f"Ignoring unreadable {preferences_file}: {exc}")
            
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
                    except OSError:
                        pass
            
            if not preferences:
                return {"status": "success", "preferences": None, "message": "No preferences file found"}
            
            # Validate the preferences structure
            if "selected_shaders" not in preferences:
                return {"status": "error", "message": "Invalid preferences file format"}
            
            return {
                "status": "success", 
                "preferences": preferences,
                "selected_shaders": preferences["selected_shaders"]
            }
            
        except Exception as e:
            decky.logger.error(f"Error loading shader preferences: {str(e)}")
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
                except (OSError, ValueError) as exc:  # If file is corrupted, start fresh
                    decky.logger.warning(f"Ignoring unreadable {preferences_file}: {exc}")
            
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

    @_worker
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
        """For the AutoHDR warning: only the Steam Deck OLED's board is known to be an OLED panel."""
        try:
            board_name = Path("/sys/devices/virtual/dmi/id/board_name").read_text().strip()
        except OSError:
            board_name = ""
        return {"status": "success", "is_oled": "Galileo" in board_name}

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

    def _fetch_reshade_page_with_curl(self, base_url: str) -> str:
        process = subprocess.run(
            ["curl", "-fsSL", "--retry", "2", "--connect-timeout", "15", "--compressed", "--http1.1", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", base_url],
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ.copy()
        )

        if process.returncode == 0 and process.stdout:
            return process.stdout

        raise RuntimeError(process.stderr.strip() or f"curl failed for {base_url}")

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

    @_worker
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

            # The script's normal progress goes to stderr too: it only matters when the install fails.
            if process.returncode != 0:
                decky.logger.error(f"ReShade install failed:\n{process.stdout}\n{process.stderr}")
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

    @_worker
    async def run_uninstall_reshade(self) -> dict:
        try:
            assets_dir = self._get_assets_dir()
            script_path = assets_dir / "reshade-uninstall.sh"
            
            if not script_path.exists():
                return {"status": "error", "message": "Uninstall script not found"}

            # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
            clean_env = {**os.environ, **self.environment}
            clean_env["LD_LIBRARY_PATH"] = ""
            
            try:
                process = subprocess.run(
                    ["/bin/bash", str(script_path)],
                    cwd=str(assets_dir),
                    env=clean_env,
                    capture_output=True,
                    text=True,
                    timeout=GAME_SCRIPT_TIMEOUT
                )
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "The ReShade uninstall timed out."}

            if process.returncode != 0:
                return {"status": "error", "message": process.stderr}

            # Remove installation markers
            marker_file = Path(self.main_path) / ".installed"
            addon_marker = Path(self.main_path) / ".installed_addon"
            if marker_file.exists():
                marker_file.unlink()
            if addon_marker.exists():
                addon_marker.unlink()

            # Clear installed configuration
            await self.clear_installed_configuration()
                
            return {"status": "success", "output": "ReShade uninstalled"}
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}

    def _resolve_steam_reshade_target(self, appid: str) -> tuple[str, str]:
        game_info = self._game_record(str(appid))
        if not game_info:
            raise ValueError(self._game_not_found_message(str(appid)))

        install_root = Path(game_info["install_path"])
        if not install_root.exists():
            raise ValueError("Game install directory does not exist.")

        target_dir, target_exe = self._guess_patch_target(game_info)
        if target_exe and target_exe.exists():
            return str(target_dir), str(target_exe)

        return str(target_dir), ""

    @_worker
    async def manage_game_reshade(self, appid: str, dll_override: str = "dxgi", selected_executable_path: str = "") -> dict:
        try:
            assets_dir = self._get_assets_dir()
            script_path = assets_dir / "reshade-game-manager.sh"

            validated_executable_path = ""
            if selected_executable_path:
                is_valid, validation_result = self._validate_selected_windows_executable_path(selected_executable_path)
                if not is_valid:
                    return {"status": "error", "message": validation_result}
                validated_executable_path = validation_result

            backend_detected_executable_path = ""

            try:
                # Use selected executable path if provided, otherwise the target the Python backend detects
                if validated_executable_path:
                    game_path = os.path.dirname(validated_executable_path)
                else:
                    game_path, backend_detected_executable_path = self._resolve_steam_reshade_target(appid)
            except ValueError as e:
                return {"status": "error", "message": str(e)}

            cmd = ["/bin/bash", str(script_path), game_path, dll_override]

            decky.logger.info(f"Applying ReShade ({dll_override}) to {game_path}")
            
            # Create environment with required LD_LIBRARY_PATH fix for Decky v3.1.10+
            clean_env = {**os.environ, **self.environment}
            clean_env["LD_LIBRARY_PATH"] = ""
            
            try:
                process = subprocess.run(
                    cmd,
                    cwd=str(assets_dir),
                    env=clean_env,
                    capture_output=True,
                    text=True,
                    timeout=GAME_SCRIPT_TIMEOUT
                )
            except subprocess.TimeoutExpired:
                decky.logger.error(f"ReShade script timed out for {game_path}")
                return {"status": "error", "message": "Applying ReShade timed out."}

            # The script's normal progress goes to stderr too: it only matters when it fails.
            if process.returncode != 0:
                decky.logger.error(f"ReShade script failed:\n{process.stdout}\n{process.stderr}")
                return {"status": "error", "message": process.stderr}
                
            return {
                "status": "success",
                "output": process.stdout,
                "target_dir": game_path,
                "target_executable": validated_executable_path or backend_detected_executable_path,
            }
        except Exception as e:
            decky.logger.error(str(e))
            return {"status": "error", "message": str(e)}


# ===== HelixSR backend =====
# Ported from DeckyHelixSRManager (https://github.com/PeroTuncay/DeckyHelixSRManager, The Unlicense):
# release lookup, verified download, HelixSR's own setup run in the background with progress, and
# the OptiScaler route (HelixSR in a HelixSR folder next to OptiScaler.ini, OptiScaler.ini pointed
# at it, the previous values remembered). Unlike the manager, only the newest release is kept:
# an older install is replaced once the newest one has been built.
class _HelixSRMixin:
    _helixsr_latest_cache = None   # (fetched_at, release)
    _helixsr_download = None   # the download in progress or its error: {tag, version, path, total, phase, error}

    # ── paths ────────────────────────────────────────────────────────────────
    def _helixsr_root(self) -> Path:
        return Path(decky.HOME) / HELIXSR_DIRNAME

    def _helixsr_current_dir(self) -> Path:
        return self._helixsr_root() / "current"

    def _helixsr_staging_dir(self) -> Path:
        return self._helixsr_root() / "staging"

    def _helixsr_setup_log(self) -> Path:
        return self._helixsr_root() / "setup.log"

    def _helixsr_setup_rc(self) -> Path:
        return self._helixsr_root() / "setup.rc"

    def _helixsr_setup_state_file(self) -> Path:
        return self._helixsr_root() / "setup.json"

    # ── HelixSR DLL inspection ───────────────────────────────────────────────
    def _helixsr_is_helixsr(self, path: Path) -> bool:
        # "HelixSR 1.4.1" from 1.3 on; 1.2.0 only names itself "HelixSR (3.1.5)"
        try:
            with open(path, "rb") as f:
                return re.search(rb"HelixSR (\d+\.\d+\.\d+|\(3\.1\.\d+\))", f.read(4 << 20)) is not None
        except OSError:
            return False

    def _helixsr_dll_version(self, path: Path) -> str | None:
        try:
            with open(path, "rb") as f:
                match = re.search(rb"\x00HelixSR (\d+\.\d+\.\d+)\x00", f.read(4 << 20))
            return match.group(1).decode() if match else None
        except OSError:
            return None

    def _helixsr_has_embedded_network(self, path: Path) -> bool:
        try:
            with open(path, "rb") as f:
                f.seek(-32, os.SEEK_END)
                return f.read(8) == HELIXSR_EMBED_MAGIC
        except OSError:
            return False

    def _helixsr_has_network(self, path: Path) -> bool:
        """True once the setup appended the network to the DLL (or left the two older files next to it)."""
        if self._helixsr_has_embedded_network(path):
            return True
        return all((Path(path).parent / name).exists() for name in HELIXSR_SEPARATE_FILES)

    def _helixsr_release_dll(self, directory: Path) -> Path | None:
        candidates = [
            Path(directory) / HELIXSR_HLX_SUBDIR / HELIXSR_DLL_HLX,
            *(folder / name for folder in (Path(directory) / HELIXSR_OUT_SUBDIR, Path(directory))
              for name in (HELIXSR_DLL_NGX, HELIXSR_DLL_FFX)),
        ]
        return next((c for c in candidates if c.exists() and self._helixsr_is_helixsr(c)), None)

    def _helixsr_dll_kind(self, dll: Path) -> str:
        """hlx: 3.0+'s HLX DLSS (OptiScaler's custom DLSS upscaler); ffx: an FSR 3.1 replacement; ngx: 1.5/1.6."""
        name = dll.name.lower()
        return "hlx" if name == HELIXSR_DLL_HLX else "ngx" if name == HELIXSR_DLL_NGX else "ffx"

    def _helixsr_installed(self) -> dict | None:
        directory = self._helixsr_current_dir()
        dll = self._helixsr_release_dll(directory)
        if not dll:
            return None
        meta = self._read_json_file(directory / HELIXSR_META_FILENAME)
        tag = str(meta.get("tag") or "") or None
        return {
            "dir": directory,
            "dll": dll,
            "tag": tag,
            "version": self._helixsr_dll_version(dll) or (tag.lstrip("v") if tag else None),
            "label": str(meta.get("label") or ""),
            "sha256": meta.get("sha256"),
            "built": self._helixsr_has_network(dll),
            "kind": self._helixsr_dll_kind(dll),
        }

    def _helixsr_built_dll(self) -> Path:
        installed = self._helixsr_installed()
        if not installed:
            raise RuntimeError("HelixSR isn't installed yet. Press \"Install HelixSR\" first.")
        if installed["kind"] == "ngx":
            raise RuntimeError("The installed HelixSR release replaces DLSS (nvngx.dll), which this plugin doesn't support.")
        if not installed["built"]:
            raise RuntimeError("HelixSR has no network yet (its build didn't finish). Press \"Install HelixSR\" again.")
        return installed["dll"]

    def _helixsr_copy_dll(self, dll: Path, dest: Path) -> None:
        """Releases before 1.4.0 keep the network in two files next to the DLL: those go along."""
        shutil.copyfile(dll, dest)
        embedded = self._helixsr_has_embedded_network(dll)
        for name in HELIXSR_SEPARATE_FILES:
            src, dst = dll.parent / name, dest.parent / name
            if src.exists() and not embedded:
                shutil.copyfile(src, dst)
            elif dst.exists():
                dst.unlink()

    # ── releases ─────────────────────────────────────────────────────────────
    def _helixsr_release_zip(self, assets: list) -> dict | None:
        """HelixSR's own zip (HelixSR-<version>.zip), not HelixSR Scaler or HelixSR Desktop."""
        zips = [a for a in assets if str(a.get("name", "")).lower().endswith(".zip")]
        own = [a for a in zips if re.fullmatch(r"helixsr-\d[\w.\-]*\.zip", a["name"].lower())]
        other = [a for a in zips if not re.search(r"scaler|desktop", a["name"].lower())]
        return (own or other or [None])[0]

    @staticmethod
    def _helixsr_release_label(release: dict) -> str:
        """The release's full name, e.g. "HelixSR 3.2.0 (pre-release)"."""
        tag = str(release.get("tag_name") or "")
        label = " ".join(str(release.get("name") or "").split()) or f"HelixSR {tag.lstrip('vV')}"
        if release.get("prerelease") and "pre-release" not in label.lower() and "prerelease" not in label.lower():
            label += " (pre-release)"
        return label

    def _helixsr_latest_release(self, use_cache: bool = True) -> dict:
        """Newest published HelixSR release (pre-releases included, drafts not) that carries HelixSR's zip."""
        now = time.time()
        cached = self._helixsr_latest_cache
        if use_cache and cached and now - cached[0] < HELIXSR_LATEST_CACHE_SECONDS:
            return cached[1]
        releases = self._request_json(HELIXSR_RELEASES_API)
        if not isinstance(releases, list):
            raise RuntimeError("Unexpected GitHub releases response")
        candidates = []
        for release in releases:
            if release.get("draft"):
                continue
            tag = str(release.get("tag_name") or "")
            asset = self._helixsr_release_zip(release.get("assets") or [])
            if not asset or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", tag):
                continue
            digest = str(asset.get("digest") or "")
            candidates.append({
                "tag": tag,
                "version": tag.lstrip("vV"),
                "label": self._helixsr_release_label(release),
                "prerelease": bool(release.get("prerelease")),
                "uploaded_at": str(asset.get("updated_at") or ""),
                "name": asset["name"],
                "url": asset["browser_download_url"],
                "size": asset.get("size"),
                "sha256": digest[7:].lower() if re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest) else None,
                "published_at": release.get("published_at") or "",
                "page": release.get("html_url"),
            })
        if not candidates:
            raise RuntimeError("No HelixSR release with a HelixSR zip found on GitHub.")
        candidates.sort(key=lambda r: r["published_at"], reverse=True)
        self._helixsr_latest_cache = (now, candidates[0])
        return candidates[0]

    def _helixsr_extract_release(self, zip_path: Path, target: Path) -> None:
        """Extracts the zip into target, dropping the single top-level folder the releases use."""
        target.mkdir(parents=True, exist_ok=True)
        root = target.resolve()
        with zipfile.ZipFile(zip_path) as archive:
            members = archive.infolist()
            tops = {m.filename.split("/", 1)[0] for m in members}
            strip = len(tops) == 1 and all("/" in m.filename for m in members)
            for member in members:
                name = member.filename.split("/", 1)[1] if strip else member.filename
                if not name or name.endswith("/") or name.startswith(HELIXSR_SKIP_DIRS):
                    continue
                dest = (target / name).resolve()
                if root not in dest.parents:
                    raise RuntimeError(f"Unsafe path in the HelixSR zip: {member.filename}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
                mode = (member.external_attr >> 16) & 0o777
                if mode:
                    os.chmod(dest, mode)
                elif dest.suffix == ".sh":
                    os.chmod(dest, 0o755)

    def _helixsr_download_to_staging(self, release: dict) -> Path:
        root = self._helixsr_root()
        root.mkdir(parents=True, exist_ok=True)
        staging = self._helixsr_staging_dir()
        shutil.rmtree(staging, ignore_errors=True)
        zip_path = root / release["name"]
        zip_path.unlink(missing_ok=True)
        progress = self._helixsr_download if isinstance(self._helixsr_download, dict) else {}
        progress["path"] = str(zip_path)   # the progress bar reads its size
        try:
            decky.logger.info(f"[HelixSR] downloading {release['tag']} from {release['url']}")
            self._download_file(release["url"], zip_path)
            progress["phase"] = "verifying"
            size = zip_path.stat().st_size
            if release.get("size") and size != int(release["size"]):
                raise RuntimeError(f"HelixSR download incomplete ({size} of {release['size']} bytes). Try again.")
            digest = self._file_sha256(zip_path)
            if release.get("sha256") and digest.lower() != release["sha256"]:
                raise RuntimeError("The HelixSR download doesn't match GitHub's SHA256 checksum, so it wasn't used. Try again.")
            progress["phase"] = "extracting"
            self._helixsr_extract_release(zip_path, staging)
        finally:
            zip_path.unlink(missing_ok=True)
        if not (staging / "helixsr-setup.sh").exists():
            raise RuntimeError(f"helixsr-setup.sh not found in {release['name']}.")
        dll = self._helixsr_release_dll(staging)
        if not dll:
            raise RuntimeError(f"No HelixSR DLL found in {release['name']}.")
        if dll.name.lower() == HELIXSR_DLL_NGX:
            raise RuntimeError(f"HelixSR {release['tag']} replaces DLSS (nvngx.dll), which this plugin doesn't support.")
        dlss_source = self._helixsr_dlss_source(staging / "helixsr-setup.sh")
        if dlss_source:
            self._helixsr_fetch_dlss(*dlss_source, progress)
        self._write_json_file(staging / HELIXSR_META_FILENAME, {
            "tag": release["tag"],
            "label": release.get("label"),
            "asset_name": release["name"],
            "sha256": digest,
            "verified": bool(release.get("sha256")),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        })
        return staging

    def _helixsr_dlss_path(self) -> Path:
        return self._helixsr_root() / HELIXSR_DLSS_FILENAME

    def _helixsr_dlss_source(self, script: Path) -> tuple[str, str] | None:
        """(url, sha256) of NVIDIA's DLSS DLL for setups that get it through --dlss (from 1.9, see
        _helixsr_setup_command), as the release's own helixsr_setup.py names and checks it."""
        text = script.read_text(errors="replace")
        if "HelixSR Freeware License" not in text:
            return None
        try:
            setup_py = (script.parent / "setup" / "helixsr_setup.py").read_text(errors="replace")
        except OSError:
            setup_py = ""
        url, sha256 = HELIXSR_DLSS_URL.search(setup_py), HELIXSR_DLSS_SHA256.search(setup_py)
        if "--dlss" not in text or not url or not sha256:
            raise RuntimeError(
                "This HelixSR release's setup changed in a way this plugin hasn't been checked against. "
                f"Run it from Desktop Mode (Konsole: {script}) or update the plugin."
            )
        return url.group(1), sha256.group(1).lower()

    def _helixsr_fetch_dlss(self, url: str, sha256: str, progress: dict) -> Path:
        path = self._helixsr_dlss_path()
        path.unlink(missing_ok=True)
        progress.update({"phase": "downloading", "path": str(path), "total": None})
        decky.logger.info(f"[HelixSR] downloading NVIDIA's DLSS DLL from {url}")
        self._download_file(url, path)
        progress["phase"] = "verifying"
        if self._file_sha256(path).lower() != sha256:
            path.unlink(missing_ok=True)
            raise RuntimeError("NVIDIA's DLSS DLL doesn't match the checksum HelixSR's setup expects, so it wasn't used. Try again.")
        return path

    # ── setup (build) ────────────────────────────────────────────────────────
    def _helixsr_clean_env(self) -> dict:
        """Decky's bundled Python sets LD_LIBRARY_PATH/PYTHON* to its own files, which breaks curl, Proton's
        wine and the setup's Python."""
        env = dict(os.environ)
        orig = env.pop("LD_LIBRARY_PATH_ORIG", None)
        for key in list(env):
            if key in ("PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH") or key.startswith(("_MEI", "_PYI")) or "_MEI" in env[key]:
                env.pop(key)
        if orig:
            env["LD_LIBRARY_PATH"] = orig
        home = str(Path(decky.HOME))
        env["HOME"] = home
        env["XDG_DATA_HOME"] = str(Path(home) / ".local/share")
        env["PATH"] = env.get("PATH", "") + ":/usr/local/bin:/usr/bin:/bin"
        return env

    def _helixsr_build_only_script(self, script: Path) -> Path:
        """1.7-1.8.1 (Apache 2.0): a copy of the setup that ends before HelixSR's own game installer."""
        text = script.read_text(errors="replace")
        if "helixsr_install.py" not in text:
            return script   # up to 1.6: the setup only builds
        if text.count(HELIXSR_GAMES_MARKER) != 1 or "helixsr_install.py" in text.split(HELIXSR_GAMES_MARKER)[0]:
            raise RuntimeError(
                "This HelixSR release's setup changed in a way this plugin hasn't been checked against. "
                f"Run it from Desktop Mode (Konsole: {script}) or update the plugin."
            )
        out = script.parent / HELIXSR_BUILD_SCRIPT
        out.write_text(text.split(HELIXSR_GAMES_MARKER)[0] + "\nexit 0\n")
        os.chmod(out, 0o755)
        return out

    def _helixsr_setup_command(self, script: Path, directory: Path) -> list[str]:
        """From 1.9 (HelixSR Freeware License) the setup runs unmodified, without --yes: 2.0 hands --yes on to
        its game installer, which then puts HelixSR into every game it finds. NVIDIA's DLSS DLL (downloaded
        and checked by the plugin) goes in with --dlss instead, so the build asks nothing, and the game
        installer gets no answer (stdin is /dev/null) and ends without changing any game. Frame generation
        for HelixSR Scaler is skipped (--no-fg), since only the upscaler is used here."""
        text = script.read_text(errors="replace")
        if "--rebuild" not in text:
            return ["bash", str(script), str(directory), "--yes"]
        if "HelixSR Freeware License" in text:
            dlss = self._helixsr_dlss_path()
            if not dlss.exists():
                raise RuntimeError("NVIDIA's DLSS DLL is missing. Press \"Install HelixSR\" again.")
            no_fg = ["--no-fg"] if "--no-fg" in text else []
            return ["bash", str(script), "--dlss", str(dlss), *no_fg]
        return ["bash", str(self._helixsr_build_only_script(script)), "--yes"]

    def _helixsr_pid_alive(self, pid) -> bool:
        try:
            cmdline = Path(f"/proc/{int(pid)}/cmdline").read_bytes()
        except (OSError, ValueError, TypeError):
            return False
        return b"helixsr" in cmdline

    def _helixsr_tail(self, path: Path, count: int = 400) -> list[str]:
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - 256 * 1024))
                text = f.read().decode(errors="replace")
        except OSError:
            return []
        # progress bars redraw with \r: keep the last state of each line
        return [line.split("\r")[-1] for line in text.splitlines()][-count:]

    def _helixsr_phase(self, lines: list[str]) -> tuple[int, str]:
        pct, label = 0, "Starting"
        for line in lines:
            for pattern, value, text in HELIXSR_PHASES:
                if re.search(pattern, line) and value >= pct:
                    pct, label = value, text
            match = HELIXSR_BUILD_PROGRESS.search(line)
            if match and pct < 100:
                bar = int(match.group(1))
                pct, label = 10 + int(bar * 0.89), f"Building the network: {match.group(2)} ({bar}%)"
        return pct, label

    def _helixsr_setup_status(self) -> dict:
        state_data = self._read_json_file(self._helixsr_setup_state_file())
        rc_file = self._helixsr_setup_rc()
        rc = None
        if rc_file.exists():
            try:
                rc = int(rc_file.read_text().strip())
            except ValueError:
                rc = -1
        running = bool(state_data.get("pid")) and rc is None and self._helixsr_pid_alive(state_data.get("pid"))
        lines = self._helixsr_tail(self._helixsr_setup_log(), 2000)
        pct, label = self._helixsr_phase(lines)
        if running:
            state = "running"
        elif state_data.get("finalized"):
            state = "succeeded"
        elif state_data.get("cancelled"):
            state = "cancelled"
        elif rc is not None:
            staged = self._helixsr_release_dll(self._helixsr_staging_dir())
            state = "succeeded" if staged and self._helixsr_has_network(staged) else "failed"
        elif state_data:
            state = "stopped"
        else:
            state = "idle"
        started = state_data.get("started")
        return {
            "state": state,
            "tag": state_data.get("tag"),
            "rc": rc,
            "progress": 100 if state == "succeeded" else pct,
            "phase": label,
            "elapsed": round(time.time() - started) if running and started else None,
            "errors": [line.strip() for line in lines if HELIXSR_ERROR_PATTERN.search(line)][-4:],
            "tail": [line for line in lines if line.strip() and not HELIXSR_PROMPT_LINE.search(line)][-4:],
            "log_path": str(self._helixsr_setup_log()),
        }

    def _helixsr_finalize(self) -> None:
        """Once the staged release is built, it replaces the installed one (games keep their own copy)."""
        state_file = self._helixsr_setup_state_file()
        state_data = self._read_json_file(state_file)
        if not state_data or state_data.get("finalized") or not self._helixsr_setup_rc().exists():
            return
        staging = self._helixsr_staging_dir()
        dll = self._helixsr_release_dll(staging)
        if not dll or not self._helixsr_has_network(dll):
            return
        current = self._helixsr_current_dir()
        previous = self._helixsr_root() / "previous"
        shutil.rmtree(previous, ignore_errors=True)
        if current.exists():
            current.rename(previous)
        staging.rename(current)
        shutil.rmtree(previous, ignore_errors=True)
        state_data["finalized"] = True
        self._write_json_file(state_file, state_data)
        decky.logger.info(f"[HelixSR] {state_data.get('tag')} built and installed to {current}")

    def _helixsr_start_setup(self, tag: str) -> subprocess.Popen:
        staging = self._helixsr_staging_dir()
        script = staging / "helixsr-setup.sh"
        command = self._helixsr_setup_command(script, staging)
        log_path = self._helixsr_setup_log()
        rc_file = self._helixsr_setup_rc()
        rc_file.unlink(missing_ok=True)
        tmp_dir = self._helixsr_root() / "tmp"
        shutil.rmtree(tmp_dir, ignore_errors=True)
        tmp_dir.mkdir(parents=True)
        env = self._helixsr_clean_env()
        env["TMPDIR"] = str(tmp_dir)
        with open(log_path, "wb") as log:
            log.write(f"[jedi] {time.ctime()}: running {' '.join(command[1:])}\n".encode())
            log.flush()
            # The wrapper records the exit code, so the result is known even if Decky restarts the plugin.
            # --yes / --dlss: the user agreed to NVIDIA's DLSS download in the confirmation dialog.
            proc = subprocess.Popen(
                ["bash", "-c", '"$@"; echo $? > "$0"', str(rc_file), *command],
                cwd=str(staging), env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        self._write_json_file(self._helixsr_setup_state_file(), {"tag": tag, "pid": proc.pid, "started": time.time()})
        return proc

    async def _helixsr_wait_setup(self, proc) -> None:
        await asyncio.to_thread(proc.wait)
        self._helixsr_dlss_path().unlink(missing_ok=True)
        try:
            await asyncio.to_thread(self._helixsr_finalize)
        except Exception as exc:
            decky.logger.error(f"[HelixSR] finalize failed: {exc}")

    # ── OptiScaler route (per game) ──────────────────────────────────────────
    def _helixsr_ini_get(self, text: str, section: str, key: str) -> str | None:
        current = None
        for line in text.splitlines():
            match = re.match(r"^\s*\[(.+?)\]\s*$", line)
            if match:
                current = match.group(1).strip().lower()
                continue
            if current == section.lower():
                match = re.match(r"^\s*([^;#=\s][^=]*?)\s*=\s*(.*?)\s*$", line)
                if match and match.group(1).lower() == key.lower():
                    return match.group(2)
        return None

    def _helixsr_ini_set(self, text: str, section: str, key: str, value: str | None) -> str:
        """Sets section/key to value (None removes the key), keeping the file's own formatting."""
        newline = "\r\n" if "\r\n" in text else "\n"
        current, sec_start, sec_end, found = None, None, None, False
        out = []
        for line in text.splitlines():
            match = re.match(r"^\s*\[(.+?)\]\s*$", line)
            if match:
                if current == section.lower():
                    sec_end = len(out)
                current = match.group(1).strip().lower()
                if current == section.lower():
                    sec_start = len(out) + 1
                out.append(line)
                continue
            if current == section.lower():
                match = re.match(r"^(\s*)([^;#=\s][^=]*?)(\s*=\s*)(.*?)(\s*)$", line)
                if match and match.group(2).lower() == key.lower():
                    found = True
                    if value is not None:
                        out.append(f"{match.group(1)}{match.group(2)}{match.group(3)}{value}")
                    continue
            out.append(line)
        if current == section.lower():
            sec_end = len(out)
        if not found and value is not None:
            if sec_start is None:
                out += ["", f"[{section}]", f"{key}={value}"]
            else:
                pos = sec_end
                while pos > sec_start and not out[pos - 1].strip():
                    pos -= 1
                out.insert(pos, f"{key}={value}")
        return newline.join(out) + newline

    def _helixsr_opti_upscaler_value(self, text: str) -> str:
        """OptiScaler 0.9+ may call FSR 3.1/4 'ffx' for Dx12Upscaler, older builds 'fsr31' (read from the ini's comment)."""
        match = re.search(r"\[Upscalers\](.*?)Dx12Upscaler\s*=", text, re.S | re.I)
        block = match.group(1) if match else ""
        return "fsr31" if ("fsr31" in block and not re.search(r"\bffx\b", block)) else "ffx"

    def _helixsr_win_path(self, path: Path) -> str:
        """Linux path -> the Windows path a Proton game sees (Z: is the Linux root)."""
        return "Z:" + os.path.realpath(path).replace("/", "\\")

    def _helixsr_apply_to_game(self, directory: Path, injector: Path) -> str:
        """HelixSR as OptiScaler's upscaler. 3.0+ (HLX DLSS): see _helixsr_apply_hlx. Up to 2.0, as OptiScaler's FFX
        upscaler: HelixSR/ next to OptiScaler.ini holds HelixSR as helixsr.dll and helixsr_upscaler.dll, AMD's
        FidelityFX DLL as amd_fidelityfx_dx12.original.dll (frame generation keeps working) and the INT8 FSR4
        upscaler as amd_fidelityfx_upscaler_dx12.amd.dll (FSR4 stays selectable)."""
        dll = self._helixsr_built_dll()
        ini = directory / "OptiScaler.ini"
        if not ini.exists():
            raise RuntimeError(f"OptiScaler.ini not found in {directory}; can't point OptiScaler at HelixSR.")
        if self._helixsr_dll_kind(dll) == "hlx":
            self._helixsr_remove_ffx_route(directory)
            return self._helixsr_apply_hlx(directory, dll, ini, injector)
        self._helixsr_remove_hlx_route(directory)
        sub = directory / HELIXSR_GAME_SUBDIR
        marker = sub / HELIXSR_GAME_MARKER
        replaced = None
        if sub.exists() and not marker.exists():
            # Not this plugin's folder (or one an earlier patch left half made): it goes, this plugin's takes its place.
            replaced = self._helixsr_foreign_folder(directory) or "files left by an earlier patch"
            decky.logger.info(f"[HelixSR] replacing {sub} ({replaced})")
            try:
                if sub.is_dir() and not sub.is_symlink():
                    shutil.rmtree(sub)
                else:
                    sub.unlink()
            except OSError as exc:
                raise RuntimeError(f"Could not remove the {HELIXSR_GAME_SUBDIR} folder already in {directory}: {exc}")
        previous = self._read_json_file(marker).get("previous") if marker.exists() else None
        created = not sub.exists()
        sub.mkdir(exist_ok=True)
        try:
            message = self._helixsr_fill_game_folder(directory, dll, ini, sub, marker, previous)
            if replaced:
                message += f" The {HELIXSR_GAME_SUBDIR} folder already there ({replaced}) was replaced."
            return message
        except Exception:
            if created:   # no half-made folder that would block the next patch
                shutil.rmtree(sub, ignore_errors=True)
            raise

    def _helixsr_foreign_folder(self, directory: Path) -> str | None:
        """Why the game's HelixSR folder isn't this plugin's (None when it only holds files this plugin puts there)."""
        sub = Path(directory) / HELIXSR_GAME_SUBDIR
        if (sub / "helixsr-install.json").exists():
            return "HelixSR's own installer"
        if (Path(directory) / "HelixSR-Scaler.files").exists():
            return "HelixSR Scaler"
        try:
            others = sorted(p.name for p in sub.iterdir() if p.name not in HELIXSR_GAME_OWN_FILES)
        except OSError as exc:
            return f"it can't be read: {exc}"
        return f"it holds {', '.join(others[:4])}{', ...' if len(others) > 4 else ''}" if others else None

    def _helixsr_fill_game_folder(self, directory: Path, dll: Path, ini: Path, sub: Path, marker: Path,
                                  previous: dict | None) -> str:
        for name in HELIXSR_GAME_OLD_NAMES:
            (sub / name).unlink(missing_ok=True)
        self._helixsr_copy_dll(dll, sub / HELIXSR_GAME_DLL)
        self._helixsr_copy_dll(dll, sub / HELIXSR_GAME_SR_DLL)
        # HelixSR forwards non-upscaling effects (frame generation) to these files next to itself.
        ffx_loader = directory / HELIXSR_DLL_FFX
        if ffx_loader.exists() and not self._helixsr_is_helixsr(ffx_loader):
            shutil.copyfile(ffx_loader, sub / "amd_fidelityfx_dx12.original.dll")
        fg_dll = directory / HELIXSR_FG_DLL
        if fg_dll.exists() and not self._helixsr_is_helixsr(fg_dll):
            shutil.copyfile(fg_dll, sub / HELIXSR_FG_DLL)
        fsr4_dll = directory / FSR4_UPSCALER_FILENAME
        keep_fsr4 = fsr4_dll.exists() and not self._helixsr_is_helixsr(fsr4_dll)
        if keep_fsr4:
            shutil.copyfile(fsr4_dll, sub / HELIXSR_FSR4_COPY_NAME)

        helix_ini = sub / "helixsr.ini"
        if not helix_ini.exists():
            template = dll.parent / "fsr3-drop-in" / "helixsr.ini"
            if template.exists():
                shutil.copyfile(template, helix_ini)
        if keep_fsr4:
            helix_text = helix_ini.read_text(encoding="utf-8", errors="replace") if helix_ini.exists() else ""
            helix_ini.write_text(
                self._helixsr_ini_set(helix_text, "Forwarding", "UpscalerDll", HELIXSR_FSR4_COPY_NAME),
                encoding="utf-8",
            )

        text = ini.read_text(encoding="utf-8", errors="replace")
        wanted = {
            ("Upscalers", "Dx12Upscaler"): self._helixsr_opti_upscaler_value(text),
            ("Libraries", "FfxDx12Path"): self._helixsr_win_path(sub / HELIXSR_GAME_DLL),
            ("Libraries", "FfxDx12SRPath"): self._helixsr_win_path(sub / HELIXSR_GAME_SR_DLL),
        }
        if self._helixsr_ini_get(text, "FSR", "UpscalerIndex") is not None:
            wanted[("FSR", "UpscalerIndex")] = "0"   # HelixSR is the first upscaler its DLL lists
        if previous is None:
            previous = {f"{s}/{k}": self._helixsr_ini_get(text, s, k) for (s, k) in wanted}
            # a folder taken over can have OptiScaler.ini pointing into it already: that's not a value to put back
            own = self._helixsr_win_path(sub).lower()
            previous = {k: (None if v and v.strip().lower().startswith(own) else v) for k, v in previous.items()}
        for (section, key), value in wanted.items():
            text = self._helixsr_ini_set(text, section, key, value)
        ini.write_text(text, encoding="utf-8")

        installed = self._helixsr_installed() or {}
        self._write_json_file(marker, {
            "previous": previous,
            "set": {f"{s}/{k}": v for (s, k), v in wanted.items()},
            "helixsr": self._helixsr_dll_version(dll),
            "tag": installed.get("tag"),
            "installed_at": datetime.now(timezone.utc).isoformat(),
        })
        version = self._helixsr_dll_version(dll) or installed.get("tag") or ""
        return (
            f"HelixSR {version} set as OptiScaler's upscaler"
            + (" (FSR4 stays selectable in OptiScaler's menu)." if keep_fsr4 else ".")
        )

    def _helixsr_hlx_folder(self, directory: Path) -> Path:
        return Path(directory) / "custom" / HELIXSR_HLX_NAME

    def _copy_hlx_injector(self, injector: Path) -> None:
        """Puts the OptiScaler build that loads custom upscalers (OPTISCALER_HLX_ASSET) in place of the game's injector."""
        bin_dir = self._ensure_runtime_binaries([OPTISCALER_HLX_ASSET["name"]])
        source = bin_dir / OPTISCALER_HLX_ASSET["name"]
        if not source.exists():
            raise RuntimeError(f"{OPTISCALER_HLX_ASSET['name']} couldn't be downloaded. Check the connection and patch again.")
        self._verify_bundled_asset(source, OPTISCALER_HLX_ASSET["sha256"], "OptiScaler for custom upscalers")
        if injector.is_symlink():   # copying onto ReShade's link would overwrite ReShade's own DLL
            injector.unlink()
        shutil.copyfile(source, injector)

    def _custom_402c_folder(self, directory: Path) -> Path:
        return Path(directory) / "custom" / CUSTOM_402C_NAME

    def _remove_custom_upscalers(self, directory: Path) -> bool:
        removed = False
        for name in (CUSTOM_402C_NAME, CUSTOM_411_NAME):
            folder = Path(directory) / "custom" / name
            if (folder / CUSTOM_UPSCALER_MARKER).exists():
                shutil.rmtree(folder, ignore_errors=True)
                removed = True
        if removed:
            try:
                (Path(directory) / "custom").rmdir()   # when nothing else is in it
            except OSError:
                pass
        return removed

    def _install_custom_upscaler(self, directory: Path, name: str, source: Path, dll_name: str) -> None:
        if not source.exists():
            raise FileNotFoundError(f"Prepared FSR4 variant missing: {source}")
        folder = Path(directory) / "custom" / name
        created = not folder.exists()
        try:
            (folder / "ffx").mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, folder / "ffx" / dll_name)
            self._write_json_file(folder / CUSTOM_UPSCALER_MARKER, {
                "sha256": self._file_sha256(source),
                "optiscaler": OPTISCALER_HLX_ASSET["version"],
                "installed_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            if created:
                shutil.rmtree(folder, ignore_errors=True)
            raise

    def _apply_combined_upscalers(self, directory: Path, fgmod_path: Path, injector: Path) -> str:
        """COMBINED_VARIANT: OptiScaler 10 (de2626f + driver DLLs as custom upscalers) lists custom/<name>/ffx and
        custom/<name>/dlss next to its own FSR 4 (the Lite runtime the patch put in): 4.0.2c's upscaler as "FSR 4.0.2c",
        Valve's 4.1.1 driver DLL as "FSR 4.1.1" and, when HelixSR 3.x is installed, HLX DLSS. FSR 4 stays the selected
        upscaler."""
        self._copy_hlx_injector(injector)
        self._install_custom_upscaler(
            directory, CUSTOM_402C_NAME, self._fsr4_variant_path(fgmod_path, "rdna23-int8"), FSR4_UPSCALER_FILENAME
        )
        self._install_custom_upscaler(
            directory,
            CUSTOM_411_NAME,
            self._fsr4_variant_extra_file_path(fgmod_path, "rdna2-valve-411-pre10", FSR4_DRIVER_OVERRIDE_FILENAME),
            CUSTOM_411_DLL,
        )
        names = ["FSR 4 (4.1.2 Lite)", CUSTOM_402C_NAME, CUSTOM_411_NAME]
        installed = self._helixsr_installed()
        if installed and installed["built"] and installed["kind"] == "hlx":
            self._helixsr_remove_ffx_route(directory)
            self._helixsr_apply_hlx(directory, installed["dll"], directory / "OptiScaler.ini", injector, select=False)
            names.append(HELIXSR_HLX_NAME)
        else:
            self._helixsr_remove_from_game(directory, restore_ini=True)
        return f"In OptiScaler (Insert): {', '.join(names)}."

    def _helixsr_apply_hlx(self, directory: Path, dll: Path, ini: Path, injector: Path, select: bool = True) -> str:
        """3.0+: HLX DLSS as OptiScaler's custom DLSS upscaler. custom/HLX DLSS/dlss/ holds helixsr.dll and
        helixsr.ini, and the game gets the OptiScaler build that loads it (OPTISCALER_HLX_ASSET); patching with
        another runtime copies that runtime's injector back. select=False only lists it in OptiScaler's menu."""
        folder = self._helixsr_hlx_folder(directory)
        marker = folder / HELIXSR_GAME_MARKER
        previous = self._read_json_file(marker).get("previous") if marker.exists() else None
        created = not folder.exists()
        try:
            dlss_dir = folder / "dlss"
            dlss_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(dll, dlss_dir / HELIXSR_DLL_HLX)
            template = dll.parent / "helixsr.ini"
            if not (dlss_dir / "helixsr.ini").exists() and template.exists():
                shutil.copyfile(template, dlss_dir / "helixsr.ini")
            self._copy_hlx_injector(injector)

            text = ini.read_text(encoding="utf-8", errors="replace")
            wanted = dict(HELIXSR_HLX_FG_KEYS)
            if select:
                wanted[("Upscalers", "Dx12Upscaler")] = HELIXSR_HLX_NAME
            if previous is None:
                previous = {f"{s}/{k}": self._helixsr_ini_get(text, s, k) for (s, k) in wanted}
            for (section, key), value in wanted.items():
                text = self._helixsr_ini_set(text, section, key, value)
            ini.write_text(text, encoding="utf-8")

            installed = self._helixsr_installed() or {}
            self._write_json_file(marker, {
                "previous": previous,
                "set": {f"{s}/{k}": v for (s, k), v in wanted.items()},
                "helixsr": self._helixsr_dll_version(dll),
                "tag": installed.get("tag"),
                "optiscaler": OPTISCALER_HLX_ASSET["version"],
                "selectable": not select,
                "installed_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            if created:   # no half-made folder that would block the next patch
                shutil.rmtree(folder, ignore_errors=True)
            raise
        version = self._helixsr_dll_version(dll) or ""
        if not select:
            return f"HelixSR {version} added as HLX DLSS."
        return f"HelixSR {version} (HLX DLSS) set as OptiScaler's upscaler. In the game, select DLSS."

    def _helixsr_game_check(self, directory: Path) -> dict | None:
        """Whether a game patched with HelixSR is set up and what helixsr.log (written next to HelixSR once
        OptiScaler loads it) says. None when the game doesn't use HelixSR."""
        sub = Path(directory) / HELIXSR_GAME_SUBDIR
        hlx = self._helixsr_hlx_folder(directory)
        ini_text = ""
        try:
            ini_text = (Path(directory) / "OptiScaler.ini").read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
        selectable = False
        if (hlx / HELIXSR_GAME_MARKER).exists():
            dll = hlx / "dlss" / HELIXSR_DLL_HLX
            upscaler = (self._helixsr_ini_get(ini_text, "Upscalers", "Dx12Upscaler") or "").strip()
            # the combined runtime only lists HLX DLSS in OptiScaler's menu: any Dx12Upscaler is fine
            selectable = bool(self._read_json_file(hlx / HELIXSR_GAME_MARKER).get("selectable"))
            configured = dll.exists() and (selectable or upscaler.lower() == HELIXSR_HLX_NAME.lower())
        elif (sub / HELIXSR_GAME_MARKER).exists():
            dll = sub / HELIXSR_GAME_SR_DLL
            sr_value = (self._helixsr_ini_get(ini_text, "Libraries", "FfxDx12SRPath") or "").strip()
            configured = dll.exists() and sr_value.lower() == self._helixsr_win_path(dll).lower()
        else:
            return None
        log = dll.parent / "helixsr.log"
        lines = self._helixsr_tail(log, 400) if log.exists() else []
        text = "\n".join(lines)
        if not lines:
            log_status = "not_loaded"
        elif "HelixSR ERROR" in text or "NOT RUNNING" in text:
            log_status = "error"
        elif "network running" in text:
            log_status = "running"
        else:
            log_status = "loaded"
        errors = [line.strip() for line in lines if "HelixSR ERROR" in line or "NOT RUNNING" in line][-2:]
        return {
            "version": self._helixsr_dll_version(dll) if dll.exists() else None,
            "configured": configured,
            "selectable": selectable,
            "log_status": log_status,
            "errors": errors,
        }

    def _helixsr_remove_from_game(self, directory: Path, restore_ini: bool = True) -> bool:
        """Removes what this plugin put in for HelixSR (either route) and, if asked, puts OptiScaler.ini's
        previous values back (only those that still hold HelixSR's value). False when there was nothing to remove."""
        removed_ffx = self._helixsr_remove_ffx_route(directory, restore_ini)
        removed_hlx = self._helixsr_remove_hlx_route(directory, restore_ini)
        return removed_ffx or removed_hlx

    def _helixsr_restore_ini(self, directory: Path, data: dict) -> None:
        ini = Path(directory) / "OptiScaler.ini"
        if not ini.exists():
            return
        text = ini.read_text(encoding="utf-8", errors="replace")
        for section_key, old in (data.get("previous") or {}).items():
            section, key = section_key.split("/", 1)
            if (self._helixsr_ini_get(text, section, key) or "") == ((data.get("set") or {}).get(section_key) or ""):
                if old is None or (key.lower().endswith("path") and str(old).strip().lower() == "plugins"):
                    old = "auto"   # never put back the old template bug
                text = self._helixsr_ini_set(text, section, key, old)
        ini.write_text(text, encoding="utf-8")

    def _helixsr_remove_hlx_route(self, directory: Path, restore_ini: bool = True) -> bool:
        folder = self._helixsr_hlx_folder(directory)
        marker = folder / HELIXSR_GAME_MARKER
        if not marker.exists():
            return False
        if restore_ini:
            self._helixsr_restore_ini(directory, self._read_json_file(marker))
        shutil.rmtree(folder, ignore_errors=True)
        try:
            folder.parent.rmdir()   # custom/, when nothing else is in it
        except OSError:
            pass
        return True

    def _helixsr_remove_ffx_route(self, directory: Path, restore_ini: bool = True) -> bool:
        sub = directory / HELIXSR_GAME_SUBDIR
        marker = sub / HELIXSR_GAME_MARKER
        if not marker.exists():
            # a folder an earlier patch left half made (only this plugin's files): its paths in OptiScaler.ini go too
            if not sub.is_dir() or self._helixsr_foreign_folder(directory):
                return False
            ini = directory / "OptiScaler.ini"
            if restore_ini and ini.exists():
                text = ini.read_text(encoding="utf-8", errors="replace")
                own = self._helixsr_win_path(sub).lower()
                for key in ("FfxDx12Path", "FfxDx12SRPath"):
                    if (self._helixsr_ini_get(text, "Libraries", key) or "").strip().lower().startswith(own):
                        text = self._helixsr_ini_set(text, "Libraries", key, "auto")
                ini.write_text(text, encoding="utf-8")
            shutil.rmtree(sub, ignore_errors=True)
            return True
        if restore_ini:
            self._helixsr_restore_ini(directory, self._read_json_file(marker))
        shutil.rmtree(sub, ignore_errors=True)
        return True

    # ── frontend API ─────────────────────────────────────────────────────────
    async def get_helixsr_status(self, check_latest: bool = True) -> dict:
        try:
            await asyncio.to_thread(self._helixsr_finalize)
        except Exception as exc:
            decky.logger.warning(f"[HelixSR] finalize failed: {exc}")
        setup = await asyncio.to_thread(self._helixsr_setup_status)
        installed = self._helixsr_installed()
        latest, latest_error = None, None
        if check_latest:
            try:
                latest = await asyncio.to_thread(self._helixsr_latest_release)
            except Exception as exc:
                latest_error = f"Could not reach GitHub: {exc}"
        is_latest = bool(
            installed and installed["built"] and latest and installed.get("tag") == latest["tag"]
            and (not latest.get("sha256") or not installed.get("sha256") or installed["sha256"] == latest["sha256"])
        )
        installed_label = None
        if installed:
            installed_label = installed["label"] or (f"HelixSR {installed['version']}" if installed["version"] else "HelixSR")
        latest_label = latest["label"] if latest else None
        # Same tag, other SHA256: the release's zip was uploaded again.
        if latest and not is_latest and installed and installed.get("tag") == latest["tag"]:
            latest_label += f" (re-uploaded {latest['uploaded_at'][:10]})" if latest.get("uploaded_at") else " (re-uploaded)"
        return {
            "status": "success",
            "installed": bool(installed and installed["built"]),
            "installed_version": installed["version"] if installed else None,
            "installed_label": installed_label,
            "latest_label": latest_label,
            "latest_prerelease": bool(latest and latest.get("prerelease")),
            "installed_tag": installed["tag"] if installed else None,
            "latest_version": latest["version"] if latest else None,
            "latest_tag": latest["tag"] if latest else None,
            "up_to_date": is_latest,
            "update_available": bool(latest) and not is_latest,
            "download": self._helixsr_download_status(),
            "setup": setup,
            "message": latest_error,
        }

    def _helixsr_download_status(self) -> dict:
        data = self._helixsr_download
        if not isinstance(data, dict):
            return {"active": False}
        done = 0
        try:
            if data.get("phase") == "downloading" and data.get("path"):
                done = os.path.getsize(data["path"])
        except OSError:
            pass
        return {
            "active": not data.get("error"),
            "tag": data.get("tag"),
            "version": data.get("version"),
            "label": data.get("label"),
            "phase": data.get("phase"),
            "bytes": done,
            "total": data.get("total"),
            "error": data.get("error"),
        }

    async def install_latest_helixsr(self) -> dict:
        """Installs the newest HelixSR release, unless it's the one installed already. Download, verification,
        extraction and the build run in the background (get_helixsr_status reports progress). The installed
        release stays in use until the newest one has been built."""
        if self._helixsr_download_status().get("active"):
            return {"status": "error", "message": "HelixSR is already being downloaded."}
        if (await asyncio.to_thread(self._helixsr_setup_status))["state"] == "running":
            return {"status": "error", "message": "HelixSR is already being built."}
        try:
            latest = await asyncio.to_thread(self._helixsr_latest_release, False)
        except Exception as exc:
            return {"status": "error", "message": f"Could not reach GitHub: {exc}"}
        installed = self._helixsr_installed()
        if (installed and installed["built"] and installed.get("tag") == latest["tag"]
                and (not latest.get("sha256") or installed.get("sha256") in (None, latest["sha256"]))):
            return {"status": "success", "started": False,
                    "message": f"{latest['label']} (the latest) is already installed."}
        self._helixsr_download = {"tag": latest["tag"], "version": latest["version"], "label": latest["label"], "path": None,
                                  "total": latest.get("size"), "phase": "downloading", "error": None}
        asyncio.get_event_loop().create_task(self._helixsr_install_task(latest))
        size_mb = f" ({int(latest['size']) / 1048576:.0f} MB)" if latest.get("size") else ""
        return {"status": "success", "started": True,
                "message": f"Downloading {latest['label']}{size_mb}, then building its network "
                           "(about 7-10 minutes on a Steam Deck). Keep the device awake."}

    async def _helixsr_install_task(self, release: dict) -> None:
        try:
            await asyncio.to_thread(self._helixsr_download_to_staging, release)
            self._helixsr_setup_state_file().unlink(missing_ok=True)
            proc = await asyncio.to_thread(self._helixsr_start_setup, release["tag"])
            self._helixsr_download = None
            await self._helixsr_wait_setup(proc)
        except Exception as exc:
            decky.logger.error(f"[HelixSR] install failed: {exc}")
            self._helixsr_dlss_path().unlink(missing_ok=True)
            if isinstance(self._helixsr_download, dict):
                self._helixsr_download["error"] = str(exc)
            else:
                self._helixsr_download = {"tag": release["tag"], "version": release["version"], "label": release.get("label"), "error": str(exc)}

    async def cancel_helixsr_setup(self) -> dict:
        state_file = self._helixsr_setup_state_file()
        state_data = self._read_json_file(state_file)
        pid = state_data.get("pid")
        if not pid or not self._helixsr_pid_alive(pid):
            return {"status": "error", "message": "No HelixSR build is running."}
        state_data["cancelled"] = True
        self._write_json_file(state_file, state_data)
        try:
            os.killpg(int(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError) as exc:
            return {"status": "error", "message": f"Could not stop the build: {exc}"}
        return {"status": "success", "message": "HelixSR build cancelled. The installed release (if any) is unchanged."}


# ===== LSFG-VK backend (merged from the Jedi LSFG-VK plugin, defaults/py_modules/lsfg_vk) =====
# Decky leaves the plugin folder itself root-owned, so Plugin Update can't create a top-level py_modules/
# there; defaults/ is in every install and writable.
sys.path.insert(0, str(Path(__file__).resolve().parent / "defaults" / "py_modules"))
from lsfg_vk.config_schema import TARGET_FPS_MAX as LSFG_TARGET_FPS_MAX, TARGET_FPS_MIN as LSFG_TARGET_FPS_MIN
from lsfg_vk.configuration import ConfigurationService as LsfgConfigurationService
from lsfg_vk.constants import (
    ACTIVE_RENDERER_STATE as MAKO_ACTIVE_RENDERER_STATE,
    MAKO_ARCHIVE_TEMPLATE,
    MAKO_RELEASE_TAG_PREFIX,
    MAKO_RELEASES_API,
)
from lsfg_vk.installation import InstallationService as LsfgInstallationService
from lsfg_vk.runtime_service import RuntimeService as LsfgRuntimeService
from lsfg_vk.steam_service import SteamService as LsfgSteamService
from lsfg_vk.wrapper_service import WrapperService as LsfgWrapperService


class _LsfgMixin:
    """Lossless Scaling frame generation through MAKO Renderer, one target FPS per game.

    The game's launch options get `~/.jedi-lsfg` before `%command%` (set by the frontend);
    that wrapper picks the game's MAKO profile from ~/.config/jedi-lsfg-vk/conf.toml.
    Same files as the standalone Jedi LSFG-VK plugin, so its games carry over.
    MAKO Renderer is always the newest render-v* release on GitHub.
    """

    _mako_release_cache = None

    def _lsfg_services(self):
        if getattr(self, "_lsfg_install", None) is None:
            runtime = LsfgRuntimeService()
            self._lsfg_steam = LsfgSteamService()
            self._lsfg_config = LsfgConfigurationService(runtime_service=runtime)
            self._lsfg_wrapper = LsfgWrapperService()
            self._lsfg_install = LsfgInstallationService(runtime_service=runtime, steam_service=self._lsfg_steam)
        return self._lsfg_install, self._lsfg_config, self._lsfg_wrapper, self._lsfg_steam

    def _lsfg_renderer_ready(self) -> bool:
        install, *_ = self._lsfg_services()
        return install._renderer_installed() and install.config_file_path.is_file()

    def _mako_installed_version(self) -> str:
        install, *_ = self._lsfg_services()
        try:
            data = json.loads((install.install_prefix / MAKO_ACTIVE_RENDERER_STATE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ""
        return str(data.get("version") or "") if isinstance(data, dict) else ""

    def _mako_latest_release(self) -> dict | None:
        """Newest published render-v* release that ships the linux .tar.xz with a SHA256 from GitHub."""
        cached = _LsfgMixin._mako_release_cache
        if cached and time.time() - cached[0] < PLUGIN_UPDATE_CACHE_SECONDS:
            return cached[1]
        best = None
        for release in self._request_json(MAKO_RELEASES_API):
            tag = str(release.get("tag_name") or "")
            if release.get("draft") or release.get("prerelease") or not tag.startswith(MAKO_RELEASE_TAG_PREFIX):
                continue
            version = tag[len(MAKO_RELEASE_TAG_PREFIX):]
            if not self._parse_version_tuple(version):
                continue
            if best and self._parse_version_tuple(version) <= self._parse_version_tuple(best["version"]):
                continue
            name = MAKO_ARCHIVE_TEMPLATE.format(version=version)
            asset = next((a for a in release.get("assets") or [] if a.get("name") == name), None)
            digest = str((asset or {}).get("digest") or "")
            if asset and digest.startswith("sha256:"):
                best = {"version": version, "name": name, "url": asset.get("browser_download_url"), "sha256": digest[7:]}
        _LsfgMixin._mako_release_cache = (time.time(), best)
        return best

    def _lsfg_ensure_latest_renderer(self) -> None:
        """Installs MAKO Renderer, or updates it, when the newest release isn't the installed one."""
        install, *_ = self._lsfg_services()
        ready = self._lsfg_renderer_ready()
        try:
            latest = self._mako_latest_release()
        except Exception as exc:
            # Offline: the installed renderer keeps working.
            if ready:
                decky.logger.warning(f"[LSFG] MAKO release check failed, keeping the installed renderer: {exc}")
                return
            raise RuntimeError(f"Could not reach GitHub for MAKO Renderer: {exc}")
        if not latest:
            if ready:
                return
            raise RuntimeError("No MAKO Renderer release found on GitHub.")
        installed = self._mako_installed_version()
        if ready and installed == latest["version"]:
            return
        with tempfile.TemporaryDirectory(prefix="jedi-mako-") as tmp:
            archive = Path(tmp) / latest["name"]
            self._download_file(latest["url"], archive)
            if self._file_sha256(archive) != latest["sha256"]:
                raise RuntimeError(f"{latest['name']} doesn't match GitHub's SHA256.")
            result = install.install(archive)
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "Could not install MAKO Renderer.")
        decky.logger.info(f"[LSFG] MAKO Renderer {installed or 'none'} -> {latest['version']}")

    def _lsfg_profile(self, appid: str):
        _, config, _, _ = self._lsfg_services()
        result = config.get_game_configs()
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "Could not read the LSFG profiles.")
        return next((game["config"] for game in result["games"] if game["appid"] == appid), None)

    @staticmethod
    def _lsfg_target(target_fps) -> int:
        return min(max(int(target_fps), LSFG_TARGET_FPS_MIN), LSFG_TARGET_FPS_MAX)

    def _lsfg_save_target(self, appid: str, target_fps) -> dict:
        _, config, _, _ = self._lsfg_services()
        profile = self._lsfg_profile(appid) or {}
        result = config.update_game_config(appid, "", {**profile, "target_fps": self._lsfg_target(target_fps)})
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "Could not save the target FPS.")
        return result["config"]

    def _lsfg_status(self, appid: str) -> dict:
        _, _, wrapper, steam = self._lsfg_services()
        state = wrapper.get(appid)
        profile = self._lsfg_profile(appid)
        return {
            "status": "success",
            "renderer_installed": self._lsfg_renderer_ready(),
            "lossless_found": steam.find_lossless_dll() is not None,
            "enabled": bool(state.get("success") and state.get("state")) and profile is not None,
            "target_fps": profile["target_fps"] if profile else LSFG_TARGET_FPS_MIN,
        }

    def _lsfg_enable(self, appid: str, target_fps, non_steam: bool) -> dict:
        _, _, wrapper, steam = self._lsfg_services()
        if steam.find_lossless_dll() is None:
            raise RuntimeError("Install Lossless Scaling on Steam first.")
        self._lsfg_ensure_latest_renderer()
        config = self._lsfg_save_target(appid, target_fps)
        current = wrapper.get(appid)
        result = wrapper.set(appid, current.get("state") or LsfgWrapperService.default_state(), False, bool(non_steam))
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "Could not update the launch wrapper.")
        return {"status": "success", "target_fps": config["target_fps"], "wrapper": result["wrapper_path"]}

    def _lsfg_disable(self, appid: str) -> dict:
        _, config, wrapper, _ = self._lsfg_services()
        for result in (wrapper.remove(appid), config.reset_game_config(appid)):
            if not result.get("success"):
                raise RuntimeError(result.get("error") or "Could not turn LSFG off.")
        return {"status": "success"}

    async def get_lsfg_status(self, appid) -> dict:
        try:
            return await asyncio.to_thread(self._lsfg_status, str(appid))
        except Exception as exc:
            decky.logger.error(f"[LSFG] status failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def enable_lsfg(self, appid, target_fps=LSFG_TARGET_FPS_MIN, non_steam: bool = False) -> dict:
        try:
            return await asyncio.to_thread(self._lsfg_enable, str(appid), target_fps, non_steam)
        except Exception as exc:
            decky.logger.error(f"[LSFG] enable failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def disable_lsfg(self, appid) -> dict:
        try:
            return await asyncio.to_thread(self._lsfg_disable, str(appid))
        except Exception as exc:
            decky.logger.error(f"[LSFG] disable failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def set_lsfg_target_fps(self, appid, target_fps) -> dict:
        try:
            config = await asyncio.to_thread(self._lsfg_save_target, str(appid), target_fps)
            return {"status": "success", "target_fps": config["target_fps"]}
        except Exception as exc:
            decky.logger.error(f"[LSFG] target FPS failed: {exc}")
            return {"status": "error", "message": str(exc)}

    def _lsfg_on_load(self) -> None:
        install, _, wrapper, _ = self._lsfg_services()
        repair = wrapper.repair()
        if not repair.get("success"):
            decky.logger.error(f"[LSFG] could not repair the launch wrapper: {repair.get('error')}")
        # With LSFG on for some game, its next launch gets the newest MAKO Renderer.
        if repair.get("success") and wrapper.list_apps().get("apps") and self._lsfg_renderer_ready():
            try:
                self._lsfg_ensure_latest_renderer()
            except Exception as exc:
                decky.logger.warning(f"[LSFG] MAKO Renderer update failed: {exc}")
        # Before any game starts, so the next launch reads current profiles.
        install.refresh_config()

    def _lsfg_on_uninstall(self) -> None:
        install, _, wrapper, _ = self._lsfg_services()
        # A passthrough wrapper keeps launch options that still name ~/.jedi-lsfg working.
        result = wrapper.neutralize()
        if not result.get("success"):
            decky.logger.warning(f"[LSFG] keeping MAKO Renderer, wrapper cleanup failed: {result.get('error')}")
            return
        install.cleanup_on_uninstall()


# ===== Unified plugin =====
class Plugin(_OptiScalerMixin, _ReShadeMixin, _HelixSRMixin, _LsfgMixin):
    # Coexistence policy ("fixed + auto-merge"): ReShade owns the graphics proxy slot
    # (default dxgi); OptiScaler/Framegen is forced onto a non-graphics proxy so the two
    # never fight over the same file.
    OPTISCALER_COEXIST_SLOT = "winmm.dll"
    GRAPHICS_PROXY_SLOTS = {
        "dxgi.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll", "d3d8.dll", "ddraw.dll", "opengl32.dll",
    }
    RESHADE_SLOT_CANDIDATES = (
        "dxgi.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll", "d3d8.dll", "ddraw.dll", "opengl32.dll", "dinput8.dll",
    )
    # What the ReShade side links into a game folder, and the files its install writes there
    RESHADE_LINK_NAMES = (
        "dxgi.dll", "d3d8.dll", "d3d9.dll", "d3d10.dll", "d3d11.dll", "d3d12.dll", "ddraw.dll", "dinput8.dll",
        "opengl32.dll", "d3dcompiler_47.dll",
    )
    RESHADE_GAME_FILES = (
        "ReShade.ini", "ReShadePreset.ini", "ReShade.log", "ReShade32.json", "ReShade64.json",
        "ReShade_README.txt", "AutoHDR.addon32", "AutoHDR.addon64",
    )

    async def _main(self):
        try:
            await asyncio.to_thread(self._remove_obsolete_binaries)
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] binary cleanup failed: {exc}")
        try:
            await asyncio.to_thread(self._lsfg_on_load)
        except Exception as exc:
            decky.logger.error(f"[LSFG] load failed: {exc}")
        decky.logger.info("Jedi ReFrameShade4All loaded")

    async def _unload(self):
        decky.logger.info("Jedi ReFrameShade4All unloaded")

    async def _uninstall(self):
        try:
            self._lsfg_on_uninstall()
        except Exception as exc:
            decky.logger.error(f"[LSFG] uninstall cleanup failed: {exc}")

    # ── coexistence helpers ──────────────────────────────────────────────────
    def _dir_has_reshade(self, directory) -> bool:
        if not directory:
            return False
        directory = Path(directory)
        return (directory / "ReShade.ini").exists() or (directory / "reshade-shaders").exists()

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
    @_worker
    async def patch_game(
        self,
        appid,
        dll_name="winmm.dll",
        current_launch_options="",
        fsr4_variant=DEFAULT_FSR4_VARIANT,
        selected_executable_path="",
    ):
        game = self._game_record(str(appid))
        if game:
            try:
                if selected_executable_path:
                    target_dir = Path(os.path.abspath(os.path.expanduser(selected_executable_path))).parent
                else:
                    target_dir, _ = self._guess_patch_target(game)
                dll_name = self._coexist_optiscaler_slot(target_dir, dll_name)
            except Exception as exc:
                decky.logger.warning(f"[JediReFrameShade] slot resolution failed: {exc}")
        result = await super().patch_game(
            str(appid),
            dll_name,
            current_launch_options,
            fsr4_variant,
            selected_executable_path,
        )
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

    # ── Proton-CachyOS FSR4_UPGRADE: only checks the game's compat tool, never downloads it ──
    def _vdf_block(self, text: str, key: str) -> str:
        """Body of the first `"key" { ... }` block in a VDF text (braces balanced)."""
        match = re.search(r'"' + re.escape(key) + r'"\s*\{', text, re.IGNORECASE)
        if not match:
            return ""
        depth, start = 1, match.end()
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i]
        return ""

    def _compat_tool_for_app(self, appid: str) -> str:
        """Internal name of the compat tool Steam uses for appid (per-game mapping, else the global default)."""
        for steam_root in self._steam_root_candidates():
            config = steam_root / "config" / "config.vdf"
            if not config.is_file():
                continue
            try:
                mapping = self._vdf_block(config.read_text(encoding="utf-8", errors="replace"), "CompatToolMapping")
            except OSError:
                continue
            if not mapping:
                continue
            for key in (str(appid), "0"):
                name = re.search(r'"' + re.escape(key) + r'"\s*\{[^{}]*?"name"\s*"([^"]*)"', mapping)
                if name and name.group(1):
                    return name.group(1)
        return ""

    def _compat_tool_vdf(self, tool_name: str) -> tuple[Path, str] | None:
        """(compatibilitytool.vdf, its text) of a custom compat tool, or None when it isn't installed there."""
        dirs = [root / "compatibilitytools.d" for root in self._steam_root_candidates()]
        dirs.append(Path("/usr/share/steam/compatibilitytools.d"))
        for base in dirs:
            if not base.is_dir():
                continue
            for vdf in base.glob("*/compatibilitytool.vdf"):
                try:
                    text = vdf.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                # Proton-CachyOS puts a `// Internal name of this tool` comment before the brace.
                if re.search(r'"' + re.escape(tool_name) + r'"\s*(?://[^\n]*\s*)?\{', text):
                    return vdf, text
        return None

    def _compat_tool_label(self, tool_name: str) -> str:
        """display_name of a custom compat tool (compatibilitytools.d), or "" when it isn't installed there."""
        found = self._compat_tool_vdf(tool_name)
        if not found:
            return ""
        label = re.search(r'"display_name"\s*"([^"]*)"', found[1])
        return label.group(1) if label else found[0].parent.name

    def _proton_takes_dll_path(self, tool_dir: Path) -> bool:
        """True when this Proton's protonfixes copies a DLL given by path in PROTON_FSR4_UPGRADE."""
        try:
            text = (tool_dir / "protonfixes" / "upscalers.py").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        return "__get_dll_manifest_from_path" in text or PROTON_LITE_MARKER in text

    def _proton_lite_installs(self) -> list[Path]:
        found = []
        for root in self._steam_root_candidates():
            base = root / "compatibilitytools.d"
            if base.is_dir():
                found += [d for d in base.iterdir() if d.is_dir() and d.name.endswith(PROTON_LITE_SUFFIX)]
        return sorted({d.resolve(): d for d in found}.values())

    async def get_cachyos_fsr4_status(self, appid) -> dict:
        try:
            tool = self._compat_tool_for_app(str(appid))
            found = self._compat_tool_vdf(tool) if tool else None
            label = self._compat_tool_label(tool) if tool else ""
            supported = "cachyos" in f"{tool} {label}".lower().replace("-", "").replace("_", "")
            lite = self._proton_lite_installs()
            previous = self._read_json_file(self._proton_lite_previous_file()).get(str(appid))
            return {
                "status": "success",
                "supported": supported,
                "tool_name": tool,
                "tool_label": label or tool,
                "takes_dll_path": bool(found) and self._proton_takes_dll_path(found[0].parent),
                "lite_tool_name": lite[-1].name if lite else None,
                "lite_proton": self._compat_tool_label(lite[-1].name) or lite[-1].name if lite else None,
                "previous_tool": previous if isinstance(previous, str) else None,
            }
        except Exception as exc:
            decky.logger.warning(f"[JediReFrameShade] cachyos status failed for {appid}: {exc}")
            return {"status": "error", "supported": False, "message": str(exc)}

    @_worker
    async def prepare_cachyos_fsr4_lite(self) -> dict:
        """Copy the FSR 4.1.2 Lite amdxcffx64.dll to ~/fgmod-proton-fsr4 for PROTON_FSR4_UPGRADE=<path>."""
        self._lite_progress = {"active": True, "lines": ["Preparing FSR 4.1.2 Lite..."], "path": None, "total": None}
        try:
            name = FSR4_LITE_412_ASSET["name"]
            src = self._ensure_runtime_binaries([name]) / name
            if not src.is_file():
                return {"status": "error", "message": f"Required bundled asset missing: {name}"}
            self._verify_bundled_asset(src, FSR4_LITE_412_ASSET["sha256"], name)
            dst_dir = Path(decky.HOME) / PROTON_FSR4_LITE_DIRNAME
            dst = dst_dir / name
            if not (dst.is_file() and self._file_sha256(dst).lower() == FSR4_LITE_412_ASSET["sha256"]):
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self._verify_bundled_asset(dst, FSR4_LITE_412_ASSET["sha256"], name)
            return {"status": "success", "path": str(dst), "version": FSR4_LITE_412_ASSET["version"]}
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] prepare_cachyos_fsr4_lite failed: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            self._lite_progress["active"] = False

    def _proton_cachyos_latest_release(self) -> dict:
        """Newest published Proton-CachyOS release with an x86_64 tarball and its .sha512sum."""
        releases = self._request_json(PROTON_CACHYOS_RELEASES_API)
        if not isinstance(releases, list):
            raise RuntimeError("Unexpected GitHub releases response")
        for release in releases:
            if release.get("draft") or release.get("prerelease"):
                continue
            assets = {a.get("name"): a for a in release.get("assets") or []}
            for name, asset in assets.items():
                match = PROTON_CACHYOS_ASSET_RE.match(name or "")
                checksum = assets.get(f"{match.group(1)}.sha512sum") if match else None
                if match and checksum:
                    return {
                        "tag": release.get("tag_name") or match.group(1),
                        "base": match.group(1),
                        "url": asset["browser_download_url"],
                        "size": asset.get("size"),
                        "sha512_url": checksum["browser_download_url"],
                    }
        raise RuntimeError("No Proton-CachyOS release with an x86_64 tarball found on GitHub.")

    def _patch_proton_upscalers(self, tool_dir: Path) -> str:
        """Makes this Proton's protonfixes take a DLL path. "native" when it already does."""
        if self._proton_takes_dll_path(tool_dir):
            return "native"
        path = tool_dir / "protonfixes" / "upscalers.py"
        text = path.read_text(encoding="utf-8")
        for old, new in PROTON_LITE_UPSCALER_PATCHES:
            if text.count(old) != 1:
                raise RuntimeError(
                    "This Proton-CachyOS release's protonfixes changed in a way the plugin hasn't been checked against."
                )
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        for cached in (tool_dir / "protonfixes" / "__pycache__").glob("upscalers.*.pyc"):
            cached.unlink(missing_ok=True)
        return "patched"

    def _proton_lite_release(self, tool_dir: Path) -> str:
        """The Proton-CachyOS release (tarball base name) a Lite copy was made from."""
        base = str(self._read_json_file(tool_dir / PROTON_LITE_RELEASE_FILE).get("base") or "")
        if not base and tool_dir.name != PROTON_LITE_TOOL_NAME:
            base = tool_dir.name[: -len(PROTON_LITE_SUFFIX)]
        return base

    @staticmethod
    def _proton_lite_in_use(tool_dir: Path) -> bool:
        """True while a running process (a game, wineserver) comes from this Proton."""
        needle = str(tool_dir.resolve()).encode()
        for proc in Path("/proc").iterdir():
            if not proc.name.isdigit():
                continue
            try:
                if needle in (proc / "cmdline").read_bytes() or needle in os.readlink(proc / "exe").encode():
                    return True
            except OSError:
                continue
        return False

    # What the Lite toggle's box in the panel shows: the steps so far and the file being downloaded.
    _lite_progress = {"active": False, "lines": [], "path": None, "total": None}

    def _lite_log(self, line: str) -> None:
        self._lite_progress["lines"].append(line)

    async def get_proton_lite_progress(self) -> dict:
        progress = self._lite_progress
        done = 0
        try:
            if progress["path"]:
                done = os.path.getsize(progress["path"])
        except OSError:
            pass
        return {
            "active": progress["active"],
            "lines": list(progress["lines"]),
            "bytes": done,
            "total": progress["total"] if progress["path"] else None,
        }

    def _install_proton_lite(self) -> dict:
        """Installs the newest Proton-CachyOS as the Lite Proton, or updates the copy when a newer release is out."""
        installed = self._proton_lite_installs()
        current = installed[-1] if installed and self._proton_takes_dll_path(installed[-1]) else None

        def keep_current(reason: str) -> dict:
            name = current.name
            return {"status": "success", "tool_name": name, "tool_label": self._compat_tool_label(name) or name,
                    "patch": "existing", "updated": False, "message": reason}

        self._lite_log("Checking Proton-CachyOS...")
        try:
            release = self._proton_cachyos_latest_release()
        except Exception as exc:
            if current:
                decky.logger.warning(f"[ProtonLite] update check failed, keeping {current.name}: {exc}")
                return keep_current("")
            raise
        self._lite_log(f"Latest: {release['base'].replace('proton-cachyos-', '').replace('-x86_64', '')}")
        if current and self._proton_lite_release(current) == release["base"]:
            self._lite_log("Already up to date")
            return keep_current("")
        if current and self._proton_lite_in_use(current):
            return keep_current("Lite Proton update skipped: close the game first.")
        try:
            return self._install_proton_lite_release(release, current)
        except Exception as exc:
            # A newer release the patch can't handle (or a failed download) leaves the working copy in place.
            if current:
                decky.logger.warning(f"[ProtonLite] update to {release['tag']} failed, keeping {current.name}: {exc}")
                return keep_current(f"Lite Proton update failed: {exc}")
            raise

    def _install_proton_lite_release(self, release: dict, current: Path | None) -> dict:
        roots = [r for r in self._steam_root_candidates() if r.is_dir()]
        if not roots:
            raise RuntimeError("Steam folder not found.")
        base = roots[0] / "compatibilitytools.d"
        base.mkdir(parents=True, exist_ok=True)
        name = PROTON_LITE_TOOL_NAME
        staging = base / f".{name}.staging"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir()
        try:
            tarball = staging / f"{release['base']}.tar.xz"
            decky.logger.info(f"[ProtonLite] downloading {release['tag']} from {release['url']}")
            self._lite_log("Downloading Proton-CachyOS...")
            self._lite_progress.update(path=str(tarball), total=release.get("size"))   # the box reads its size
            try:
                self._download_file(release["url"], tarball)
            finally:
                self._lite_progress.update(path=None, total=None)
            if release.get("size") and tarball.stat().st_size != int(release["size"]):
                raise RuntimeError("Proton-CachyOS download incomplete. Try again.")
            self._lite_log("Verifying SHA512...")
            sums = staging / "sha512sum"
            self._download_file(release["sha512_url"], sums)
            expected = sums.read_text(errors="replace").split()[0].lower()
            digest = hashlib.sha512()
            with open(tarball, "rb") as fd:
                for chunk in iter(lambda: fd.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                raise RuntimeError("The Proton-CachyOS download doesn't match its SHA512 checksum, so it wasn't used. Try again.")
            self._lite_log("Extracting...")
            try:
                result = subprocess.run(
                    ["tar", "-xJf", str(tarball), "-C", str(staging), "--no-same-owner"],
                    capture_output=True, text=True, check=False, timeout=EXTRACT_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError("Extracting Proton-CachyOS timed out. Try again.")
            if result.returncode != 0:
                raise RuntimeError(f"Could not extract Proton-CachyOS: {result.stderr.strip() or result.returncode}")
            tarball.unlink()
            tool_dir = staging / release["base"]
            vdf = tool_dir / "compatibilitytool.vdf"
            if not vdf.is_file():
                raise RuntimeError("compatibilitytool.vdf not found in the Proton-CachyOS tarball.")
            self._lite_log("Injecting FSR 4.1.2 Lite...")
            patch = self._patch_proton_upscalers(tool_dir)
            # Its own internal name and label, so it sits next to the stock Proton-CachyOS in Steam.
            label = release["base"].replace("proton-cachyos-", "Proton-CachyOS ") + " (FSR4 Lite)"
            text = vdf.read_text(encoding="utf-8", errors="replace")
            text = re.sub(r'"' + re.escape(release["base"]) + r'"(\s*(?://[^\n]*)?\s*\{)', f'"{name}"\\1', text, count=1)
            text = re.sub(r'"display_name"\s*"[^"]*"', f'"display_name" "{label}"', text, count=1)
            if f'"{name}"' not in text:
                raise RuntimeError("Unexpected compatibilitytool.vdf in the Proton-CachyOS tarball.")
            vdf.write_text(text, encoding="utf-8")
            self._write_json_file(tool_dir / PROTON_LITE_RELEASE_FILE, {"tag": release["tag"], "base": release["base"]})
            self._lite_log("Installing in Steam...")
            # The previous copy goes (the same name in place, or the old per-release name), so Steam lists one.
            # It's moved aside first, so a failed swap puts it back instead of leaving half of it.
            olds = self._proton_lite_installs()
            target = base / name
            trash = base / f".{name}.old"
            shutil.rmtree(trash, ignore_errors=True)
            if target.exists():
                target.rename(trash)
            try:
                tool_dir.rename(target)
            except Exception:
                if trash.exists() and not target.exists():
                    trash.rename(target)
                raise
            shutil.rmtree(trash, ignore_errors=True)
            for old in olds:
                if old.resolve() != target.resolve():
                    shutil.rmtree(old, ignore_errors=True)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        decky.logger.info(f"[ProtonLite] installed {name} from {release['tag']} ({patch})")
        return {"status": "success", "tool_name": name, "tool_label": label, "patch": patch,
                "updated": current is not None, "previous_tool_name": current.name if current else None}

    async def install_proton_lite(self) -> dict:
        self._lite_progress["active"] = True
        try:
            return await asyncio.to_thread(self._install_proton_lite)
        except Exception as exc:
            decky.logger.error(f"[ProtonLite] install failed: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            self._lite_progress = {"active": False, "lines": [], "path": None, "total": None}

    def _proton_lite_previous_file(self) -> Path:
        return Path(decky.HOME) / PROTON_FSR4_LITE_DIRNAME / "previous_compat_tools.json"

    async def remember_compat_tool(self, appid, tool_name: str) -> dict:
        """Keeps the Proton a game had before the Lite toggle switched it, so turning it off puts it back."""
        try:
            path = self._proton_lite_previous_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            previous = self._read_json_file(path)
            previous[str(appid)] = str(tool_name or "")
            self._write_json_file(path, previous)
            return {"status": "success"}
        except Exception as exc:
            decky.logger.error(f"[ProtonLite] remember_compat_tool failed: {exc}")
            return {"status": "error", "message": str(exc)}

    def _proton_lite_pending_file(self) -> Path:
        return Path(decky.HOME) / PROTON_FSR4_LITE_DIRNAME / "pending_compat_tools.json"

    async def get_lite_proton_pending(self) -> list:
        """Games with the Lite toggle on that wait for Steam to list the Lite Proton (it does after a restart)."""
        return list(self._read_json_file(self._proton_lite_pending_file()))

    async def set_lite_proton_pending(self, appid, pending: bool) -> dict:
        try:
            path = self._proton_lite_pending_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            games = self._read_json_file(path)
            if pending:
                games[str(appid)] = True
            else:
                games.pop(str(appid), None)
            self._write_json_file(path, games)
            return {"status": "success"}
        except Exception as exc:
            decky.logger.error(f"[ProtonLite] set_lite_proton_pending failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def get_combined_game_status(self, appid) -> dict:
        return await asyncio.to_thread(self._combined_game_status, appid)

    def _combined_game_status(self, appid) -> dict:
        game = self._game_record(str(appid))
        opti = self._game_status(str(appid), game)
        directory = None
        if opti.get("target_dir"):
            directory = Path(opti["target_dir"])
        elif game:
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
            "optiscaler_variant": opti.get("fsr4_variant"),
            "optiscaler_variant_label": opti.get("fsr4_variant_label"),
            "helixsr": self._helixsr_game_check(directory) if directory and opti.get("patched") else None,
            "reshade_present": reshade_present,
            "reshade_slot": self._detect_reshade_slot(directory) if reshade_present else None,
            "both_active": bool(opti.get("patched")) and reshade_present,
            "target_dir": str(directory) if directory else None,
        }

    # ── OptiScaler version/update status (mirrors get_reshade_update_status) ──
    # ── Plugin self-update (GitHub releases → Decky's installer) ─────────────
    _plugin_update_cache = None   # (fetched_at, release)

    def _plugin_installed_version(self) -> str:
        version = str(getattr(decky, "DECKY_PLUGIN_VERSION", "") or "").strip()
        if version:
            return version
        try:
            return str(json.loads((Path(decky.DECKY_PLUGIN_DIR) / "package.json").read_text()).get("version") or "")
        except Exception:
            return ""

    def _plugin_latest_release(self, use_cache: bool = True) -> dict | None:
        """Newest published release (no drafts, no pre-releases like the binaries ones) that carries the plugin zip."""
        cached = Plugin._plugin_update_cache
        if use_cache and cached and time.time() - cached[0] < PLUGIN_UPDATE_CACHE_SECONDS:
            return cached[1]
        best = None
        for release in self._request_json(PLUGIN_RELEASES_API):
            if release.get("draft") or release.get("prerelease"):
                continue
            for asset in release.get("assets") or []:
                match = PLUGIN_ZIP_RE.match(str(asset.get("name") or ""))
                if not match:
                    continue
                version = match.group(1)
                if best is None or self._parse_version_tuple(version) > self._parse_version_tuple(best["version"]):
                    digest = str(asset.get("digest") or "")
                    best = {
                        "version": version,
                        "tag": release.get("tag_name"),
                        "url": asset.get("browser_download_url"),
                        "size": asset.get("size"),
                        "sha256": digest[7:] if digest.startswith("sha256:") else "",
                        "notes": str(release.get("body") or "")[:1500],
                    }
        Plugin._plugin_update_cache = (time.time(), best)
        return best

    async def get_plugin_update_status(self, force: bool = False) -> dict:
        installed = self._plugin_installed_version()
        try:
            latest = await asyncio.to_thread(self._plugin_latest_release, not force)
        except Exception as exc:
            decky.logger.warning(f"[JediReFrameShade] plugin update check failed: {exc}")
            return {"status": "error", "installed_version": installed, "message": f"Could not reach GitHub: {exc}"}
        if not latest:
            return {"status": "success", "installed_version": installed, "latest_version": None, "update_available": False}
        return {
            "status": "success",
            "plugin_name": getattr(decky, "DECKY_PLUGIN_NAME", "") or "Jedi-ReFrameShade4All",
            "installed_version": installed,
            "latest_version": latest["version"],
            "update_available": self._is_update_available(installed, latest["version"]),
            "url": latest["url"],
            "sha256": latest["sha256"],
            "size": latest["size"],
            "notes": latest["notes"],
        }

    def _apply_plugin_update(self, latest: dict) -> list[str]:
        """Write the release zip over this plugin. Decky owns the plugin folder itself (only files already
        in it can be replaced), so nothing is written until every file is known to be writable, the zip
        matches GitHub's SHA256 and the new package.json's remote binaries are in bin/. Files the new
        release doesn't have (old binaries, removed files) are deleted first."""
        if not latest.get("sha256"):
            raise RuntimeError("GitHub gave no SHA256 for the release zip.")
        plugin_dir = Path(decky.DECKY_PLUGIN_DIR)
        with tempfile.TemporaryDirectory(prefix="jedi-update-") as tmp:
            archive = Path(tmp) / "plugin.zip"
            self._download_file(latest["url"], archive)
            if self._file_sha256(archive) != latest["sha256"]:
                raise RuntimeError("The downloaded zip doesn't match GitHub's SHA256.")
            with zipfile.ZipFile(archive) as zf:
                files = {}
                release_files = set()
                for info in zf.infolist():
                    parts = Path(info.filename).parts[1:]   # drop the zip's top folder
                    if info.is_dir() or not parts:
                        continue
                    if ".." in parts or Path(info.filename).is_absolute():
                        raise RuntimeError(f"Unsafe path in the zip: {info.filename}")
                    data = zf.read(info)
                    target = plugin_dir.joinpath(*parts)
                    release_files.add(target)
                    if target.is_file() and self._file_sha256(target) == hashlib.sha256(data).hexdigest():
                        continue
                    files[target] = data
            blocked = [
                str(path.relative_to(plugin_dir)) for path in files
                if not (os.access(path, os.W_OK) if path.exists() else os.access(self._existing_parent(path), os.W_OK))
            ]
            if blocked:
                raise RuntimeError("Can't write " + ", ".join(blocked) + ". Install the update from Decky's settings instead.")
            package = json.loads(files.get(plugin_dir / "package.json") or (plugin_dir / "package.json").read_bytes())
            binaries = package.get("remote_binary") or []
            self._remove_obsolete_plugin_files(plugin_dir, release_files | {plugin_dir / "bin" / b["name"] for b in binaries})
            self._fetch_remote_binaries(plugin_dir / "bin", binaries)
            # main.py last: if anything fails before it, the plugin that runs is still the old one.
            for path in sorted(files, key=lambda p: (p == plugin_dir / "main.py", p == plugin_dir / "dist" / "index.js")):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(files[path])
            return [str(path.relative_to(plugin_dir)) for path in files]

    def _remove_obsolete_plugin_files(self, plugin_dir: Path, keep: set) -> list[str]:
        """Deletes what's in the plugin folder but not in `keep`, then the folders left empty. Files Decky
        keeps root-owned (directly in the plugin folder) can't be deleted and stay."""
        removed = []
        for root, dirs, names in os.walk(plugin_dir, topdown=False):
            root_path = Path(root)
            for name in names + [d for d in dirs if (root_path / d).is_symlink()]:
                path = root_path / name
                if path in keep:
                    continue
                try:
                    path.unlink()
                    removed.append(str(path.relative_to(plugin_dir)))
                except OSError as exc:
                    decky.logger.warning(f"[JediReFrameShade] can't remove old {path}: {exc}")
            if root_path != plugin_dir and not root_path.is_symlink():
                try:
                    root_path.rmdir()
                except OSError:
                    pass
        if removed:
            decky.logger.info(f"[JediReFrameShade] removed old plugin files: {removed}")
        return removed

    def _remove_obsolete_binaries(self) -> None:
        """bin/ keeps only package.json's remote binaries: older releases' downloads go."""
        bin_dir = self._get_bin_dir()
        if not bin_dir.is_dir():
            return
        names = {entry["name"] for entry in self._load_remote_binary_manifest()}
        for path in bin_dir.iterdir():
            if path.name in names or path.is_dir():
                continue
            try:
                path.unlink()
                decky.logger.info(f"[JediReFrameShade] removed old binary {path.name}")
            except OSError as exc:
                decky.logger.warning(f"[JediReFrameShade] can't remove old binary {path}: {exc}")

    def _existing_parent(self, path: Path) -> Path:
        while not path.exists():
            path = path.parent
        return path

    def _fetch_remote_binaries(self, bin_dir: Path, binaries: list) -> None:
        """What Decky's installer does after unzipping: every remote binary in bin/, checked against its SHA256."""
        bin_dir.mkdir(parents=True, exist_ok=True)
        for binary in binaries:
            target = bin_dir / binary["name"]
            if target.is_file() and self._file_sha256(target) == binary["sha256hash"]:
                continue
            part = bin_dir / f".{binary['name']}.part"
            try:
                self._download_file(binary["url"], part)
                if self._file_sha256(part) != binary["sha256hash"]:
                    raise RuntimeError(f"{binary['name']} doesn't match its SHA256.")
                os.replace(part, target)
            finally:
                part.unlink(missing_ok=True)

    async def install_plugin_update(self) -> dict:
        installed = self._plugin_installed_version()
        try:
            latest = await asyncio.to_thread(self._plugin_latest_release, False)
            if not latest or not self._is_update_available(installed, latest["version"]):
                return {"status": "error", "message": "No newer release to install."}
            changed = await asyncio.to_thread(self._apply_plugin_update, latest)
            decky.logger.info(f"[JediReFrameShade] plugin updated {installed} -> {latest['version']}: {changed}")
            return {
                "status": "success",
                "plugin_name": getattr(decky, "DECKY_PLUGIN_NAME", "") or "Jedi-ReFrameShade4All",
                "version": latest["version"],
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] plugin update failed: {exc}")
            return {"status": "error", "message": str(exc)}

    # ── One-button "Patch All": install engines if needed + patch both mods ───
    @_worker
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
                return {"status": "error", "message": self._game_not_found_message(str(appid))}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before patching."}
            if FSR4_VARIANTS.get(str(fsr4_variant or ""), {}).get("helixsr"):
                try:
                    self._helixsr_built_dll()
                except RuntimeError as exc:
                    return {"status": "error", "message": str(exc)}

            # 1) ensure OptiScaler engine
            fg = await self.check_fgmod_path()
            if not fg.get("exists"):
                r = await self.run_install_fgmod(fsr4_variant)
                if r.get("status") != "success":
                    return {"status": "error", "message": f"OptiScaler install failed: {r.get('message') or r.get('output')}"}

            # 2) ensure ReShade engine
            try:
                rs = await self.check_reshade_path()
            except Exception:
                rs = {"exists": False}
            if not rs.get("exists"):
                r = await self.run_install_reshade(bool(with_reshade_addon), False, None)
                if r.get("status") != "success":
                    return {"status": "error", "message": f"ReShade install failed: {r.get('message') or r.get('output')}"}

            # 3) resolve a single target directory/exe so both mods land together
            target_dir, target_exe = self._guess_patch_target(game)

            # 4) patch Frame Generation FIRST (winmm). This MUST run before ReShade:
            #    OptiScaler's proxy-DLL cleanup backs up every proxy slot (incl. dxgi), so
            #    if ReShade's dxgi.dll were already there it would be moved to dxgi.dll.b
            #    and ReShade would never load. winmm is not touched by ReShade afterwards.
            pr = await self.patch_game(
                str(appid),
                "winmm.dll",
                current_launch_options,
                fsr4_variant,
                str(target_exe) if target_exe else "",
            )
            if pr.get("status") != "success":
                return {"status": "error", "message": f"Frame Generation patch failed: {pr.get('message')}"}

            # 5) patch ReShade (graphics slot dxgi) AFTER Frame Generation.
            if target_exe:
                rr = await self.manage_game_reshade(str(appid), "dxgi", str(target_exe))
            else:
                rr = await self.manage_game_reshade(str(appid), "dxgi")
            if rr.get("status") != "success":
                return {"status": "error", "message": f"ReShade patch failed (Frame Generation was applied): {rr.get('message') or rr.get('output')}"}

            # Both mods are now in the folder → always hand back the merged overrides.
            launch_options = self._merge_launch_options(["dxgi.dll", "winmm.dll"], True)
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "target_dir": pr.get("target_dir") or (str(target_dir) if target_dir else None),
                "launch_options": launch_options,
                "message": f"Patched {game['name']}: Frame Generation and ReShade.",
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] patch_all_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    # ── Full removal: every folder of the game, every file the mods put there ─────
    def _game_mod_dirs(self, game: dict) -> tuple[list[Path], list[Path]]:
        """Folders of the game holding OptiScaler / ReShade files. The patch target can change between
        patches (and a marker can be lost), so a remove that looked at one folder left the others patched."""
        root = Path(game["install_path"]) if game.get("install_path") else None
        if not root or not root.is_dir():
            return [], []
        recursive = not (game.get("shortcut_exe") and self._is_unsafe_scan_root(root))
        reshade_links = {*self.RESHADE_LINK_NAMES, *(f"{name}.b" for name in self.RESHADE_LINK_NAMES)}
        opti_dirs, reshade_dirs = [], []
        for dirpath, dirnames, filenames in os.walk(root):
            directory = Path(dirpath)
            names = set(filenames) | set(dirnames)
            if names & {MARKER_FILENAME, "OptiScaler.ini", "D3D12_Optiscaler"}:
                opti_dirs.append(directory)
            if names & {*self.RESHADE_GAME_FILES, "ReShade_shaders"} or any(
                self._is_reshade_link(directory / name) for name in names & reshade_links
            ):
                reshade_dirs.append(directory)
            if not recursive:
                break
            dirnames[:] = [d for d in dirnames if d not in ("D3D12_Optiscaler", "ReShade_shaders", HELIXSR_GAME_SUBDIR)]
        return opti_dirs, reshade_dirs

    def _is_reshade_dll_copy(self, path: Path) -> bool:
        """A ReShade DLL copied (not linked) into the game, as the old manual install did."""
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
                return False
            data = path.read_bytes()
        except OSError:
            return False
        return "crosire".encode("utf-16-le") in data and "ReShade".encode("utf-16-le") in data

    def _remove_reshade_from_dir(self, directory: Path) -> list[str]:
        """ReShade's links (dangling ones and .b copies an older patch set aside too), its copies and every
        file the install wrote, ReShadePreset.ini included. OptiScaler's files stay."""
        removed = []
        for name in self.RESHADE_LINK_NAMES:
            for path in (directory / name, directory / f"{name}.b"):
                if self._is_reshade_link(path) or (name != "d3dcompiler_47.dll" and self._is_reshade_dll_copy(path)):
                    path.unlink()
                    removed.append(path.name)
        for name in self.RESHADE_GAME_FILES:
            path = directory / name
            if path.is_symlink() or path.is_file():
                path.unlink()
                removed.append(name)
        shaders = directory / "ReShade_shaders"
        if shaders.is_symlink() or shaders.is_file():
            shaders.unlink()
            removed.append(shaders.name)
        elif shaders.is_dir():
            shutil.rmtree(shaders)
            removed.append(shaders.name)
        decky.logger.info(f"[JediReFrameShade] ReShade removed from {directory}: {removed}")
        return removed

    def _marker_launch_options(self, opti_dirs: list[Path]) -> str:
        """The launch options a game had before its first OptiScaler patch."""
        for directory in opti_dirs:
            marker = directory / MARKER_FILENAME
            if marker.exists():
                opts = str(self._read_marker(marker).get("original_launch_options") or "")
                if not self._is_managed_launch_options(opts):
                    return opts
        return ""

    def _strip_managed_launch_options(self, opts: str) -> str:
        """The current launch options without this plugin's DLL overrides and SteamDeck=0."""
        ours = {"d3dcompiler_47", *(Path(name).stem.lower() for name in (*VALID_DLL_NAMES, *self.RESHADE_LINK_NAMES))}

        def keep_theirs(match):
            entries = [e for e in match.group(1).strip('"').split(";") if e and e.split("=")[0].strip().lower() not in ours]
            return f'WINEDLLOVERRIDES="{";".join(entries)}"' if entries else ""

        text = re.sub(r'WINEDLLOVERRIDES=("[^"]*"|\S*)', keep_theirs, opts or "")
        text = " ".join(re.sub(r"(?<!\S)SteamDeck=0(?!\S)", "", text).split())
        return "" if text == "%command%" else text

    def _restored_launch_options(self, current_launch_options: str, original_launch_options: str) -> str:
        return self._strip_managed_launch_options(current_launch_options) or original_launch_options

    def _unpatch_optiscaler_dirs(self, opti_dirs: list[Path]) -> list[str]:
        errors = []
        for directory in opti_dirs:
            result = self._manual_unpatch_directory_impl(directory)
            if result.get("status") != "success":
                errors.append(str(result.get("message")))
        return errors

    @_worker
    async def unpatch_all_game(self, appid, current_launch_options="") -> dict:
        """Remove both mods from every folder of the chosen game and give back the user's launch options."""
        try:
            game = self._game_record(str(appid))
            if not game:
                return {"status": "error", "message": self._game_not_found_message(str(appid))}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before removing."}

            opti_dirs, reshade_dirs = self._game_mod_dirs(game)
            original_launch_options = self._marker_launch_options(opti_dirs)
            errors = self._unpatch_optiscaler_dirs(opti_dirs)
            # ReShade after OptiScaler: OptiScaler's unpatch puts back the files it had set aside
            for directory in reshade_dirs:
                try:
                    self._remove_reshade_from_dir(directory)
                except OSError as exc:
                    errors.append(f"ReShade in {directory}: {exc}")

            folders = {*opti_dirs, *reshade_dirs}
            if not folders:
                message = f"No OptiScaler or ReShade files found in {game['name']}."
            else:
                message = f"Removed ReShade + Frame Generation from {game['name']} ({len(folders)} folder{'s' if len(folders) > 1 else ''})."
            if errors:
                message += " Some files could not be removed: " + "; ".join(errors)
            decky.logger.info(f"[JediReFrameShade] unpatch_all_game: appid={appid} opti={opti_dirs} reshade={reshade_dirs}")
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "launch_options": self._restored_launch_options(current_launch_options, original_launch_options),
                "message": message,
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] unpatch_all_game failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    # ── Partial removal: drop one mod and keep the other one working ─────────
    def _resolve_partial_removal_target(self, game: dict):
        """Directory (and exe, when known) that holds the mods for a Steam game."""
        install_root = Path(game["install_path"])
        marker = self._find_marker(install_root) if install_root.exists() else None
        if marker:
            target_dir = Path(self._read_marker(marker).get("target_dir", str(marker.parent)))
            try:
                _, guessed_exe = self._guess_patch_target(game)
            except Exception:
                guessed_exe = None
            exe = guessed_exe if guessed_exe and Path(guessed_exe).parent == target_dir else None
            return target_dir, exe
        try:
            return self._guess_patch_target(game)
        except Exception:
            return (install_root if install_root.exists() else None), None

    @_worker
    async def remove_optiscaler_only(self, appid, current_launch_options: str = "") -> dict:
        """Remove Frame Generation from every folder of a game and keep ReShade running.

        The OptiScaler cleanup puts back the game DLLs it had set aside (d3dcompiler_47 included),
        so ReShade is re-linked afterwards and the launch options are rebuilt for it alone.
        """
        try:
            game = self._game_record(str(appid))
            if not game:
                return {"status": "error", "message": self._game_not_found_message(str(appid))}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before removing."}

            target_dir, target_exe = self._resolve_partial_removal_target(game)
            reshade_present = self._dir_has_reshade(target_dir)
            reshade_slot = self._detect_reshade_slot(target_dir) if reshade_present else None
            opti_dirs, _ = self._game_mod_dirs(game)
            was_patched = bool(opti_dirs)
            original_launch_options = self._marker_launch_options(opti_dirs)
            errors = self._unpatch_optiscaler_dirs(opti_dirs)
            if errors:
                return {"status": "error", "message": "; ".join(errors)}

            # Nothing was actually removed → ReShade's links were never touched.
            reshade_kept = reshade_present and not was_patched
            reshade_error = ""
            if reshade_present and was_patched:
                rr = await self.manage_game_reshade(
                    str(appid),
                    reshade_slot.replace(".dll", ""),
                    str(target_exe) if target_exe else "",
                )
                reshade_kept = rr.get("status") == "success"
                if not reshade_kept:
                    reshade_error = str(rr.get("message") or rr.get("output") or "unknown error")

            removed_label = (
                f"Removed Frame Generation from {game['name']}."
                if was_patched
                else f"No Frame Generation patch found for {game['name']}."
            )
            if reshade_kept:
                launch_options = self._merge_launch_options([reshade_slot], include_d3dcompiler=True)
                message = f"{removed_label} ReShade kept on {reshade_slot}."
            else:
                launch_options = self._restored_launch_options(current_launch_options, original_launch_options)
                message = removed_label
                if reshade_present:
                    message += f" ReShade could not be restored ({reshade_error}) — re-apply it."

            decky.logger.info(
                f"[JediReFrameShade] remove_optiscaler_only: appid={appid} dir={target_dir} reshade_kept={reshade_kept}"
            )
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "target_dir": str(target_dir) if target_dir else None,
                "reshade_kept": reshade_kept,
                "reshade_slot": reshade_slot if reshade_kept else None,
                "launch_options": launch_options,
                "message": message,
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] remove_optiscaler_only failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}

    @_worker
    async def remove_reshade_only(self, appid, current_launch_options: str = "") -> dict:
        """Remove ReShade from every folder of a game and keep Frame Generation patched, rebuilding
        the launch options for the OptiScaler slot alone."""
        try:
            game = self._game_record(str(appid))
            if not game:
                return {"status": "error", "message": self._game_not_found_message(str(appid))}
            if self._is_game_running(game):
                return {"status": "error", "message": "Close the game before removing."}

            target_dir, _ = self._resolve_partial_removal_target(game)
            _, reshade_dirs = self._game_mod_dirs(game)
            errors = []
            for directory in reshade_dirs:
                try:
                    self._remove_reshade_from_dir(directory)
                except OSError as exc:
                    errors.append(f"{directory}: {exc}")
            if errors:
                return {"status": "error", "message": "ReShade removal failed: " + "; ".join(errors)}

            opti = self._game_status(str(appid), game)
            optiscaler_kept = bool(opti.get("patched")) and bool(opti.get("dll_name"))
            removed_label = f"Removed ReShade from {game['name']}." if reshade_dirs else f"No ReShade files found in {game['name']}."
            if optiscaler_kept:
                launch_options = self._merge_launch_options([opti["dll_name"]], include_d3dcompiler=False)
                message = f"{removed_label} Frame Generation kept on {opti['dll_name']}."
            else:
                launch_options = self._strip_managed_launch_options(current_launch_options)
                message = removed_label

            decky.logger.info(
                f"[JediReFrameShade] remove_reshade_only: appid={appid} dir={target_dir} optiscaler_kept={optiscaler_kept}"
            )
            return {
                "status": "success",
                "appid": str(appid),
                "name": game["name"],
                "target_dir": str(target_dir) if target_dir else None,
                "optiscaler_kept": optiscaler_kept,
                "optiscaler_slot": opti.get("dll_name") if optiscaler_kept else None,
                "launch_options": launch_options,
                "message": message,
            }
        except Exception as exc:
            decky.logger.error(f"[JediReFrameShade] remove_reshade_only failed for {appid}: {exc}")
            return {"status": "error", "message": str(exc)}
