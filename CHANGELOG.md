# Changelog

## 1.1.12

### Added
- HelixSR download progress: the download (about 130 MB from HelixSR 1.9.3, which now bundles HelixSR Scaler), its SHA256 check and the extraction run in the background with a progress bar, followed by the build. A failed download is shown in the panel; the installed HelixSR stays untouched.

### Changed
- HelixSR Scaler (`helixsr-scaler/`, ~205 MB in HelixSR 1.9.3's zip) is no longer extracted: it isn't used here and the setup builds the network without it. An installed release now takes about 8 MB.
- Checked against HelixSR 1.9.3 and DeckyHelixSRManager 0.10.2: same setup flags, FSR4 forwarding and frame generation forwarding.

### Fixed
- The HelixSR build was started from a worker thread, which made the install report an error ("no current event loop") although the build was running.

## 1.1.11

### Added
- **HelixSR** as an upscaler runtime (*HelixSR | DLSS Model E on AMD*, experimental), ported from [DeckyHelixSRManager](https://github.com/PeroTuncay/DeckyHelixSRManager). Selecting it shows whether the newest HelixSR release is installed; if not, **Install/Update HelixSR** downloads it (SHA256-verified) and runs HelixSR's setup in the background with a progress bar (`get_helixsr_status`, `install_latest_helixsr`, `cancel_helixsr_setup`). Only one release is kept: a new build replaces the old one once it succeeds.
- Patching with HelixSR sets it as OptiScaler's FFX upscaler from a per-game `HelixSR/` folder (FSR4 4.0.2c stays selectable, frame generation keeps working); switching runtime or unpatching restores `OptiScaler.ini` and removes the folder.

### Changed
- The *FSR4 runtime* dropdown is now **Upscaler runtime (FSR4 / HelixSR)**.

### Fixed
- HelixSR not showing in OptiScaler's FFX Upscaler list (only FSR 4.0.2c did): in the game, HelixSR is now `helixsr.dll` / `helixsr_upscaler.dll`, so the loader no longer hands back the FSR DLL the game already loaded under the same name. Re-patch the game to apply.
- Old OptiScaler.ini template bug: an unanchored `Path=auto` → `Path=plugins` also set `OptiDllPath`, `NvapiPath`, `FfxDx12*Path`, `XeSSPath`, `TTFFontPath`, … to `plugins`. Only `[Plugins] Path` gets it now, and patching repairs existing game INIs.
- The game status shows the applied upscaler runtime and, for HelixSR, what `helixsr.log` reports (loaded / upscaling / network not running), with a **Check HelixSR again** button.

## 1.0.10

### Updated
- Bundled OptiScaler from `0.9.3-final` to the official `0.9.4-final.20260718` archive (FFX 2.3 SDK / FSR 4.1.1), matching Decky-Framegen `0.17`.
- FSR4 runtimes relabeled to match upstream: *4.0.2c RDNA2/3 Compatibility*, *4.1.1 FFX 2.3 SDK*, *4.1.1 Driver Override* and *4.1.1 Valve RDNA2 Compatibility*. The SDK, driver-override and Valve RDNA2 paths now all use the 0.9.4 FSR 4.1.1 upscaler.

### Added
- The FSR4 runtime dropdown now shows a short description of the selected runtime (ported from Decky-Framegen).
- **Non-Steam game detection**: shortcuts from Steam's `shortcuts.vdf` appear in the game picker. Direct `.exe` shortcuts support Patch All, per-engine patching, status and removal, with launch options applied to the shortcut automatically; launcher shortcuts (Heroic, Lutris, …) point the user to the manual exe picker. Broad folders (home, drive roots) are never scanned recursively.

### Fixed
- Variant extra DLLs (`amdxcffx64.dll`, `amdxc64.dll`) are only copied into the game folder when present.

## 1.0.9

### Added
- **Partial removal**, the counterpart of the existing "Apply only …" actions: **🗑️ Remove only OptiScaler** in *Framegen Management* and **🗑️ Remove only ReShade** in *ReShade Management*, both for Steam games and for manually chosen non‑Steam `.exe` folders (`remove_optiscaler_only`, `remove_reshade_only`, `remove_optiscaler_only_manual`, `remove_reshade_only_manual`).
- Removing one mod keeps the other working: the OptiScaler cleanup wipes every proxy slot, so ReShade is re‑linked on its slot afterwards. Launch options are rewritten for whatever remains (Steam games are updated automatically; non‑Steam users get the new launch command copied to the clipboard) and cleared when nothing remains.

## 1.0.8

### Added
- Ported Decky-Framegen `v0.16.3-pre` FSR4 runtime matrix: RDNA3/4 official 4.1.1 and experimental RDNA2 Valve 4.1.1 pre10 with its dedicated injector.
- Variant-aware patching now copies runtime extra DLLs, applies OptiScaler.ini overrides, detects variants by extra files, and exposes the new runtimes in the panel.

### Fixed
- Framegen unpatch/wrapper cleanup now handles `amdxcffx64.dll` and `amdxc64.dll` backups correctly.

## 1.0.7

### Updated
- Bundled OptiScaler from `0.9.2a` to the official `0.9.3-final.20260618` archive.
- Project and release references now point to Jedi‑ReFrameShade4All and the official OptiScaler release.

### Fixed
- OptiScaler install now resolves helper scripts from `defaults/assets` in sideload/store packages and fails clearly if any helper is missing.
- Missing runtime binaries are downloaded from the hash-pinned `remote_binary` manifest when necessary.
- Updates are prepared and validated in a staging directory before atomically replacing `~/fgmod`, preserving the previous install on failure.
- Explicit updates no longer fall back to the old bundled build while reporting success; downloaded release size and SHA-256 are verified.
- Legacy installs without an install manifest are correctly offered the current update.

## 1.0.0

First release — fusion of **OptiScaler Frame Generation** (Decky‑Framegen 0.15.6) and **ReShade with add‑ons** (LetMeReShade) into a single Decky plugin.

### Added
- Single back‑end (`main.py`) combining both projects via `_OptiScalerMixin` + `_ReShadeMixin` under one Decky `Plugin` class.
- **One‑button "Patch All"** primary flow (`patch_all_game` / `unpatch_all_game`): pick one Steam game → installs OptiScaler + ReShade engines if missing, patches both into the same folder (ReShade `dxgi` + Frame Generation `winmm`), and sets the merged launch options automatically. `get_engines_status` powers the status line. Detailed per‑engine controls now live under an **Advanced controls** toggle.
- **Coexistence layer** so both run on the same game: ReShade keeps the graphics slot (`dxgi`, auto‑detected); Frame Generation is forced onto `winmm`; launch options merge into a single `WINEDLLOVERRIDES`.
  - `get_combined_game_status`, `set_slots_manual`, and a **Coexistence / DLL slots** UI section with a manual slot picker.
- **FRAMEGEN MANAGEMENT** widget mirroring **RESHADE MANAGEMENT**: installed state, version, *up to date / update available*, and an Install/Update button. The FSR4 runtime is chosen once (top section) and shared.
- **Precise OptiScaler update check** (`get_optiscaler_update_status`): compares the installed archive **asset name** vs. the newest GitHub release asset (not the tag), so no false "update available". The **Update** button (`update_optiscaler`) force‑downloads the newest complete archive.
- Unified front‑end (`src/index.tsx`); plugin renamed to **Jedi ReFrameShade4All**.

### Fixed
- **"Asks to install again" loop**: caused by two concurrent install buttons writing to `~/fgmod`. Fixed by collapsing to a single install/update entry.
- **Duplicate install button**: removed the redundant "Install OptiScaler" widget that did the same thing as "Setup OptiScaler Mod".

### Removed
- Dead source files: `OptiScalerHeader`, `OptiScalerWiki`, `SteamGamePatcher`, `InstallationStatus`, `SteamGamesSection`, `HeroicGamesSection`, `InstalledGamesSection`, `exports.ts`.

### Inherited
- OptiScaler: FSR4 variants (incl. Steam Deck / RDNA2‑3 INT8), idempotent patch/unpatch, install manifest, Steam‑OS‑beta UI.
- ReShade: add‑on support, AutoHDR, shader pack selection, Steam + Heroic + manual `.exe` patching.

### Notes
- Not yet validated end‑to‑end on Steam Deck hardware.
- ReShade add‑on toggle ships **off** (anti‑cheat warning).
