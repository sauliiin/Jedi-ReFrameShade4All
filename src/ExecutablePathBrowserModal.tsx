import { useEffect, useRef, useState, type FocusEvent } from "react";
import { ConfirmModal, DialogButton } from "@decky/ui";
import { callable } from "@decky/api";

interface BrowserEntry {
  name: string;
  path: string;
  is_dir: boolean;
  is_file: boolean;
  is_hidden: boolean;
  is_symlink: boolean;
}

interface BrowserResponse {
  status: string;
  current_path?: string;
  parent_path?: string | null;
  entries?: BrowserEntry[];
  message?: string;
}

interface SdCardPathResponse {
  status: string;
  path?: string;
  available?: boolean;
  message?: string;
}

interface ExecutablePathBrowserModalProps {
  initialPath?: string;
  onConfirm: (path: string) => void;
  onCancel: () => void;
  closeModal?: () => void;
}

const browseFilesystemForExecutable = callable<[string, boolean], BrowserResponse>("browse_filesystem_for_executable");
const getSdCardMountPath = callable<[], SdCardPathResponse>("get_sd_card_mount_path");
const logError = callable<[string], void>("log_error");

const DEFAULT_QUICK_PATHS = [
  { label: "Home", path: "/home/deck" },
  { label: "Common", path: "/home/deck/.steam/steam/steamapps/common" },
  { label: "SD Card", path: "/run/media" }
];

const getButtonStyle = (isFocused: boolean, isSelected = false) => ({
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

const ExecutablePathBrowserModal = ({
  initialPath = "/home/deck",
  onConfirm,
  onCancel,
  closeModal
}: ExecutablePathBrowserModalProps) => {
  const [currentPath, setCurrentPath] = useState<string>(initialPath);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [entries, setEntries] = useState<BrowserEntry[]>([]);
  const [quickPaths, setQuickPaths] = useState(DEFAULT_QUICK_PATHS);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [focusedItemKey, setFocusedItemKey] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const parentButtonRef = useRef<HTMLDivElement | null>(null);
  const entryButtonRefs = useRef<Array<HTMLDivElement | null>>([]);

  useEffect(() => {
    void loadDirectory(currentPath, true);
  }, [currentPath]);

  useEffect(() => {
    void loadSdCardPath();
  }, []);

  useEffect(() => {
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

  const loadDirectory = async (path: string, includeHidden: boolean) => {
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
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setError(`Error loading directory: ${message}`);
      await logError(`ExecutablePathBrowserModal -> loadDirectory: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadSdCardPath = async () => {
    try {
      const response = await getSdCardMountPath();
      if (response.status !== "success" || !response.path) {
        return;
      }

      setQuickPaths((previousQuickPaths) => (
        previousQuickPaths.map((quickPath) => (
          quickPath.label === "SD Card"
            ? { ...quickPath, path: response.path! }
            : quickPath
        ))
      ));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      await logError(`ExecutablePathBrowserModal -> loadSdCardPath: ${message}`);
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

  const handleItemFocus = (event: FocusEvent<HTMLElement>) => {
    event.currentTarget.scrollIntoView({
      block: "center",
      inline: "nearest"
    });
  };

  const handleButtonFocus = (focusKey: string) => {
    setFocusedItemKey(focusKey);
  };

  const handleButtonBlur = (focusKey: string) => {
    setFocusedItemKey((currentFocusKey) => (currentFocusKey === focusKey ? null : currentFocusKey));
  };

  const renderDescription = () => {
    return (
      <div style={{ textAlign: "left", maxHeight: "60vh", overflowY: "auto", paddingRight: "8px", paddingBottom: "8px" }}>
        <div
          style={{
            marginBottom: "12px",
            padding: "8px",
            borderRadius: "4px",
            backgroundColor: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.12)",
            fontSize: "0.85em",
            wordBreak: "break-all"
          }}
        >
          Current path: {currentPath}
        </div>

        <div style={{ marginBottom: "12px" }}>
          <div style={{ fontSize: "0.85em", fontWeight: "bold", marginBottom: "6px" }}>
            Quick locations
          </div>
          <div
            style={{
              display: "flex",
              gap: "6px",
              width: "100%"
            }}
          >
            {quickPaths.map((quickPath) => (
              <div
                key={`${quickPath.label}:${quickPath.path}`}
                style={{ flex: "1 1 0", minWidth: 0, display: "flex" }}
                onFocusCapture={(event) => {
                  handleItemFocus(event);
                  handleButtonFocus(`quick:${quickPath.path}`);
                }}
                onBlurCapture={() => handleButtonBlur(`quick:${quickPath.path}`)}
              >
                <DialogButton
                  onClick={() => {
                    setSelectedPath("");
                    setCurrentPath(quickPath.path);
                  }}
                  style={{
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
                  }}
                >
                  {quickPath.label}
                </DialogButton>
              </div>
            ))}
          </div>
        </div>

        {error ? (
          <div
            style={{
              padding: "10px",
              borderRadius: "4px",
              backgroundColor: "#ff6b6b",
              color: "white",
              fontSize: "0.85em"
            }}
          >
            {error}
          </div>
        ) : loading ? (
          <div style={{ padding: "20px", textAlign: "center" }}>Loading entries...</div>
        ) : (
          <>
            <div
              style={{
                maxHeight: "36vh",
                overflowY: "auto",
                borderRadius: "4px",
                border: "1px solid rgba(255,255,255,0.08)",
                padding: "4px 4px 16px 4px",
                scrollBehavior: "smooth",
                scrollPaddingBottom: "72px"
              }}
            >
              <div style={{ paddingBottom: "8px" }}>
                {parentPath && (
                  <div
                    onFocusCapture={(event) => {
                      handleItemFocus(event);
                      handleButtonFocus(`parent:${parentPath}`);
                    }}
                    onBlurCapture={() => handleButtonBlur(`parent:${parentPath}`)}
                  >
                    <DialogButton
                      ref={(element) => {
                        parentButtonRef.current = element;
                      }}
                      onClick={() => {
                        setSelectedPath("");
                        setCurrentPath(parentPath);
                      }}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "10px",
                        marginBottom: "8px",
                        borderRadius: "4px",
                        ...getButtonStyle(focusedItemKey === `parent:${parentPath}`),
                        color: "white",
                        cursor: "pointer",
                        minHeight: "42px"
                      }}
                    >
                      .. Parent Directory
                    </DialogButton>
                  </div>
                )}

                {entries.length === 0 ? (
                  <div style={{ padding: "12px", opacity: 0.8, fontSize: "0.85em" }}>
                    No folders or `.exe` files found here.
                  </div>
                ) : (
                  entries.map((entry, index) => {
                    const isSelected = selectedPath === entry.path;
                    const focusKey = `entry:${entry.path}`;
                    return (
                      <div
                        key={entry.path}
                        onFocusCapture={(event) => {
                          handleItemFocus(event);
                          handleButtonFocus(focusKey);
                        }}
                        onBlurCapture={() => handleButtonBlur(focusKey)}
                      >
                        <DialogButton
                          ref={(element) => {
                            entryButtonRefs.current[index] = element;
                          }}
                          onClick={() => {
                            if (entry.is_dir) {
                              setSelectedPath("");
                              setCurrentPath(entry.path);
                              return;
                            }

                            setSelectedPath(entry.path);
                          }}
                          style={{
                            width: "100%",
                            textAlign: "left",
                            padding: "10px",
                            marginBottom: "8px",
                            borderRadius: "4px",
                            ...getButtonStyle(focusedItemKey === focusKey, isSelected),
                            color: "white",
                            cursor: "pointer",
                            minHeight: "56px"
                          }}
                        >
                          <div style={{ fontSize: "0.9em", fontWeight: "bold", marginBottom: "3px" }}>
                            {entry.is_dir ? "📁" : "🎮"} {entry.name}
                          </div>
                          <div style={{ fontSize: "0.75em", opacity: 0.75, wordBreak: "break-all" }}>
                            {entry.path}
                          </div>
                          <div style={{ fontSize: "0.72em", opacity: 0.6, marginTop: "3px" }}>
                            {entry.is_dir ? "Folder" : "Windows executable"}
                            {entry.is_symlink ? " • Symlink" : ""}
                            {entry.is_hidden ? " • Hidden" : ""}
                          </div>
                        </DialogButton>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {selectedPath && (
              <div
                style={{
                  marginTop: "12px",
                  padding: "10px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(76, 175, 80, 0.14)",
                  border: "1px solid rgba(76, 175, 80, 0.35)",
                  fontSize: "0.82em",
                  wordBreak: "break-all"
                }}
              >
                Selected executable: {selectedPath}
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <ConfirmModal
      strTitle="Choose exe path"
      strDescription={renderDescription()}
      strOKButtonText="Use Selected exe"
      strCancelButtonText="Cancel"
      onOK={handleConfirm}
      onCancel={handleCancel}
      bOKDisabled={loading || !!error || !selectedPath}
    />
  );
};

export default ExecutablePathBrowserModal;
