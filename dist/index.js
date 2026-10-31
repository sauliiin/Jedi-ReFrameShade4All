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
const patchGame = callable("patch_game");
const removeOptiScalerOnly = callable("remove_optiscaler_only");

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
// launch options.
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
// The LSFG-VK launch wrapper; Steam runs it in front of the game.
const LSFG_WRAPPER = "~/.jedi-lsfg";
// Wrappers from decky-lsfg-vk and MAKO Decky: two frame generation layers on one game don't work together.
const LEGACY_LSFG_WRAPPER = /^(?:~\/\.?lsfg|~\/\.local\/bin\/(?:lsfg|lsfg-vk-experimental|mako-run|mako-launch)|mako-run|mako-launch|\/home\/[^/]+\/(?:\.?lsfg|\.local\/bin\/(?:lsfg|lsfg-vk-experimental|mako-run|mako-launch)))$/;
function hasLsfgWrapper(opts) {
    const tokens = (opts || "").trim().split(/\s+/);
    const command = tokens.indexOf("%command%");
    return command > 0 && tokens[command - 1] === LSFG_WRAPPER;
}
// Puts ~/.jedi-lsfg right before %command% (on) or takes it out (off), keeping the rest of the launch options.
function withLsfgWrapper(opts, enabled) {
    const tokens = (opts || "").trim().split(/\s+/).filter((t) => t && t !== LSFG_WRAPPER && !LEGACY_LSFG_WRAPPER.test(t));
    if (enabled) {
        let command = tokens.indexOf("%command%");
        if (command < 0) {
            // Like Steam: leading NAME=value assignments stay in front of the command.
            command = 0;
            while (command < tokens.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(tokens[command]))
                command++;
            tokens.splice(command, 0, "%command%");
        }
        tokens.splice(command, 0, LSFG_WRAPPER);
    }
    const next = tokens.join(" ");
    return next === "%command%" ? "" : next;
}
// For writers that rebuild the launch options from scratch: keeps ~/.jedi-lsfg when the game had it.
async function setLaunchOptionsKeepingLsfg(appId, options) {
    const current = await getLaunchOptions$1(appId);
    const next = hasLsfgWrapper(current) ? withLsfgWrapper(options, true) : options;
    SteamClient.Apps.SetAppLaunchOptions(appId, next);
    return next;
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
// 4.0.2c, 4.1.1, 4.1.2 Lite and HLX DLSS in one game, picked in OptiScaler's menu.
const DEFAULT_FSR4_VARIANT = "deck-all";
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

function OptiScalerControls({ pathExists, setPathExists, fgmodInfo, fsr4Variant = DEFAULT_FSR4_VARIANT, appid = "", targetExePath = "", }) {
    const [installing, setInstalling] = SP_REACT.useState(false);
    const [uninstalling, setUninstalling] = SP_REACT.useState(false);
    const [applying, setApplying] = SP_REACT.useState(false);
    const [removingOnly, setRemovingOnly] = SP_REACT.useState(false);
    const [result, setResult] = SP_REACT.useState("");
    const [dllName, setDllName] = SP_REACT.useState(DEFAULT_PROXY_DLL);
    const [updateStatus, setUpdateStatus] = SP_REACT.useState(null);
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
        if (!appid)
            return;
        try {
            setApplying(true);
            setResult("Applying OptiScaler to the selected game…");
            const current = await getLaunchOptions$1(parseInt(appid, 10));
            const r = await patchGame(appid, dllName, current, fsr4Variant, targetExePath || "");
            if (r.status === "success") {
                if (r.launch_options) {
                    try {
                        r.launch_options = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), r.launch_options);
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
        catch (e) {
            setResult(`❌ ${String(e)}`);
            console.error(e);
        }
        finally {
            setApplying(false);
        }
    };
    // Takes OptiScaler out of the chosen game while leaving ReShade patched: the
    // backend re-links ReShade afterwards and hands back the remaining overrides.
    const handleRemoveOnlyOpti = async () => {
        if (!appid)
            return;
        try {
            setRemovingOnly(true);
            setResult("Removing OptiScaler from the selected game…");
            const current = await getLaunchOptions$1(parseInt(appid, 10));
            const r = await removeOptiScalerOnly(appid, targetExePath || "", current);
            if (r.status === "success") {
                try {
                    r.launch_options = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), r.launch_options || "");
                }
                catch (e) {
                    console.error(e);
                }
                setResult(`✅ ${r.message || "OptiScaler removed."}` +
                    (r.launch_options
                        ? `\n\nLaunch options updated automatically:\n${r.launch_options}`
                        : "\n\nLaunch options cleared."));
            }
            else {
                setResult(`❌ ${r.message || "Failed"}`);
            }
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            console.error(e);
        }
        finally {
            setRemovingOnly(false);
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
            appid ? (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
                window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                    window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7, wordBreak: "break-all" } }, targetExePath ? `Target: ${targetExePath}` : "Target: automatic detection")),
                window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                    window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyOnlyOpti, disabled: applying || removingOnly }, applying ? "Applying…" : "Apply only OptiScaler")),
                window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                    window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleRemoveOnlyOpti, disabled: applying || removingOnly }, removingOnly ? "Removing…" : "🗑️ Remove only OptiScaler")))) : (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7 } }, "Pick a game above to apply or remove it."))))),
        window.SP_REACT.createElement(InstructionCard, { pathExists: pathExists }),
        result && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: {
                    padding: "12px",
                    marginTop: "8px",
                    backgroundColor: "var(--decky-selected-ui-bg)",
                    borderRadius: "4px",
                    whiteSpace: "pre-wrap",
                } }, result))),
        window.SP_REACT.createElement(UninstallButton, { pathExists: pathExists, uninstalling: uninstalling, onUninstallClick: handleUninstallClick })));
}

const listInstalledGames = callable("list_installed_games");
const getEnginesStatus = callable("get_engines_status");
const getCombinedGameStatus$1 = callable("get_combined_game_status");
const patchAllGame = callable("patch_all_game");
const unpatchAllGame = callable("unpatch_all_game");
const getCachyosFsr4Status = callable("get_cachyos_fsr4_status");
const prepareCachyosFsr4Lite = callable("prepare_cachyos_fsr4_lite");
const installProtonLite = callable("install_proton_lite");
const getProtonLiteUpdateStatus = callable("get_proton_lite_update_status");
// Every Lite Proton copy's internal name ends with this (up to 1.1.23 it also carried the release).
const LITE_TOOL_SUFFIX = "-jedi-fsr4lite";
const rememberCompatTool = callable("remember_compat_tool");
const getLiteProtonPending = callable("get_lite_proton_pending");
const setLiteProtonPending = callable("set_lite_proton_pending");
const getLsfgStatus = callable("get_lsfg_status");
const enableLsfg = callable("enable_lsfg");
const disableLsfg = callable("disable_lsfg");
const setLsfgTargetFps = callable("set_lsfg_target_fps");
// LSFG-VK target FPS: the slider only saves the value it settles on (each save rewrites MAKO's profiles).
const LSFG_FPS_MIN = 60;
const LSFG_FPS_MAX = 120;
const LSFG_SAVE_DEBOUNCE_MS = 300;
const LSFG_FPS_NOTCHES = [60, 90, 120].map((value, notchIndex) => ({ notchIndex, label: String(value), value }));
// Steam's CompatManager service replaced SteamClient.Apps.GetAvailableCompatTools (same request as
// decky-wine-cellar's steamCompat.ts). Only the tool names are read from its protobuf answer.
class CompatToolsResponse {
    tools = [];
    static deserializeBinaryFromReader(response, reader) {
        while (reader.nextField() && !reader.isEndGroup()) {
            if (reader.getFieldNumber() !== 1 && reader.getFieldNumber() !== 2) {
                reader.skipField();
                continue;
            }
            const tool = { strToolName: "" };
            reader.readMessage(tool, (item, fields) => {
                while (fields.nextField() && !fields.isEndGroup()) {
                    if (fields.getFieldNumber() === 1)
                        item.strToolName = fields.readString();
                    else
                        fields.skipField();
                }
            });
            if (tool.strToolName)
                response.tools.push(tool);
        }
    }
}
async function compatManagerTools(appId) {
    const transport = DFL.findModuleExport((e) => e?.SendMsg && e?.GetConnectionDetails);
    const message = DFL.findModuleExport((e) => e?.Init && e?.InitFromMsg && e?.InitFromPacket);
    const protobuf = DFL.findModule((m) => m?.BinaryWriter && m?.BinaryReader);
    if (!transport || !message || !protobuf)
        throw new Error("CompatManager not found");
    class CompatToolsRequest {
        serializeBinary() {
            const writer = new protobuf.BinaryWriter();
            writer.writeUint32(1, appId);
            return writer.getResultBuffer();
        }
    }
    const response = await transport.SendMsg("CompatManager.GetCompatTools#1", message.Init(CompatToolsRequest), CompatToolsResponse, { ePrivilege: 1, eClientExecutionSite: 2 });
    if (!response.BIsValid() || !response.BSuccess())
        throw new Error(response.GetErrorMessage());
    return response.Body().tools;
}
// The tools Steam lists for a game, or null when it doesn't say (a game always has some, so empty is no answer).
async function listedCompatTools(appId) {
    for (const source of [compatManagerTools, (id) => SteamClient.Apps.GetAvailableCompatTools(id)]) {
        try {
            const tools = await Promise.race([source(appId), new Promise((resolve) => setTimeout(() => resolve(null), 3000))]);
            if (tools?.length)
                return tools;
        }
        catch (e) {
            await logError$4(`listedCompatTools: ${String(e)}`).catch(() => null);
        }
    }
    return null;
}
function isCachyosTool(name, label) {
    return /cachyos/.test(`${name} ${label}`.toLowerCase().replace(/[-_\s]/g, ""));
}
// Sets the patched Proton-CachyOS for the game once Steam lists it (Steam picks up new tools on restart).
// When Steam doesn't say what it lists, it's set anyway: the dialog asks the user to check it.
async function selectLiteProton(appid, status) {
    if (!status?.lite_tool_name)
        return null;
    if (status.tool_name === status.lite_tool_name)
        return status;
    const tools = await listedCompatTools(parseInt(appid, 10));
    if (tools && !tools.some((t) => t.strToolName === status.lite_tool_name))
        return null;
    // Moving off an older Lite copy keeps the Proton the game had before Lite.
    if (!(status.tool_name || "").endsWith(LITE_TOOL_SUFFIX))
        await rememberCompatTool(appid, status.tool_name || "");
    SteamClient.Apps.SpecifyCompatTool(parseInt(appid, 10), status.lite_tool_name);
    return { ...status, supported: true, previous_tool: status.tool_name || "", tool_name: status.lite_tool_name, tool_label: status.lite_proton, takes_dll_path: true };
}
// The game's Proton as Steam has it right now, or null for Steam's default. config.vdf can lag behind, and so
// can appDetailsStore, so that one is only the fallback.
function liveCompatTool(appId) {
    return new Promise((resolve) => {
        let done = false;
        let reg = null;
        const cached = () => {
            try {
                return window.appDetailsStore?.GetAppDetails?.(appId);
            }
            catch (e) {
                return null;
            }
        };
        const finish = (details) => {
            if (done)
                return;
            done = true;
            try {
                reg?.unregister();
            }
            catch (e) { }
            resolve(details?.strCompatToolName ? { name: details.strCompatToolName, label: details.strCompatToolDisplayName || details.strCompatToolName } : null);
        };
        try {
            reg = SteamClient.Apps.RegisterForAppDetails(appId, finish);
            if (done)
                reg?.unregister();
        }
        catch (e) {
            finish(cached());
        }
        setTimeout(() => finish(cached()), 1500);
    });
}
// The backend's status with the game's live Proton.
function withLiveCompatTool(status, live) {
    const s = status || { supported: false };
    if (!live)
        return s;
    return {
        ...s,
        tool_name: live.name,
        tool_label: live.label,
        supported: isCachyosTool(live.name, live.label),
        takes_dll_path: live.name === s.lite_tool_name || (live.name === s.tool_name && !!s.takes_dll_path),
    };
}
async function getLiteStatus(id) {
    const [r, live] = await Promise.all([
        getCachyosFsr4Status(id).catch((e) => logError$4(`SteamGameCombinedSection -> cachyos status: ${String(e)}`).then(() => null)),
        liveCompatTool(parseInt(id, 10)),
    ]);
    return withLiveCompatTool(r, live);
}
// Steam lists the Lite Proton after a restart: this sets it for the games the Lite toggle left waiting. Steam
// may still be starting when the plugin loads, so it tries a few times.
const LITE_PENDING_TRIES = 6;
const LITE_PENDING_RETRY_MS = 5000;
async function selectPendingLiteProton(attempt = 1) {
    let selected = false;
    let waiting = false;
    for (const id of await getLiteProtonPending()) {
        const current = await getLaunchOptions(parseInt(id, 10)).catch(() => "");
        if (!fsr4LitePathIn(current)) {
            // Lite was turned off, unless these are empty because Steam hasn't answered yet.
            if (current || attempt >= LITE_PENDING_TRIES)
                await setLiteProtonPending(id, false);
            else
                waiting = true;
            continue;
        }
        const status = await getLiteStatus(id);
        const done = status.takes_dll_path ? status : await selectLiteProton(id, status);
        if (done) {
            await setLiteProtonPending(id, false);
            selected = selected || !status.takes_dll_path;
        }
        else {
            waiting = true;
        }
    }
    if (selected)
        toaster.toast({ title: "Jedi ReFrameShade4All", body: "FSR 4.1.2 Lite Proton set." });
    if (waiting && attempt < LITE_PENDING_TRIES)
        setTimeout(() => void selectPendingLiteProton(attempt + 1).catch((e) => logError$4(`selectPendingLiteProton: ${String(e)}`)), LITE_PENDING_RETRY_MS);
}
// Asks the user to check the game's Proton: with any other Proton the Lite DLL isn't loaded.
function showLiteProtonModal(status) {
    if (status?.takes_dll_path) {
        DFL.showModal(window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: "Check the Proton", strDescription: `Confirm "${status.tool_label}" is selected in the game's Properties → Compatibility.`, strOKButtonText: "Done", bAlertDialog: true }));
        return;
    }
    DFL.showModal(window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: "Restart Steam", strDescription: `"${status?.lite_proton}" installed. Restart Steam to finish.`, strOKButtonText: "Restart Steam", strCancelButtonText: "Later", onOK: () => SteamClient.User.StartRestart(false) }));
}
// Proton-CachyOS variables the toggles add as NAME=1.
const FSR4_UPGRADE_ENV = "FSR4_UPGRADE";
const FSR4_INDICATOR_ENV = "PROTON_FSR4_INDICATOR";
// Set to the Lite DLL's absolute path: the plugin's patched Proton-CachyOS copies that file into the prefix
// and turns FSR4_UPGRADE on itself, so the Lite toggle never touches FSR4_UPGRADE.
const PROTON_FSR4_UPGRADE_ENV = "PROTON_FSR4_UPGRADE";
const FSR4_LITE_DIR = "/fgmod-proton-fsr4/";
// Adds/removes NAME=value while keeping the rest of the launch options.
function withLaunchEnv(opts, name, enabled, value = "1") {
    const rest = (opts || "").replace(new RegExp(`(^|\\s)${name}=\\S*`, "g"), " ").trim().replace(/\s+/g, " ");
    if (!enabled)
        return rest === "%command%" ? "" : rest;
    if (!rest)
        return `${name}=${value} %command%`;
    return rest.includes("%command%") ? `${name}=${value} ${rest}` : `${name}=${value} %command% ${rest}`;
}
function hasLaunchEnv(opts, name) {
    return new RegExp(`(^|\\s)${name}=1(\\s|$)`).test(opts || "");
}
// The Lite DLL path in PROTON_FSR4_UPGRADE, or "" when the launch options don't point at it.
function fsr4LitePathIn(opts) {
    const m = (opts || "").match(new RegExp(`(?:^|\\s)${PROTON_FSR4_UPGRADE_ENV}=(\\S+)`));
    return m && m[1].includes(FSR4_LITE_DIR) ? m[1] : "";
}
// PROTON_FSR4_UPGRADE=<Lite DLL>; "" removes it.
function withProtonFsr4(opts, dll) {
    return withLaunchEnv(opts, PROTON_FSR4_UPGRADE_ENV, !!dll, dll);
}
const logError$4 = callable("log_error");
// What the game's HelixSR folder and helixsr.log say (helixsr.log appears once OptiScaler loads HelixSR).
function HelixSRGameStatus({ info }) {
    const lines = [];
    if (!info.configured) {
        lines.push({ color: "#ffb84d", text: "⚠️ OptiScaler.ini doesn't point at HelixSR anymore. Press Patch All again." });
    }
    if (info.log_status === "running") {
        lines.push({ color: "green", text: `✅ HelixSR ${info.version || ""} is upscaling${info.last_upscale ? `: ${info.last_upscale}` : ""}` });
    }
    else if (info.log_status === "error") {
        lines.push({ color: "#ff6b6b", text: `❌ HelixSR loaded but its network isn't running.${info.errors?.length ? `\n${info.errors.join("\n")}` : ""}` });
    }
    else if (info.log_status === "loaded") {
        lines.push({ color: undefined, text: `HelixSR ${info.version || ""} was loaded but hasn't upscaled yet. In OptiScaler (Insert), pick "HLX DLSS" (3.x) or "FSR HelixSR" (2.0) as the upscaler.` });
    }
    else {
        lines.push({ color: undefined, text: info.selectable
                ? `HelixSR ${info.version || ""} is set up. In OptiScaler (Insert), pick "HLX DLSS".`
                : `HelixSR ${info.version || ""} is set up but hasn't been loaded yet. Start the game and select DLSS as its upscaler.` });
    }
    if (info.log_time) {
        lines.push({ color: undefined, text: `helixsr.log: ${info.log_time}` });
    }
    return (window.SP_REACT.createElement("div", { style: { marginTop: "4px", whiteSpace: "pre-wrap", wordBreak: "break-word" } }, lines.map((l, i) => (window.SP_REACT.createElement("div", { key: i, style: { color: l.color, opacity: l.color ? 1 : 0.8 } }, l.text)))));
}
const getHelixSRStatus = callable("get_helixsr_status");
const installLatestHelixSR = callable("install_latest_helixsr");
const cancelHelixSRSetup = callable("cancel_helixsr_setup");
const formatElapsed = (seconds) => {
    const s = Math.max(0, Math.floor(seconds || 0));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};
// HelixSR runtime: shows whether the newest HelixSR release is installed and, if not,
// downloads it and builds its network on this device (replacing the installed one).
function HelixSRPanel() {
    const [info, setInfo] = SP_REACT.useState(null);
    const [working, setWorking] = SP_REACT.useState(false);
    const [message, setMessage] = SP_REACT.useState("");
    const refresh = async () => {
        try {
            setInfo(await getHelixSRStatus(true));
        }
        catch (e) {
            await logError$4(`HelixSRPanel -> status: ${String(e)}`);
        }
    };
    const building = info?.setup?.state === "running";
    const download = info?.download;
    const downloading = Boolean(download?.active);
    const busy = building || downloading;
    SP_REACT.useEffect(() => {
        void refresh();
    }, []);
    SP_REACT.useEffect(() => {
        if (!busy)
            return () => { };
        const id = setInterval(() => void refresh(), 1500);
        return () => clearInterval(id);
    }, [busy]);
    const doInstall = async () => {
        try {
            setWorking(true);
            setMessage("Checking the latest HelixSR release…");
            const r = await installLatestHelixSR();
            setMessage(r.status === "success" ? `✅ ${r.message || "Done"}` : `❌ ${r.message || "Failed"}`);
        }
        catch (e) {
            setMessage(`❌ ${String(e)}`);
        }
        finally {
            setWorking(false);
            await refresh();
        }
    };
    const handleInstall = () => {
        DFL.showModal(window.SP_REACT.createElement(DFL.ConfirmModal, { strTitle: `${info?.installed ? "Update to" : "Install"} ${info?.latest_label || "HelixSR"}?`, strDescription: "HelixSR's setup downloads NVIDIA's DLSS 310.7.0 DLL from NVIDIA's GitHub (NVIDIA's license applies), a portable Python and Microsoft's shader compiler, builds the network on this device and deletes NVIDIA's DLL again. It takes about 7-10 minutes on a Steam Deck: keep it plugged in and awake. The installed HelixSR (if any) is replaced once the build succeeds.", strOKButtonText: "Download and build", strCancelButtonText: "Cancel", onOK: () => void doInstall() }));
    };
    const handleCancel = async () => {
        try {
            const r = await cancelHelixSRSetup();
            setMessage(r.status === "success" ? `✅ ${r.message}` : `❌ ${r.message || "Failed"}`);
        }
        catch (e) {
            setMessage(`❌ ${String(e)}`);
        }
        finally {
            await refresh();
        }
    };
    const setup = info?.setup;
    // Full release names: "HelixSR 3.2.0 (pre-release)", or "(re-uploaded …)" for a new zip under the same tag.
    const installedName = info?.installed_label || `HelixSR ${info?.installed_version || ""}`.trim();
    const installedLine = !info
        ? "Checking HelixSR…"
        : info.installed
            ? info.up_to_date
                ? `🟢 ${installedName} installed (latest)`
                : info.latest_label
                    ? `🟡 ${installedName} installed — ${info.latest_label} available`
                    : `🟢 ${installedName} installed`
            : `⚪ HelixSR not installed${info.latest_label ? ` (latest: ${info.latest_label})` : ""}`;
    const showInstallButton = info && !busy && !info.up_to_date;
    const mb = (bytes) => `${((bytes || 0) / 1048576).toFixed(0)} MB`;
    const downloadText = !downloading
        ? ""
        : download.phase === "verifying"
            ? "Verifying the download (SHA256)…"
            : download.phase === "extracting"
                ? "Extracting…"
                : download.total
                    ? `Downloading: ${mb(download.bytes)} of ${mb(download.total)}`
                    : `Downloading: ${mb(download.bytes)}`;
    const downloadProgress = !downloading
        ? 0
        : download.phase === "downloading"
            ? (download.total ? Math.min(99, Math.floor((download.bytes / download.total) * 100)) : 0)
            : 100;
    return (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", padding: "8px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px" } },
                window.SP_REACT.createElement("div", null, installedLine),
                info?.message && window.SP_REACT.createElement("div", { style: { opacity: 0.7, marginTop: "2px" } }, info.message),
                setup?.state === "failed" && (window.SP_REACT.createElement("div", { style: { color: "#ff6b6b", marginTop: "4px", whiteSpace: "pre-wrap", wordBreak: "break-word" } },
                    "❌ The last HelixSR build failed.",
                    (setup.errors || []).length > 0 ? `\n${setup.errors.join("\n")}` : "",
                    `\nLog: ${setup.log_path}`)),
                download?.error && (window.SP_REACT.createElement("div", { style: { color: "#ff6b6b", marginTop: "4px", whiteSpace: "pre-wrap", wordBreak: "break-word" } }, `❌ ${download.label || `HelixSR ${download.version || ""}`} download failed: ${download.error}`)),
                setup?.state === "stopped" && (window.SP_REACT.createElement("div", { style: { opacity: 0.7, marginTop: "4px" } }, "The last HelixSR build was interrupted (sleep or restart). Start it again.")))),
        downloading && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ProgressBarWithInfo, { layout: "below", bottomSeparator: "none", indeterminate: download.phase === "downloading" && !download.total,nProgress: downloadProgress, sOperationText: downloadText, description: `${download.label || `HelixSR ${download.version || ""}`}: the build starts right after. You can close this menu.` }))),
        building && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ProgressBarWithInfo, { layout: "below", bottomSeparator: "none", nProgress: setup.progress || 0, sOperationText: setup.phase || "Building HelixSR…", sTimeRemaining: setup.elapsed != null ? formatElapsed(setup.elapsed) : undefined, description: `Building HelixSR ${setup.tag || ""} — about 7-10 minutes on a Steam Deck. You can close this menu.` }))),
        showInstallButton && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleInstall, disabled: working }, working
                ? "Starting…"
                : info.installed
                    ? `⬆️ Update to ${info.latest_label || "the latest HelixSR"}`
                    : `⬇️ Install ${info.latest_label || "HelixSR"}`))),
        building && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleCancel }, "Cancel HelixSR build"))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.8em", opacity: 0.6 } }, "After installing or updating HelixSR, press Patch All again. In-game: pick HLX DLSS in OptiScaler (Insert).")),
        message && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", whiteSpace: "pre-wrap", opacity: 0.85 } }, message)))));
}
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
function gameOptionLabel(game) {
    return game.non_steam ? `${game.name} · non-Steam` : game.name;
}
function SteamGameCombinedSection({ fsr4Variant, appid, setAppid, }) {
    const [games, setGames] = SP_REACT.useState([]);
    const [engines, setEngines] = SP_REACT.useState(null);
    const [status, setStatus] = SP_REACT.useState(null);
    const [addon, setAddon] = SP_REACT.useState(true);
    const [busy, setBusy] = SP_REACT.useState(false);
    const [result, setResult] = SP_REACT.useState("");
    const [cachyos, setCachyos] = SP_REACT.useState(null);
    const [fsr4Upgrade, setFsr4Upgrade] = SP_REACT.useState(false);
    const [fsr4Indicator, setFsr4Indicator] = SP_REACT.useState(false);
    const [fsr4LitePath, setFsr4LitePath] = SP_REACT.useState("");
    const [lsfg, setLsfg] = SP_REACT.useState(null);
    const [lsfgFps, setLsfgFps] = SP_REACT.useState(LSFG_FPS_MIN);
    const lsfgSaveTimer = SP_REACT.useRef(null);
    SP_REACT.useEffect(() => () => clearTimeout(lsfgSaveTimer.current), []);
    // On only while the backend has the game's profile and ~/.jedi-lsfg is in its launch options.
    const loadLsfg = async (id) => {
        setLsfg(null);
        try {
            const [r, current] = await Promise.all([getLsfgStatus(id), getLaunchOptions(parseInt(id, 10)).catch(() => "")]);
            if (r.status !== "success") {
                await logError$4(`SteamGameCombinedSection -> lsfg status: ${r.message}`);
                return;
            }
            setLsfg({ ...r, enabled: r.enabled && hasLsfgWrapper(current) });
            setLsfgFps(r.target_fps);
        }
        catch (e) {
            await logError$4(`SteamGameCombinedSection -> lsfg: ${String(e)}`);
        }
    };
    const handleLsfgToggle = async (enabled) => {
        if (!appid)
            return;
        const id = parseInt(appid, 10);
        try {
            setBusy(true);
            if (!enabled) {
                const next = withLsfgWrapper(await getLaunchOptions(id), false);
                SteamClient.Apps.SetAppLaunchOptions(id, next);
                setLsfg({ ...lsfg, enabled: false });
                const r = await disableLsfg(appid);
                setResult(r.status === "success" ? `✅ Launch options: ${next || "(empty)"}` : `❌ ${r.message || "Could not turn LSFG-VK off."}`);
                return;
            }
            if (!lsfg?.renderer_installed)
                setResult("Installing MAKO Renderer…");
            const nonSteam = !!games.find((g) => g.appid === appid)?.non_steam;
            const r = await enableLsfg(appid, lsfgFps, nonSteam);
            if (r.status !== "success") {
                setResult(`❌ ${r.message || "Could not turn LSFG-VK on."}`);
                return;
            }
            const next = withLsfgWrapper(await getLaunchOptions(id), true);
            SteamClient.Apps.SetAppLaunchOptions(id, next);
            setLsfg({ ...lsfg, renderer_installed: true, lossless_found: true, enabled: true });
            setLsfgFps(r.target_fps);
            setResult(`✅ Launch options: ${next}`);
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            await logError$4(`SteamGameCombinedSection -> lsfg toggle: ${String(e)}`);
        }
        finally {
            setBusy(false);
        }
    };
    const handleLsfgFps = (value) => {
        setLsfgFps(value);
        clearTimeout(lsfgSaveTimer.current);
        const id = appid;
        lsfgSaveTimer.current = setTimeout(async () => {
            const r = await setLsfgTargetFps(id, value).catch((e) => ({ status: "error", message: String(e) }));
            if (r.status !== "success")
                setResult(`❌ ${r.message || "Could not save the target FPS."}`);
        }, LSFG_SAVE_DEBOUNCE_MS);
    };
    const loadCachyos = async (id) => {
        setCachyos(null);
        try {
            let [r, current] = await Promise.all([getLiteStatus(id), getLaunchOptions(parseInt(id, 10)).catch(() => "")]);
            const litePath = fsr4LitePathIn(current);
            // Up to 1.1.22 the Lite toggle also added FSR4_UPGRADE=1, which turned the FSR4 toggle on with it.
            if (litePath && hasLaunchEnv(current, FSR4_UPGRADE_ENV)) {
                current = withLaunchEnv(current, FSR4_UPGRADE_ENV, false);
                SteamClient.Apps.SetAppLaunchOptions(parseInt(id, 10), current);
            }
            // The toggles show first, so nothing below can hide them.
            setCachyos(r);
            setFsr4Upgrade(hasLaunchEnv(current, FSR4_UPGRADE_ENV));
            setFsr4Indicator(hasLaunchEnv(current, FSR4_INDICATOR_ENV));
            setFsr4LitePath(litePath);
            // Lite on but the game isn't on the Lite Proton yet: switch it once Steam lists it (after a restart).
            if (litePath && !r.takes_dll_path) {
                const selected = await selectLiteProton(id, r);
                if (selected) {
                    setCachyos(selected);
                    showLiteProtonModal(selected);
                }
            }
        }
        catch (e) {
            await logError$4(`SteamGameCombinedSection -> cachyos: ${String(e)}`);
        }
    };
    const applyProtonFsr4 = async (dll) => {
        const current = await getLaunchOptions(parseInt(appid, 10));
        const next = withProtonFsr4(current, dll);
        SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), next);
        setFsr4LitePath(dll);
        return next;
    };
    // On: the game on a Proton-CachyOS that takes the Lite DLL (the plugin's patched copy, installed only when
    // missing) and PROTON_FSR4_UPGRADE=<Lite DLL> in its launch options. FSR4 and the watermark stay their own
    // toggles. Off: the variable goes and the game's previous Proton comes back.
    const handleFsr4LiteToggle = async (enabled) => {
        if (!appid)
            return;
        try {
            setBusy(true);
            if (!enabled) {
                const next = await applyProtonFsr4("");
                setResult(`✅ Launch options: ${next || "(empty)"}`);
                if (cachyos?.lite_tool_name && (cachyos.tool_name || "").endsWith(LITE_TOOL_SUFFIX) && cachyos.previous_tool !== null && cachyos.previous_tool !== undefined) {
                    SteamClient.Apps.SpecifyCompatTool(parseInt(appid, 10), cachyos.previous_tool);
                    setCachyos({ ...cachyos, supported: isCachyosTool(cachyos.previous_tool, ""), tool_name: cachyos.previous_tool, tool_label: cachyos.previous_tool || "Steam default", takes_dll_path: false });
                    setResult("✅ FSR 4.1.2 Lite off.");
                }
                return;
            }
            const r = await prepareCachyosFsr4Lite();
            if (r.status !== "success" || !r.path) {
                setResult(`❌ ${r.message || "Could not prepare the FSR 4.1.2 Lite DLL."}`);
                return;
            }
            // Always checks Proton-CachyOS's newest release: a newer one replaces the Lite copy (same name, so
            // games keep it); otherwise the copy already there is reused.
            setResult("Checking Proton-CachyOS…");
            const upd = await getProtonLiteUpdateStatus().catch(() => null);
            if (upd?.status === "success" && upd.update_available)
                setResult(upd.installed ? `Updating the Lite Proton to ${upd.latest} (~330 MB)…` : "Installing the Lite Proton (~330 MB)…");
            const inst = await installProtonLite();
            if (inst.status !== "success") {
                setResult(`❌ ${inst.message || "Could not install the Lite Proton."}`);
                return;
            }
            let status = await getLiteStatus(appid);
            if (!status.takes_dll_path) {
                status = (await selectLiteProton(appid, status)) || status;
                if (!status.takes_dll_path)
                    await setLiteProtonPending(appid, true);
            }
            const next = await applyProtonFsr4(r.path);
            setCachyos(status);
            const note = inst.message ? `\n${inst.message}` : inst.updated ? `\nLite Proton updated: ${inst.tool_label}.` : "";
            setResult(status.takes_dll_path
                ? `✅ FSR 4.1.2 Lite on.${note}\n\n${next}`
                : `✅ Lite Proton installed. Restart Steam to finish.${note}\n\n${next}`);
            showLiteProtonModal(status);
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            await logError$4(`SteamGameCombinedSection -> fsr4Lite: ${String(e)}`);
        }
        finally {
            setBusy(false);
        }
    };
    const handleLaunchEnvToggle = async (name, enabled, setChecked, value = "1") => {
        if (!appid)
            return;
        try {
            const current = await getLaunchOptions(parseInt(appid, 10));
            const next = withLaunchEnv(current, name, enabled, value);
            SteamClient.Apps.SetAppLaunchOptions(parseInt(appid, 10), next);
            setChecked(enabled);
            setResult(`✅ Launch options: ${next || "(empty)"}`);
        }
        catch (e) {
            setResult(`❌ ${String(e)}`);
            await logError$4(`SteamGameCombinedSection -> ${name}: ${String(e)}`);
        }
    };
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
            const r = await patchAllGame(appid, fsr4Variant, addon, current, "");
            if (r.status === "success") {
                if (r.launch_options && fsr4Upgrade)
                    r.launch_options = withLaunchEnv(r.launch_options, FSR4_UPGRADE_ENV, true);
                if (r.launch_options && fsr4LitePath)
                    r.launch_options = withProtonFsr4(r.launch_options, fsr4LitePath);
                if (r.launch_options && fsr4Indicator)
                    r.launch_options = withLaunchEnv(r.launch_options, FSR4_INDICATOR_ENV, true);
                if (r.launch_options) {
                    try {
                        r.launch_options = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), r.launch_options);
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
            const current = await getLaunchOptions(parseInt(appid, 10));
            const r = await unpatchAllGame(appid, current);
            if (r.status === "success") {
                try {
                    r.launch_options = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), r.launch_options || "");
                }
                catch (e) {
                    await logError$4(`SetAppLaunchOptions(remove): ${String(e)}`);
                }
                setResult(`✅ ${r.message || "Removed"}` +
                    (r.launch_options ? `\n\nLaunch options restored:\n${r.launch_options}` : "\n\nLaunch options cleared."));
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
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "\uD83C\uDFAE Game \u2014 Patch All" },
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.9em", opacity: 0.85 } },
                "Pick a game and press ",
                window.SP_REACT.createElement("b", null, "Patch All"),
                ": OptiScaler + ReShade, launch options included.")),
        engines && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.82em", opacity: 0.7 } },
                engines.optiscaler_installed ? `🟢 OptiScaler ${engines.optiscaler_version || ""}` : "⚪ OptiScaler not installed",
                "  •  ",
                engines.reshade_installed ? `🟢 ReShade ${engines.reshade_version || ""}` : "⚪ ReShade not installed"))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.DropdownItem, { rgOptions: games.map((g) => ({ data: g.appid, label: gameOptionLabel(g) })), selectedOption: appid, onChange: (o) => {
                    setAppid(o.data);
                    setResult("");
                    void loadStatus(o.data);
                    void loadCachyos(o.data);
                    void loadLsfg(o.data);
                }, strDefaultLabel: "Select a game..." })),
        appid && lsfg && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ToggleField, { label: "LSFG-VK", description: lsfg.lossless_found ? "Lossless Scaling frame generation." : "Needs Lossless Scaling on Steam.", checked: lsfg.enabled, disabled: busy, onChange: (v) => void handleLsfgToggle(v) }))),
        appid && lsfg?.enabled && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.SliderField, { label: `Target FPS · ${lsfgFps}`, value: lsfgFps, min: LSFG_FPS_MIN, max: LSFG_FPS_MAX, step: 1, notchCount: LSFG_FPS_NOTCHES.length, notchLabels: LSFG_FPS_NOTCHES, notchTicksVisible: true, showValue: false, onChange: handleLsfgFps }))),
        status && appid && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", padding: "8px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px" } },
                window.SP_REACT.createElement("div", null,
                    "Frame Generation: ",
                    status.optiscaler_patched ? `on (${status.optiscaler_slot})` : "off"),
                status.optiscaler_patched && status.optiscaler_variant_label && (window.SP_REACT.createElement("div", null,
                    "Upscaler runtime: ",
                    status.optiscaler_variant_label)),
                window.SP_REACT.createElement("div", null,
                    "ReShade: ",
                    status.reshade_present ? `on (${status.reshade_slot})` : "off"),
                status.both_active && window.SP_REACT.createElement("div", { style: { color: "green", marginTop: "2px" } }, "\u2705 Both active and coexisting"),
                status.helixsr && window.SP_REACT.createElement(HelixSRGameStatus, { info: status.helixsr })))),
        status && appid && status.helixsr && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: () => void loadStatus(appid), disabled: busy }, "\ud83d\udd04 Check HelixSR again"))),
        appid && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            // FSR4 and the watermark: for Proton-CachyOS games, games on Lite, or while their variable is still set.
            (cachyos?.supported || fsr4LitePath || fsr4Upgrade) && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: "Proton-CachyOS FSR4", description: `Turns on FSR4${cachyos?.tool_label ? ` (${cachyos.tool_label})` : ""}.`, checked: fsr4Upgrade, disabled: busy, onChange: (v) => void handleLaunchEnvToggle(FSR4_UPGRADE_ENV, v, setFsr4Upgrade) }))),
            // Lite brings its own Proton, so it shows for every game.
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: "Proton FSR4 → 4.1.2 Lite", description: "FSR 4.1.2 Lite via its own Proton-CachyOS. FSR 3.1, DX12 games.", checked: !!fsr4LitePath, disabled: busy || !cachyos, onChange: (v) => void handleFsr4LiteToggle(v) })),
            // The patched Proton is installed but Steam doesn't list it yet: it needs a restart.
            fsr4LitePath && cachyos && !cachyos.takes_dll_path && cachyos.lite_tool_name && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: { fontSize: "0.82em", color: "#ffb84d" } }, "⚠️ Restart Steam to finish."))),
            fsr4LitePath && cachyos && !cachyos.takes_dll_path && cachyos.lite_tool_name && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: () => SteamClient.User.StartRestart(false), disabled: busy }, "🔄 Restart Steam"))),
            (cachyos?.supported || fsr4LitePath || fsr4Indicator) && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: "Show FSR watermark", description: "Shows which FSR runs, top left.", checked: fsr4Indicator, disabled: busy, onChange: (v) => void handleLaunchEnvToggle(FSR4_INDICATOR_ENV, v, setFsr4Indicator) }))),
            window.SP_REACT.createElement(HelixSRPanel, null),
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
const getCombinedGameStatus = callable("get_combined_game_status");
const removeReShadeOnly = callable("remove_reshade_only");
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
function ReShadeInstallerSection({ appid, targetExePath = "" }) {
    const [installing, setInstalling] = SP_REACT.useState(false);
    const [uninstalling, setUninstalling] = SP_REACT.useState(false);
    const [applyingToSteamGame, setApplyingToSteamGame] = SP_REACT.useState(false);
    const [removingFromGame, setRemovingFromGame] = SP_REACT.useState(false);
    const [installResult, setInstallResult] = SP_REACT.useState(null);
    const [uninstallResult, setUninstallResult] = SP_REACT.useState(null);
    const [steamGameResult, setSteamGameResult] = SP_REACT.useState(null);
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
    SP_REACT.useEffect(() => {
        setSteamGameResult(null);
    }, [appid]);
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
                message: "Pick a game above first."
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
            setSteamGameResult({
                status: "success",
                message: "Applying ReShade to the selected game..."
            });
            const result = await manageGameReShade(appid, "install", selectedSteamGameApi, "", targetExePath || "");
            if (result.status !== "success") {
                setSteamGameResult({
                    status: "error",
                    message: result.message || result.output || "Failed to apply ReShade."
                });
                return;
            }
            const resolvedApi = getResolvedReShadeApi(result.output, selectedSteamGameApi);
            const appliedTarget = result.target_executable || result.target_dir;
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
            let launchOptions = buildSteamLaunchOptions(resolvedApi, optiscalerSlot);
            try {
                launchOptions = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), launchOptions);
            }
            catch (e) {
                await logError$2(`ReShadeInstallerSection -> SetAppLaunchOptions: ${String(e)}`);
            }
            setSteamGameResult({
                status: "success",
                output: `ReShade applied with ${resolvedApi.toUpperCase()}.\n` +
                    (appliedTarget ? `Target: ${appliedTarget}\n` : "") +
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
    // Drops ReShade from the chosen game and keeps OptiScaler patched: the backend
    // reports the slot that stays behind so the overrides can be rebuilt for it.
    const handleRemoveOnlyReShade = async () => {
        if (!appid)
            return;
        try {
            setRemovingFromGame(true);
            setSteamGameResult({ status: "success", message: "Removing ReShade…" });
            const current = await getLaunchOptions$1(parseInt(appid, 10));
            const result = await removeReShadeOnly(appid, targetExePath || "", current);
            if (result.status !== "success") {
                setSteamGameResult({
                    status: "error",
                    message: result.message || result.output || "Failed to remove ReShade."
                });
                return;
            }
            try {
                result.launch_options = await setLaunchOptionsKeepingLsfg(parseInt(appid, 10), result.launch_options || "");
            }
            catch (e) {
                await logError$2(`ReShadeInstallerSection -> SetAppLaunchOptions: ${String(e)}`);
            }
            setSteamGameResult({
                status: "success",
                output: `${result.message || "ReShade removed."}\n` +
                    (result.launch_options
                        ? `Launch options updated automatically:\n${result.launch_options}`
                        : "Launch options cleared.")
            });
        }
        catch (e) {
            setSteamGameResult({ status: "error", message: String(e) });
            await logError$2(`ReShadeInstallerSection -> removeOnlyReShade: ${String(e)}`);
        }
        finally {
            setRemovingFromGame(false);
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
        pathExists === true && appid && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.DropdownItem, { rgOptions: RESHADE_DLL_OPTIONS, selectedOption: selectedSteamGameApi, onChange: (option) => {
                        setSelectedSteamGameApi(option.data);
                        setSteamGameResult(null);
                    }, strDefaultLabel: "Game ReShade API" })),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7, wordBreak: "break-all" } }, targetExePath ? `Target: ${targetExePath}` : "Target: automatic detection")),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleApplyReShadeToSteamGame, disabled: applyingToSteamGame || removingFromGame || !appid }, applyingToSteamGame ? "Applying ReShade..." : "Apply only ReShade")),
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleRemoveOnlyReShade, disabled: applyingToSteamGame || removingFromGame || !appid }, removingFromGame ? "Removing ReShade..." : "🗑️ Remove only ReShade")))),
        pathExists === true && !appid && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", opacity: 0.7 } }, "Pick a game above to apply or remove it."))),
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
                : `❌ Error: ${steamGameResult.message || "Operation failed"}`)))));
}

const getPluginUpdateStatus = callable("get_plugin_update_status");
const installPluginUpdate = callable("install_plugin_update");
// Plugin self-update: compares this plugin with its newest GitHub release; the backend writes the
// release over the plugin and Decky reloads it. (Decky's own install prompt didn't show from the Quick Access menu.)
// Survives the reload after an update, so the reloaded panel can say it worked.
const PLUGIN_UPDATED_KEY = "jedi-reframeshade4all-updated-to";
function PluginUpdateSection() {
    const [info, setInfo] = SP_REACT.useState(null);
    const [checking, setChecking] = SP_REACT.useState(false);
    const [updating, setUpdating] = SP_REACT.useState(false);
    const [message, setMessage] = SP_REACT.useState("");
    const refresh = async (force = false) => {
        try {
            setChecking(true);
            const status = await getPluginUpdateStatus(force);
            setInfo(status);
            let updatedTo = null;
            try {
                updatedTo = localStorage.getItem(PLUGIN_UPDATED_KEY);
                if (updatedTo)
                    localStorage.removeItem(PLUGIN_UPDATED_KEY);
            }
            catch (e) { }
            if (updatedTo && updatedTo === status?.installed_version) {
                setMessage(`✅ Updated to v${updatedTo}.`);
                toaster.toast({ title: "Jedi ReFrameShade4All", body: `Updated to v${updatedTo}.` });
            }
        }
        catch (e) {
            await logError$4(`PluginUpdateSection -> status: ${String(e)}`);
        }
        finally {
            setChecking(false);
        }
    };
    SP_REACT.useEffect(() => {
        void refresh();
    }, []);
    const handleUpdate = async () => {
        try {
            setUpdating(true);
            setMessage(`Downloading v${info.latest_version}… this can take a few minutes.`);
            const r = await installPluginUpdate();
            if (r.status !== "success") {
                setMessage(`❌ ${r.message || "Update failed."}\n\nOr install it in Decky's settings from URL:\n${info.url}`);
                return;
            }
            setMessage(`✅ v${r.version} installed. Reloading the plugin…`);
            try {
                localStorage.setItem(PLUGIN_UPDATED_KEY, r.version);
            }
            catch (e) { }
            try {
                await window.DeckyBackend.call("loader/reload_plugin", r.plugin_name || manifest.name);
            }
            catch (e) {
                setMessage(`✅ v${r.version} installed. Restart the Steam Deck (or Decky) to load it.`);
                await logError$4(`PluginUpdateSection -> reload: ${String(e)}`);
            }
        }
        catch (e) {
            setMessage(`❌ ${String(e)}`);
            await logError$4(`PluginUpdateSection -> install: ${String(e)}`);
        }
        finally {
            setUpdating(false);
        }
    };
    const statusLine = !info
        ? "Checking for updates…"
        : info.status !== "success"
            ? `⚠️ ${info.message || "Could not check for updates."}`
            : info.update_available
                ? `🟡 v${info.installed_version} installed — v${info.latest_version} available`
                : `🟢 v${info.installed_version || "?"} installed (latest)`;
    const size = info?.size ? ` (${Math.round(info.size / 1048576)} MB)` : "";
    return (window.SP_REACT.createElement(DFL.PanelSection, { title: "Plugin Update" },
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em" } }, statusLine)),
        info?.update_available && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: handleUpdate, disabled: updating }, updating ? "Updating…" : `⬆️ Update to v${info.latest_version}${size}`))),
        window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement(DFL.ButtonItem, { layout: "below", onClick: () => void refresh(true), disabled: checking || updating }, checking ? "Checking…" : "🔄 Check for updates")),
        message && (window.SP_REACT.createElement(DFL.PanelSectionRow, null,
            window.SP_REACT.createElement("div", { style: { fontSize: "0.85em", whiteSpace: "pre-wrap", wordBreak: "break-all", opacity: 0.85 } }, message)))));
}
function MainContent() {
    const [pathExists, setPathExists] = SP_REACT.useState(null);
    const [fgmodInfo, setFgmodInfo] = SP_REACT.useState(null);
    const [advanced, setAdvanced] = SP_REACT.useState(false);
    // One FSR4 runtime for every game, shared with the advanced OptiScaler controls.
    const fsr4Variant = DEFAULT_FSR4_VARIANT;
    // The game is also picked once at the top and reused by the advanced sections.
    const [selectedAppid, setSelectedAppid] = SP_REACT.useState("");
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
    return (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
        window.SP_REACT.createElement(SteamGameCombinedSection, { fsr4Variant: fsr4Variant, appid: selectedAppid, setAppid: setSelectedAppid }),
        window.SP_REACT.createElement(DFL.PanelSection, null,
            window.SP_REACT.createElement(DFL.PanelSectionRow, null,
                window.SP_REACT.createElement(DFL.ToggleField, { label: "Advanced controls", description: "Per-engine install, proxy DLL, ReShade shaders/AutoHDR.", checked: advanced, onChange: setAdvanced }))),
        advanced && (window.SP_REACT.createElement(window.SP_REACT.Fragment, null,
            window.SP_REACT.createElement(OptiScalerControls, { pathExists: pathExists, setPathExists: setPathExists, fgmodInfo: fgmodInfo, fsr4Variant: fsr4Variant, appid: selectedAppid }),
            window.SP_REACT.createElement(ReShadeInstallerSection, { appid: selectedAppid }))),
        window.SP_REACT.createElement(PluginUpdateSection, null)));
}
var index = definePlugin(() => {
    void selectPendingLiteProton().catch((e) => logError$4(`selectPendingLiteProton: ${String(e)}`));
    return {
        name: "Jedi ReFrameShade4All",
        titleView: window.SP_REACT.createElement("div", null, "Jedi ReFrameShade4All"),
        alwaysRender: true,
        content: window.SP_REACT.createElement(MainContent, null),
        icon: window.SP_REACT.createElement(MdOutlineAutoAwesomeMotion, null),
        onDismount() {
            console.log("Jedi ReFrameShade4All Plugin unmounted");
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map
