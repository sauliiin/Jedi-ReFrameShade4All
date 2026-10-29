LOCAL_PREFIX = ".local"
LOCAL_BIN = ".local/bin"
LOCAL_LIB = ".local/lib"
LOCAL_LIB32 = ".local/lib32"
LOCAL_SHARE = ".local/share"
CONFIG_DIR = ".config/jedi-lsfg-vk"

WRAPPER_FILENAME = ".jedi-lsfg"
CONFIG_FILENAME = "conf.toml"
OWNERSHIP_FILENAME = "renderer_ownership.json"

# MAKO Renderer (GPL-3.0-or-later) provides the Vulkan layer with Adaptive
# Frame Generation. The newest renderer release is downloaded from GitHub.
MAKO_RELEASES_API = "https://api.github.com/repos/eugeniosegala/MAKO/releases?per_page=30"
MAKO_RELEASE_TAG_PREFIX = "render-v"
MAKO_ARCHIVE_TEMPLATE = "MAKO-Renderer-v{version}-linux.tar.xz"
ARCHIVE_INSTALLER = "Install MAKO Renderer"
LAUNCHER_FILENAME = "mako-launch"
CLI_FILENAME = "mako-cli"
INSTALLER_FILENAME = "mako-installer"
LIB_FILENAME = "libmako-render.so"
LAYER_MANIFEST = "share/mako-render/vulkan/implicit_layer.d/VkLayer_MAKO_render.json"
LAYER_MANIFEST_X86 = "share/mako-render/vulkan/implicit_layer.d/VkLayer_MAKO_render.x86.json"
INSTALLER_STATE = "share/mako-render/installer/installed-files.sha256"
# Written by the MAKO installer: {"version": "<installed version>", ...}
ACTIVE_RENDERER_STATE = "share/mako-render/active-renderer.json"

LOSSLESS_DLL_FILENAME = "Lossless.dll"
STEAM_LOSSLESS_SCALING_APP_ID = "993090"
# Suggested branch when Lossless.dll is missing; any branch that ships it works.
STEAM_LOSSLESS_SCALING_BRANCH = "public"

# Launch-time variables set by the Steam wrapper.
COMPETING_LSFG_DISABLE_ENVS = ("DISABLE_LSFG", "DISABLE_LSFGVK")
