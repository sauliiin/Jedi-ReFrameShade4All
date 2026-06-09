import { useEffect, useState } from "react";
import { ButtonItem, DropdownItem, PanelSection, PanelSectionRow } from "@decky/ui";
import { callable } from "@decky/api";

const getCombinedGameStatus = callable<
  [appid: string],
  {
    status: string;
    name?: string;
    optiscaler_patched?: boolean;
    optiscaler_slot?: string | null;
    reshade_present?: boolean;
    reshade_slot?: string | null;
    both_active?: boolean;
    target_dir?: string | null;
  }
>("get_combined_game_status");

const setSlotsManual = callable<
  [appid: string, optiscaler_slot: string, fsr4_variant: string, current_launch_options: string],
  { status: string; message?: string; output?: string; launch_options?: string; coexist_with_reshade?: boolean }
>("set_slots_manual");

const logError = callable<[string], void>("log_error");

type CombinedStatus = {
  optiscaler_patched?: boolean;
  optiscaler_slot?: string | null;
  reshade_present?: boolean;
  reshade_slot?: string | null;
  both_active?: boolean;
};

const OPTISCALER_SLOTS = [
  { data: "winmm.dll", label: "winmm (recommended — avoids ReShade)" },
  { data: "version.dll", label: "version" },
  { data: "dbghelp.dll", label: "dbghelp" },
  { data: "wininet.dll", label: "wininet" },
  { data: "winhttp.dll", label: "winhttp" },
  { data: "dxgi.dll", label: "dxgi (⚠️ conflicts with ReShade)" },
];

export default function ConflictSlotSection({
  appid,
  fsr4Variant,
}: {
  appid: string;
  fsr4Variant: string;
}) {
  const [status, setStatus] = useState<CombinedStatus | null>(null);
  const [slot, setSlot] = useState<string>("winmm.dll");
  const [busy, setBusy] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");

  const loadStatus = async (id: string) => {
    try {
      const s = await getCombinedGameStatus(id);
      setStatus(s);
      if (s.optiscaler_slot) setSlot(s.optiscaler_slot);
    } catch (e) {
      await logError(`ConflictSlotSection -> status: ${String(e)}`);
    }
  };

  // The game is chosen once in "Steam Game — Patch All"; this section just reuses it.
  useEffect(() => {
    if (appid) {
      void loadStatus(appid);
    } else {
      setStatus(null);
    }
  }, [appid]);

  const handleApply = async () => {
    if (!appid) {
      setResult('Pick a game in "Steam Game — Patch All" above first.');
      return;
    }
    try {
      setBusy(true);
      setResult("Applying Frame Generation slot...");
      const r = await setSlotsManual(appid, slot, fsr4Variant, "");
      setResult(
        r.status === "success"
          ? `✅ ${r.output || r.message || "Applied"}${r.launch_options ? `\nLaunch options: ${r.launch_options}` : ""}`
          : `❌ ${r.message || "Failed"}`
      );
      await loadStatus(appid);
    } catch (e) {
      setResult(`❌ ${String(e)}`);
      await logError(`ConflictSlotSection -> apply: ${String(e)}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PanelSection title="Coexistence / DLL slots">
      <PanelSectionRow>
        <div style={{ fontSize: "0.9em", opacity: 0.8 }}>
          By default ReShade uses the graphics DLL (dxgi) and Frame Generation uses winmm, so both run
          together automatically. Use this only to change the Frame Generation slot for the game selected
          above in "Steam Game — Patch All".
        </div>
      </PanelSectionRow>

      {!appid && (
        <PanelSectionRow>
          <div style={{ fontSize: "0.85em", opacity: 0.7 }}>
            Pick a game in "Steam Game — Patch All" above first.
          </div>
        </PanelSectionRow>
      )}

      {appid && status && (
        <PanelSectionRow>
          <div
            style={{
              fontSize: "0.85em",
              padding: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.05)",
              borderRadius: "4px",
            }}
          >
            <div>Frame Generation: {status.optiscaler_patched ? `on (${status.optiscaler_slot})` : "off"}</div>
            <div>ReShade: {status.reshade_present ? `on (${status.reshade_slot})` : "off"}</div>
            {status.both_active && (
              <div style={{ color: "green", marginTop: "2px" }}>✅ Both active and coexisting</div>
            )}
          </div>
        </PanelSectionRow>
      )}

      {appid && (
        <>
          <PanelSectionRow>
            <DropdownItem
              rgOptions={OPTISCALER_SLOTS}
              selectedOption={slot}
              onChange={(o) => setSlot(o.data as string)}
              strDefaultLabel="Frame Generation DLL slot"
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleApply} disabled={busy}>
              {busy ? "Applying..." : "🔧 Apply Frame Generation slot"}
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
            }}
          >
            {result}
          </div>
        </PanelSectionRow>
      )}
    </PanelSection>
  );
}
