import { useState } from "react";
import {
  ButtonItem,
  ConfirmModal,
  DropdownItem,
  PanelSection,
  PanelSectionRow,
  showModal
} from "@decky/ui";
import { callable } from "@decky/api";
import ExecutablePathBrowserModal from "./ExecutablePathBrowserModal";

interface DllOverride {
  label: string;
  value: string;
}

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

const DLL_OVERRIDES: DllOverride[] = [
  { label: "Automatic (Detect API)", value: "auto" },
  { label: "DXGI (DirectX 10/11/12)", value: "dxgi" },
  { label: "D3D9 (DirectX 9)", value: "d3d9" },
  { label: "D3D8 (DirectX 8)", value: "d3d8" },
  { label: "D3D11 (DirectX 11)", value: "d3d11" },
  { label: "DDraw (DirectDraw)", value: "ddraw" },
  { label: "DInput8 (DirectInput)", value: "dinput8" },
  { label: "OpenGL32 (OpenGL)", value: "opengl32" }
];

const installReShadeForManualExe = callable<[string, string, string], InstallResponse>("install_reshade_for_heroic_game");
const uninstallReShadeForManualExe = callable<[string], InstallResponse>("uninstall_reshade_for_heroic_game");
const detectGameApi = callable<[string], InstallResponse>("detect_heroic_game_api");
const checkReShadePath = callable<[], PathCheckResponse>("check_reshade_path");
const logError = callable<[string], void>("log_error");

const getDirectoryForPath = (path: string) => {
  const separatorIndex = path.lastIndexOf("/");
  return separatorIndex > 0 ? path.slice(0, separatorIndex) : path;
};

const getFilenameForPath = (path: string) => path.split("/").pop() || "Unknown.exe";

const ChooseExePathSection = () => {
  const [selectedExecutablePath, setSelectedExecutablePath] = useState<string>("");
  const [selectedDll, setSelectedDll] = useState<DllOverride>(DLL_OVERRIDES[0]);
  const [apiDetecting, setApiDetecting] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");

  const handleChooseExecutablePath = async () => {
    try {
      const startPath = selectedExecutablePath ? getDirectoryForPath(selectedExecutablePath) : "/home/deck";
      const modalResult = showModal(
        <ExecutablePathBrowserModal
          initialPath={startPath}
          onConfirm={(path) => {
            setSelectedExecutablePath(path);
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

  const handleInstallReShade = async () => {
    if (!selectedExecutablePath) {
      setResult("Please choose a Windows executable first.");
      return;
    }

    try {
      const reshadeCheck = await checkReShadePath();
      if (!reshadeCheck.exists) {
        setResult("Please install ReShade first before patching games.");
        return;
      }

      const executableDirectory = getDirectoryForPath(selectedExecutablePath);
      let finalDllOverride = selectedDll.value;

      if (finalDllOverride === "auto") {
        setApiDetecting(true);
        setResult("Detecting best API for the selected executable...");

        const detectionResponse = await detectGameApi(executableDirectory);
        if (detectionResponse.status === "success" && detectionResponse.api) {
          finalDllOverride = detectionResponse.api;
          setResult(`Detected ${finalDllOverride.toUpperCase()} as the best API.`);
        } else {
          finalDllOverride = "dxgi";
          setResult(`API detection failed: ${detectionResponse.message || "Unknown error"}. Using DXGI as fallback.`);
        }

        setApiDetecting(false);
      }

      const selectedFilename = getFilenameForPath(selectedExecutablePath);
      const launchOverride = `WINEDLLOVERRIDES="d3dcompiler_47=n;${finalDllOverride}=n,b"`;

      showModal(
        <ConfirmModal
          strTitle="Confirm Manual Patch"
          strDescription={`Install ReShade to ${selectedFilename} with ${finalDllOverride.toUpperCase()}?\n\nPath: ${selectedExecutablePath}`}
          strOKButtonText="Install"
          strCancelButtonText="Cancel"
          onOK={async () => {
            setResult("Installing ReShade...");

            const installResponse = await installReShadeForManualExe(
              executableDirectory,
              finalDllOverride,
              selectedExecutablePath
            );

            if (installResponse.status !== "success") {
              setResult(`Failed to install ReShade: ${installResponse.message || "Unknown error"}`);
              return;
            }

            setResult(
              `ReShade installed successfully to ${selectedFilename} with ${finalDllOverride.toUpperCase()} API.\n` +
              `If this game is launched outside Steam, add ${launchOverride} to the launcher environment.\n` +
              "Press HOME key in-game to open ReShade overlay."
            );
          }}
        />
      );
    } catch (error) {
      setApiDetecting(false);
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
      await logError(`ChooseExePathSection -> handleInstallReShade: ${String(error)}`);
    }
  };

  const handleUninstallReShade = async () => {
    if (!selectedExecutablePath) {
      setResult("Please choose a Windows executable first.");
      return;
    }

    try {
      const reshadeCheck = await checkReShadePath();
      if (!reshadeCheck.exists) {
        setResult("ReShade is not installed.");
        return;
      }

      const executableDirectory = getDirectoryForPath(selectedExecutablePath);
      const selectedFilename = getFilenameForPath(selectedExecutablePath);

      showModal(
        <ConfirmModal
          strTitle="Confirm Manual Uninstall"
          strDescription={`Remove ReShade from ${selectedFilename}?\n\nPath: ${selectedExecutablePath}`}
          strOKButtonText="Uninstall"
          strCancelButtonText="Cancel"
          onOK={async () => {
            setResult("Uninstalling ReShade...");

            const uninstallResponse = await uninstallReShadeForManualExe(executableDirectory);
            if (uninstallResponse.status !== "success") {
              setResult(`Failed to uninstall ReShade: ${uninstallResponse.message || "Unknown error"}`);
              return;
            }

            setResult(`ReShade uninstalled successfully from ${selectedFilename}.`);
          }}
        />
      );
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
      await logError(`ChooseExePathSection -> handleUninstallReShade: ${String(error)}`);
    }
  };

  return (
    <PanelSection title="Choose exe path">
      <PanelSectionRow>
        <div style={{ fontSize: "0.9em", opacity: 0.8 }}>
          Patch any Windows game executable manually. This is ideal for non-Steam launchers and custom setups.
          {" "}Browse to the game folder first, then pick the `.exe`.
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={handleChooseExecutablePath}>
          📁 Choose exe path
        </ButtonItem>
      </PanelSectionRow>

      {selectedExecutablePath && (
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
                Selected: {getFilenameForPath(selectedExecutablePath)}
              </div>
              <div style={{ opacity: 0.75, wordBreak: "break-all" }}>
                Path: {selectedExecutablePath}
              </div>
            </div>
          </PanelSectionRow>

          <PanelSectionRow>
            <DropdownItem
              rgOptions={DLL_OVERRIDES.map((dll) => ({
                data: dll.value,
                label: dll.label
              }))}
              selectedOption={selectedDll.value}
              onChange={(option) => {
                const nextSelection = DLL_OVERRIDES.find((dll) => dll.value === option.data);
                if (nextSelection) {
                  setSelectedDll(nextSelection);
                  setResult("");
                }
              }}
              strDefaultLabel="Select DLL override..."
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleInstallReShade} disabled={apiDetecting}>
              {apiDetecting ? "Detecting API..." : "🔧 Install ReShade"}
            </ButtonItem>
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleUninstallReShade}>
              🗑️ Uninstall ReShade
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
    </PanelSection>
  );
};

export default ChooseExePathSection;
