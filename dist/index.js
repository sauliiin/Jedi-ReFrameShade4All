// Decky Loader will pass this api in, it's versioned to allow for backwards compatibility.
// @ts-ignore

// Prevents it from being duplicated in output.
const manifest = {"name":"Jedi-ReFrameShade4All","author":"Jedi (OptiScaler by xXJSONDeruloXx, ReShade by itsOwen)","flags":[],"api_version":1,"publish":{"tags":["DLSS","Framegen","upscaling","FSR","reshade","shaders"],"description":"All-in-one: OptiScaler frame generation/upscaling + ReShade (with addons) in a single plugin, with automatic DLL-slot coexistence so both run together.","image":"https://raw.githubusercontent.com/sauliiin/Jedi-ReFrameShade4All/refs/heads/master/assets/optiscaler_final.png"}};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
// Initialize
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
// Version 1 throws on version mismatch so we have to account for that here.
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const toaster = api.toaster;
const definePlugin = (fn) => {
    return (...args) => {
        // TODO: Maybe wrap this
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }
function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } } return target; }
function _extends() { _extends = Object.assign ? Object.assign.bind() : function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(obj, key, value) { key = _toPropertyKey(key); if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var {
        attr,
        size,
        title
      } = props,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function MdOutlineAutoAwesomeMotion (props) {
  return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 24 24"},"child":[{"tag":"path","attr":{"fill":"none","d":"M0 0h24v24H0z"},"child":[]},{"tag":"path","attr":{"d":"M14 2H4c-1.1 0-2 .9-2 2v10h2V4h10V2zm4 4H8c-1.1 0-2 .9-2 2v10h2V8h10V6zm2 4h-8c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2v-8c0-1.1-.9-2-2-2zm0 10h-8v-8h8v8z"},"child":[]}]})(props);
}

const getOptiScalerUpdateStatus = callable("get_optiscaler_update_status");
const updateOptiScaler = callable("update_optiscaler");
const runInstallFGMod$1 = callable("run_install_fgmod");
const runUninstallFGMod = callable("run_uninstall_fgmod");
const checkFGModPath$1 = callable("check_fgmod_path");
callable("list_installed_games");
const logError$5 = callable("log_error");
const runManualPatch$1 = callable("manual_patch_directory");
const patchGame = callable("patch_game");

/**
 * Utility for creating a timer that automatically clears after specified timeout
 * @param callback Function to call when timer completes
 * @param timeout Timeout in milliseconds
 * @returns Cleanup function that can be used in useEffect
 */
const createAutoCleanupTimer = (callback, timeout) => {
    const timer = setTimeout(callback, timeout);
    return () => clearTimeout(timer);
};
/**
 * Safe wrapper for async operations to handle errors consistently
 * @param operation Async operation to perform
 * @param errorContext Context string for error logging
 */
const safeAsyncOperation = async (operation, errorContext) => {
    try {
        return await operation();
    }
    catch (e) {
        logError$5(`${errorContext}: ${String(e)}`);
        console.error(e);
        return undefined;
    }
};

// Helpers shared by the OptiScaler/ReShade sections for reading and writing Steam
// launch options and for copying launch commands to the clipboard (non-Steam games).
/** Read the current launch options for a Steam app id. */
function getLaunchOptions$1(appId) {
    return new Promise((resolve) => {
        try {
            const reg = SteamClient.Apps.RegisterForAppDetails(appId, (details) => {
                resolve(details?.strLaunchOptions || "");
                try {
                    reg.unregister();
                }
                catch {
                    /* noop */
                }
            });
            setTimeout(() => {
                try {
                    reg.unregister();
                }
                catch {
                    /* noop */
                }
                resolve("");
            }, 1500);
        }
        catch {
            resolve("");
        }
    });
}
/** Write launch options for a Steam app id. */
function setLaunchOptions(appId, options) {
    SteamClient.Apps.SetAppLaunchOptions(appId, options);
}
const dllBase = (slot) => slot.replace(/\.dll$/i, "");
/**
 * Build the launch command used for non-Steam games, applying the chosen proxy
 * DLL slots. `OptiScaler.asi` needs no WINEDLLOVERRIDES entry.
 */
function buildLaunchCommand(slots, includeD3dcompiler = false) {
    const parts = [];
    const seen = new Set();
    if (includeD3dcompiler) {
        parts.push("d3dcompiler_47=n");
        seen.add("d3dcompiler_47");
    }
    for (const slot of slots) {
        if (!slot || slot === "OptiScaler.asi")
            continue;
        const base = dllBase(slot);
        if (base && !seen.has(base)) {
            parts.push(`${base}=n,b`);
            seen.add(base);
        }
    }
    const overrides = parts.length ? `WINEDLLOVERRIDES="${parts.join(";")}" ` : "";
    return `${overrides}SteamDeck=0 %command%`;
}
/**
 * Try the clipboard copy several times before giving up. Some failures are
 * transient (clipboard momentarily busy / focus not settled), so a couple of
 * quick retries meaningfully improves the automatic-copy success rate.
 */
async function copyWithRetry(text, attempts = 4, delayMs = 150) {
    for (let i = 0; i < attempts; i += 1) {
        if (await copyTextToClipboard(text))
            return true;
        if (i < attempts - 1) {
            await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
    }
    return false;
}
/**
 * Attempt the automatic copy (with retry). On final failure raise a toast so the
 * user knows to use the manual "Copy launch options" fallback button. Returns
 * whether the automatic copy ultimately succeeded.
 */
async function autoCopyLaunchCommand(text) {
    const ok = await copyWithRetry(text);
    if (!ok) {
        toaster.toast({
            title: "Couldn't copy launch options",
            body: 'Press "Copy launch options" to copy it and paste into your launcher.',
        });
    }
    return ok;
}
/**
 * Copy text to the clipboard using the input-simulation trick that works in
 * Steam gaming mode, falling back to the async clipboard API.
 */
async function copyTextToClipboard(text) {
    try {
        const tempInput = document.createElement("input");
        tempInput.value = text;
        tempInput.style.position = "absolute";
        tempInput.style.left = "-9999px";
        document.body.appendChild(tempInput);
        tempInput.focus();
        tempInput.select();
        let copied = false;
        try {
            copied = document.execCommand("copy");
        }
        catch {
            copied = false;
        }
        if (!copied) {
            try {
                await navigator.clipboard.writeText(text);
                copied = true;
            }
            catch {
                copied = false;
            }
        }
        document.body.removeChild(tempInput);
        return copied;
    }
    catch {
        return false;
    }
}

// Shared constants for the application
// Common style definitions
const STYLES = {
    instructionCard: {
        padding: '14px',
        backgroundColor: 'var(--decky-selected-ui-bg)',
        borderRadius: '8px',
        border: '1px solid var(--decky-border-color)',
        marginTop: '8px',
        fontSize: '13px',
        lineHeight: '1.4'
    }
};
// Proxy DLL name options for OptiScaler injection
const PROXY_DLL_OPTIONS = [
    { value: "dxgi.dll", label: "dxgi.dll (default)", hint: "Works for most DX12 games. Default." },
    { value: "winmm.dll", label: "winmm.dll", hint: "Use when dxgi.dll conflicts with an existing game file." },
    { value: "version.dll", label: "version.dll", hint: "Common fallback; works well with many launchers." },
    { value: "dbghelp.dll", label: "dbghelp.dll", hint: "Use for debug helper hook paths." },
    { value: "winhttp.dll", label: "winhttp.dll", hint: "Use when other DLL names conflict." },
    { value: "wininet.dll", label: "wininet.dll", hint: "Use when other DLL names conflict." },
    { value: "OptiScaler.asi", label: "OptiScaler.asi", hint: "For ASI loaders. Requires an ASI loader already installed in the game." },
];
const DEFAULT_PROXY_DLL = "dxgi.dll";
const DEFAULT_FSR4_VARIANT = "rdna23-int8";
// Common timeout values
const TIMEOUTS = {
    resultDisplay: 5000, // 5 seconds
    pathCheck: 3000 // 3 seconds
};
// Message strings
const MESSAGES = {
    uninstalling: "Removing OptiScaler...",
    uninstallButton: "Remove OptiScaler Mod",
    instructionText: "For extended OptiScaler options, assign a back button to a keyboard's 'Insert' key."
};

function InstructionCard({ pathExists }) {
    if (pathExists !== true)
        return null;
    return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
        window.SP_REACT.createElement("div", { style: STYLES.instructionCard },
            window.SP_REACT.createElement("div", { style: { whiteSpace: 'pre-line' } }, MESSAGES.instructionText))));
}

function UninstallButton({ pathExists, uninstalling, onUninstallClick }) {
    if (pathExists !== true)
        return null;
    return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
        window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: onUninstallClick, disabled: uninstalling },
            window.SP_REACT.createElement("div", { style: {
                    color: '#ef4444',
                    fontWeight: 'bold'
                } }, uninstalling ? MESSAGES.uninstalling : MESSAGES.uninstallButton))));
}

// THIS FILE IS AUTO GENERATED
function FaCheck (props) {
  return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M173.898 439.404l-166.4-166.4c-9.997-9.997-9.997-26.206 0-36.204l36.203-36.204c9.997-9.998 26.207-9.998 36.204 0L192 312.69 432.095 72.596c9.997-9.997 26.207-9.997 36.204 0l36.203 36.204c9.997 9.997 9.997 26.206 0 36.204l-294.4 294.401c-9.998 9.997-26.207 9.997-36.204-.001z"},"child":[]}]})(props);
}function FaClipboard (props) {
  return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 384 512"},"child":[{"tag":"path","attr":{"d":"M384 112v352c0 26.51-21.49 48-48 48H48c-26.51 0-48-21.49-48-48V112c0-26.51 21.49-48 48-48h80c0-35.29 28.71-64 64-64s64 28.71 64 64h80c26.51 0 48 21.49 48 48zM192 40c-13.255 0-24 10.745-24 24s10.745 24 24 24 24-10.745 24-24-10.745-24-24-24m96 114v-20a6 6 0 0 0-6-6H102a6 6 0 0 0-6 6v20a6 6 0 0 0 6 6h180a6 6 0 0 0 6-6z"},"child":[]}]})(props);
}

/**
 * Reliable "copy launch command" button. The copy runs synchronously inside the
 * click handler (a genuine user gesture) before any await, which is the only way
 * clipboard writes succeed in Steam's gaming-mode CEF — auto-copying after an
 * await silently fails because the transient user-activation is already gone.
 */
function CopyLaunchButton({ command, label = "Copy launch options" }) {
    const [copied, setCopied] = SP_REACT.useState(false);
    SP_REACT.useEffect(() => {
        if (!copied)
            return undefined;
        const timer = setTimeout(() => setCopied(false), 3000);
        return () => clearTimeout(timer);
    }, [copied]);
    if (!command)
        return null;
    const handleCopy = () => {
        // Fire the copy first, within the user gesture; update feedback after.
        void copyTextToClipboard(command).then((ok) => setCopied(ok));
    };
    return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
        window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleCopy },
            window.SP_REACT.createElement("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
                copied ? window.SP_REACT.createElement(FaCheck, { style: { color: "#4CAF50" } }) : window.SP_REACT.createElement(FaClipboard, null),
                window.SP_REACT.createElement("div", { style: { color: copied ? "#4CAF50" : "inherit", fontWeight: copied ? "bold" : "normal" } }, copied ? "Copied to clipboard" : label)))));
}

const folderForExe$1 = (exePath) => {
    const idx = exePath.lastIndexOf("/");
    return idx > 0 ? exePath.slice(0, idx) : exePath;
};
function OptiScalerControls({ pathExists, setPathExists, fgmodInfo, fsr4Variant = DEFAULT_FSR4_VARIANT, appid = "", targetExePath = "", }) {
    const [installing, setInstalling] = SP_REACT.useState(false);
    const [uninstalling, setUninstalling] = SP_REACT.useState(false);
    const [applying, setApplying] = SP_REACT.useState(false);
    const [result, setResult] = SP_REACT.useState("");
    const [launchCmd, setLaunchCmd] = SP_REACT.useState("");
    const [copyFailed, setCopyFailed] = SP_REACT.useState(false);
    const [dllName, setDllName] = SP_REACT.useState(DEFAULT_PROXY_DLL);
    const [updateStatus, setUpdateStatus] = SP_REACT.useState(null);
    const steamMode = Boolean(appid);
    const targetFolder = targetExePath ? folderForExe$1(targetExePath) : "";
    const refreshUpdateStatus = async () => {
        try {
            setUpdateStatus(await getOptiScalerUpdateStatus());
        }
        catch (e) {
            console.error(e);
        }
    };
    SP_REACT.useEffect(() => {
        void refreshUpdateStatus();
    }, [pathExists]);
    SP_REACT.useEffect(() => {
        if (result) {
            return createAutoCleanupTimer(() => setResult(""), TIMEOUTS.resultDisplay);
        }
        return () => { };
    }, [result]);
    const handleInstallOrUpdate = async () => {
        try {
            setInstalling(true);
            const doUpdate = pathExists === true && Boolean(updateStatus?.update_available);
            setResult(doUpdate ? "Updating OptiScaler…" : "Installing OptiScaler…");
            const r = doUpdate ? await updateOptiScaler(fsr4Variant) : await runInstallFGMod$1(fsr4Variant);
            setResult(r.status === "success" ? `✅ ${r.output || r.message || "Done"}` : `❌ ${r.message || "Failed"}`);
            if (r.status === "success") {
                setPathExists?.(true);
                await refreshUpdateStatus();
            }
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            console.error(e);
        }
        finally {
            setInstalling(false);
        }
    };
    const handleApplyOnlyOpti = async () => {
        try {
            setApplying(true);
            setLaunchCmd("");
            setCopyFailed(false);
            if (steamMode) {
                setResult("Applying OptiScaler to the selected Steam game…");
                const current = await getLaunchOptions$1(parseInt(appid, 10));
                const r = await patchGame(appid, dllName, current, fsr4Variant);
                if (r.status === "success") {
                    if (r.launch_options) {
                        try {
                            setLaunchOptions(parseInt(appid, 10), r.launch_options);
                        }
                        catch (e) {
                            console.error(e);
                        }
                    }
                    setResult(`✅ ${r.message || "OptiScaler applied."}` +
                        (r.launch_options ? `\n\nLaunch options set automatically:\n${r.launch_options}` : ""));
                }
                else {
                    setResult(`❌ ${r.message || "Failed"}`);
                }
            }
            else {
                if (!targetFolder) {
                    setResult('Choose a game .exe in "Choose exe/folder path" above first.');
                    return;
                }
                setResult("Applying OptiScaler to the selected folder…");
                const r = await runManualPatch$1(targetFolder, dllName, fsr4Variant);
                if (r.status === "success") {
                    const cmd = buildLaunchCommand([dllName]);
                    setLaunchCmd(cmd);
                    const copied = await autoCopyLaunchCommand(cmd);
                    setCopyFailed(!copied);
                    setResult(`✅ ${r.message || r.output || "OptiScaler applied."}\n\n` +
                        `Launch command:\n${cmd}\n\n` +
                        (copied
                            ? "Launch options copied automatically — paste them into your launcher."
                            : '⚠️ Could not copy automatically. Press "Copy launch options" below.'));
                }
                else {
                    setResult(`❌ ${r.message || "Failed"}`);
                }
            }
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            console.error(e);
        }
        finally {
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
        }
        catch (e) {
            console.error(e);
        }
        finally {
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
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "Framegen Management" },
        pathExists !== null && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { color: pathExists ? "green" : "red" } }, pathExists ? (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
                "\uD83D\uDFE2 OptiScaler Is Installed",
                fgmodInfo?.version && (window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", opacity: 0.8, marginTop: "4px" } },
                    "Installed version: ",
                    fgmodInfo.version)),
                updateStatus?.status === "success" && updateStatus.latest_version && (window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7, marginTop: "2px" } },
                    "Latest upstream: ",
                    updateStatus.latest_version,
                    updateStatus.update_available ? " (update available)" : " (up to date)")))) : ("🔴 OptiScaler Not Installed")))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleInstallOrUpdate, disabled: installing }, installButtonText)),
        pathExists === true && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.DropdownItem, { layout: "below", label: "Proxy DLL name", description: PROXY_DLL_OPTIONS.find((o) => o.value === dllName)?.hint, menuLabel: "Proxy DLL name", selectedOption: dllName, rgOptions: PROXY_DLL_OPTIONS.map((o) => ({ data: o.value, label: o.label })), onChange: (option) => setDllName(String(option.data)) })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyOnlyOpti, disabled: applying || (!steamMode && !targetFolder) }, applying ? "Applying…" : "Apply only OptiScaler")),
            !steamMode && !targetFolder && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7 } }, "Choose a game .exe in \"Choose exe/folder path\" above first."))))),
        window.SP_REACT.createElement(InstructionCard, { pathExists: pathExists }),
        result && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "8px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    whiteSpace: "pre-wrap",
                } }, result))),
        copyFailed && window.SP_REACT.createElement(CopyLaunchButton, { command: launchCmd }),
        window.SP_REACT.createElement(UninstallButton, { pathExists: pathExists, uninstalling: uninstalling, onUninstallClick: handleUninstallClick })));
}

const listInstalledGames = callable("list_installed_games");
const getEnginesStatus = callable("get_engines_status");
const getCombinedGameStatus$1 = callable("get_combined_game_status");
const patchAllGame = callable("patch_all_game");
const unpatchAllGame = callable("unpatch_all_game");
const logError$4 = callable("log_error");
const FSR4_OPTIONS = [
    { data: "rdna23-int8", label: "Steam Deck / RDNA2-3 (recommended)" },
    { data: "rdna4-native", label: "RDNA4 native" },
];
function getLaunchOptions(appId) {
    return new Promise((resolve) => {
        try {
            const reg = SteamClient.Apps.RegisterForAppDetails(appId, (details) => {
                resolve(details?.strLaunchOptions || "");
                try {
                    reg.unregister();
                }
                catch {
                    /* noop */
                }
            });
            setTimeout(() => {
                try {
                    reg.unregister();
                }
                catch {
                    /* noop */
                }
                resolve("");
            }, 1500);
        }
        catch {
            resolve("");
        }
    });
}
function SteamGameCombinedSection({ fsr4Variant, setFsr4Variant, appid, setAppid, }) {
    const [games, setGames] = SP_REACT.useState([]);
    const [engines, setEngines] = SP_REACT.useState(null);
    const [status, setStatus] = SP_REACT.useState(null);
    const [addon, setAddon] = SP_REACT.useState(true);
    const [busy, setBusy] = SP_REACT.useState(false);
    const [result, setResult] = SP_REACT.useState("");
    const refreshEngines = async () => {
        try {
            setEngines(await getEnginesStatus());
        }
        catch (e) {
            await logError$4(`SteamGameCombinedSection -> engines: ${String(e)}`);
        }
    };
    const loadStatus = async (id) => {
        try {
            setStatus(await getCombinedGameStatus$1(id));
        }
        catch (e) {
            await logError$4(`SteamGameCombinedSection -> status: ${String(e)}`);
        }
    };
    SP_REACT.useEffect(() => {
        (async () => {
            try {
                const r = await listInstalledGames();
                if (r.status === "success")
                    setGames(r.games || []);
            }
            catch (e) {
                await logError$4(`SteamGameCombinedSection -> list: ${String(e)}`);
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
            const r = await patchAllGame(appid, fsr4Variant, addon, current);
            if (r.status === "success") {
                if (r.launch_options) {
                    try {
                        SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), r.launch_options);
                    }
                    catch (e) {
                        await logError$4(`SetAppLaunchOptions: ${String(e)}`);
                    }
                }
                setResult(`✅ ${r.message || "Done"}${r.launch_options ? `\n\nLaunch options set automatically:\n${r.launch_options}` : ""}`);
            }
            else {
                setResult(`❌ ${r.message || "Failed"}`);
            }
            await refreshEngines();
            await loadStatus(appid);
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            await logError$4(`SteamGameCombinedSection -> patchAll: ${String(e)}`);
        }
        finally {
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
                }
                catch (e) {
                    await logError$4(`SetAppLaunchOptions(remove): ${String(e)}`);
                }
                setResult(`✅ ${r.message || "Removed"}`);
            }
            else {
                setResult(`❌ ${r.message || "Failed"}`);
            }
            await loadStatus(appid);
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            await logError$4(`SteamGameCombinedSection -> removeAll: ${String(e)}`);
        }
        finally {
            setBusy(false);
        }
    };
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "\uD83C\uDFAE Steam Game \u2014 Patch All" },
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", opacity: 0.85 } },
                "Pick a Steam game and press ",
                window.SP_REACT.createElement("b", null, "Patch All"),
                ". It installs OptiScaler (Frame Generation) and ReShade if needed, applies both to the game, and sets the launch options for you.")),
        engines && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.82em", opacity: 0.7 } },
                engines.optiscaler_installed ? `🟢 OptiScaler ${engines.optiscaler_version || ""}` : "⚪ OptiScaler not installed",
                "  •  ",
                engines.reshade_installed ? `🟢 ReShade ${engines.reshade_version || ""}` : "⚪ ReShade not installed"))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.82em", opacity: 0.7 } }, "Pick a Steam Game")),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.DropdownItem, { rgOptions: games.map((g) => ({ data: g.appid, label: g.name })), selectedOption: appid, onChange: (o) => {
                    setAppid(o.data);
                    setResult("");
                    void loadStatus(o.data);
                }, strDefaultLabel: "Select a game..." })),
        status && appid && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", padding: "8px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px" } },
                window.SP_REACT.createElement("div", null,
                    "Frame Generation: ",
                    status.optiscaler_patched ? `on (${status.optiscaler_slot})` : "off"),
                window.SP_REACT.createElement("div", null,
                    "ReShade: ",
                    status.reshade_present ? `on (${status.reshade_slot})` : "off"),
                status.both_active && window.SP_REACT.createElement("div", { style: { color: "green", marginTop: "2px" } }, "\u2705 Both active and coexisting")))),
        appid && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.DropdownItem, { label: "FSR4 runtime", rgOptions: FSR4_OPTIONS, selectedOption: fsr4Variant, onChange: (o) => setFsr4Variant(o.data), strDefaultLabel: "FSR4 runtime" })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: "ReShade add-ons", description: "Enables add-on support (avoid in anti-cheat online games).", checked: addon, onChange: setAddon })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handlePatchAll, disabled: busy }, busy ? "Working…" : "🚀 Patch All (FrameGen + ReShade)")),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleRemoveAll, disabled: busy }, "\uD83D\uDDD1\uFE0F Remove All")))),
        result && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "8px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    whiteSpace: "pre-wrap",
                    fontSize: "0.85em",
                } }, result))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.8em", opacity: 0.6 } }, "In-game: press HOME for the ReShade overlay or INSERT for OptiScaler."))));
}

// src/ShaderSelectionModal.tsx

const getAvailableShaders = callable("get_available_shaders");
const logError$3 = callable("log_error");
const ShaderSelectionModal = ({ onConfirm, onCancel, addonEnabled, autoHdrEnabled, closeModal, mode = 'install', initialSelectedShaders = [] }) => {
    const [shaderPackages, setShaderPackages] = SP_REACT.useState([]);
    const [selectedShaders, setSelectedShaders] = SP_REACT.useState(new Set());
    const [selectAll, setSelectAll] = SP_REACT.useState(true);
    const [loading, setLoading] = SP_REACT.useState(true);
    const [error, setError] = SP_REACT.useState('');
    SP_REACT.useEffect(() => {
        loadAvailableShaders();
    }, []);
    SP_REACT.useEffect(() => {
        // Initialize with saved preferences if provided
        if (initialSelectedShaders.length > 0 && shaderPackages.length > 0) {
            const initialSet = new Set(initialSelectedShaders);
            setSelectedShaders(initialSet);
            setSelectAll(initialSelectedShaders.length === shaderPackages.length);
        }
    }, [initialSelectedShaders, shaderPackages]);
    const loadAvailableShaders = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await getAvailableShaders();
            if (response.status === "success" && response.shaders) {
                setShaderPackages(response.shaders);
                // Initialize based on mode and initial selections
                if (initialSelectedShaders.length > 0) {
                    const initialSet = new Set(initialSelectedShaders);
                    setSelectedShaders(initialSet);
                    setSelectAll(initialSelectedShaders.length === response.shaders.length);
                }
                else {
                    // Default behavior: select all shaders
                    const allShaderIds = new Set(response.shaders.map(shader => shader.id));
                    setSelectedShaders(allShaderIds);
                    setSelectAll(true);
                }
            }
            else {
                setError(response.message || 'Failed to load shader packages');
            }
        }
        catch (err) {
            const errorMsg = err instanceof Error ? err.message : String(err);
            setError(`Error loading shaders: ${errorMsg}`);
            await logError$3(`ShaderSelectionModal -> loadAvailableShaders: ${errorMsg}`);
        }
        finally {
            setLoading(false);
        }
    };
    const handleShaderToggle = (shaderId, enabled) => {
        const newSelectedShaders = new Set(selectedShaders);
        if (enabled) {
            newSelectedShaders.add(shaderId);
        }
        else {
            newSelectedShaders.delete(shaderId);
        }
        setSelectedShaders(newSelectedShaders);
        // Update select all state
        setSelectAll(newSelectedShaders.size === shaderPackages.length);
    };
    const handleSelectAllToggle = (enabled) => {
        if (enabled) {
            // Select all shaders
            const allShaderIds = new Set(shaderPackages.map(shader => shader.id));
            setSelectedShaders(allShaderIds);
        }
        else {
            // Deselect all shaders
            setSelectedShaders(new Set());
        }
        setSelectAll(enabled);
    };
    const handleConfirm = () => {
        const selectedShaderIds = Array.from(selectedShaders);
        onConfirm(selectedShaderIds);
        if (closeModal)
            closeModal();
    };
    const handleCancel = () => {
        onCancel();
        if (closeModal)
            closeModal();
    };
    const calculateTotalSize = () => {
        let totalSize = 0;
        shaderPackages.forEach(shader => {
            if (selectedShaders.has(shader.id)) {
                // Parse size from string like "15.2MB" to number
                const sizeMatch = shader.size_mb.match(/(\d+\.?\d*)/);
                if (sizeMatch) {
                    totalSize += parseFloat(sizeMatch[1]);
                }
            }
        });
        return totalSize.toFixed(1);
    };
    const getModalTitle = () => {
        return mode === 'manage' ? 'Manage Shader Preferences' : 'Select Shader Packages';
    };
    const getConfirmButtonText = () => {
        return mode === 'manage' ? 'Save Preferences' : 'Install';
    };
    const getInstallSummary = () => {
        const selectedCount = selectedShaders.size;
        const totalCount = shaderPackages.length;
        if (mode === 'manage') {
            return `Shader Packages: ${selectedCount}/${totalCount} selected\nThese preferences will be used for future installations.`;
        }
        let summary = "Installing ReShade";
        if (addonEnabled) {
            summary += " with Addon Support";
        }
        if (autoHdrEnabled) {
            summary += " + AutoHDR";
        }
        summary += `\n\nShader Packages: ${selectedCount}/${totalCount} selected`;
        if (selectedCount > 0) {
            summary += ` (~${calculateTotalSize()}MB)`;
        }
        return summary;
    };
    const getDescription = () => {
        const isManageMode = mode === 'manage';
        return (window.SP_REACT.createElement("div", { style: {
                textAlign: 'left',
                maxHeight: '60vh',
                overflowY: 'auto',
                fontSize: '0.9em',
                lineHeight: '1.3',
                paddingRight: '8px'
            } }, loading ? (window.SP_REACT.createElement("div", { style: { padding: '20px', textAlign: 'center' } }, "Loading shader packages...")) : error ? (window.SP_REACT.createElement("div", { style: {
                padding: '12px',
                backgroundColor: '#ff6b6b',
                borderRadius: '4px',
                color: 'white',
                marginBottom: '12px',
                fontSize: '0.85em'
            } }, error)) : (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement("div", { style: { marginBottom: '12px', fontSize: '0.85em', opacity: 0.8 } }, isManageMode
                ? "Configure your preferred shader packages. These selections will be automatically used for future ReShade installations."
                : "Choose which shader packages to install. You can add more later."),
            window.SP_REACT.createElement("div", { style: {
                    marginBottom: '12px',
                    padding: '8px',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(255,255,255,0.05)'
                } },
                window.SP_REACT.createElement("div", { style: {
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        maxWidth: '100%'
                    } },
                    window.SP_REACT.createElement("div", { style: {
                            flex: '1',
                            marginRight: '12px',
                            fontSize: '0.9em',
                            fontWeight: 'bold'
                        } },
                        "Select All (",
                        shaderPackages.length,
                        " packages)"),
                    window.SP_REACT.createElement("div", { style: {
                            flexShrink: 0,
                            width: '65px',
                            height: '35px',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            overflow: 'hidden',
                            position: 'relative'
                        } },
                        window.SP_REACT.createElement("div", { style: {
                                maxWidth: '60px',
                                maxHeight: '32px',
                                overflow: 'hidden'
                            } },
                            window.SP_REACT.createElement(DFL.ToggleField, { checked: selectAll, onChange: handleSelectAllToggle }))))),
            shaderPackages.map((shader) => (window.SP_REACT.createElement("div", { key: shader.id, style: {
                    marginBottom: '8px',
                    padding: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(255,255,255,0.02)'
                } },
                window.SP_REACT.createElement("div", { style: {
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        maxWidth: '100%'
                    } },
                    window.SP_REACT.createElement("div", { style: {
                            flex: '1',
                            marginRight: '12px',
                            minWidth: 0
                        } },
                        window.SP_REACT.createElement("div", { style: {
                                fontWeight: 'bold',
                                fontSize: '0.85em',
                                marginBottom: '2px',
                                wordWrap: 'break-word',
                                overflow: 'hidden'
                            } }, shader.name),
                        window.SP_REACT.createElement("div", { style: {
                                fontSize: '0.75em',
                                opacity: 0.8,
                                marginBottom: '4px',
                                wordWrap: 'break-word',
                                lineHeight: '1.2',
                                overflow: 'hidden'
                            } }, shader.description),
                        window.SP_REACT.createElement("div", { style: {
                                fontSize: '0.7em',
                                opacity: 0.6,
                                fontStyle: 'italic'
                            } },
                            "Size: ",
                            shader.size_mb)),
                    window.SP_REACT.createElement("div", { style: {
                            flexShrink: 0,
                            width: '65px',
                            height: '35px',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            marginTop: '2px',
                            overflow: 'hidden',
                            position: 'relative'
                        } },
                        window.SP_REACT.createElement("div", { style: {
                                maxWidth: '60px',
                                maxHeight: '32px',
                                overflow: 'hidden'
                            } },
                            window.SP_REACT.createElement(DFL.ToggleField, { checked: selectedShaders.has(shader.id), onChange: (enabled) => handleShaderToggle(shader.id, enabled) }))))))),
            window.SP_REACT.createElement("div", { style: {
                    marginTop: '12px',
                    padding: '10px',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    fontSize: '0.8em',
                    border: '1px solid rgba(255,255,255,0.15)'
                } },
                window.SP_REACT.createElement("div", { style: { fontWeight: 'bold', marginBottom: '6px' } }, isManageMode ? 'Preferences Summary:' : 'Installation Summary:'),
                window.SP_REACT.createElement("div", { style: { whiteSpace: 'pre-line', lineHeight: '1.3' } }, getInstallSummary()))))));
    };
    return (window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: getModalTitle(), strDescription: getDescription(), strOKButtonText: loading ? "Loading..." : getConfirmButtonText(), strCancelButtonText: "Cancel", onOK: handleConfirm, onCancel: handleCancel, bOKDisabled: loading || error !== '' || selectedShaders.size === 0 }));
};

const runInstallReShade$1 = callable("run_install_reshade");
const runUninstallReShade = callable("run_uninstall_reshade");
const checkReShadePath$1 = callable("check_reshade_path");
const getReShadeUpdateStatus = callable("get_reshade_update_status");
const detectSteamDeckModel = callable("detect_steam_deck_model");
const logError$2 = callable("log_error");
const saveShaderPreferences = callable("save_shader_preferences");
const loadShaderPreferences = callable("load_shader_preferences");
const hasShaderPreferences = callable("has_shader_preferences");
const saveAutoHdrPreference = callable("save_autohdr_preference");
const loadAutoHdrPreference = callable("load_autohdr_preference");
const loadInstalledConfiguration = callable("load_installed_configuration");
const manageGameReShade = callable("manage_game_reshade");
const installReShadeForManualExe$1 = callable("install_reshade_for_heroic_game");
const detectGameApi$1 = callable("detect_heroic_game_api");
const getCombinedGameStatus = callable("get_combined_game_status");
const RESHADE_DLL_OPTIONS = [
    { data: "auto", label: "Automatic (Detect API)" },
    { data: "dxgi", label: "DXGI (DirectX 10/11/12)" },
    { data: "d3d9", label: "D3D9 (DirectX 9)" },
    { data: "d3d8", label: "D3D8 (DirectX 8)" },
    { data: "d3d11", label: "D3D11 (DirectX 11)" },
    { data: "ddraw", label: "DDraw (DirectDraw)" },
    { data: "dinput8", label: "DInput8 (DirectInput)" },
    { data: "opengl32", label: "OpenGL32 (OpenGL)" }
];
const getDllBase = (slot) => slot.replace(/\.dll$/i, "");
const getResolvedReShadeApi = (output, selectedApi) => {
    const match = (output || "").match(/Selected API:\s*([a-z0-9_]+)/i);
    if (match?.[1])
        return match[1].toLowerCase();
    return selectedApi === "auto" ? "dxgi" : selectedApi;
};
const buildSteamLaunchOptions = (reshadeApi, optiscalerSlot) => {
    const parts = ["d3dcompiler_47=n"];
    const seen = new Set();
    [reshadeApi, optiscalerSlot || ""].forEach((slot) => {
        const base = getDllBase(slot);
        if (base && !seen.has(base)) {
            parts.push(`${base}=n,b`);
            seen.add(base);
        }
    });
    return `WINEDLLOVERRIDES="${parts.join(";")}" SteamDeck=0 %command%`;
};
const folderForExe = (exePath) => {
    const idx = exePath.lastIndexOf("/");
    return idx > 0 ? exePath.slice(0, idx) : exePath;
};
function ReShadeInstallerSection({ appid, targetExePath = "" }) {
    const [installing, setInstalling] = SP_REACT.useState(false);
    const [uninstalling, setUninstalling] = SP_REACT.useState(false);
    const [applyingToSteamGame, setApplyingToSteamGame] = SP_REACT.useState(false);
    const [installResult, setInstallResult] = SP_REACT.useState(null);
    const [uninstallResult, setUninstallResult] = SP_REACT.useState(null);
    const [steamGameResult, setSteamGameResult] = SP_REACT.useState(null);
    const [launchCmd, setLaunchCmd] = SP_REACT.useState("");
    const [copyFailed, setCopyFailed] = SP_REACT.useState(false);
    const [pathExists, setPathExists] = SP_REACT.useState(null);
    const [addonEnabled, setAddonEnabled] = SP_REACT.useState(false);
    const [autoHdrEnabled, setAutoHdrEnabled] = SP_REACT.useState(false);
    const [selectedSteamGameApi, setSelectedSteamGameApi] = SP_REACT.useState("auto");
    const [currentVersionInfo, setCurrentVersionInfo] = SP_REACT.useState(null);
    const [updateStatus, setUpdateStatus] = SP_REACT.useState(null);
    const [initialLoad, setInitialLoad] = SP_REACT.useState(true);
    const [showingAddonDialog, setShowingAddonDialog] = SP_REACT.useState(false);
    const [pendingAddonState, setPendingAddonState] = SP_REACT.useState(false);
    const [deckModel, setDeckModel] = SP_REACT.useState(null);
    const [modelLoading, setModelLoading] = SP_REACT.useState(true);
    const [installedConfig, setInstalledConfig] = SP_REACT.useState(null);
    const [configChanged, setConfigChanged] = SP_REACT.useState(false);
    const [hasPreferences, setHasPreferences] = SP_REACT.useState(false);
    const [preferencesInfo, setPreferencesInfo] = SP_REACT.useState(null);
    const refreshLocalInstallState = async (syncAddonState = false) => {
        try {
            const result = await checkReShadePath$1();
            setPathExists(result.exists);
            setCurrentVersionInfo(result.exists ? result.version_info || null : null);
            if (syncAddonState) {
                setAddonEnabled(result.is_addon);
            }
            return result;
        }
        catch (e) {
            await logError$2(`refreshLocalInstallState: ${String(e)}`);
            return null;
        }
    };
    const refreshInstalledConfig = async (installExists = pathExists) => {
        try {
            if (installExists === false) {
                setInstalledConfig(null);
                return;
            }
            const result = await loadInstalledConfiguration();
            if (result.status === "success") {
                setInstalledConfig(result.config || null);
            }
            else {
                setInstalledConfig(null);
            }
        }
        catch (e) {
            setInstalledConfig(null);
            await logError$2(`Error loading installed configuration: ${String(e)}`);
        }
    };
    const refreshUpdateState = async (withAddon) => {
        try {
            const result = await getReShadeUpdateStatus(withAddon);
            setUpdateStatus(result);
        }
        catch (e) {
            setUpdateStatus({
                status: "error",
                message: String(e)
            });
            await logError$2(`Error loading update status: ${String(e)}`);
        }
    };
    const refreshPostInstallState = async (withAddon) => {
        const localState = await refreshLocalInstallState();
        await refreshInstalledConfig(localState?.exists ?? null);
        await refreshUpdateState(withAddon);
    };
    SP_REACT.useEffect(() => {
        let isMounted = true;
        const checkPath = async (syncAddonState = false) => {
            try {
                const result = await checkReShadePath$1();
                if (!isMounted)
                    return;
                setPathExists(result.exists);
                setCurrentVersionInfo(result.exists ? result.version_info || null : null);
                if (syncAddonState) {
                    setAddonEnabled(result.is_addon);
                }
            }
            catch (e) {
                await logError$2(`useEffect -> checkPath: ${String(e)}`);
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
    SP_REACT.useEffect(() => {
        const detectDeckModelInfo = async () => {
            try {
                setModelLoading(true);
                const result = await detectSteamDeckModel();
                setDeckModel(result);
            }
            catch (e) {
                await logError$2(`Steam Deck model detection error: ${String(e)}`);
            }
            finally {
                setModelLoading(false);
            }
        };
        detectDeckModelInfo();
    }, []);
    SP_REACT.useEffect(() => {
        const checkPreferences = async () => {
            try {
                const result = await hasShaderPreferences();
                if (result.status === "success") {
                    setHasPreferences(result.has_preferences);
                    setPreferencesInfo(result);
                }
            }
            catch (e) {
                await logError$2(`Error checking shader preferences: ${String(e)}`);
            }
        };
        checkPreferences();
    }, []);
    SP_REACT.useEffect(() => {
        const loadAutoHdrPref = async () => {
            try {
                const result = await loadAutoHdrPreference();
                if (result.status === "success") {
                    setAutoHdrEnabled(result.autohdr_enabled);
                }
            }
            catch (e) {
                await logError$2(`Error loading AutoHDR preference: ${String(e)}`);
            }
        };
        loadAutoHdrPref();
    }, []);
    SP_REACT.useEffect(() => {
        void refreshInstalledConfig();
    }, [pathExists]);
    SP_REACT.useEffect(() => {
        if (initialLoad) {
            return;
        }
        void refreshUpdateState(addonEnabled);
    }, [addonEnabled, initialLoad]);
    SP_REACT.useEffect(() => {
        if (!installedConfig || pathExists !== true) {
            setConfigChanged(false);
            return;
        }
        const currentConfig = {
            with_addon: addonEnabled,
            with_autohdr: autoHdrEnabled,
            selected_shaders: []
        };
        const checkConfigChange = async () => {
            try {
                const shaderPrefs = await loadShaderPreferences();
                if (shaderPrefs.status === "success" && shaderPrefs.selected_shaders) {
                    currentConfig.selected_shaders = shaderPrefs.selected_shaders;
                }
                const hasChanged = currentConfig.with_addon !== installedConfig.with_addon ||
                    currentConfig.with_autohdr !== installedConfig.with_autohdr ||
                    JSON.stringify(currentConfig.selected_shaders.sort()) !== JSON.stringify((installedConfig.selected_shaders || []).sort());
                setConfigChanged(hasChanged);
            }
            catch (e) {
                await logError$2(`Error checking config changes: ${String(e)}`);
            }
        };
        checkConfigChange();
    }, [addonEnabled, autoHdrEnabled, installedConfig, pathExists]);
    SP_REACT.useEffect(() => {
        if (!installResult)
            return undefined;
        const timer = setTimeout(() => setInstallResult(null), 5000);
        return () => clearTimeout(timer);
    }, [installResult]);
    SP_REACT.useEffect(() => {
        if (!uninstallResult)
            return undefined;
        const timer = setTimeout(() => setUninstallResult(null), 5000);
        return () => clearTimeout(timer);
    }, [uninstallResult]);
    SP_REACT.useEffect(() => {
        if (!steamGameResult)
            return undefined;
        const timer = setTimeout(() => setSteamGameResult(null), 8000);
        return () => clearTimeout(timer);
    }, [steamGameResult]);
    const executeInstall = async (selectedShaders) => {
        try {
            setInstalling(true);
            const result = await runInstallReShade$1(addonEnabled, autoHdrEnabled, selectedShaders);
            setInstallResult(result);
            if (result.status === "success") {
                await refreshPostInstallState(addonEnabled);
                setConfigChanged(false);
            }
        }
        catch (e) {
            setInstallResult({ status: "error", message: String(e) });
            await logError$2(`Install error: ${String(e)}`);
        }
        finally {
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
            const modalResult = DFL.showModal(window.SP_REACT.createElement(ShaderSelectionModal, { onConfirm: async (selectedShaders) => {
                    await executeInstall(selectedShaders);
                }, onCancel: () => {
                    // Modal closes through closeModal.
                }, addonEnabled: addonEnabled, autoHdrEnabled: autoHdrEnabled, closeModal: () => modalResult.Close() }));
        }
        catch (e) {
            setInstallResult({ status: "error", message: String(e) });
            await logError$2(`Install error: ${String(e)}`);
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
        }
        catch (e) {
            setUninstallResult({ status: "error", message: String(e) });
            await logError$2(`Uninstall error: ${String(e)}`);
        }
        finally {
            setUninstalling(false);
        }
    };
    const handleApplyReShadeToSteamGame = async () => {
        if (!appid) {
            setSteamGameResult({
                status: "error",
                message: 'Pick a game in "Steam Game - Patch All" above first.'
            });
            return;
        }
        if (!pathExists) {
            setSteamGameResult({
                status: "error",
                message: "Install ReShade first before applying it to a Steam game."
            });
            return;
        }
        try {
            setApplyingToSteamGame(true);
            setSteamGameResult({
                status: "success",
                message: "Applying ReShade to selected Steam game..."
            });
            const result = await manageGameReShade(appid, "install", selectedSteamGameApi, "", "");
            if (result.status !== "success") {
                setSteamGameResult({
                    status: "error",
                    message: result.message || result.output || "Failed to apply ReShade."
                });
                return;
            }
            const resolvedApi = getResolvedReShadeApi(result.output, selectedSteamGameApi);
            let optiscalerSlot = null;
            try {
                const combinedStatus = await getCombinedGameStatus(appid);
                if (combinedStatus.status === "success" && combinedStatus.optiscaler_patched) {
                    optiscalerSlot = combinedStatus.optiscaler_slot || null;
                }
            }
            catch (e) {
                await logError$2(`ReShadeInstallerSection -> getCombinedGameStatus: ${String(e)}`);
            }
            const launchOptions = buildSteamLaunchOptions(resolvedApi, optiscalerSlot);
            try {
                SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), launchOptions);
            }
            catch (e) {
                await logError$2(`ReShadeInstallerSection -> SetAppLaunchOptions: ${String(e)}`);
            }
            setSteamGameResult({
                status: "success",
                output: `ReShade applied with ${resolvedApi.toUpperCase()}.\n` +
                    `Launch options set automatically:\n${launchOptions}`
            });
        }
        catch (e) {
            setSteamGameResult({ status: "error", message: String(e) });
            await logError$2(`ReShadeInstallerSection -> applyToSteamGame: ${String(e)}`);
        }
        finally {
            setApplyingToSteamGame(false);
        }
    };
    const handleApplyOnlyReShadeNonSteam = async () => {
        if (!targetExePath) {
            setSteamGameResult({
                status: "error",
                message: 'Choose a game .exe in "Choose exe/folder path" above first.'
            });
            return;
        }
        if (!pathExists) {
            setSteamGameResult({
                status: "error",
                message: "Install ReShade first before applying it to a game."
            });
            return;
        }
        try {
            setApplyingToSteamGame(true);
            setLaunchCmd("");
            setCopyFailed(false);
            const folder = folderForExe(targetExePath);
            let resolvedApi = selectedSteamGameApi;
            if (resolvedApi === "auto") {
                setSteamGameResult({ status: "success", message: "Detecting best ReShade API…" });
                const detection = await detectGameApi$1(folder);
                resolvedApi = detection.status === "success" && detection.api ? detection.api : "dxgi";
            }
            setSteamGameResult({ status: "success", message: `Applying ReShade (${resolvedApi.toUpperCase()})…` });
            const result = await installReShadeForManualExe$1(folder, resolvedApi, targetExePath);
            if (result.status !== "success") {
                setSteamGameResult({
                    status: "error",
                    message: result.message || result.output || "Failed to apply ReShade."
                });
                return;
            }
            const launchCommand = buildLaunchCommand([resolvedApi], true);
            setLaunchCmd(launchCommand);
            const copied = await autoCopyLaunchCommand(launchCommand);
            setCopyFailed(!copied);
            setSteamGameResult({
                status: "success",
                output: `ReShade applied with ${resolvedApi.toUpperCase()}.\n` +
                    `Launch command:\n${launchCommand}\n\n` +
                    (copied
                        ? "Launch options copied automatically — paste them into your launcher."
                        : '⚠️ Could not copy automatically. Press "Copy launch options" below.')
            });
        }
        catch (e) {
            setSteamGameResult({ status: "error", message: String(e) });
            await logError$2(`ReShadeInstallerSection -> applyOnlyReShadeNonSteam: ${String(e)}`);
        }
        finally {
            setApplyingToSteamGame(false);
        }
    };
    const handleManageShaders = async () => {
        let currentPreferences = [];
        try {
            const loadResult = await loadShaderPreferences();
            if (loadResult.status === "success" && loadResult.selected_shaders) {
                currentPreferences = loadResult.selected_shaders;
            }
        }
        catch (e) {
            await logError$2(`Error loading preferences: ${String(e)}`);
        }
        const modalResult = DFL.showModal(window.SP_REACT.createElement(ShaderSelectionModal, { onConfirm: async (selectedShaders) => {
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
                    }
                    else {
                        setInstallResult({
                            status: "error",
                            message: result.message || "Failed to save preferences"
                        });
                    }
                }
                catch (e) {
                    setInstallResult({ status: "error", message: String(e) });
                    await logError$2(`Save preferences error: ${String(e)}`);
                }
            }, onCancel: () => {
                // Modal closes through closeModal.
            }, addonEnabled: addonEnabled, autoHdrEnabled: autoHdrEnabled, mode: "manage", initialSelectedShaders: currentPreferences, closeModal: () => modalResult.Close() }));
    };
    const handleAddonToggle = () => {
        if (!addonEnabled) {
            setShowingAddonDialog(true);
            setPendingAddonState(true);
            DFL.showModal(window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: "Enable ReShade Addon Support?", strDescription: "Using ReShade with addon support is generally not recommended when playing online multiplayer games with anti-cheat systems, as the addon functionality can trigger anti-cheat detection due to its potential for modification beyond just visual post-processing, which could be interpreted as cheating; most anti-cheat systems only whitelist the basic ReShade functionality with limited addons support.", strOKButtonText: "Enable Anyway", strCancelButtonText: "Cancel", onOK: () => {
                    setAddonEnabled(true);
                    setShowingAddonDialog(false);
                    setPendingAddonState(false);
                }, onCancel: () => {
                    setShowingAddonDialog(false);
                    setPendingAddonState(false);
                } }));
            return;
        }
        setAddonEnabled(false);
        setAutoHdrEnabled(false);
        void saveAutoHdrPreference(false).catch(async (e) => {
            await logError$2(`Error saving AutoHDR preference: ${String(e)}`);
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
                }
                else {
                    warningMessage += `Detected Steam Deck ${deckModel.model} - AutoHDR is optimized for your display. `;
                }
            }
            else if (!modelLoading) {
                warningMessage += "Could not detect Steam Deck model. AutoHDR is optimized for OLED displays. ";
            }
            warningMessage += "AutoHDR only works with DirectX 10/11/12 games. Continue?";
            DFL.showModal(window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: warningTitle, strDescription: warningMessage, strOKButtonText: "Enable AutoHDR", strCancelButtonText: "Cancel", onOK: async () => {
                    setAutoHdrEnabled(true);
                    try {
                        await saveAutoHdrPreference(true);
                    }
                    catch (e) {
                        await logError$2(`Error saving AutoHDR preference: ${String(e)}`);
                    }
                } }));
            return;
        }
        setAutoHdrEnabled(false);
        try {
            await saveAutoHdrPreference(false);
        }
        catch (e) {
            await logError$2(`Error saving AutoHDR preference: ${String(e)}`);
        }
    };
    const getInstallButtonText = () => {
        if (installing) {
            if (pathExists && configChanged)
                return "Reinstalling ReShade...";
            if (pathExists && updateStatus?.update_available)
                return "Updating ReShade...";
            return "Installing ReShade...";
        }
        let text = "🔧 Install ReShade";
        if (pathExists && configChanged) {
            text = "🔧 Reinstall ReShade";
        }
        else if (pathExists && updateStatus?.update_available) {
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
        if (modelLoading)
            return null;
        if (deckModel && deckModel.status === "success") {
            if (deckModel.model === "Not Steam Deck") {
                return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                    window.SP_REACT.createElement("div", { style: {
                            fontSize: "0.9em",
                            color: "gray",
                            marginBottom: "8px"
                        } }, "Non Steam Deck device detected")));
            }
            const isOptimal = deckModel.is_oled;
            const statusColor = isOptimal ? "green" : "orange";
            const statusIcon = isOptimal ? "🟢" : "🟡";
            const displayText = deckModel.model === "OLED" || deckModel.model === "LCD"
                ? `${statusIcon} Steam Deck ${deckModel.model} detected`
                : `${statusIcon} ${deckModel.model} detected`;
            return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: {
                        fontSize: "0.9em",
                        color: statusColor,
                        marginBottom: "8px"
                    } },
                    displayText,
                    !isOptimal && deckModel.model !== "Not Steam Deck" && (window.SP_REACT.createElement("div", { style: { fontSize: "0.8em", opacity: 0.8, marginTop: "2px" } }, "AutoHDR optimized for OLED")))));
        }
        return null;
    };
    const renderPreferencesInfo = () => {
        if (!hasPreferences || !preferencesInfo)
            return null;
        return (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "8px",
                    marginBottom: "8px",
                    backgroundColor: "rgba(0, 255, 0, 0.1)",
                    borderRadius: "4px",
                    border: "1px solid rgba(0, 255, 0, 0.3)",
                    fontSize: "0.9em"
                } },
                "\uD83D\uDCCB Shader preferences saved (",
                preferencesInfo.shader_count,
                " packages)",
                window.SP_REACT.createElement("div", { style: { fontSize: "0.8em", opacity: 0.8, marginTop: "2px" } }, "Will be used automatically for installations"))));
    };
    // A Steam game chosen at the top targets that game; otherwise we patch the
    // manually chosen non-Steam .exe.
    const steamMode = Boolean(appid);
    const shouldShowInstallButton = pathExists === false ||
        configChanged ||
        Boolean(pathExists && updateStatus?.update_available);
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "ReShade Management" },
        pathExists !== null && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { color: pathExists ? "green" : "red" } }, pathExists ? (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
                "\uD83D\uDFE2 ReShade Is Installed",
                currentVersionInfo && (window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", opacity: 0.8, marginTop: "4px" } },
                    "Installed version: ",
                    currentVersionInfo.version,
                    currentVersionInfo.addon ? " (with Addon Support)" : "")),
                updateStatus?.status === "success" && updateStatus.latest_version && (window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7, marginTop: "2px" } },
                    "Latest upstream: ",
                    updateStatus.latest_version,
                    updateStatus.update_available ? " (update available)" : " (up to date)")))) : ("🔴 ReShade Not Installed")))),
        addonEnabled && renderDeckModelInfo(),
        pathExists === false && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleManageShaders }, "\uD83D\uDCE6 Select Packages to Install"))),
        renderPreferencesInfo(),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ToggleField, { label: "Enable Addon Support", description: pathExists ? "Changes require reinstallation" : "Install ReShade with addon support", checked: showingAddonDialog ? pendingAddonState : addonEnabled, onChange: handleAddonToggle, disabled: showingAddonDialog })),
        addonEnabled && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ToggleField, { label: "Include AutoHDR Components", description: "For Steam Deck OLED HDR gaming (DX10/11/12 only)", checked: autoHdrEnabled, onChange: handleAutoHdrToggle }))),
        pathExists === true && steamMode && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.DropdownItem, { rgOptions: RESHADE_DLL_OPTIONS, selectedOption: selectedSteamGameApi, onChange: (option) => {
                        setSelectedSteamGameApi(option.data);
                        setSteamGameResult(null);
                    }, strDefaultLabel: "Steam game ReShade API" })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyReShadeToSteamGame, disabled: applyingToSteamGame || !appid }, applyingToSteamGame ? "Applying ReShade..." : "Apply only ReShade")))),
        pathExists === true && !steamMode && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.DropdownItem, { label: "Proxy DLL name", menuLabel: "Proxy DLL name", rgOptions: RESHADE_DLL_OPTIONS, selectedOption: selectedSteamGameApi, onChange: (option) => {
                        setSelectedSteamGameApi(option.data);
                        setSteamGameResult(null);
                    }, strDefaultLabel: "Proxy DLL name" })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyOnlyReShadeNonSteam, disabled: applyingToSteamGame || !targetExePath }, applyingToSteamGame ? "Applying ReShade..." : "Apply only ReShade")),
            !targetExePath && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7 } }, "Choose a game .exe in \"Choose exe/folder path\" above first."))))),
        pathExists === true && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: STYLES.instructionCard },
                "Press HOME key in-game to access the ReShade overlay.",
                addonEnabled && autoHdrEnabled && (window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", marginTop: "4px", opacity: 0.8 } }, "AutoHDR works with DirectX 10/11/12 games only."))))),
        shouldShowInstallButton && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleInstallClick, disabled: installing }, getInstallButtonText()))),
        pathExists === true && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleUninstallClick, disabled: uninstalling },
                window.SP_REACT.createElement("div", { style: { color: "#ef4444", fontWeight: "bold" } }, uninstalling ? "Uninstalling..." : "🗑️ Uninstall ReShade")))),
        installResult && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "16px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    color: installResult.status === "success" ? "green" : "red"
                } }, installResult.status === "success"
                ? `✅ ${installResult.output || installResult.message || "Operation completed successfully!"}`
                : `❌ Error: ${installResult.message || "Operation failed"}`))),
        uninstallResult && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "16px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    color: uninstallResult.status === "success" ? "green" : "red"
                } }, uninstallResult.status === "success"
                ? "✅ ReShade uninstalled successfully!"
                : `❌ Error: ${uninstallResult.message || "Uninstallation failed"}`))),
        steamGameResult && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "16px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    color: steamGameResult.status === "success" ? "green" : "red",
                    whiteSpace: "pre-wrap"
                } }, steamGameResult.status === "success"
                ? `✅ ${steamGameResult.output || steamGameResult.message || "Operation completed successfully!"}`
                : `❌ Error: ${steamGameResult.message || "Operation failed"}`))),
        !steamMode && copyFailed && window.SP_REACT.createElement(CopyLaunchButton, { command: launchCmd })));
}

const browseFilesystemForExecutable = callable("browse_filesystem_for_executable");
const getSdCardMountPath = callable("get_sd_card_mount_path");
const logError$1 = callable("log_error");
const DEFAULT_QUICK_PATHS = [
    { label: "Home", path: "/home/deck" },
    { label: "Common", path: "/home/deck/.steam/steam/steamapps/common" },
    { label: "SD Card", path: "/run/media" }
];
const getButtonStyle = (isFocused, isSelected = false) => ({
    border: isSelected
        ? "1px solid rgba(116, 226, 138, 0.95)"
        : isFocused
            ? "1px solid rgba(255, 255, 255, 0.95)"
            : "1px solid rgba(255,255,255,0.12)",
    backgroundColor: isSelected
        ? "rgba(76, 175, 80, 0.22)"
        : isFocused
            ? "rgba(255, 255, 255, 0.18)"
            : "rgba(255,255,255,0.04)",
    boxShadow: isFocused
        ? "0 0 0 2px rgba(255, 255, 255, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.06)"
        : "none",
    transform: isFocused ? "scale(1.01)" : "scale(1)",
    transition: "background-color 120ms ease, border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease"
});
const ExecutablePathBrowserModal = ({ initialPath = "/home/deck", onConfirm, onCancel, closeModal }) => {
    const [currentPath, setCurrentPath] = SP_REACT.useState(initialPath);
    const [parentPath, setParentPath] = SP_REACT.useState(null);
    const [entries, setEntries] = SP_REACT.useState([]);
    const [quickPaths, setQuickPaths] = SP_REACT.useState(DEFAULT_QUICK_PATHS);
    const [selectedPath, setSelectedPath] = SP_REACT.useState("");
    const [focusedItemKey, setFocusedItemKey] = SP_REACT.useState(null);
    const [loading, setLoading] = SP_REACT.useState(true);
    const [error, setError] = SP_REACT.useState("");
    const parentButtonRef = SP_REACT.useRef(null);
    const entryButtonRefs = SP_REACT.useRef([]);
    SP_REACT.useEffect(() => {
        void loadDirectory(currentPath, true);
    }, [currentPath]);
    SP_REACT.useEffect(() => {
        void loadSdCardPath();
    }, []);
    SP_REACT.useEffect(() => {
        if (loading || !!error) {
            return;
        }
        const focusTimer = window.setTimeout(() => {
            const firstEntryButton = entryButtonRefs.current.find(Boolean) || null;
            const focusTarget = parentButtonRef.current || firstEntryButton;
            focusTarget?.focus();
        }, 60);
        return () => {
            window.clearTimeout(focusTimer);
        };
    }, [loading, error, currentPath, parentPath, entries.length]);
    const loadDirectory = async (path, includeHidden) => {
        try {
            setLoading(true);
            setError("");
            const response = await browseFilesystemForExecutable(path, includeHidden);
            if (response.status !== "success" || !response.current_path || !response.entries) {
                setError(response.message || "Failed to load directory contents.");
                return;
            }
            setCurrentPath(response.current_path);
            setParentPath(response.parent_path || null);
            setEntries(response.entries);
            if (selectedPath && !selectedPath.startsWith(`${response.current_path}/`) && selectedPath !== response.current_path) {
                setSelectedPath("");
            }
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            setError(`Error loading directory: ${message}`);
            await logError$1(`ExecutablePathBrowserModal -> loadDirectory: ${message}`);
        }
        finally {
            setLoading(false);
        }
    };
    const loadSdCardPath = async () => {
        try {
            const response = await getSdCardMountPath();
            if (response.status !== "success" || !response.path) {
                return;
            }
            setQuickPaths((previousQuickPaths) => (previousQuickPaths.map((quickPath) => (quickPath.label === "SD Card"
                ? { ...quickPath, path: response.path }
                : quickPath))));
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            await logError$1(`ExecutablePathBrowserModal -> loadSdCardPath: ${message}`);
        }
    };
    const handleConfirm = () => {
        if (!selectedPath) {
            return;
        }
        onConfirm(selectedPath);
        if (closeModal) {
            closeModal();
        }
    };
    const handleCancel = () => {
        onCancel();
        if (closeModal) {
            closeModal();
        }
    };
    const handleItemFocus = (event) => {
        event.currentTarget.scrollIntoView({
            block: "center",
            inline: "nearest"
        });
    };
    const handleButtonFocus = (focusKey) => {
        setFocusedItemKey(focusKey);
    };
    const handleButtonBlur = (focusKey) => {
        setFocusedItemKey((currentFocusKey) => (currentFocusKey === focusKey ? null : currentFocusKey));
    };
    const renderDescription = () => {
        return (window.SP_REACT.createElement("div", { style: { textAlign: "left", maxHeight: "60vh", overflowY: "auto", paddingRight: "8px", paddingBottom: "8px" } },
            window.SP_REACT.createElement("div", { style: {
                    marginBottom: "12px",
                    padding: "8px",
                    borderRadius: "4px",
                    backgroundColor: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    fontSize: "0.85em",
                    wordBreak: "break-all"
                } },
                "Current path: ",
                currentPath),
            window.SP_REACT.createElement("div", { style: { marginBottom: "12px" } },
                window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", fontWeight: "bold", marginBottom: "6px" } }, "Quick locations"),
                window.SP_REACT.createElement("div", { style: {
                        display: "flex",
                        gap: "6px",
                        width: "100%"
                    } }, quickPaths.map((quickPath) => (window.SP_REACT.createElement("div", { key: `${quickPath.label}:${quickPath.path}`, style: { flex: "1 1 0", minWidth: 0, display: "flex" }, onFocusCapture: (event) => {
                        handleItemFocus(event);
                        handleButtonFocus(`quick:${quickPath.path}`);
                    }, onBlurCapture: () => handleButtonBlur(`quick:${quickPath.path}`) },
                    window.SP_REACT.createElement(DFL.DialogButton, { onClick: () => {
                            setSelectedPath("");
                            setCurrentPath(quickPath.path);
                        }, style: {
                            width: "100%",
                            boxSizing: "border-box",
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            padding: "6px 10px",
                            borderRadius: "4px",
                            ...getButtonStyle(focusedItemKey === `quick:${quickPath.path}`),
                            color: "white",
                            fontSize: "0.8em",
                            cursor: "pointer",
                            minHeight: "38px"
                        } }, quickPath.label)))))),
            error ? (window.SP_REACT.createElement("div", { style: {
                    padding: "10px",
                    borderRadius: "4px",
                    backgroundColor: "#ff6b6b",
                    color: "white",
                    fontSize: "0.85em"
                } }, error)) : loading ? (window.SP_REACT.createElement("div", { style: { padding: "20px", textAlign: "center" } }, "Loading entries...")) : (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
                window.SP_REACT.createElement("div", { style: {
                        maxHeight: "36vh",
                        overflowY: "auto",
                        borderRadius: "4px",
                        border: "1px solid rgba(255,255,255,0.08)",
                        padding: "4px 4px 16px 4px",
                        scrollBehavior: "smooth",
                        scrollPaddingBottom: "72px"
                    } },
                    window.SP_REACT.createElement("div", { style: { paddingBottom: "8px" } },
                        parentPath && (window.SP_REACT.createElement("div", { onFocusCapture: (event) => {
                                handleItemFocus(event);
                                handleButtonFocus(`parent:${parentPath}`);
                            }, onBlurCapture: () => handleButtonBlur(`parent:${parentPath}`) },
                            window.SP_REACT.createElement(DFL.DialogButton, { ref: (element) => {
                                    parentButtonRef.current = element;
                                }, onClick: () => {
                                    setSelectedPath("");
                                    setCurrentPath(parentPath);
                                }, style: {
                                    width: "100%",
                                    textAlign: "left",
                                    padding: "10px",
                                    marginBottom: "8px",
                                    borderRadius: "4px",
                                    ...getButtonStyle(focusedItemKey === `parent:${parentPath}`),
                                    color: "white",
                                    cursor: "pointer",
                                    minHeight: "42px"
                                } }, ".. Parent Directory"))),
                        entries.length === 0 ? (window.SP_REACT.createElement("div", { style: { padding: "12px", opacity: 0.8, fontSize: "0.85em" } }, "No folders or `.exe` files found here.")) : (entries.map((entry, index) => {
                            const isSelected = selectedPath === entry.path;
                            const focusKey = `entry:${entry.path}`;
                            return (window.SP_REACT.createElement("div", { key: entry.path, onFocusCapture: (event) => {
                                    handleItemFocus(event);
                                    handleButtonFocus(focusKey);
                                }, onBlurCapture: () => handleButtonBlur(focusKey) },
                                window.SP_REACT.createElement(DFL.DialogButton, { ref: (element) => {
                                        entryButtonRefs.current[index] = element;
                                    }, onClick: () => {
                                        if (entry.is_dir) {
                                            setSelectedPath("");
                                            setCurrentPath(entry.path);
                                            return;
                                        }
                                        setSelectedPath(entry.path);
                                    }, style: {
                                        width: "100%",
                                        textAlign: "left",
                                        padding: "10px",
                                        marginBottom: "8px",
                                        borderRadius: "4px",
                                        ...getButtonStyle(focusedItemKey === focusKey, isSelected),
                                        color: "white",
                                        cursor: "pointer",
                                        minHeight: "56px"
                                    } },
                                    window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", fontWeight: "bold", marginBottom: "3px" } },
                                        entry.is_dir ? "📁" : "🎮",
                                        " ",
                                        entry.name),
                                    window.SP_REACT.createElement("div", { style: { fontSize: "0.75em", opacity: 0.75, wordBreak: "break-all" } }, entry.path),
                                    window.SP_REACT.createElement("div", { style: { fontSize: "0.72em", opacity: 0.6, marginTop: "3px" } },
                                        entry.is_dir ? "Folder" : "Windows executable",
                                        entry.is_symlink ? " • Symlink" : "",
                                        entry.is_hidden ? " • Hidden" : ""))));
                        })))),
                selectedPath && (window.SP_REACT.createElement("div", { style: {
                        marginTop: "12px",
                        padding: "10px",
                        borderRadius: "4px",
                        backgroundColor: "rgba(76, 175, 80, 0.14)",
                        border: "1px solid rgba(76, 175, 80, 0.35)",
                        fontSize: "0.82em",
                        wordBreak: "break-all"
                    } },
                    "Selected executable: ",
                    selectedPath))))));
    };
    return (window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: "Choose exe path", strDescription: renderDescription(), strOKButtonText: "Use Selected exe", strCancelButtonText: "Cancel", onOK: handleConfirm, onCancel: handleCancel, bOKDisabled: loading || !!error || !selectedPath }));
};

const checkFGModPath = callable("check_fgmod_path");
const runInstallFGMod = callable("run_install_fgmod");
const runManualPatch = callable("manual_patch_directory");
const runManualUnpatch = callable("manual_unpatch_directory");
const checkReShadePath = callable("check_reshade_path");
const runInstallReShade = callable("run_install_reshade");
const installReShadeForManualExe = callable("install_reshade_for_heroic_game");
const uninstallReShadeForManualExe = callable("uninstall_reshade_for_heroic_game");
const detectGameApi = callable("detect_heroic_game_api");
const logError = callable("log_error");
const getDirectoryForPath = (path) => {
    const separatorIndex = path.lastIndexOf("/");
    return separatorIndex > 0 ? path.slice(0, separatorIndex) : path;
};
const getFilenameForPath = (path) => path.split("/").pop() || "Unknown.exe";
const ChooseExePathSection = ({ exePath, setExePath, fsr4Variant }) => {
    const [applyingBoth, setApplyingBoth] = SP_REACT.useState(false);
    const [removingBoth, setRemovingBoth] = SP_REACT.useState(false);
    const [launchCmd, setLaunchCmd] = SP_REACT.useState("");
    const [copyFailed, setCopyFailed] = SP_REACT.useState(false);
    const [result, setResult] = SP_REACT.useState("");
    const handleChooseExecutablePath = async () => {
        try {
            const startPath = exePath ? getDirectoryForPath(exePath) : "/home/deck";
            const modalResult = DFL.showModal(window.SP_REACT.createElement(ExecutablePathBrowserModal, { initialPath: startPath, onConfirm: (path) => {
                    // Picking the .exe automatically stores its folder as the OptiScaler target.
                    setExePath(path);
                    setResult("");
                }, onCancel: () => {
                    // Modal closes through closeModal.
                }, closeModal: () => modalResult.Close() }));
        }
        catch (error) {
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
            setResult(`✅ FrameGen (winmm) + ReShade (${reshadeApi.toUpperCase()}) applied to ${selectedFilename}.\n\n` +
                `Launch command:\n${cmd}\n\n` +
                (copied
                    ? "Launch options copied automatically — paste them into your launcher.\n"
                    : '⚠️ Could not copy automatically. Press "Copy launch options" below.\n') +
                "Press HOME in-game for the ReShade overlay or INSERT for OptiScaler.");
        }
        catch (error) {
            setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
            await logError(`ChooseExePathSection -> handleApplyBoth: ${String(error)}`);
        }
        finally {
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
                setResult(`✅ Frame Generation + ReShade removed from ${selectedFilename}.\n\n` +
                    "Remember to clear the launch command from your launcher.");
            }
            else {
                setResult("⚠️ Partial removal:\n" +
                    `• Frame Generation: ${okOpti ? "removed" : unpatch.message || "failed"}\n` +
                    `• ReShade: ${okReshade ? "removed" : reshadeRemove.message || "failed"}`);
            }
        }
        catch (error) {
            setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
            await logError(`ChooseExePathSection -> handleRemoveBoth: ${String(error)}`);
        }
        finally {
            setRemovingBoth(false);
        }
    };
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "Choose exe/folder path" },
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", opacity: 0.8 } },
                "Patch any Windows game executable manually. This is ideal for non-Steam launchers and custom setups.",
                " ",
                "Browse to the game folder first, then pick the `.exe`.")),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleChooseExecutablePath }, "\uD83D\uDCC1 Choose exe/folder path")),
        exePath && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: {
                        padding: "8px",
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                        borderRadius: "4px",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        fontSize: "0.85em"
                    } },
                    window.SP_REACT.createElement("div", { style: { fontWeight: "bold", marginBottom: "4px" } },
                        "Selected: ",
                        getFilenameForPath(exePath)),
                    window.SP_REACT.createElement("div", { style: { opacity: 0.75, wordBreak: "break-all" } },
                        "Path: ",
                        exePath))),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyBoth, disabled: applyingBoth || removingBoth }, applyingBoth ? "Applying…" : "Apply both (FrameGen + ReShade)")),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleRemoveBoth, disabled: applyingBoth || removingBoth }, removingBoth ? "Removing…" : "🗑️ Remove All")))),
        result && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "16px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    whiteSpace: "pre-wrap"
                } }, result))),
        copyFailed && window.SP_REACT.createElement(CopyLaunchButton, { command: launchCmd })));
};

function MainContent() {
    const [pathExists, setPathExists] = SP_REACT.useState(null);
    const [fgmodInfo, setFgmodInfo] = SP_REACT.useState(null);
    const [advanced, setAdvanced] = SP_REACT.useState(false);
    // FSR4 runtime is chosen once in the top section and shared with the advanced OptiScaler controls.
    const [fsr4Variant, setFsr4Variant] = SP_REACT.useState(DEFAULT_FSR4_VARIANT);
    // The Steam game is also picked once at the top and reused by the advanced sections.
    const [selectedAppid, setSelectedAppid] = SP_REACT.useState("");
    // Non-Steam target executable picked in the advanced "Choose exe/folder path" section.
    const [exePath, setExePath] = SP_REACT.useState("");
    SP_REACT.useEffect(() => {
        const checkPath = async () => {
            const result = await safeAsyncOperation(async () => await checkFGModPath$1(), 'MainContent -> checkPath');
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
    return (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
        window.SP_REACT.createElement(SteamGameCombinedSection, { fsr4Variant: fsr4Variant, setFsr4Variant: setFsr4Variant, appid: selectedAppid, setAppid: setSelectedAppid }),
        window.SP_REACT.createElement(DFL.PanelSection, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: steamMode ? "Steam Controls" : "Advanced controls", description: "Per-engine install, proxy DLL, ReShade shaders/AutoHDR, and manual patching.", checked: advanced, onChange: setAdvanced }))),
        advanced && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            !steamMode && (window.SP_REACT.createElement(ChooseExePathSection, { exePath: exePath, setExePath: setExePath, fsr4Variant: fsr4Variant })),
            window.SP_REACT.createElement(OptiScalerControls, { pathExists: pathExists, setPathExists: setPathExists, fgmodInfo: fgmodInfo, fsr4Variant: fsr4Variant, appid: selectedAppid, targetExePath: exePath }),
            window.SP_REACT.createElement(ReShadeInstallerSection, { appid: selectedAppid, targetExePath: exePath })))));
}
var index = definePlugin(() => ({
    name: "Jedi ReFrameShade4All",
    titleView: window.SP_REACT.createElement("div", null, "Jedi ReFrameShade4All"),
    alwaysRender: true,
    content: window.SP_REACT.createElement(MainContent, null),
    icon: window.SP_REACT.createElement(MdOutlineAutoAwesomeMotion, null),
    onDismount() {
        console.log("Jedi ReFrameShade4All Plugin unmounted");
    },
}));

export { index as default };
//# sourceMappingURL=index.js.map
