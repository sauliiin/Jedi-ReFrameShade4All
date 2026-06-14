import { callable } from "@decky/api";

export const getOptiScalerUpdateStatus = callable<
  [],
  {
    status: string;
    installed_version?: string | null;
    latest_version?: string | null;
    update_available?: boolean;
    message?: string;
  }
>("get_optiscaler_update_status");

export const updateOptiScaler = callable<
  [selected_default_variant?: string],
  { status: string; message?: string; output?: string; version?: string }
>("update_optiscaler");

export const runInstallFGMod = callable<
  [selected_default_variant?: string],
  {
    status: string;
    message?: string;
    output?: string;
    version?: string;
    selected_default_variant?: string;
    selected_default_variant_label?: string;
  }
>("run_install_fgmod");

export const runUninstallFGMod = callable<
  [],
  { status: string; message?: string; output?: string }
>("run_uninstall_fgmod");

export const checkFGModPath = callable<
  [],
  {
    exists: boolean;
    version?: string | null;
    selected_fsr4_variant?: string | null;
    selected_fsr4_variant_label?: string | null;
    install_manifest_present?: boolean;
  }
>("check_fgmod_path");

export const listInstalledGames = callable<
  [],
  { status: string; message?: string; games: { appid: string; name: string; install_found?: boolean }[] }
>("list_installed_games");

export const logError = callable<[string], void>("log_error");

export const runManualPatch = callable<
  [string, string, string],
  {
    status: string;
    message?: string;
    output?: string;
    fsr4_variant?: string;
    fsr4_variant_label?: string;
    fsr4_upscaler_sha256?: string;
    optiscaler_version?: string | null;
  }
>("manual_patch_directory");

export const patchGame = callable<
  [appid: string, dll_name: string, current_launch_options: string, fsr4_variant: string],
  {
    status: string;
    message?: string;
    appid?: string;
    name?: string;
    dll_name?: string;
    target_dir?: string;
    launch_options?: string;
    original_launch_options?: string;
    optiscaler_version?: string | null;
    fsr4_variant?: string;
    fsr4_variant_label?: string;
    fsr4_upscaler_sha256?: string;
  }
>("patch_game");
