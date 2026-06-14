// Helpers shared by the OptiScaler/ReShade sections for reading and writing Steam
// launch options and for copying launch commands to the clipboard (non-Steam games).
import { toaster } from "@decky/api";

/** Read the current launch options for a Steam app id. */
export function getLaunchOptions(appId: number): Promise<string> {
  return new Promise((resolve) => {
    try {
      const reg = SteamClient.Apps.RegisterForAppDetails(appId, (details: { strLaunchOptions?: string }) => {
        resolve(details?.strLaunchOptions || "");
        try {
          reg.unregister();
        } catch {
          /* noop */
        }
      });
      setTimeout(() => {
        try {
          reg.unregister();
        } catch {
          /* noop */
        }
        resolve("");
      }, 1500);
    } catch {
      resolve("");
    }
  });
}

/** Write launch options for a Steam app id. */
export function setLaunchOptions(appId: number, options: string): void {
  SteamClient.Apps.SetAppLaunchOptions(appId, options);
}

const dllBase = (slot: string) => slot.replace(/\.dll$/i, "");

/**
 * Build the launch command used for non-Steam games, applying the chosen proxy
 * DLL slots. `OptiScaler.asi` needs no WINEDLLOVERRIDES entry.
 */
export function buildLaunchCommand(slots: string[], includeD3dcompiler = false): string {
  const parts: string[] = [];
  const seen = new Set<string>();
  if (includeD3dcompiler) {
    parts.push("d3dcompiler_47=n");
    seen.add("d3dcompiler_47");
  }
  for (const slot of slots) {
    if (!slot || slot === "OptiScaler.asi") continue;
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
export async function copyWithRetry(text: string, attempts = 4, delayMs = 150): Promise<boolean> {
  for (let i = 0; i < attempts; i += 1) {
    if (await copyTextToClipboard(text)) return true;
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
export async function autoCopyLaunchCommand(text: string): Promise<boolean> {
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
export async function copyTextToClipboard(text: string): Promise<boolean> {
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
    } catch {
      copied = false;
    }
    if (!copied) {
      try {
        await navigator.clipboard.writeText(text);
        copied = true;
      } catch {
        copied = false;
      }
    }
    document.body.removeChild(tempInput);
    return copied;
  } catch {
    return false;
  }
}
