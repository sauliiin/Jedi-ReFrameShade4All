# Jedi ReFrameShade4All

**One Decky plugin that runs OptiScaler (Frame Generation + upscaling) and ReShade (with add-ons) together — on the same game, without fighting over the same DLL.**

It fuses two mature Decky plugins into a single panel:

- **Frame Generation / upscaling** — based on [Decky‑Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen) (OptiScaler `0.15.6`). Ships the complete bundled, hash‑verified build; GitHub auto‑update is **opt‑in**.
- **ReShade with add‑ons** — based on [LetMeReShade(All)](https://github.com/itsOwen/LetMeReShade) (downloads ReShade from reshade.me, shader packs, AutoHDR, Steam + Heroic support, manual `.exe` patching).

> ⚠️ **Community fan‑merge.** This is an unofficial combination of two separate projects. It builds cleanly and the UI/back‑end are wired together, but the two injectors were never designed to coexist — **test it per game** and read the *Coexistence* and *Safety* sections below.

---

## How it works — and why the two mods don't conflict

### Proxy‑DLL injection (the "door")

Both OptiScaler and ReShade get into a game the same way: **proxy‑DLL injection**. They drop a file named after a Windows system DLL that the game already loads (e.g. `dxgi.dll`) right next to the game's `.exe`. When the game starts, it loads that file thinking it's the real system DLL — and the mod rides in with it. Think of the proxy DLL as a **door**: it's only how the mod *gets into* the process; it is not where the mod does its work.

### The conflict

A folder can only contain **one** `dxgi.dll`. Out of the box **both mods default to `dxgi.dll`**, so installing both means one overwrites the other and only one ever loads.

### The fix: put each mod on a different slot

A game loads many system DLLs, not just `dxgi`. So this plugin puts each mod on a **different door**:

| Mod | Proxy slot used | Why |
|-----|-----------------|-----|
| **ReShade** | `dxgi.dll` (auto‑detects the graphics API) | it owns the graphics DLL + ships its own `d3dcompiler_47.dll` |
| **Frame Generation (OptiScaler)** | `winmm.dll` | a non‑graphics slot ReShade never touches → no collision |

Why `winmm` is safe: ReShade only ever uses the graphics‑family slots `d3d8 d3d9 d3d11 ddraw dinput8 dxgi opengl32`. `winmm` is **not** in that list, and OptiScaler officially supports it — so the two never fight over the same file.

### Is `winmm.dll` real? Won't using it instead of `dxgi.dll` cost performance?

**It's a real, standard Windows DLL — not invented here.** `winmm.dll` is the **Windows Multimedia API** (multimedia timers like `timeGetTime`/`timeBeginPeriod`, `PlaySound`/`waveOut` audio, MIDI, joystick). Practically every game loads it, and it exists in Proton/Wine. It is also one of OptiScaler's **officially supported** proxy slots (`dxgi, winmm, dbghelp, version, wininet, winhttp, OptiScaler.asi`) — we just pick `winmm` to leave `dxgi` free for ReShade. OptiScaler‑on‑`winmm` + ReShade‑on‑`dxgi` is the well‑known community combo for running both together.

**There is no FPS penalty.** The proxy DLL is only the *loader*. Once OptiScaler is inside the process — via **any** slot — it installs its real hooks at runtime on the APIs that matter: `nvngx` (DLSS) and the **DXGI swap‑chain** (present / frame generation). Those hooks are identical whether OptiScaler was loaded through `dxgi.dll` or `winmm.dll`. The proxy itself just thin‑forwards calls to the real system DLL; `winmm`'s functions (timers/audio) are rare and trivial, so the overhead is microseconds — it does not affect frame rate.

The only thing the slot choice affects is **whether the game loads that DLL at all** (i.e. whether injection happens), not speed. `winmm` is loaded by the vast majority of games; for the rare title that doesn't, switch the slot (`version`, `dbghelp`, …) in the **Coexistence / DLL slots** section.

### Merged launch options

Each proxy only activates if Proton/Wine is told to load the local DLL instead of the system one. With two mods, the launch options must enable **both** — the plugin builds and sets this for you automatically:

```
WINEDLLOVERRIDES="d3dcompiler_47=n;dxgi=n,b;winmm=n,b" SteamDeck=0 %command%
```

(`dxgi` → ReShade, `winmm` → OptiScaler, `d3dcompiler_47` → ReShade's shader compiler.)

### Install order matters

ReShade installs its `dxgi.dll` as a **symlink**. OptiScaler's patch routine **backs up any pre‑existing proxy DLL** (including `dxgi`) by moving it to `*.b`. So if OptiScaler ran *after* ReShade, it would move ReShade's `dxgi.dll` → `dxgi.dll.b` and ReShade would silently stop loading (the "HOME does nothing" symptom). **Patch All** therefore applies **Frame Generation (`winmm`) first, then ReShade (`dxgi`)** — ReShade never touches `winmm`, so neither one displaces the other.

### Same folder

Both mods must land in the **same folder** (the one the game loads DLLs from). The plugin resolves the target executable **once** and passes that exact path to both installers, so they always land together.

### Runtime note (not a file conflict)

At runtime both mods hook the DXGI swap‑chain — ReShade for post‑processing, OptiScaler for frame generation. They generally coexist, but **load order can be game‑specific**; if a particular title misbehaves, the manual slot picker in **Coexistence / DLL slots** is the escape hatch.

---

## Features

**One‑button flow**
- **Patch All**: pick a Steam game → installs OptiScaler + ReShade if missing, patches both into the game, and sets the merged launch options automatically. **Remove All** reverts everything. Detailed per‑engine controls live under an **Advanced controls** toggle.

**Frame Generation / OptiScaler** (FRAMEGEN MANAGEMENT)
- Install/uninstall with an **installed vs. latest** version widget (same style as ReShade); precise *up to date / update available* and a one‑click **Update**.
- FSR4 runtime variants, incl. the **Steam Deck / RDNA2‑3 INT8** optimized path (chosen once, shared).
- Per‑game patch/unpatch (Steam) and manual **folder** patching.
- Default install uses the complete bundled `0.9.2a`; Update force‑downloads the newest upstream archive.

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
│  ├─ index.tsx                     # composes sections, shared FSR4 state, Advanced toggle
│  ├─ SteamGameCombinedSection.tsx  # primary one-button "Patch All" (both mods)
│  ├─ ConflictSlotSection.tsx       # coexistence + manual slot picker (Advanced)
│  ├─ ReShadeInstallerSection.tsx   # "ReShade Management" — install/version/update/add-ons/shaders
│  ├─ ChooseExePathSection.tsx      # ReShade manual .exe patcher for non-Steam games
│  ├─ ExecutablePathBrowserModal.tsx, ShaderSelectionModal.tsx  # ReShade modals
│  ├─ components/                   # "Framegen Management" — OptiScalerControls + helpers
│  ├─ api/index.ts                  # typed backend callables
│  └─ utils/, types/               # helpers, constants, type decls
├─ defaults/assets/         # fgmod*.sh + reshade-*.sh install/patch scripts
├─ bin/                     # OptiScaler binaries (gitignored; via remote_binary)
└─ dist/                    # build output (gitignored)
```

The panel is two parallel sections under an **Advanced controls** toggle — **FRAMEGEN MANAGEMENT** (`components/OptiScalerControls.tsx`) and **RESHADE MANAGEMENT** (`ReShadeInstallerSection.tsx`) — each showing install state, version, and *up to date / update available* with an Install/Update button.

**Back‑end architecture:** the two original `main.py` files are combined into one Decky‑safe `Plugin` class using mixins (`_OptiScalerMixin`, `_ReShadeMixin`). Method‑name collisions (`_main`, `_unload`, `list_installed_games`, `log_error`) are resolved in the final `Plugin`, which also adds the one‑button flow (`patch_all_game` / `unpatch_all_game`) and the coexistence layer (`patch_game` slot override, `get_combined_game_status`, `set_slots_manual`). `patch_all_game` applies Frame Generation (winmm) **before** ReShade (dxgi) so OptiScaler's proxy cleanup can't displace ReShade's DLL.

**OptiScaler updates** are *precise*: `get_optiscaler_update_status` compares the **installed archive asset name** (from the install manifest) against the newest GitHub release asset — the bundled `_Reup` archive is byte‑identical to upstream's "latest", so it reports *up to date* until a genuinely newer release ships. The **Update** button (`update_optiscaler`) then force‑downloads that newer complete archive; plain install/reinstall uses the bundled one (instant, offline).

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
