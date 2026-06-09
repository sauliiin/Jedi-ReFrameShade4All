import { useEffect, useState } from "react";
import { ButtonItem, DropdownItem, PanelSection, PanelSectionRow, ToggleField } from "@decky/ui";
import { callable } from "@decky/api";

const listInstalledGames = callable<
  [],
  { status: string; games: { appid: string; name: string }[] }
>("list_installed_games");

const getEnginesStatus = callable<
  [],
  {
    status: string;
    optiscaler_installed?: boolean;
    optiscaler_version?: string | null;
    reshade_installed?: boolean;
    reshade_version?: string | null;
  }
>("get_engines_status");

const getCombinedGameStatus = callable<
  [appid: string],
  {
    status: string;
    optiscaler_patched?: boolean;
    optiscaler_slot?: string | null;
    reshade_present?: boolean;
    reshade_slot?: string | null;
    both_active?: boolean;
  }
>("get_combined_game_status");

const patchAllGame = callable<
  [appid: string, fsr4_variant: string, with_reshade_addon: boolean, current_launch_options: string],
  { status: string; message?: string; launch_options?: string; name?: string }
>("patch_all_game");

const unpatchAllGame = callable<
  [appid: string],
  { status: string; message?: string; launch_options?: string; name?: string }
>("unpatch_all_game");

const logError = callable<[string], void>("log_error");

const FSR4_OPTIONS = [
  { data: "rdna23-int8", label: "Steam Deck / RDNA2-3 (recommended)" },
  { data: "rdna4-native", label: "RDNA4 native" },
];

type Engines = {
  optiscaler_installed?: boolean;
  optiscaler_version?: string | null;
  reshade_installed?: boolean;
  reshade_version?: string | null;
};

type GameStatus = {
  optiscaler_patched?: boolean;
  optiscaler_slot?: string | null;
  reshade_present?: boolean;
  reshade_slot?: string | null;
  both_active?: boolean;
};

function getLaunchOptions(appId: number): Promise<string> {
  return new Promise((resolve) => {
    try {
      const reg = SteamClient.Apps.RegisterForAppDetails(appId, (details: { strLaunchOptions?: string }) => {
        resolve(details?.strLaunchOptions || "");
        try {
          reg.unregister();
        } catch {
          /* noop */
        }
      });
      setTimeout(() => {
        try {
          reg.unregister();
        } catch {
          /* noop */
        }
        resolve("");
      }, 1500);
    } catch {
      resolve("");
    }
  });
}

export default function SteamGameCombinedSection() {
  const [games, setGames] = useState<{ appid: string; name: string }[]>([]);
  const [appid, setAppid] = useState<string>("");
  const [engines, setEngines] = useState<Engines | null>(null);
  const [status, setStatus] = useState<GameStatus | null>(null);
  const [variant, setVariant] = useState<string>("rdna23-int8");
  const [addon, setAddon] = useState<boolean>(true);
  const [busy, setBusy] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");

  const refreshEngines = async () => {
    try {
      setEngines(await getEnginesStatus());
    } catch (e) {
      await logError(`SteamGameCombinedSection -> engines: ${String(e)}`);
    }
  };

  const loadStatus = async (id: string) => {
    try {
      setStatus(await getCombinedGameStatus(id));
    } catch (e) {
      await logError(`SteamGameCombinedSection -> status: ${String(e)}`);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const r = await listInstalledGames();
        if (r.status === "success") setGames(r.games || []);
      } catch (e) {
        await logError(`SteamGameCombinedSection -> list: ${String(e)}`);
      }
    })();
    void refreshEngines();
  }, []);

  const handlePatchAll = async () => {
    if (!appid) {
      setResult("Select a game first.");
      return;
    }
    try {
      setBusy(true);
      setResult("Patching… installing OptiScaler/ReShade if needed — this can take a while.");
      const current = await getLaunchOptions(parseInt(appid, 10));
      const r = await patchAllGame(appid, variant, addon, current);
      if (r.status === "success") {
        if (r.launch_options) {
          try {
            SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), r.launch_options);
          } catch (e) {
            await logError(`SetAppLaunchOptions: ${String(e)}`);
          }
        }
        setResult(`✅ ${r.message || "Done"}${r.launch_options ? `\n\nLaunch options set automatically:\n${r.launch_options}` : ""}`);
      } else {
        setResult(`❌ ${r.message || "Failed"}`);
      }
      await refreshEngines();
      await loadStatus(appid);
    } catch (e) {
      setResult(`❌ ${String(e)}`);
      await logError(`SteamGameCombinedSection -> patchAll: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  };

  const handleRemoveAll = async () => {
    if (!appid) {
      setResult("Select a game first.");
      return;
    }
    try {
      setBusy(true);
      setResult("Removing both mods…");
      const r = await unpatchAllGame(appid);
      if (r.status === "success") {
        try {
          SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), r.launch_options || "");
        } catch (e) {
          await logError(`SetAppLaunchOptions(remove): ${String(e)}`);
        }
        setResult(`✅ ${r.message || "Removed"}`);
      } else {
        setResult(`❌ ${r.message || "Failed"}`);
      }
      await loadStatus(appid);
    } catch (e) {
      setResult(`❌ ${String(e)}`);
      await logError(`SteamGameCombinedSection -> removeAll: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PanelSection title="🎮 Steam Game — Patch All">
      <PanelSectionRow>
        <div style={{ fontSize: "0.9em", opacity: 0.85 }}>
          Pick a Steam game and press <b>Patch All</b>. It installs OptiScaler (Frame Generation) and ReShade
          if needed, applies both to the game, and sets the launch options for you.
        </div>
      </PanelSectionRow>

      {engines && (
        <PanelSectionRow>
          <div style={{ fontSize: "0.82em", opacity: 0.7 }}>
            {engines.optiscaler_installed ? `🟢 OptiScaler ${engines.optiscaler_version || ""}` : "⚪ OptiScaler not installed"}
            {"  •  "}
            {engines.reshade_installed ? `🟢 ReShade ${engines.reshade_version || ""}` : "⚪ ReShade not installed"}
          </div>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <DropdownItem
          rgOptions={games.map((g) => ({ data: g.appid, label: g.name }))}
          selectedOption={appid}
          onChange={(o) => {
            setAppid(o.data as string);
            setResult("");
            void loadStatus(o.data as string);
          }}
          strDefaultLabel="Select a game..."
        />
      </PanelSectionRow>

      {status && appid && (
        <PanelSectionRow>
          <div style={{ fontSize: "0.85em", padding: "8px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
            <div>Frame Generation: {status.optiscaler_patched ? `on (${status.optiscaler_slot})` : "off"}</div>
            <div>ReShade: {status.reshade_present ? `on (${status.reshade_slot})` : "off"}</div>
            {status.both_active && <div style={{ color: "green", marginTop: "2px" }}>✅ Both active and coexisting</div>}
          </div>
        </PanelSectionRow>
      )}

      {appid && (
        <>
          <PanelSectionRow>
            <DropdownItem
              label="FSR4 runtime"
              rgOptions={FSR4_OPTIONS}
              selectedOption={variant}
              onChange={(o) => setVariant(o.data as string)}
              strDefaultLabel="FSR4 runtime"
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ToggleField
              label="ReShade add-ons"
              description="Enables add-on support (avoid in anti-cheat online games)."
              checked={addon}
              onChange={setAddon}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handlePatchAll} disabled={busy}>
              {busy ? "Working…" : "🚀 Patch All (Frame Gen + ReShade)"}
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleRemoveAll} disabled={busy}>
              🗑️ Remove All
            </ButtonItem>
          </PanelSectionRow>
        </>
      )}

      {result && (
        <PanelSectionRow>
          <div
            style={{
              padding: "12px",
              marginTop: "8px",
              backgroundColor: "var(--decky-selected-ui-bg)",
              borderRadius: "4px",
              whiteSpace: "pre-wrap",
              fontSize: "0.85em",
            }}
          >
            {result}
          </div>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <div style={{ fontSize: "0.8em", opacity: 0.6 }}>In-game: press HOME for the ReShade overlay.</div>
      </PanelSectionRow>
    </PanelSection>
  );
}
