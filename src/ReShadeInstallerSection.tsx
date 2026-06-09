import { useEffect, useState } from "react";
import {
  ButtonItem,
  ConfirmModal,
  PanelSection,
  PanelSectionRow,
  ToggleField,
  showModal
} from "@decky/ui";
import { callable } from "@decky/api";
import ShaderSelectionModal from "./ShaderSelectionModal";

interface InstallResult {
  status: string;
  message?: string;
  output?: string;
}

interface PathCheckResponse {
  exists: boolean;
  is_addon: boolean;
  version_info?: {
    version: string;
    addon: boolean;
  };
}

interface UpdateStatusResponse {
  status: string;
  installed_version?: string;
  latest_version?: string;
  update_available?: boolean;
  message?: string;
}

interface DeckModelResponse {
  status: string;
  model: string;
  is_oled: boolean;
  message?: string;
}

const runInstallReShade = callable<[boolean, boolean, string[]], InstallResult>("run_install_reshade");
const runUninstallReShade = callable<[], InstallResult>("run_uninstall_reshade");
const checkReShadePath = callable<[], PathCheckResponse>("check_reshade_path");
const getReShadeUpdateStatus = callable<[boolean], UpdateStatusResponse>("get_reshade_update_status");
const detectSteamDeckModel = callable<[], DeckModelResponse>("detect_steam_deck_model");
const logError = callable<[string], void>("log_error");
const saveShaderPreferences = callable<[string[]], InstallResult>("save_shader_preferences");
const loadShaderPreferences = callable<[], any>("load_shader_preferences");
const hasShaderPreferences = callable<[], any>("has_shader_preferences");
const saveAutoHdrPreference = callable<[boolean], InstallResult>("save_autohdr_preference");
const loadAutoHdrPreference = callable<[], any>("load_autohdr_preference");
const loadInstalledConfiguration = callable<[], any>("load_installed_configuration");

function ReShadeInstallerSection() {
  const [installing, setInstalling] = useState<boolean>(false);
  const [uninstalling, setUninstalling] = useState<boolean>(false);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [uninstallResult, setUninstallResult] = useState<InstallResult | null>(null);
  const [pathExists, setPathExists] = useState<boolean | null>(null);
  const [addonEnabled, setAddonEnabled] = useState<boolean>(false);
  const [autoHdrEnabled, setAutoHdrEnabled] = useState<boolean>(false);
  const [currentVersionInfo, setCurrentVersionInfo] = useState<{ version: string; addon: boolean } | null>(null);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatusResponse | null>(null);
  const [initialLoad, setInitialLoad] = useState<boolean>(true);
  const [showingAddonDialog, setShowingAddonDialog] = useState<boolean>(false);
  const [pendingAddonState, setPendingAddonState] = useState<boolean>(false);
  const [deckModel, setDeckModel] = useState<DeckModelResponse | null>(null);
  const [modelLoading, setModelLoading] = useState<boolean>(true);
  const [installedConfig, setInstalledConfig] = useState<any>(null);
  const [configChanged, setConfigChanged] = useState<boolean>(false);
  const [hasPreferences, setHasPreferences] = useState<boolean>(false);
  const [preferencesInfo, setPreferencesInfo] = useState<any>(null);

  const refreshLocalInstallState = async (syncAddonState = false) => {
    try {
      const result = await checkReShadePath();
      setPathExists(result.exists);
      setCurrentVersionInfo(result.exists ? result.version_info || null : null);

      if (syncAddonState) {
        setAddonEnabled(result.is_addon);
      }

      return result;
    } catch (e) {
      await logError(`refreshLocalInstallState: ${String(e)}`);
      return null;
    }
  };

  const refreshInstalledConfig = async (installExists: boolean | null = pathExists) => {
    try {
      if (installExists === false) {
        setInstalledConfig(null);
        return;
      }

      const result = await loadInstalledConfiguration();
      if (result.status === "success") {
        setInstalledConfig(result.config || null);
      } else {
        setInstalledConfig(null);
      }
    } catch (e) {
      setInstalledConfig(null);
      await logError(`Error loading installed configuration: ${String(e)}`);
    }
  };

  const refreshUpdateState = async (withAddon: boolean) => {
    try {
      const result = await getReShadeUpdateStatus(withAddon);
      setUpdateStatus(result);
    } catch (e) {
      setUpdateStatus({
        status: "error",
        message: String(e)
      });
      await logError(`Error loading update status: ${String(e)}`);
    }
  };

  const refreshPostInstallState = async (withAddon: boolean) => {
    const localState = await refreshLocalInstallState();
    await refreshInstalledConfig(localState?.exists ?? null);
    await refreshUpdateState(withAddon);
  };

  useEffect(() => {
    let isMounted = true;

    const checkPath = async (syncAddonState = false) => {
      try {
        const result = await checkReShadePath();
        if (!isMounted) return;

        setPathExists(result.exists);
        setCurrentVersionInfo(result.exists ? result.version_info || null : null);

        if (syncAddonState) {
          setAddonEnabled(result.is_addon);
        }
      } catch (e) {
        await logError(`useEffect -> checkPath: ${String(e)}`);
      }
    };

    checkPath(true).finally(() => {
      if (isMounted) {
        setInitialLoad(false);
      }
    });

    const intervalId = setInterval(() => {
      void checkPath(false);
    }, 3000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const detectDeckModelInfo = async () => {
      try {
        setModelLoading(true);
        const result = await detectSteamDeckModel();
        setDeckModel(result);
      } catch (e) {
        await logError(`Steam Deck model detection error: ${String(e)}`);
      } finally {
        setModelLoading(false);
      }
    };

    detectDeckModelInfo();
  }, []);

  useEffect(() => {
    const checkPreferences = async () => {
      try {
        const result = await hasShaderPreferences();
        if (result.status === "success") {
          setHasPreferences(result.has_preferences);
          setPreferencesInfo(result);
        }
      } catch (e) {
        await logError(`Error checking shader preferences: ${String(e)}`);
      }
    };

    checkPreferences();
  }, []);

  useEffect(() => {
    const loadAutoHdrPref = async () => {
      try {
        const result = await loadAutoHdrPreference();
        if (result.status === "success") {
          setAutoHdrEnabled(result.autohdr_enabled);
        }
      } catch (e) {
        await logError(`Error loading AutoHDR preference: ${String(e)}`);
      }
    };

    loadAutoHdrPref();
  }, []);

  useEffect(() => {
    void refreshInstalledConfig();
  }, [pathExists]);

  useEffect(() => {
    if (initialLoad) {
      return;
    }

    void refreshUpdateState(addonEnabled);
  }, [addonEnabled, initialLoad]);

  useEffect(() => {
    if (!installedConfig || pathExists !== true) {
      setConfigChanged(false);
      return;
    }

    const currentConfig = {
      with_addon: addonEnabled,
      with_autohdr: autoHdrEnabled,
      selected_shaders: [] as string[]
    };

    const checkConfigChange = async () => {
      try {
        const shaderPrefs = await loadShaderPreferences();
        if (shaderPrefs.status === "success" && shaderPrefs.selected_shaders) {
          currentConfig.selected_shaders = shaderPrefs.selected_shaders;
        }

        const hasChanged =
          currentConfig.with_addon !== installedConfig.with_addon ||
          currentConfig.with_autohdr !== installedConfig.with_autohdr ||
          JSON.stringify(currentConfig.selected_shaders.sort()) !== JSON.stringify((installedConfig.selected_shaders || []).sort());

        setConfigChanged(hasChanged);
      } catch (e) {
        await logError(`Error checking config changes: ${String(e)}`);
      }
    };

    checkConfigChange();
  }, [addonEnabled, autoHdrEnabled, installedConfig, pathExists]);

  useEffect(() => {
    if (!installResult) return undefined;
    const timer = setTimeout(() => setInstallResult(null), 5000);
    return () => clearTimeout(timer);
  }, [installResult]);

  useEffect(() => {
    if (!uninstallResult) return undefined;
    const timer = setTimeout(() => setUninstallResult(null), 5000);
    return () => clearTimeout(timer);
  }, [uninstallResult]);

  const executeInstall = async (selectedShaders: string[]) => {
    try {
      setInstalling(true);
      const result = await runInstallReShade(
        addonEnabled,
        autoHdrEnabled,
        selectedShaders
      );
      setInstallResult(result);

      if (result.status === "success") {
        await refreshPostInstallState(addonEnabled);
        setConfigChanged(false);
      }
    } catch (e) {
      setInstallResult({ status: "error", message: String(e) });
      await logError(`Install error: ${String(e)}`);
    } finally {
      setInstalling(false);
    }
  };

  const handleInstallClick = async () => {
    try {
      const prefResult = await loadShaderPreferences();

      if (prefResult.status === "success" && prefResult.selected_shaders && prefResult.selected_shaders.length > 0) {
        await executeInstall(prefResult.selected_shaders);
        return;
      }

      const modalResult = showModal(
        <ShaderSelectionModal
          onConfirm={async (selectedShaders: string[]) => {
            await executeInstall(selectedShaders);
          }}
          onCancel={() => {
            // Modal closes through closeModal.
          }}
          addonEnabled={addonEnabled}
          autoHdrEnabled={autoHdrEnabled}
          closeModal={() => modalResult.Close()}
        />
      );
    } catch (e) {
      setInstallResult({ status: "error", message: String(e) });
      await logError(`Install error: ${String(e)}`);
    }
  };

  const handleUninstallClick = async () => {
    try {
      setUninstalling(true);
      const result = await runUninstallReShade();
      setUninstallResult(result);

      if (result.status === "success") {
        setAddonEnabled(false);
        setAutoHdrEnabled(false);
        setInstalledConfig(null);
        setConfigChanged(false);
        await refreshPostInstallState(false);
      }
    } catch (e) {
      setUninstallResult({ status: "error", message: String(e) });
      await logError(`Uninstall error: ${String(e)}`);
    } finally {
      setUninstalling(false);
    }
  };

  const handleManageShaders = async () => {
    let currentPreferences: string[] = [];

    try {
      const loadResult = await loadShaderPreferences();
      if (loadResult.status === "success" && loadResult.selected_shaders) {
        currentPreferences = loadResult.selected_shaders;
      }
    } catch (e) {
      await logError(`Error loading preferences: ${String(e)}`);
    }

    const modalResult = showModal(
      <ShaderSelectionModal
        onConfirm={async (selectedShaders: string[]) => {
          try {
            const result = await saveShaderPreferences(selectedShaders);
            if (result.status === "success") {
              setHasPreferences(true);
              setPreferencesInfo({
                has_preferences: true,
                shader_count: selectedShaders.length,
                last_updated: Date.now()
              });
              setInstallResult({
                status: "success",
                message: `Shader preferences saved! ${selectedShaders.length} packages selected.`
              });
            } else {
              setInstallResult({
                status: "error",
                message: result.message || "Failed to save preferences"
              });
            }
          } catch (e) {
            setInstallResult({ status: "error", message: String(e) });
            await logError(`Save preferences error: ${String(e)}`);
          }
        }}
        onCancel={() => {
          // Modal closes through closeModal.
        }}
        addonEnabled={addonEnabled}
        autoHdrEnabled={autoHdrEnabled}
        mode="manage"
        initialSelectedShaders={currentPreferences}
        closeModal={() => modalResult.Close()}
      />
    );
  };

  const handleAddonToggle = () => {
    if (!addonEnabled) {
      setShowingAddonDialog(true);
      setPendingAddonState(true);
      showModal(
        <ConfirmModal
          strTitle="Enable ReShade Addon Support?"
          strDescription="Using ReShade with addon support is generally not recommended when playing online multiplayer games with anti-cheat systems, as the addon functionality can trigger anti-cheat detection due to its potential for modification beyond just visual post-processing, which could be interpreted as cheating; most anti-cheat systems only whitelist the basic ReShade functionality with limited addons support."
          strOKButtonText="Enable Anyway"
          strCancelButtonText="Cancel"
          onOK={() => {
            setAddonEnabled(true);
            setShowingAddonDialog(false);
            setPendingAddonState(false);
          }}
          onCancel={() => {
            setShowingAddonDialog(false);
            setPendingAddonState(false);
          }}
        />
      );
      return;
    }

    setAddonEnabled(false);
    setAutoHdrEnabled(false);
    void saveAutoHdrPreference(false).catch(async (e) => {
      await logError(`Error saving AutoHDR preference: ${String(e)}`);
    });
  };

  const handleAutoHdrToggle = async () => {
    if (!autoHdrEnabled) {
      let warningTitle = "Enable AutoHDR Components?";
      let warningMessage = "AutoHDR components will be installed with ReShade. ";

      if (deckModel) {
        if (!deckModel.is_oled) {
          warningTitle = "LCD Model Warning";
          warningMessage += `You have a Steam Deck ${deckModel.model}. AutoHDR is optimized for OLED displays and may not work properly or cause visual issues on LCD models. `;
        } else {
          warningMessage += `Detected Steam Deck ${deckModel.model} - AutoHDR is optimized for your display. `;
        }
      } else if (!modelLoading) {
        warningMessage += "Could not detect Steam Deck model. AutoHDR is optimized for OLED displays. ";
      }

      warningMessage += "AutoHDR only works with DirectX 10/11/12 games. Continue?";

      showModal(
        <ConfirmModal
          strTitle={warningTitle}
          strDescription={warningMessage}
          strOKButtonText="Enable AutoHDR"
          strCancelButtonText="Cancel"
          onOK={async () => {
            setAutoHdrEnabled(true);
            try {
              await saveAutoHdrPreference(true);
            } catch (e) {
              await logError(`Error saving AutoHDR preference: ${String(e)}`);
            }
          }}
        />
      );
      return;
    }

    setAutoHdrEnabled(false);
    try {
      await saveAutoHdrPreference(false);
    } catch (e) {
      await logError(`Error saving AutoHDR preference: ${String(e)}`);
    }
  };

  const getInstallButtonText = () => {
    if (installing) {
      if (pathExists && configChanged) return "Reinstalling ReShade...";
      if (pathExists && updateStatus?.update_available) return "Updating ReShade...";
      return "Installing ReShade...";
    }

    let text = "🔧 Install ReShade";
    if (pathExists && configChanged) {
      text = "🔧 Reinstall ReShade";
    } else if (pathExists && updateStatus?.update_available) {
      text = "🔧 Update ReShade";
    }

    if (addonEnabled) {
      text += " with Addon Support";
    }
    if (autoHdrEnabled) {
      text += " + AutoHDR";
    }
    if (hasPreferences && preferencesInfo && preferencesInfo.shader_count > 0) {
      text += ` (${preferencesInfo.shader_count} shader packages)`;
    }

    return text;
  };

  const renderDeckModelInfo = () => {
    if (modelLoading) return null;

    if (deckModel && deckModel.status === "success") {
      if (deckModel.model === "Not Steam Deck") {
        return (
          <PanelSectionRow>
            <div
              style={{
                fontSize: "0.9em",
                color: "gray",
                marginBottom: "8px"
              }}
            >
              Non Steam Deck device detected
            </div>
          </PanelSectionRow>
        );
      }

      const isOptimal = deckModel.is_oled;
      const statusColor = isOptimal ? "green" : "orange";
      const statusIcon = isOptimal ? "🟢" : "🟡";
      const displayText =
        deckModel.model === "OLED" || deckModel.model === "LCD"
          ? `${statusIcon} Steam Deck ${deckModel.model} detected`
          : `${statusIcon} ${deckModel.model} detected`;

      return (
        <PanelSectionRow>
          <div
            style={{
              fontSize: "0.9em",
              color: statusColor,
              marginBottom: "8px"
            }}
          >
            {displayText}
            {!isOptimal && deckModel.model !== "Not Steam Deck" && (
              <div style={{ fontSize: "0.8em", opacity: 0.8, marginTop: "2px" }}>
                AutoHDR optimized for OLED
              </div>
            )}
          </div>
        </PanelSectionRow>
      );
    }

    return null;
  };

  const renderPreferencesInfo = () => {
    if (!hasPreferences || !preferencesInfo) return null;

    return (
      <PanelSectionRow>
        <div
          style={{
            padding: "8px",
            marginBottom: "8px",
            backgroundColor: "rgba(0, 255, 0, 0.1)",
            borderRadius: "4px",
            border: "1px solid rgba(0, 255, 0, 0.3)",
            fontSize: "0.9em"
          }}
        >
          📋 Shader preferences saved ({preferencesInfo.shader_count} packages)
          <div style={{ fontSize: "0.8em", opacity: 0.8, marginTop: "2px" }}>
            Will be used automatically for installations
          </div>
        </div>
      </PanelSectionRow>
    );
  };

  const shouldShowInstallButton =
    pathExists === false ||
    configChanged ||
    Boolean(pathExists && updateStatus?.update_available);

  return (
    <PanelSection title="ReShade Management">
      {pathExists !== null && (
        <PanelSectionRow>
          <div style={{ color: pathExists ? "green" : "red" }}>
            {pathExists ? (
              <>
                🟢 ReShade Is Installed
                {currentVersionInfo && (
                  <div style={{ fontSize: "0.9em", opacity: 0.8, marginTop: "4px" }}>
                    Installed version: {currentVersionInfo.version}
                    {currentVersionInfo.addon ? " (with Addon Support)" : ""}
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
              "🔴 ReShade Not Installed"
            )}
          </div>
        </PanelSectionRow>
      )}

      {addonEnabled && renderDeckModelInfo()}

      {pathExists === false && (
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={handleManageShaders}>
            📦 Select Packages to Install
          </ButtonItem>
        </PanelSectionRow>
      )}

      {renderPreferencesInfo()}

      <PanelSectionRow>
        <ToggleField
          label="Enable Addon Support"
          description={pathExists ? "Changes require reinstallation" : "Install ReShade with addon support"}
          checked={showingAddonDialog ? pendingAddonState : addonEnabled}
          onChange={handleAddonToggle}
          disabled={showingAddonDialog}
        />
      </PanelSectionRow>

      {addonEnabled && (
        <PanelSectionRow>
          <ToggleField
            label="Include AutoHDR Components"
            description="For Steam Deck OLED HDR gaming (DX10/11/12 only)"
            checked={autoHdrEnabled}
            onChange={handleAutoHdrToggle}
          />
        </PanelSectionRow>
      )}

      {pathExists === true && configChanged && (
        <PanelSectionRow>
          <div
            style={{
              padding: "12px",
              marginBottom: "12px",
              backgroundColor: "#ffa726",
              borderRadius: "4px",
              color: "white"
            }}
          >
            ⚠️ Configuration changed - Reinstallation required to apply changes
          </div>
        </PanelSectionRow>
      )}

      {shouldShowInstallButton && (
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={handleInstallClick} disabled={installing}>
            {getInstallButtonText()}
          </ButtonItem>
        </PanelSectionRow>
      )}

      {pathExists === true && (
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={handleUninstallClick} disabled={uninstalling}>
            {uninstalling ? "Uninstalling..." : "🗑️ Uninstall ReShade"}
          </ButtonItem>
        </PanelSectionRow>
      )}

      {installResult && (
        <PanelSectionRow>
          <div
            style={{
              padding: "12px",
              marginTop: "16px",
              backgroundColor: "var(--decky-selected-ui-bg)",
              borderRadius: "4px",
              color: installResult.status === "success" ? "green" : "red"
            }}
          >
            {installResult.status === "success"
              ? `✅ ${installResult.output || installResult.message || "Operation completed successfully!"}`
              : `❌ Error: ${installResult.message || "Operation failed"}`}
          </div>
        </PanelSectionRow>
      )}

      {uninstallResult && (
        <PanelSectionRow>
          <div
            style={{
              padding: "12px",
              marginTop: "16px",
              backgroundColor: "var(--decky-selected-ui-bg)",
              borderRadius: "4px",
              color: uninstallResult.status === "success" ? "green" : "red"
            }}
          >
            {uninstallResult.status === "success"
              ? "✅ ReShade uninstalled successfully!"
              : `❌ Error: ${uninstallResult.message || "Uninstallation failed"}`}
          </div>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <div>
          Press HOME key in-game to access the ReShade overlay.
          {addonEnabled && autoHdrEnabled && (
            <div style={{ fontSize: "0.9em", marginTop: "4px", opacity: 0.8 }}>
              AutoHDR works with DirectX 10/11/12 games only.
            </div>
          )}
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default ReShadeInstallerSection;
