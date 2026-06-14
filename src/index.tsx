import { definePlugin } from "@decky/api";
import { MdOutlineAutoAwesomeMotion } from "react-icons/md";
import { useState, useEffect } from "react";
import { PanelSection, PanelSectionRow, ToggleField } from "@decky/ui";
import { OptiScalerControls } from "./components";
import { checkFGModPath } from "./api";
import { safeAsyncOperation } from "./utils";
import { TIMEOUTS, DEFAULT_FSR4_VARIANT } from "./utils/constants";
import SteamGameCombinedSection from "./SteamGameCombinedSection";
import ReShadeInstallerSection from "./ReShadeInstallerSection";
import ChooseExePathSection from "./ChooseExePathSection";

type FgmodInfo = {
  exists: boolean;
  version?: string | null;
  selected_fsr4_variant?: string | null;
  selected_fsr4_variant_label?: string | null;
  install_manifest_present?: boolean;
};

function MainContent() {
  const [pathExists, setPathExists] = useState<boolean | null>(null);
  const [fgmodInfo, setFgmodInfo] = useState<FgmodInfo | null>(null);
  const [advanced, setAdvanced] = useState<boolean>(false);
  // FSR4 runtime is chosen once in the top section and shared with the advanced OptiScaler controls.
  const [fsr4Variant, setFsr4Variant] = useState<string>(DEFAULT_FSR4_VARIANT);
  // The Steam game is also picked once at the top and reused by the advanced sections.
  const [selectedAppid, setSelectedAppid] = useState<string>("");
  // Non-Steam target executable picked in the advanced "Choose exe/folder path" section.
  const [exePath, setExePath] = useState<string>("");

  useEffect(() => {
    const checkPath = async () => {
      const result = await safeAsyncOperation(
        async () => await checkFGModPath(),
        'MainContent -> checkPath'
      );
      if (result) {
        setFgmodInfo(result);
        setPathExists(result.exists);
      }
    };

    checkPath();
    const intervalId = setInterval(checkPath, TIMEOUTS.pathCheck);
    return () => clearInterval(intervalId);
  }, []);

  // A Steam game chosen at the top switches the advanced area into "Steam" mode;
  // otherwise the advanced area targets a manually chosen .exe (non-Steam games).
  const steamMode = Boolean(selectedAppid);

  return (
    <>
      {/* Primary one-button flow: pick a game, apply both mods at once */}
      <SteamGameCombinedSection
        fsr4Variant={fsr4Variant}
        setFsr4Variant={setFsr4Variant}
        appid={selectedAppid}
        setAppid={setSelectedAppid}
      />

      <PanelSection>
        <PanelSectionRow>
          <ToggleField
            label={steamMode ? "Steam Controls" : "Advanced controls"}
            description="Per-engine install, proxy DLL, ReShade shaders/AutoHDR, and manual patching."
            checked={advanced}
            onChange={setAdvanced}
          />
        </PanelSectionRow>
      </PanelSection>

      {advanced && (
        <>
          {!steamMode && (
            <ChooseExePathSection
              exePath={exePath}
              setExePath={setExePath}
              fsr4Variant={fsr4Variant}
            />
          )}
          <OptiScalerControls
            pathExists={pathExists}
            setPathExists={setPathExists}
            fgmodInfo={fgmodInfo}
            fsr4Variant={fsr4Variant}
            appid={selectedAppid}
            targetExePath={exePath}
          />
          <ReShadeInstallerSection appid={selectedAppid} targetExePath={exePath} />
        </>
      )}
    </>
  );
}

export default definePlugin(() => ({
  name: "Jedi ReFrameShade4All",
  titleView: <div>Jedi ReFrameShade4All</div>,
  alwaysRender: true,
  content: <MainContent />,
  icon: <MdOutlineAutoAwesomeMotion />,
  onDismount() {
    console.log("Jedi ReFrameShade4All Plugin unmounted");
  },
}));
