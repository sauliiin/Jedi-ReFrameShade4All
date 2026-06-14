import { useState } from "react";
import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  showModal
} from "@decky/ui";
import { callable } from "@decky/api";
import ExecutablePathBrowserModal from "./ExecutablePathBrowserModal";
import { autoCopyLaunchCommand, buildLaunchCommand } from "./utils/steam";
import { CopyLaunchButton } from "./components";

interface InstallResponse {
  status: string;
  message?: string;
  output?: string;
  api?: string;
}

interface PathCheckResponse {
  exists: boolean;
  is_addon: boolean;
}

interface FgModPathResponse {
  exists: boolean;
  version?: string | null;
}

const checkFGModPath = callable<[], FgModPathResponse>("check_fgmod_path");
const runInstallFGMod = callable<[string], InstallResponse>("run_install_fgmod");
const runManualPatch = callable<[string, string, string], InstallResponse>("manual_patch_directory");
const runManualUnpatch = callable<[string], InstallResponse>("manual_unpatch_directory");
const checkReShadePath = callable<[], PathCheckResponse>("check_reshade_path");
const runInstallReShade = callable<[boolean, boolean, string[]], InstallResponse>("run_install_reshade");
const installReShadeForManualExe = callable<[string, string, string], InstallResponse>("install_reshade_for_heroic_game");
const uninstallReShadeForManualExe = callable<[string], InstallResponse>("uninstall_reshade_for_heroic_game");
const detectGameApi = callable<[string], InstallResponse>("detect_heroic_game_api");
const logError = callable<[string], void>("log_error");

const getDirectoryForPath = (path: string) => {
  const separatorIndex = path.lastIndexOf("/");
  return separatorIndex > 0 ? path.slice(0, separatorIndex) : path;
};

const getFilenameForPath = (path: string) => path.split("/").pop() || "Unknown.exe";

interface ChooseExePathSectionProps {
  exePath: string;
  setExePath: (path: string) => void;
  fsr4Variant: string;
}

const ChooseExePathSection = ({ exePath, setExePath, fsr4Variant }: ChooseExePathSectionProps) => {
  const [applyingBoth, setApplyingBoth] = useState<boolean>(false);
  const [removingBoth, setRemovingBoth] = useState<boolean>(false);
  const [launchCmd, setLaunchCmd] = useState<string>("");
  const [copyFailed, setCopyFailed] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");

  const handleChooseExecutablePath = async () => {
    try {
      const startPath = exePath ? getDirectoryForPath(exePath) : "/home/deck";
      const modalResult = showModal(
        <ExecutablePathBrowserModal
          initialPath={startPath}
          onConfirm={(path) => {
            // Picking the .exe automatically stores its folder as the OptiScaler target.
            setExePath(path);
            setResult("");
          }}
          onCancel={() => {
            // Modal closes through closeModal.
          }}
          closeModal={() => modalResult.Close()}
        />
      );
    } catch (error) {
      setResult(`Error choosing executable: ${error instanceof Error ? error.message : String(error)}`);
      await logError(`ChooseExePathSection -> handleChooseExecutablePath: ${String(error)}`);
    }
  };

  const handleApplyBoth = async () => {
    if (!exePath) {
      setResult("Please choose a game .exe first.");
      return;
    }

    try {
      setApplyingBoth(true);
      setLaunchCmd("");
      setCopyFailed(false);
      const executableDirectory = getDirectoryForPath(exePath);
      const selectedFilename = getFilenameForPath(exePath);

      // 1. Make sure both engines are installed.
      setResult("Checking engines…");
      const fg = await checkFGModPath();
      if (!fg.exists) {
        setResult("Installing OptiScaler engine…");
        const fgInstall = await runInstallFGMod(fsr4Variant);
        if (fgInstall.status !== "success") {
          setResult(`❌ Failed to install OptiScaler: ${fgInstall.message || "Unknown error"}`);
          return;
        }
      }

      const rs = await checkReShadePath();
      if (!rs.exists) {
        setResult("Installing ReShade engine…");
        const rsInstall = await runInstallReShade(false, false, []);
        if (rsInstall.status !== "success") {
          setResult(`❌ Failed to install ReShade: ${rsInstall.message || "Unknown error"}`);
          return;
        }
      }

      // 2. Frame Generation on winmm.dll (coexists with ReShade on the graphics DLL).
      setResult(`Applying Frame Generation to ${selectedFilename}…`);
      const patch = await runManualPatch(executableDirectory, "winmm.dll", fsr4Variant);
      if (patch.status !== "success") {
        setResult(`❌ Failed to apply Frame Generation: ${patch.message || "Unknown error"}`);
        return;
      }

      // 3. ReShade with the best detected API for this executable.
      setResult("Detecting best ReShade API…");
      const detection = await detectGameApi(executableDirectory);
      const reshadeApi = detection.status === "success" && detection.api ? detection.api : "dxgi";

      setResult(`Applying ReShade (${reshadeApi.toUpperCase()}) to ${selectedFilename}…`);
      const reshade = await installReShadeForManualExe(executableDirectory, reshadeApi, exePath);
      if (reshade.status !== "success") {
        setResult(`❌ Failed to apply ReShade: ${reshade.message || "Unknown error"}`);
        return;
      }

      // 4. Build the combined launch command for non-Steam launchers and copy it.
      const cmd = buildLaunchCommand([reshadeApi, "winmm.dll"], true);
      setLaunchCmd(cmd);
      const copied = await autoCopyLaunchCommand(cmd);
      setCopyFailed(!copied);
      setResult(
        `✅ FrameGen (winmm) + ReShade (${reshadeApi.toUpperCase()}) applied to ${selectedFilename}.\n\n` +
          `Launch command:\n${cmd}\n\n` +
          (copied
            ? "Launch options copied automatically — paste them into your launcher.\n"
            : '⚠️ Could not copy automatically. Press "Copy launch options" below.\n') +
          "Press HOME in-game for the ReShade overlay or INSERT for OptiScaler."
      );
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
      await logError(`ChooseExePathSection -> handleApplyBoth: ${String(error)}`);
    } finally {
      setApplyingBoth(false);
    }
  };

  const handleRemoveBoth = async () => {
    if (!exePath) {
      setResult("Please choose a game .exe first.");
      return;
    }

    try {
      setRemovingBoth(true);
      setLaunchCmd("");
      setCopyFailed(false);
      const executableDirectory = getDirectoryForPath(exePath);
      const selectedFilename = getFilenameForPath(exePath);

      setResult(`Removing FrameGen + ReShade from ${selectedFilename}…`);
      const unpatch = await runManualUnpatch(executableDirectory);
      const reshadeRemove = await uninstallReShadeForManualExe(executableDirectory);

      const okOpti = unpatch.status === "success";
      const okReshade = reshadeRemove.status === "success";

      if (okOpti && okReshade) {
        setResult(
          `✅ Frame Generation + ReShade removed from ${selectedFilename}.\n\n` +
            "Remember to clear the launch command from your launcher."
        );
      } else {
        setResult(
          "⚠️ Partial removal:\n" +
            `• Frame Generation: ${okOpti ? "removed" : unpatch.message || "failed"}\n` +
            `• ReShade: ${okReshade ? "removed" : reshadeRemove.message || "failed"}`
        );
      }
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
      await logError(`ChooseExePathSection -> handleRemoveBoth: ${String(error)}`);
    } finally {
      setRemovingBoth(false);
    }
  };

  return (
    <PanelSection title="Choose exe/folder path">
      <PanelSectionRow>
        <div style={{ fontSize: "0.9em", opacity: 0.8 }}>
          Patch any Windows game executable manually. This is ideal for non-Steam launchers and custom setups.
          {" "}Browse to the game folder first, then pick the `.exe`.
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={handleChooseExecutablePath}>
          📁 Choose exe/folder path
        </ButtonItem>
      </PanelSectionRow>

      {exePath && (
        <>
          <PanelSectionRow>
            <div
              style={{
                padding: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.05)",
                borderRadius: "4px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                fontSize: "0.85em"
              }}
            >
              <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                Selected: {getFilenameForPath(exePath)}
              </div>
              <div style={{ opacity: 0.75, wordBreak: "break-all" }}>
                Path: {exePath}
              </div>
            </div>
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleApplyBoth} disabled={applyingBoth || removingBoth}>
              {applyingBoth ? "Applying…" : "Apply both (FrameGen + ReShade)"}
            </ButtonItem>
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleRemoveBoth} disabled={applyingBoth || removingBoth}>
              {removingBoth ? "Removing…" : "🗑️ Remove All"}
            </ButtonItem>
          </PanelSectionRow>
        </>
      )}

      {result && (
        <PanelSectionRow>
          <div
            style={{
              padding: "12px",
              marginTop: "16px",
              backgroundColor: "var(--decky-selected-ui-bg)",
              borderRadius: "4px",
              whiteSpace: "pre-wrap"
            }}
          >
            {result}
          </div>
        </PanelSectionRow>
      )}

      {copyFailed && <CopyLaunchButton command={launchCmd} />}
    </PanelSection>
  );
};

export default ChooseExePathSection;
