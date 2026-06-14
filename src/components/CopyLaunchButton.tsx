import { useEffect, useState } from "react";
import { ButtonItem, PanelSectionRow } from "@decky/ui";
import { FaClipboard, FaCheck } from "react-icons/fa";
import { copyTextToClipboard } from "../utils/steam";

interface CopyLaunchButtonProps {
  command: string;
  label?: string;
}

/**
 * Reliable "copy launch command" button. The copy runs synchronously inside the
 * click handler (a genuine user gesture) before any await, which is the only way
 * clipboard writes succeed in Steam's gaming-mode CEF — auto-copying after an
 * await silently fails because the transient user-activation is already gone.
 */
export function CopyLaunchButton({ command, label = "Copy launch options" }: CopyLaunchButtonProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return undefined;
    const timer = setTimeout(() => setCopied(false), 3000);
    return () => clearTimeout(timer);
  }, [copied]);

  if (!command) return null;

  const handleCopy = () => {
    // Fire the copy first, within the user gesture; update feedback after.
    void copyTextToClipboard(command).then((ok) => setCopied(ok));
  };

  return (
    <PanelSectionRow>
      <ButtonItem layout="below" onClick={handleCopy}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {copied ? <FaCheck style={{ color: "#4CAF50" }} /> : <FaClipboard />}
          <div style={{ color: copied ? "#4CAF50" : "inherit", fontWeight: copied ? "bold" : "normal" }}>
            {copied ? "Copied to clipboard" : label}
          </div>
        </div>
      </ButtonItem>
    </PanelSectionRow>
  );
}
