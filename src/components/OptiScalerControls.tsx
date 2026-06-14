import { useState, useEffect } from "react";
import { ButtonItem, DropdownItem, PanelSection, PanelSectionRow } from "@decky/ui";
import {
  runInstallFGMod,
  runUninstallFGMod,
  updateOptiScaler,
  getOptiScalerUpdateStatus,
  patchGame,
  runManualPatch,
} from "../api";
import { createAutoCleanupTimer } from "../utils";
import { buildLaunchCommand, copyTextToClipboard, getLaunchOptions, setLaunchOptions } from "../utils/steam";
import { TIMEOUTS, PROXY_DLL_OPTIONS, DEFAULT_PROXY_DLL, DEFAULT_FSR4_VARIANT } from "../utils/constants";
import { InstructionCard } from "./InstructionCard";
import { UninstallButton } from "./UninstallButton";

interface FgmodInfo {
  exists: boolean;
  version?: string | null;
  selected_fsr4_variant?: string | null;
  selected_fsr4_variant_label?: string | null;
  install_manifest_present?: boolean;
}

interface UpdateStatus {
  status: string;
  installed_version?: string | null;
  latest_version?: string | null;
  update_available?: boolean;
  message?: string;
}

interface OptiScalerControlsProps {
  pathExists: boolean | null;
  setPathExists?: (exists: boolean | null) => void;
  fgmodInfo?: FgmodInfo | null;
  // FSR4 runtime is chosen in the top "Steam Game — Patch All" section and shared here.
  fsr4Variant?: string;
  // A Steam game picked at the top switches "Apply only OptiScaler" to patch that game.
  appid?: string;
  // Otherwise the chosen non-Steam .exe path is used (folder is derived from it).
  targetExePath?: string;
}

const folderForExe = (exePath: string) => {
  const idx = exePath.lastIndexOf("/");
  return idx > 0 ? exePath.slice(0, idx) : exePath;
};

export function OptiScalerControls({
  pathExists,
  setPathExists,
  fgmodInfo,
  fsr4Variant = DEFAULT_FSR4_VARIANT,
  appid = "",
  targetExePath = "",
}: OptiScalerControlsProps) {
  const [installing, setInstalling] = useState(false);
  const [uninstalling, setUninstalling] = useState(false);
  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<string>("");
  const [dllName, setDllName] = useState<string>(DEFAULT_PROXY_DLL);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);

  const steamMode = Boolean(appid);
  const targetFolder = targetExePath ? folderForExe(targetExePath) : "";

  const refreshUpdateStatus = async () => {
    try {
      setUpdateStatus(await getOptiScalerUpdateStatus());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    void refreshUpdateStatus();
  }, [pathExists]);

  useEffect(() => {
    if (result) {
      return createAutoCleanupTimer(() => setResult(""), TIMEOUTS.resultDisplay);
    }
    return () => {};
  }, [result]);

  const handleInstallOrUpdate = async () => {
    try {
      setInstalling(true);
      const doUpdate = pathExists === true && Boolean(updateStatus?.update_available);
      setResult(doUpdate ? "Updating OptiScaler…" : "Installing OptiScaler…");
      const r = doUpdate ? await updateOptiScaler(fsr4Variant) : await runInstallFGMod(fsr4Variant);
      setResult(r.status === "success" ? `✅ ${r.output || r.message || "Done"}` : `❌ ${r.message || "Failed"}`);
      if (r.status === "success") {
        setPathExists?.(true);
        await refreshUpdateStatus();
      }
    } catch (e) {
      setResult(`❌ ${String(e)}`);
      console.error(e);
    } finally {
      setInstalling(false);
    }
  };

  const handleApplyOnlyOpti = async () => {
    try {
      setApplying(true);
      if (steamMode) {
        setResult("Applying OptiScaler to the selected Steam game…");
        const current = await getLaunchOptions(parseInt(appid, 10));
        const r = await patchGame(appid, dllName, current, fsr4Variant);
        if (r.status === "success") {
          if (r.launch_options) {
            try {
              setLaunchOptions(parseInt(appid, 10), r.launch_options);
            } catch (e) {
              console.error(e);
            }
          }
          setResult(
            `✅ ${r.message || "OptiScaler applied."}` +
              (r.launch_options ? `\n\nLaunch options set automatically:\n${r.launch_options}` : "")
          );
        } else {
          setResult(`❌ ${r.message || "Failed"}`);
        }
      } else {
        if (!targetFolder) {
          setResult('Choose a game .exe in "Choose exe/folder path" above first.');
          return;
        }
        setResult("Applying OptiScaler to the selected folder…");
        const r = await runManualPatch(targetFolder, dllName, fsr4Variant);
        if (r.status === "success") {
          const cmd = buildLaunchCommand([dllName]);
          const copied = await copyTextToClipboard(cmd);
          setResult(
            `✅ ${r.message || r.output || "OptiScaler applied."}\n\n` +
              `Launch command ${copied ? "copied to clipboard" : "(copy it manually)"}:\n${cmd}`
          );
        } else {
          setResult(`❌ ${r.message || "Failed"}`);
        }
      }
    } catch (e) {
      setResult(`❌ ${String(e)}`);
      console.error(e);
    } finally {
      setApplying(false);
    }
  };

  const handleUninstallClick = async () => {
    try {
      setUninstalling(true);
      const r = await runUninstallFGMod();
      setResult(r.status === "success" ? "✅ OptiScaler removed." : `❌ ${r.message || "Failed"}`);
      if (r.status === "success") {
        setPathExists?.(false);
        setUpdateStatus(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setUninstalling(false);
    }
  };

  const installButtonText = installing
    ? "Working…"
    : pathExists === true
      ? updateStatus?.update_available
        ? "🔧 Update OptiScaler"
        : "🔧 Reinstall OptiScaler"
      : "🔧 Install OptiScaler";

  return (
    <PanelSection title="Framegen Management">
      {pathExists !== null && (
        <PanelSectionRow>
          <div style={{ color: pathExists ? "green" : "red" }}>
            {pathExists ? (
              <>
                🟢 OptiScaler Is Installed
                {fgmodInfo?.version && (
                  <div style={{ fontSize: "0.9em", opacity: 0.8, marginTop: "4px" }}>
                    Installed version: {fgmodInfo.version}
                  </div>
                )}
                {updateStatus?.status === "success" && updateStatus.latest_version && (
                  <div style={{ fontSize: "0.85em", opacity: 0.7, marginTop: "2px" }}>
                    Latest upstream: {updateStatus.latest_version}
                    {updateStatus.update_available ? " (update available)" : " (up to date)"}
                  </div>
                )}
              </>
            ) : (
              "🔴 OptiScaler Not Installed"
            )}
          </div>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={handleInstallOrUpdate} disabled={installing}>
          {installButtonText}
        </ButtonItem>
      </PanelSectionRow>

      {pathExists === true && (
        <>
          <PanelSectionRow>
            <DropdownItem
              layout="below"
              label="Proxy DLL name"
              description={PROXY_DLL_OPTIONS.find((o) => o.value === dllName)?.hint}
              menuLabel="Proxy DLL name"
              selectedOption={dllName}
              rgOptions={PROXY_DLL_OPTIONS.map((o) => ({ data: o.value, label: o.label }))}
              onChange={(option) => setDllName(String(option.data))}
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={handleApplyOnlyOpti}
              disabled={applying || (!steamMode && !targetFolder)}
            >
              {applying ? "Applying…" : "Apply only OptiScaler"}
            </ButtonItem>
          </PanelSectionRow>

          {!steamMode && !targetFolder && (
            <PanelSectionRow>
              <div style={{ fontSize: "0.85em", opacity: 0.7 }}>
                Choose a game .exe in "Choose exe/folder path" above first.
              </div>
            </PanelSectionRow>
          )}
        </>
      )}

      <InstructionCard pathExists={pathExists} />

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

      <UninstallButton
        pathExists={pathExists}
        uninstalling={uninstalling}
        onUninstallClick={handleUninstallClick}
      />
    </PanelSection>
  );
}
