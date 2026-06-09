# Jedi ReFrameShade4All

**One Decky plugin that runs OptiScaler (Frame Generation + upscaling) and ReShade (with add-ons) together — on the same game, without fighting over the same DLL.**

It fuses two mature Decky plugins into a single panel:

- **Frame Generation / upscaling** — based on [Decky‑Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen) (OptiScaler `0.15.6`). Ships the complete bundled, hash‑verified build; GitHub auto‑update is **opt‑in**.
- **ReShade with add‑ons** — based on [LetMeReShade(All)](https://github.com/itsOwen/LetMeReShade) (downloads ReShade from reshade.me, shader packs, AutoHDR, Steam + Heroic support, manual `.exe` patching).

> ⚠️ **Community fan‑merge.** This is an unofficial combination of two separate projects. It builds cleanly and the UI/back‑end are wired together, but the two injectors were never designed to coexist — **test it per game** and read the *Coexistence* and *Safety* sections below.

---

## Why a single plugin?

Both OptiScaler and ReShade inject themselves by **proxying a Windows DLL** that the game loads (the classic "drop a fake `dxgi.dll` next to the `.exe`" trick). If both try to be `dxgi.dll`, you get a direct file conflict and only one loads.

**Jedi ReFrameShade4All resolves this automatically:**

| Mod | Default proxy slot | Notes |
|-----|--------------------|-------|
| ReShade | `dxgi.dll` (auto‑detects the graphics API) | owns the graphics DLL + `d3dcompiler_47.dll` |
| Frame Generation (OptiScaler) | `winmm.dll` | forced onto a non‑graphics slot so it never collides |

When both are applied to the same game, the plugin merges the launch options into a single string, e.g.:

```
WINEDLLOVERRIDES="d3dcompiler_47=n;dxgi=n,b;winmm=n,b" SteamDeck=0 %command%
```

The **Coexistence / DLL slots** section in the UI shows what is active on a game and lets you pick the Frame Generation slot manually if a specific title needs it.

---

## Features

**One‑button flow**
- **Patch All**: pick a Steam game → installs OptiScaler + ReShade if missing, patches both into the game, and sets the merged launch options automatically. **Remove All** reverts everything. Detailed per‑engine controls live under an **Advanced controls** toggle.

**Frame Generation / OptiScaler**
- Install/uninstall OptiScaler; the installed bundle version is shown.
- FSR4 runtime variants, incl. the **Steam Deck / RDNA2‑3 INT8** optimized path.
- Per‑game patch/unpatch (Steam) and manual **folder** patching.
- Optional GitHub auto‑update (**opt‑in**); defaults to the complete bundled `0.9.2a`.

**ReShade**
- ReShade **with add‑on support** (toggle) and optional **AutoHDR** (OLED‑oriented).
- Downloads ReShade from reshade.me with an **installed vs. latest** version widget.
- Shader pack selection (AstrayFX, MartyMcFly, prod80, SweetFX, RetroArch…).
- Steam games + **Heroic** games + manual **`.exe`** patching ("Choose exe path").

**Coexistence**
- Automatic, conflict‑free default slots (ReShade `dxgi`, Frame Gen `winmm`) + a **manual slot override** per game.

---

## Installation

### Option A — sideload the release zip (easiest)
1. Grab `Jedi-ReFrameShade4All.zip` from the project's Releases.
2. On the Deck (Desktop Mode): Decky → ⚙ → **Developer Mode** → **Install Plugin from ZIP**.
3. Back in Game Mode, open the plugin, pick a Steam game and press **Patch All**.

### Option B — build from source
See [Building](#building) below, then zip the folder (with `bin/` + `dist/`) and sideload as in Option A.

---

## Usage

**The simple path — one button:**

1. **Steam Game — Patch All**: pick a game, (optionally) toggle *ReShade add‑ons* and the *FSR4 runtime*, then press **🚀 Patch All**. It installs OptiScaler and ReShade if they aren't yet, applies both to the game, and sets the launch options automatically. **Remove All** reverts it.
2. In‑game: press **HOME** for the ReShade overlay.

**Advanced controls** (toggle near the top) expose the original per‑engine UIs when you need them:
- OptiScaler: install/uninstall, FSR4 variant, proxy DLL, manual folder patch.
- ReShade: add‑on/AutoHDR toggles, shader pack selection, per‑game and manual `.exe` patching.
- Coexistence / DLL slots: inspect what's active and override the Frame Generation slot per game.

> **Patch All puts ReShade on `dxgi`**, which covers DX11/DX12 (most games). For DX9/Vulkan/OpenGL titles, use **Advanced → ReShade**, which auto‑detects the API.

> Auto‑update for OptiScaler is **opt‑in** — set `DECKY_OPTISCALER_AUTO_UPDATE=1`. By default the complete bundled `0.9.2a` build is used (the official upstream archive omits the Frame Generation components).

---

## Building

Requirements: **Node.js ≥ 18** and **pnpm**.

```bash
pnpm install
pnpm build      # outputs dist/index.js
```

The OptiScaler binaries (`bin/`) and ReShade assets are **not committed** — they are listed under `remote_binary` in `package.json` and fetched by Decky's build tooling, or you can drop the three OptiScaler files into `bin/` manually for a self‑contained sideload zip.

> **Filesystem note:** pnpm uses symlinks. If your working copy lives on NTFS/exFAT (no symlink support), build in an ext4/`/tmp` location and copy `dist/` back.

---

## Project structure

```
Jedi-ReFrameShade4All/
├─ main.py                  # merged back-end: _OptiScalerMixin + _ReShadeMixin → Plugin
├─ plugin.json              # Decky manifest (name/id: Jedi-ReFrameShade4All)
├─ package.json             # deps + merged remote_binary list
├─ src/                     # React/TSX frontend
│  ├─ index.tsx                     # composes every section, names the plugin
│  ├─ SteamGameCombinedSection.tsx  # NEW: one-button "Patch All" (both mods)
│  ├─ ConflictSlotSection.tsx       # NEW: coexistence + manual slot picker
│  ├─ ReShadeInstallerSection.tsx   # ReShade install/version/add-ons/shaders
│  ├─ components/                   # OptiScaler UI (from Decky-Framegen)
│  └─ *.tsx                         # ReShade UI (from LetMeReShade)
├─ defaults/assets/         # fgmod*.sh + reshade-*.sh install/patch scripts
├─ bin/                     # OptiScaler binaries (gitignored; via remote_binary)
└─ dist/                    # build output (gitignored)
```

**Back‑end architecture:** the two original `main.py` files are combined into one Decky‑safe `Plugin` class using mixins (`_OptiScalerMixin`, `_ReShadeMixin`). Method‑name collisions (`_main`, `_unload`, `list_installed_games`, `log_error`) are resolved in the final `Plugin`, which also adds the one‑button flow (`patch_all_game` / `unpatch_all_game`) and the coexistence layer (`patch_game` slot override, `get_combined_game_status`, `set_slots_manual`). `patch_all_game` applies Frame Generation (winmm) **before** ReShade (dxgi) so OptiScaler's proxy cleanup can't displace ReShade's DLL.

---

## Safety & disclaimers

- **Anti‑cheat:** ReShade **with add‑ons** can trip anti‑cheat in online games. Use add‑ons only where it's allowed; the toggle ships **off** with a warning.
- **Runtime conflicts:** both mods hook the DXGI swap‑chain (Frame Gen for generation, ReShade for post‑processing). It usually works, but load order can be game‑specific — the manual slot picker is the escape hatch.
- This project ships/manages third‑party binaries (OptiScaler, ReShade, FSR/XeSS/DLSS‑to‑FSR components). Their licenses live in `defaults/assets/licenses/`.

---

## Credits & licenses

- **OptiScaler Frame Generation** — [Decky‑Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen) by xXJSONDeruloXx, and the [OptiScaler](https://github.com/optiscaler/OptiScaler) project.
- **ReShade integration** — [LetMeReShade](https://github.com/itsOwen/LetMeReShade) by itsOwen, and [ReShade](https://reshade.me) by crosire.
- Built on the Decky plugin template.

Both upstream plugins are **BSD‑3‑Clause**; this merge is distributed under the same terms (see `LICENSE`). All trademarks and bundled components belong to their respective owners.
