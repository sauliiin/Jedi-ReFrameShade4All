# Jedi ReFrameShade4All

**One Decky plugin that runs OptiScaler (Frame Generation + upscaling) and ReShade (with add-ons) together — on the same game, without fighting over the same DLL.**

It fuses two mature Decky plugins into a single panel:

- **Frame Generation / upscaling** — based on [Decky‑Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen). Ships the complete bundled, hash‑verified OptiScaler `0.9.4` build (FFX 2.3 SDK / FSR 4.1.1); GitHub auto‑update is **opt‑in**.
- **ReShade with add‑ons** — based on [LetMeReShade(All)](https://github.com/itsOwen/LetMeReShade) (downloads ReShade from reshade.me, shader packs, AutoHDR).

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
- **Patch All**: pick a Steam game **or a non‑Steam shortcut** → installs OptiScaler + ReShade if missing, patches both into the game, and sets the merged launch options automatically. **Remove All** reverts everything: it looks through every folder of the game, so nothing either mod put there is left behind, and gives back your own launch options. Detailed per‑engine controls live under an **Advanced controls** toggle.
- **Non‑Steam shortcuts** are read from `userdata/<id>/config/shortcuts.vdf` and listed next to Steam games when they point straight at a Windows `.exe`; they get the full one‑button flow, including launch options set on the shortcut automatically. Shortcuts that start a launcher (Heroic, Lutris, Bottles, …) aren't listed: the game folder can't be known from the shortcut.
- **Plugin Update**: the panel checks this plugin's newest GitHub release and installs it itself (zip checked against GitHub's SHA256, missing binaries fetched), then Decky reloads the plugin.

**LSFG-VK** (merged from [Jedi LSFG-VK](https://github.com/sauliiin/Jedi-LSFG-VK))
- **LSFG-VK** toggle, right below the game picker: Lossless Scaling frame generation through [MAKO Renderer](https://github.com/eugeniosegala/MAKO). Needs [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) installed through Steam (any branch that ships `Lossless.dll`).
- **Always the newest MAKO Renderer**: turning the toggle on, and loading the plugin while some game has it on, compares the installed renderer (`~/.local/share/mako-render/active-renderer.json`) with the newest `render-v*` release on GitHub. When it's missing or older, the plugin downloads `MAKO-Renderer-v<version>-linux.tar.xz`, checks it against GitHub's SHA-256 and runs its installer into `~/.local`. Offline, an installed renderer keeps working.
- On: adds `~/.jedi-lsfg` right before `%command%` in the game's launch options and saves a MAKO profile for the game in `~/.config/jedi-lsfg-vk/conf.toml`. Off: removes both. A `~/.lsfg` or `mako-run` wrapper already in the launch options is replaced, since two frame generation layers don't work together.
- **Target FPS** slider (60–120), shown while the toggle is on, saved as soon as the slider stops. The target is a floor, not a cap: a game that runs above it keeps its real FPS, and generation only fills the gap below it, in fractional steps up to 4x. Every 3 seconds MAKO checks whether the game can run faster on its own. Use a target no higher than the display's refresh rate.
- Patch All, Remove All and the per-engine apply/remove buttons keep `~/.jedi-lsfg` in the launch options.
- Same files as the standalone Jedi LSFG-VK plugin, so games turned on there show as on here. Uninstalling the standalone plugin from Decky removes those profiles: turn the toggle on again afterwards. Flatpak apps aren't supported here.

**Frame Generation / OptiScaler** (FRAMEGEN MANAGEMENT)
- Install/uninstall with an **installed vs. latest** version widget (same style as ReShade); precise *up to date / update available* and a one‑click **Update**.
- **One upscaler setup for every game**, picked in OptiScaler's menu (Insert): Patch All gives the game an OptiScaler 10 injector built from master `de2626f` plus [a small patch](https://github.com/sauliiin/Jedi-ReFrameShade4All/releases/tag/optiscaler-10-de2626f-jedi1) that also takes AMD driver DLLs, which loads custom upscalers from `custom/<name>/ffx` and `custom/<name>/dlss` next to `OptiScaler.ini`. The menu then lists:
  - **FSR 4** — FSR 4.1.2 from AMD's unmodified, signed `amdxcffx64.dll` / `amdvkffx64.dll` 2.4.0.4370 (Adrenalin 26.10.1) with the 4.1.1 SDK upscaler. It starts on the INT8 Lite model made for APUs (`FSR.Fsr4GpuSupport=4`, `FSR.Fsr4Model=3`); that DLL also has the full INT8 and the RDNA2 INT8 models, which OptiScaler's **FSR4 Model** combo switches to in the game. It is the selected upscaler after patching (`Upscalers.Dx12Upscaler=ffx`, `FSR.UpscalerIndex=0`).
  - **FSR 4.0.2c** — the bundled INT8 4.0.2c upscaler, in `custom/FSR 4.0.2c/ffx/`.
  - **FSR 4.1.1** (experimental) — Valve's `amdxcffx64.dll` 2.3.0.2913 (the old **4.1.1 Valve RDNA2 Compatibility** runtime), in `custom/FSR 4.1.1/ffx/`. It runs its INT8 model even with INT8 Lite selected, as it has no Lite model. Valve's `amdxc64.dll` isn't installed with it.
  - **HLX DLSS** (experimental, when HelixSR 3.x is installed) — [HelixSR](https://github.com/lonewolf0622/HelixSR) runs NVIDIA's DLSS Model E network as D3D12 compute shaders (DX12 games only), in `custom/HLX DLSS/dlss/`. Releases ship no NVIDIA files, so the panel only checks whether the **newest** HelixSR release (pre-releases included) is installed, showing releases by their full name (e.g. *HelixSR 3.2.0 (pre-release)*; a zip uploaded again under the same tag shows as *re-uploaded <date>*) and, if not, downloads it (verified against GitHub's SHA256) and runs HelixSR's own setup, which builds the network on the device (about 7–10 minutes on a Steam Deck; downloads NVIDIA's DLSS DLL after you confirm). The build lives in `~/fgmod-helixsr/current` and replaces the older one only once it succeeds. After installing or updating HelixSR, press **Patch All** again.
  - Frame generation is Nukems FG (`FGInput=NvngxFG` + `FGNvngxReplacement=Nukems`). Unpatching removes the `custom/` folders and puts back the previous values. Games patched with an older runtime keep it until they are patched again.
  - FSR 4 can silently fall back to FSR3 on unsupported hardware; set `FSR_Fsr4EnableWatermark=true` to confirm the active path (`FSR4`, `FSR4-i8`, `FSR4L-i8` or `FSR3`).
- **Proton-CachyOS FSR4** toggle: when Steam runs the game with Proton-CachyOS, it adds `FSR4_UPGRADE=1` to the launch options (`FSR4_UPGRADE=1 %command%`); turning it off removes only that. Nothing is downloaded.
- **Show FSR watermark** toggle (below it): adds `PROTON_FSR4_INDICATOR=1`, so AMD's FSR watermark shows top left which FSR runs. Both toggles only show for games Steam runs with Proton-CachyOS or with the Lite toggle on. With OptiScaler, its own watermark is `FSR_Fsr4EnableWatermark=true`.
- **Proton FSR4 → 4.1.2 Lite** toggle (experimental, any Proton, no need to have Proton-CachyOS installed): runs the game with FSR 4.1.2 Lite (`FSR4L-i8`) without OptiScaler. Released Proton-CachyOS ignores a DLL path in `PROTON_FSR4_UPGRADE`, so the toggle installs the newest Proton-CachyOS release (x86_64, about 330 MB, SHA-512 checked) into `compatibilitytools.d` as **Proton-CachyOS … (FSR4 Lite)**, with `protonfixes/upscalers.py` patched to copy that DLL into the prefix. Each time the toggle is turned on it checks Proton-CachyOS's newest release: when it's newer than the copy, it downloads it, patches it the same way and replaces the copy (skipped while a game runs on it; offline, or if the new release can't be patched, the working copy stays). The copy's internal name is always `proton-cachyos-jedi-fsr4lite`, so Steam lists one **Proton-CachyOS … (FSR4 Lite)** and games set to it keep it after an update; its label shows the new release after a Steam restart. The toggle then sets that Proton for the game and adds `PROTON_FSR4_UPGRADE=<Lite DLL>` to the launch options (that Proton turns `FSR4_UPGRADE` on by itself, so **Proton-CachyOS FSR4** and the watermark stay their own toggles). A dialog asks you to check the game's Proton in **Properties → Compatibility**. Steam lists a new Proton only after a restart, so the first time the dialog offers **Restart Steam**, and the plugin sets the Proton by itself when it loads after that restart. Turning it off removes the variable and puts back the game's previous Proton; the copy stays in `compatibilitytools.d/proton-cachyos-jedi-fsr4lite`. Games with native FSR 3.1, DX12 only.
- Per‑game patch/unpatch.
- Default install uses the complete bundled `0.9.4`; Update force‑downloads and verifies the newest upstream archive.

**ReShade**
- ReShade **with add‑on support** (toggle) and optional **AutoHDR** (OLED‑oriented).
- Downloads ReShade from reshade.me with an **installed vs. latest** version widget.
- Shader pack selection (AstrayFX, MartyMcFly, prod80, SweetFX, RetroArch…).
- Per‑game patch/unpatch, with the API auto‑detected.

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

1. **Steam Game — Patch All**: pick a game, (optionally) toggle *ReShade add‑ons*, then press **🚀 Patch All**. It installs OptiScaler and ReShade if they aren't yet, applies both to the game, and sets the launch options automatically. **Remove All** reverts it.
2. In‑game: press **HOME** for the ReShade overlay.

**Advanced controls** (toggle near the top) expose the original per‑engine UIs when you need them:
- OptiScaler: install/uninstall, FSR4 variant, proxy DLL, **Apply only OptiScaler** / **🗑️ Remove only OptiScaler**.
- ReShade: add‑on/AutoHDR toggles, shader pack selection, **Apply only ReShade** / **🗑️ Remove only ReShade**.
- Coexistence / DLL slots: inspect what's active and override the Frame Generation slot per game.

> **Removing one mod keeps the other one working.** OptiScaler's cleanup puts back the game DLLs it had set aside, so **Remove only OptiScaler** re‑links ReShade afterwards; both partial removals then rewrite the launch options for whatever stays behind (and give back your own when nothing does). Removing ReShade also deletes `ReShadePreset.ini`.

> **Patch All puts ReShade on `dxgi`**, which covers DX11/DX12 (most games). For DX9/Vulkan/OpenGL titles, use **Advanced → ReShade**, which auto‑detects the API.

> Auto‑update for OptiScaler is **opt‑in** — set `DECKY_OPTISCALER_AUTO_UPDATE=1`. By default the complete bundled `0.9.4` build is used. An explicit update is downloaded and verified before it replaces the installed bundle.

---

## Building

Requirements: **Node.js ≥ 18** and **pnpm**.

```bash
pnpm install
pnpm build      # outputs dist/index.js
```

The OptiScaler binaries (`bin/`) and ReShade assets are **not committed** — they are listed under `remote_binary` in `package.json` and fetched by Decky's build tooling, or you can drop the OptiScaler runtime files into `bin/` manually for a self‑contained sideload zip.

> **Filesystem note:** pnpm uses symlinks. If your working copy lives on NTFS/exFAT (no symlink support), build in an ext4/`/tmp` location and copy `dist/` back.

---

## Project structure

```
Jedi-ReFrameShade4All/
├─ main.py                  # merged back-end: _OptiScalerMixin + _ReShadeMixin + _HelixSRMixin + _LsfgMixin → Plugin
├─ defaults/py_modules/lsfg_vk/  # LSFG-VK services from Jedi LSFG-VK (MAKO install, profiles, ~/.jedi-lsfg wrapper)
├─ plugin.json              # Decky manifest (name/id: Jedi-ReFrameShade4All)
├─ package.json             # deps + merged remote_binary list
├─ src/                     # React/TSX frontend
│  ├─ index.tsx                     # composes sections, shared FSR4 state, Advanced toggle
│  ├─ SteamGameCombinedSection.tsx  # primary one-button "Patch All" (both mods)
│  ├─ ConflictSlotSection.tsx       # coexistence + manual slot picker (Advanced)
│  ├─ ReShadeInstallerSection.tsx   # "ReShade Management" — install/version/update/add-ons/shaders
│  ├─ ShaderSelectionModal.tsx      # ReShade shader pack picker
│  ├─ components/                   # "Framegen Management" — OptiScalerControls + helpers
│  ├─ api/index.ts                  # typed backend callables
│  └─ utils/, types/               # helpers, constants, type decls
├─ defaults/assets/         # fgmod*.sh + reshade-*.sh install/patch scripts
├─ bin/                     # OptiScaler binaries (gitignored; via remote_binary)
└─ dist/                    # build output (gitignored)
```

The panel is two parallel sections under an **Advanced controls** toggle — **FRAMEGEN MANAGEMENT** (`components/OptiScalerControls.tsx`) and **RESHADE MANAGEMENT** (`ReShadeInstallerSection.tsx`) — each showing install state, version, and *up to date / update available* with an Install/Update button.

**Back‑end architecture:** the two original `main.py` files are combined into one Decky‑safe `Plugin` class using mixins (`_OptiScalerMixin`, `_ReShadeMixin`). Method‑name collisions (`_main`, `_unload`, `list_installed_games`, `log_error`) are resolved in the final `Plugin`, which also adds the one‑button flow (`patch_all_game` / `unpatch_all_game`) and the coexistence layer (`patch_game` slot override, `get_combined_game_status`, `set_slots_manual`). `patch_all_game` applies Frame Generation (winmm) **before** ReShade (dxgi) so OptiScaler's proxy cleanup can't displace ReShade's DLL.

**OptiScaler updates** are *precise*: `get_optiscaler_update_status` compares the **installed archive asset name** (from the install manifest) against the newest GitHub release asset. The **Update** button (`update_optiscaler`) downloads and verifies that archive in a staging directory, then replaces the installed bundle only after validation; plain install/reinstall uses the hash-pinned bundled build.

---

## Safety & disclaimers

- **Anti‑cheat:** ReShade **with add‑ons** can trip anti‑cheat in online games. Use add‑ons only where it's allowed; the toggle ships **off** with a warning.
- **Runtime conflicts:** both mods hook the DXGI swap‑chain (Frame Gen for generation, ReShade for post‑processing). It usually works, but load order can be game‑specific — the manual slot picker is the escape hatch.
- This project ships/manages third‑party binaries (OptiScaler, ReShade, FSR/XeSS/DLSS‑to‑FSR components). Their licenses live in `defaults/assets/licenses/`.

---

## Credits & licenses

- **OptiScaler Frame Generation** — [Decky‑Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen) by xXJSONDeruloXx, and the [OptiScaler](https://github.com/optiscaler/OptiScaler) project.
- **HelixSR runtime** — [HelixSR](https://github.com/lonewolf0622/HelixSR) by lonewolf0622 (HelixSR Freeware License; downloaded unmodified, never bundled). Release check, download, setup and OptiScaler integration ported from [DeckyHelixSRManager](https://github.com/PeroTuncay/DeckyHelixSRManager) by PeroTuncay (The Unlicense).
- **ReShade integration** — [LetMeReShade](https://github.com/itsOwen/LetMeReShade) by itsOwen, and [ReShade](https://reshade.me) by crosire.
- **LSFG-VK** — [Jedi LSFG-VK](https://github.com/sauliiin/Jedi-LSFG-VK), based on [decky-lsfg-vk](https://github.com/xXJSONDeruloXx/decky-lsfg-vk) by Kurt Himebauch (BSD-3-Clause, `defaults/py_modules/lsfg_vk/LICENSE`); [MAKO](https://github.com/eugeniosegala/MAKO) by Eugenio Segala and contributors (GPL-3.0-or-later; MAKO Renderer is downloaded unmodified from its newest release, never bundled); [lsfg-vk](https://lsfg-vk.dev/) by PancakeTAS; and the [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) developers.
- Built on the Decky plugin template.

Both upstream plugins are **BSD‑3‑Clause**; this merge is distributed under the same terms (see `LICENSE`). All trademarks and bundled components belong to their respective owners.
