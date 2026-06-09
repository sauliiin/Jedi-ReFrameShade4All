# Changelog

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
- **"Asks to install again" loop**: caused by two concurrent install buttons writing to `~/fgmod`. Fixed by collapsing to a single install/update entry. (The bundled archive is byte‑identical to upstream's "latest", so the download path was never the cause.)
- **Duplicate install button**: removed the redundant "Install OptiScaler" widget that did the same thing as "Setup OptiScaler Mod".

### Removed
- Dead source files: `OptiScalerHeader`, `OptiScalerWiki`, `SteamGamePatcher`, `InstallationStatus`, `SteamGamesSection`, `HeroicGamesSection`, `InstalledGamesSection`, `exports.ts`.

### Inherited
- OptiScaler: FSR4 variants (incl. Steam Deck / RDNA2‑3 INT8), idempotent patch/unpatch, install manifest, Steam‑OS‑beta UI.
- ReShade: add‑on support, AutoHDR, shader pack selection, Steam + Heroic + manual `.exe` patching.

### Notes
- Not yet validated end‑to‑end on Steam Deck hardware.
- ReShade add‑on toggle ships **off** (anti‑cheat warning).
