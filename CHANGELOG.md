# Changelog

## 1.1.25

### Fixed
- **Proton FSR4 → 4.1.2 Lite** didn't switch the game to the Lite Proton. It relied on `SteamClient.Apps.GetAvailableCompatTools`, which Steam's `CompatManager` service replaced. It now asks `CompatManager.GetCompatTools#1` first, then the old call, 3 seconds each. If neither answers, it sets the Proton anyway and the dialog asks you to check it.
- After the Steam restart the first install asks for, the plugin sets the Lite Proton by itself when it loads, and shows a toast. The game no longer has to be reopened in the panel. Backend: `get_lite_proton_pending`, `set_lite_proton_pending`, `~/fgmod-proton-fsr4/pending_compat_tools.json`.
- The game's Proton is read from `RegisterForAppDetails` first. `appDetailsStore` is only the fallback, because a stale value could skip the switch.
- **Proton-CachyOS FSR4** and **Show FSR watermark** stayed hidden after the switch until the game was reloaded in the panel, and while waiting for the restart. They now show whenever Lite is on.

### Removed
- **Remove Lite Proton** button and `uninstall_proton_lite`: it deleted the copy for every game without warning. The copy stays in `compatibilitytools.d/proton-cachyos-jedi-fsr4lite`.

## 1.1.24

### Added
- **LSFG-VK** toggle, right below the game picker, merged from the [Jedi LSFG-VK](https://github.com/sauliiin/Jedi-LSFG-VK) plugin (1.2.1): Lossless Scaling frame generation through MAKO Renderer. On, it saves the game's MAKO profile in `~/.config/jedi-lsfg-vk/conf.toml` and adds `~/.jedi-lsfg` before `%command%` in the launch options. Off removes both. Needs Lossless Scaling on Steam.
- **Always the newest MAKO Renderer** (Jedi LSFG-VK pinned 4.6.0): turning LSFG-VK on, and loading the plugin while some game has it on, installs or updates MAKO Renderer when the newest `render-v*` GitHub release isn't the installed one (read from `active-renderer.json`). The archive is checked against GitHub's SHA-256. Offline, an installed renderer keeps working.
- **Target FPS** slider (60–120) below the toggle while it is on. Same policy as Jedi LSFG-VK: the target is a floor, generation fills the gap in fractional steps up to 4x.
- Backend: `defaults/py_modules/lsfg_vk` (Jedi LSFG-VK's services without Flatpak, its own updater and the pinned MAKO version), `_LsfgMixin` with `get_lsfg_status`, `enable_lsfg`, `disable_lsfg`, `set_lsfg_target_fps`. On load the plugin repairs the `~/.jedi-lsfg` wrapper and refreshes `conf.toml`; on uninstall it leaves a passthrough wrapper and removes MAKO Renderer if it installed it.
- **Proton FSR4 → 4.1.2 Lite** updates its Proton: turning it on checks Proton-CachyOS's newest GitHub release and, when it's newer than the Lite copy, downloads it (SHA-512 checked), patches it and replaces the copy. Skipped while a game runs on it; offline or when the new release can't be patched, the working copy stays and the panel says so. Backend: `get_proton_lite_update_status`.
- **HelixSR pre-releases**: the newest HelixSR release counts even when it's a pre-release (now HelixSR 3.2.0).

### Changed
- Patch All, Remove All and the per-engine apply/remove buttons keep `~/.jedi-lsfg` when they rewrite the launch options.
- The Lite Proton's internal name is now always `proton-cachyos-jedi-fsr4lite` (was `proton-cachyos-<release>-jedi-fsr4lite`), so an update replaces it in place: Steam lists a single copy and games keep it. The first update removes the old per-release copy: restart Steam and reopen each Lite game in the panel once, which moves it to the new copy (its earlier Proton is still the one restored when Lite is turned off).
- **Plugin Update** deletes what the new release no longer has (old binaries in `bin/`, removed files) before writing it, and each load removes `bin/` files no release lists anymore, so the plugin folder doesn't pile up old versions.
- **Plugin Update** says it worked: after the reload the panel shows "✅ Updated to v<version>." and Decky shows a toast.
- The HelixSR panel shows full release names (installed, latest, button, dialog), e.g. *HelixSR 3.2.0 (pre-release)*.

### Fixed
- HelixSR offered an "update" to the version already installed. HelixSR-3.1.0.zip was uploaded again under the same tag (new SHA-256); that now shows as *HelixSR 3.1.0 (re-uploaded 2026-10-29)*.

## 1.1.23

### Changed
- **One upscaler setup for every game**: the **Upscaler runtime** picker is gone. Patch All gives the game OptiScaler 10 (master `de2626f`) and three upscalers to pick from in OptiScaler's menu (Insert):
  - **FSR 4**: FSR 4.1.2 (`amdxcffx64.dll` 2.4.0.4370). It starts on the Lite model; its **FSR4 Model** combo also has the full INT8 and the RDNA2 INT8 models.
  - **FSR 4.0.2c**: the bundled 4.0.2c upscaler, in `custom/FSR 4.0.2c/ffx/`.
  - **HLX DLSS**: when HelixSR 3.x is installed, in `custom/HLX DLSS/dlss/`.
- FSR 4 is the selected upscaler after patching. The HelixSR panel always shows; after installing or updating HelixSR, press Patch All again.
- Games patched with an older runtime keep it until they are patched again. Unpatching removes the `custom/` folders. Backend: variant `deck-all`.

### Removed
- **Detect target .exe** and the **Target executable** picker. Patch All and the advanced controls always find the game's `.exe` themselves.

### Fixed
- Turning on **Proton FSR4 → 4.1.2 Lite** also turned on **Proton-CachyOS FSR4**. Lite now only adds `PROTON_FSR4_UPGRADE=<Lite DLL>` (the Lite Proton turns `FSR4_UPGRADE` on by itself), so the two toggles are independent. Games where Lite is on lose the `FSR4_UPGRADE=1` the old toggle added the next time they are opened in the panel.

## 1.1.22

### Fixed
- **HelixSR 3.x** failed with "No HelixSR DLL found in HelixSR-3.1.0.zip". From 3.0, HelixSR's DLSS network (**HLX DLSS**) is `HelixSR/helixsr.dll`, an NGX (DLSS) runtime with no FFX exports, so it can no longer be OptiScaler's FFX upscaler.

### Added
- **HLX DLSS** through OptiScaler (experimental): patching with a HelixSR 3.x build puts `helixsr.dll` and `helixsr.ini` into `custom/HLX DLSS/dlss/` next to `OptiScaler.ini`, sets `Dx12Upscaler=HLX DLSS` and gives the game an OptiScaler 10 injector built from master `de2626f` (`OptiScaler_10.0.0-master.de2626f.dll`, the first build that loads custom upscalers, and runs a custom DLSS upscaler on AMD GPUs). Nukems frame generation keeps working (`FGInput=NvngxFG`, `FGNvngxReplacement=Nukems`). In the game, select DLSS.
- Switching runtime or unpatching removes `custom/HLX DLSS/` and puts back the previous `OptiScaler.ini` values; patching again with another runtime puts that runtime's injector back. Games patched with HelixSR 2.0.0 keep working until they are patched again.
- The game status reads HelixSR 3.x's log (`NGX: render AxB output CxD`).

## 1.1.21

### Fixed
- **Proton-CachyOS FSR4**, **Proton FSR4 → 4.1.2 Lite** and **Show FSR watermark** could all disappear. They only showed when the game's Proton read from `config.vdf` was Proton-CachyOS, and they waited for the Lite Proton switch, which could hang. The panel now reads the game's Proton from Steam itself (`strCompatToolName`), shows the toggles before trying the switch, and gives the switch 3 seconds.
- The Lite toggle shows for every game, since it brings its own Proton. FSR4 and the watermark also show while their variable is set, so they can be turned off.
- **Proton FSR4 → 4.1.2 Lite** never downloads the Lite Proton again once it is installed: the backend reuses the existing copy (`install_proton_lite`).

## 1.1.20

### Added
- **Proton FSR4 → 4.1.2 Lite** toggle (experimental), between **Proton-CachyOS FSR4** and **Show FSR watermark**, for games Steam runs with Proton-CachyOS: FSR 4.1.2 Lite (`FSR4L-i8`) without OptiScaler. Released Proton-CachyOS (up to `cachyos-11.0-20261015`) ignores a DLL path in `PROTON_FSR4_UPGRADE` and uses 4.1.1, so the toggle installs the newest Proton-CachyOS release (x86_64 tarball, SHA-512 checked) into `compatibilitytools.d` as **Proton-CachyOS … (FSR4 Lite)**, with `protonfixes/upscalers.py` patched to copy the given DLL into the prefix. It installs it only when it isn't there yet. It then sets that Proton for the game (`SteamClient.Apps.SpecifyCompatTool`), copies the bundled FSR 4.1.2 Lite `amdxcffx64.dll` (2.4.0.4370, SHA-256 checked) to `~/fgmod-proton-fsr4/` and adds `FSR4_UPGRADE=1 PROTON_FSR4_UPGRADE=<that path>` to the launch options. The watermark stays its own toggle.
- A dialog asks to check the game's Proton in **Properties → Compatibility** once the toggle has set it. Steam lists a new Proton only after a restart: the first time the dialog offers **Restart Steam**, and the plugin sets the Proton (and shows the dialog) the next time the game is opened in the panel.
- Turning the toggle off removes both variables and puts back the game's previous Proton. **Remove Lite Proton** deletes the copy. Patch All keeps the variables while the toggle is on. Backend: `prepare_cachyos_fsr4_lite`, `install_proton_lite`, `uninstall_proton_lite`, `remember_compat_tool`.

### Changed
- Shorter descriptions for the Proton-CachyOS toggles.

### Fixed
- The Proton-CachyOS name next to the FSR4 toggle showed the tool's internal name: its `compatibilitytool.vdf` has a comment between the name and the brace, which the lookup didn't allow.

## 1.1.19

### Changed
- Clearer description for the **Proton-CachyOS FSR4** toggle: it says the toggle turns on Proton-CachyOS's FSR4 upgrade for the game. It still only adds `FSR4_UPGRADE=1`.

## 1.1.18

### Changed
- The **Proton-CachyOS FSR4** and **Show FSR watermark** toggles only show for games Steam runs with Proton-CachyOS. They used to show disabled, with a "Needs Proton-CachyOS" note, for every other game. Patch All only keeps `FSR4_UPGRADE=1` / `PROTON_FSR4_INDICATOR=1` for Proton-CachyOS games.

## 1.1.17

### Added
- **Show FSR watermark** toggle under **Proton-CachyOS FSR4**: adds `PROTON_FSR4_INDICATOR=1` to the launch options (Proton-CachyOS's shorthand for `FSR_WATERMARK=1` + `FSR_FG_WATERMARK=1`), so AMD's driver shows which FSR runs, top left; turning it off removes only that. Like the FSR4 toggle, it needs Proton-CachyOS set for the game, and Patch All keeps it.

## 1.1.16

### Added
- **Proton-CachyOS FSR4** toggle above the upscaler runtime picker. It checks which Proton Steam uses for the game (`CompatToolMapping` in `config/config.vdf`, else the global default) and, when it is Proton-CachyOS, adds `FSR4_UPGRADE=1` to the launch options (turning it off removes only that). Nothing is downloaded or installed. Patch All keeps `FSR4_UPGRADE=1` in the launch options it sets while the toggle is on. Backend: `get_cachyos_fsr4_status`.

### Fixed
- **Plugin Update** did nothing when pressed: Decky's install prompt opens in the main window and never showed from the Quick Access menu. The plugin now updates itself (`install_plugin_update`): it downloads the release zip, checks it against GitHub's SHA256, fetches missing remote binaries into `bin/` (each checked against its SHA256), checks every changed file can be written before writing any (`main.py` last), then asks Decky to reload it.

## 1.1.15

### Added
- **Plugin Update** at the bottom of the panel: it checks this plugin's newest GitHub release (`get_plugin_update_status`) and installs it through Decky's own installer, which asks to confirm, checks the zip against GitHub's SHA256 and reloads the plugin.

### Changed
- Shorter Patch All intro, and the second "Pick a game" line above the game list is gone.
- The "This game still uses the runtime above. Press Patch All to switch it to HelixSR." warning is gone from the game status.

### Removed
- **Choose exe/folder path** (manual `.exe`/folder patching for non-Steam games), its file browser and every message pointing to it. Advanced controls now act on the game picked at the top. Non-Steam shortcuts that start a launcher (Heroic, Lutris, …) are no longer listed, since they can't be patched without that picker. Backend: `manual_patch_directory`, `manual_unpatch_directory`, `remove_optiscaler_only_manual`, `remove_reshade_only_manual`, `install_reshade_for_heroic_game`, `uninstall_reshade_for_heroic_game`, `detect_heroic_game_api`, `browse_filesystem_for_executable`, `get_sd_card_mount_path`, `validate_windows_executable_path`, `get_path_defaults`, `unpatch_game` and the Heroic helpers.

### Fixed
- **Remove All**, **Remove only OptiScaler** and **Remove only ReShade** left files behind:
  - They only cleaned one folder: OptiScaler's first marker, and ReShade the folder the target detection guessed at removal time. Patches made to another target `.exe`, or a folder whose marker was lost, stayed patched. They now go through every folder of the game.
  - A re-patch stashed ReShade's `d3dcompiler_47.dll` link as an "original" `d3dcompiler_47.dll.b`, and removing OptiScaler later put it back. OptiScaler's patch and unpatch now leave ReShade's links alone, and old `.b` copies of them are deleted.
  - ReShade removal now also deletes `ReShadePreset.ini` (the install creates it), dangling links left after ReShade itself was uninstalled, and ReShade DLLs the old manual install copied instead of linking.
  - Remove All handed back the launch options from the first patch even when you had changed them since. It now keeps your current ones minus this plugin's DLL overrides and `SteamDeck=0`.
- OptiScaler's unpatch deleted the game's whole `plugins` folder. It now removes only `OptiPatcher.asi`, and the folder only if nothing else is in it.
- Uninstalling OptiScaler also removes `.fgmod-staging-*` / `.fgmod-backup-*` folders left by interrupted installs.

## 1.1.14

### Fixed
- Patching with HelixSR failed with "There's already a HelixSR folder next to OptiScaler.ini that this plugin didn't create". A `HelixSR/` folder already in the game (left half made by an earlier patch, or made by another tool) is now replaced by the plugin's own, and the patch message says what was there. The plugin made the folder first and its record of it (`jedi-helixsr.json`) last, so a patch that stopped half way left such a folder: a patch that fails now removes the folder it made. Switching runtime or unpatching also removes a half-made folder, with OptiScaler.ini's paths into it set back to auto.

## 1.1.13

### Added
- **4.1.2 Lite | FSR4L-i8** upscaler runtime (experimental): AMD's FSR 4.1.2 INT8 Lite model, the smaller INT8 model AMD made for APUs (Steam Deck, RDNA2/3 iGPUs). It ships AMD's unmodified, signed Adrenalin 26.10.1 driver FSR (`amdxcffx64.dll` and, for Vulkan games, `amdvkffx64.dll`, 2.4.0.4370) with an OptiScaler 10 injector built from master `2128299c` (the first build that selects 4.1.2 models and keeps the AMD vendor id for `amdxcffx64` while spoofing). The FFX/XeSS libraries stay 0.9.4's: they are the same files in OptiScaler 10.
- Patching with it sets OptiScaler 10's keys (`Fsr4GpuSupport=4`, `Fsr4Model=3`, `Dx12Upscaler=ffx`, `UpscalerIndex=0`) and keeps Nukems frame generation working (`FGInput=NvngxFG`, `FGNvngxReplacement=Nukems`: OptiScaler 10 reads `FGInput=nukems` as no FG). Switching a game to another runtime puts the 0.9.4 values back.

### Fixed
- HelixSR 2.0.0 failed with "No HelixSR DLL found": 2.0 keeps the DLL in `HelixSR-fsrfg/`. The setup also stopped getting `--yes`, which 2.0 hands on to its game installer (it would have put HelixSR into every game it finds): the plugin downloads NVIDIA's DLSS DLL itself (checked against the release's own SHA256) and passes it with `--dlss`, so the build asks nothing and the game installer changes no game.

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
