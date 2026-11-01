#!/bin/bash

XDG_DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
MAIN_PATH=${MAIN_PATH:-"$XDG_DATA_HOME/reshade"}
RESHADE_PATH="$MAIN_PATH/reshade"
GLOBAL_INI=${GLOBAL_INI:-"ReShade.ini"}

log_message() {
    echo "[DEBUG] $1" >&2
}

# Enhanced function to detect game architecture and API with improved patterns
detect_game_arch_and_api_enhanced() {
    local game_path="$1"
    local arch="64"  # Default to 64-bit
    local detected_api="dxgi"  # Default to DXGI
    
    log_message "Enhanced analysis of game directory: $game_path"
    
    # Find all exe files in the game directory and subdirectories
    local exe_files=()
    while IFS= read -r -d '' exe; do
        exe_files+=("$exe")
    done < <(find "$game_path" -name "*.exe" -type f -print0 2>/dev/null)
    
    if [ ${#exe_files[@]} -eq 0 ]; then
        log_message "No executable files found in game directory"
        echo "${arch},${detected_api}"
        return 0
    fi
    
    log_message "Found ${#exe_files[@]} executable files"
    
    # Score and sort executables by likelihood of being the main game executable
    local scored_exes=()
    
    for exe in "${exe_files[@]}"; do
        local filename=$(basename "$exe")
        local filename_lower=$(echo "$filename" | tr '[:upper:]' '[:lower:]')
        local file_size=0
        local score=0
        
        # Get file size
        if [ -f "$exe" ]; then
            file_size=$(stat -c%s "$exe" 2>/dev/null || echo "0")
        fi
        
        # Skip obvious utility files
        if [[ "$filename_lower" =~ (unins|setup|install|redist|prereq|crash|launcher|updater|patcher) ]]; then
            log_message "Skipping utility executable: $filename"
            continue
        fi
        
        # Size-based scoring (larger = more likely to be main game)
        local size_mb=$((file_size / 1024 / 1024))
        if [ $size_mb -gt 50 ]; then
            score=$((score + 100))
        elif [ $size_mb -gt 20 ]; then
            score=$((score + 50))
        elif [ $size_mb -gt 5 ]; then
            score=$((score + 20))
        elif [ $size_mb -lt 1 ]; then
            score=$((score - 50))
        fi
        
        # Path-based scoring (discovered patterns)
        local rel_path=$(echo "$exe" | sed "s|$game_path/||")
        if [[ "$rel_path" =~ binaries/win64 ]]; then
            score=$((score + 30))  # Unreal Engine pattern
        elif [[ "$rel_path" =~ bin ]]; then
            score=$((score + 20))   # Common bin directory
        elif [[ ! "$rel_path" =~ / ]]; then
            score=$((score + 10))   # Root directory
        fi
        
        # Filename-based scoring
        if [[ "$filename_lower" =~ (game|main|client|app) ]]; then
            score=$((score + 15))
        fi
        
        # Special patterns from real data
        if [[ "$filename_lower" =~ shipping ]]; then
            score=$((score + 25))   # Unreal shipping builds
        elif [[ "$filename_lower" =~ win64 ]]; then
            score=$((score + 10))   # 64-bit indicator
        fi
        
        # Penalty for deep nesting (utilities often deeply nested)
        local path_depth=$(echo "$rel_path" | tr -cd '/' | wc -c)
        if [ $path_depth -gt 3 ]; then
            score=$((score - path_depth * 5))
        fi
        
        # Only include non-utility files
        if [ $score -gt -500 ]; then
            scored_exes+=("$score:$exe:$size_mb")
            log_message "Scored executable: $filename (score: $score, size: ${size_mb}MB)"
        fi
    done
    
    if [ ${#scored_exes[@]} -eq 0 ]; then
        log_message "No suitable executables found after filtering"
        # Fallback: try to find ANY exe files and pick the largest one
        log_message "Attempting fallback detection - looking for any .exe files"
        
        local fallback_exes=()
        for exe in "${exe_files[@]}"; do
            local filename=$(basename "$exe")
            local file_size=0
            
            if [ -f "$exe" ]; then
                file_size=$(stat -c%s "$exe" 2>/dev/null || echo "0")
            fi
            
            # Only include files larger than 100KB to exclude tiny utilities
            if [ $file_size -gt 102400 ]; then
                fallback_exes+=("$file_size:$exe")
                log_message "Fallback candidate: $filename (size: $((file_size / 1024))KB)"
            fi
        done
        
        if [ ${#fallback_exes[@]} -gt 0 ]; then
            # Sort by size and pick the largest
            local largest_exe=""
            local largest_size=0
            
            for fallback_exe in "${fallback_exes[@]}"; do
                local size=$(echo "$fallback_exe" | cut -d: -f1)
                local exe=$(echo "$fallback_exe" | cut -d: -f2-)
                
                if [ $size -gt $largest_size ]; then
                    largest_size=$size
                    largest_exe="$exe"
                fi
            done
            
            if [ ! -z "$largest_exe" ]; then
                log_message "Fallback detection selected: $largest_exe (size: $((largest_size / 1024))KB)"
                best_exe="$largest_exe"
                best_score=1  # Low score to indicate fallback was used
            fi
        fi
        
        if [ -z "$best_exe" ]; then
            log_message "Even fallback detection failed - no suitable executables found"
            echo "${arch},${detected_api}"
            return 0
        fi
    fi
    
    # Sort by score (highest first) and get the best executable
    local best_exe=""
    local best_score=0
    
    for scored_exe in "${scored_exes[@]}"; do
        local score=$(echo "$scored_exe" | cut -d: -f1)
        local exe=$(echo "$scored_exe" | cut -d: -f2)
        
        if [ $score -gt $best_score ]; then
            best_score=$score
            best_exe="$exe"
        fi
    done
    
    if [ ! -z "$best_exe" ]; then
        log_message "Selected best executable: $best_exe (score: $best_score)"
        
        # Check architecture of the selected executable - FIXED VARIABLE SCOPE
        local file_info
        file_info=$(file "$best_exe" 2>/dev/null)
        log_message "File info for selected executable: $file_info"
        
        # FIXED: Reset variables to ensure clean state
        arch="64"  # Reset to default
        detected_api="dxgi"  # Reset to default
        
        # FIXED: More precise matching to avoid variable contamination
        if echo "$file_info" | grep -q "x86-64"; then
            arch="64"
            detected_api="dxgi"
            log_message "Detected 64-bit executable (x86-64), using DXGI"
        elif echo "$file_info" | grep -q "PE32+"; then
            arch="64"
            detected_api="dxgi"
            log_message "Detected 64-bit executable (PE32+), using DXGI"
        elif echo "$file_info" | grep -q "PE32 executable" && ! echo "$file_info" | grep -q "PE32+"; then
            arch="32"
            detected_api="d3d9"
            log_message "Detected 32-bit executable (PE32), using D3D9"
        elif echo "$file_info" | grep -q "Intel i386"; then
            arch="32"
            detected_api="d3d9"
            log_message "Detected 32-bit executable (i386), using D3D9"
        else
            log_message "Could not determine architecture from file info, using defaults"
        fi
        
        # Check for API-specific DLLs in the executable directory
        local exe_dir
        exe_dir=$(dirname "$best_exe")
        
        if [ -f "$exe_dir/d3d9.dll" ]; then
            detected_api="d3d9"
            log_message "Found d3d9.dll, using D3D9 API"
        elif [ -f "$exe_dir/d3d11.dll" ]; then
            detected_api="d3d11"
            log_message "Found d3d11.dll, using D3D11 API"
        elif [ -f "$exe_dir/d3d12.dll" ]; then
            detected_api="d3d12"
            log_message "Found d3d12.dll, using D3D12 API"
        elif [ -f "$exe_dir/d3d8.dll" ]; then
            detected_api="d3d8"
            log_message "Found d3d8.dll, using D3D8 API"
        elif [ -f "$exe_dir/opengl32.dll" ]; then
            detected_api="opengl32"
            log_message "Found opengl32.dll, using OpenGL API"
        elif [ -f "$exe_dir/dxgi.dll" ]; then
            detected_api="dxgi"
            log_message "Found dxgi.dll, using DXGI API"
        fi
    fi
    
    log_message "Final detection result - Architecture: $arch, API: $detected_api"
    # FIXED: Ensure we only return clean values
    echo "${arch},${detected_api}"
}

setup_game_reshade() {
    local game_path="$1"
    local dll_override="$2"
    local arch="$3"
    
    log_message "Setting up ReShade:"
    log_message "Game path: $game_path"
    log_message "DLL override: $dll_override"
    log_message "Architecture: $arch-bit"
    
    # FIXED: Validate and sanitize input parameters
    if [ -z "$arch" ] || [[ ! "$arch" =~ ^(32|64)$ ]]; then
        log_message "Error: Invalid architecture: '$arch'. Must be '32' or '64'"
        return 1
    fi
    
    if [ -z "$dll_override" ]; then
        log_message "Error: DLL override is empty"
        return 1
    fi
    
    # Verify ReShade installation
    if [ ! -d "$RESHADE_PATH/latest" ]; then
        log_message "Error: ReShade is not installed in $RESHADE_PATH/latest"
        return 1
    fi
    
    # Check ReShade DLL with clean architecture value
    local reshade_dll="ReShade${arch}.dll"
    if [ ! -f "$RESHADE_PATH/latest/$reshade_dll" ]; then
        log_message "Error: Required ReShade DLL not found: $reshade_dll"
        log_message "Looking for: $RESHADE_PATH/latest/$reshade_dll"
        return 1
    fi

    # Check d3dcompiler
    local d3dcompiler="$RESHADE_PATH/d3dcompiler_47.dll.${arch}"
    if [ ! -f "$d3dcompiler" ]; then
        log_message "Error: d3dcompiler_47.dll not found for $arch-bit"
        log_message "Looking for: $d3dcompiler"
        return 1
    fi

    # Create symbolic links
    log_message "Creating symbolic links..."
    
    # Link ReShade DLL
    log_message "Linking ReShade DLL: $reshade_dll -> $dll_override.dll"
    [ -L "$game_path/$dll_override.dll" ] && unlink "$game_path/$dll_override.dll"
    if ! ln -sfv "$RESHADE_PATH/latest/$reshade_dll" "$game_path/$dll_override.dll"; then
        log_message "Failed to create DLL symlink"
        return 1
    fi
    
    # Link d3dcompiler
    log_message "Linking d3dcompiler: $d3dcompiler"
    [ -L "$game_path/d3dcompiler_47.dll" ] && unlink "$game_path/d3dcompiler_47.dll"
    if ! ln -sfv "$d3dcompiler" "$game_path/d3dcompiler_47.dll"; then
        log_message "Failed to create d3dcompiler symlink"
        return 1
    fi
    
    # Link shader directory
    if [ -d "$MAIN_PATH/ReShade_shaders" ]; then
        log_message "Linking shader directory"
        [ -L "$game_path/ReShade_shaders" ] && unlink "$game_path/ReShade_shaders"
        if ! ln -sfv "$MAIN_PATH/ReShade_shaders" "$game_path/"; then
            log_message "Failed to create shaders symlink"
            return 1
        fi
    fi
    
    # Link ReShade.ini
    if [ "$GLOBAL_INI" != "0" ] && [ -f "$MAIN_PATH/$GLOBAL_INI" ]; then
        log_message "Linking ReShade.ini"
        [ -L "$game_path/ReShade.ini" ] && unlink "$game_path/ReShade.ini"
        if ! ln -sfv "$MAIN_PATH/$GLOBAL_INI" "$game_path/ReShade.ini"; then
            log_message "Failed to create ini symlink"
            return 1
        fi
    fi
    
    # Copy AutoHDR addon files if available AND compatible with the selected API
    local autohdr_compatible=false
    case "$dll_override" in
        "dxgi"|"d3d11"|"d3d12")
            autohdr_compatible=true
            log_message "API $dll_override is compatible with AutoHDR"
            ;;
        "d3d9"|"d3d8"|"opengl32"|"ddraw"|"dinput8")
            autohdr_compatible=false
            log_message "API $dll_override is NOT compatible with AutoHDR (requires DirectX 10/11/12)"
            ;;
        *)
            autohdr_compatible=false
            log_message "Unknown API $dll_override, skipping AutoHDR for safety"
            ;;
    esac
    
    if [ "$autohdr_compatible" = true ]; then
        local autohdr_addon="$MAIN_PATH/AutoHDR_addons/AutoHDR.addon${arch}"
        if [ -f "$autohdr_addon" ]; then
            log_message "Copying AutoHDR addon for ${arch}-bit architecture (API: $dll_override)"
            if cp "$autohdr_addon" "$game_path/AutoHDR.addon${arch}"; then
                log_message "AutoHDR addon copied successfully"
            else
                log_message "Warning: Failed to copy AutoHDR addon"
            fi
        else
            log_message "AutoHDR addon file not found: $autohdr_addon"
        fi
    else
        log_message "Skipping AutoHDR addon installation for API: $dll_override"
        # Remove any existing AutoHDR addon files if they exist from previous installations
        if [ -f "$game_path/AutoHDR.addon${arch}" ]; then
            log_message "Removing existing AutoHDR addon (incompatible with $dll_override)"
            rm -f "$game_path/AutoHDR.addon${arch}"
        fi
    fi
    
    # Handle ReShadePreset.ini - preserve existing user settings
    log_message "Handling ReShadePreset.ini"
    local preset_file="$game_path/ReShadePreset.ini"
    
    # Only create the file if it doesn't already exist (preserve existing user settings)
    if [ ! -f "$preset_file" ]; then
        local game_name=$(basename "$(dirname "$game_path")" 2>/dev/null || basename "$game_path")
        cat > "$preset_file" << EOF
# ReShade Preset Configuration for $game_name
# This file will be automatically populated when you save presets in ReShade
# Press HOME key in-game to open ReShade overlay
# Go to Settings -> General -> "Reload all shaders" if shaders don't appear

# Example preset configuration:
# [Preset1]
# Techniques=SMAA,Clarity,LumaSharpen
# PreprocessorDefinitions=

# Uncomment and modify the lines below to create a default preset:
# [Default]
# Techniques=
# PreprocessorDefinitions=
EOF
        
        # Set proper permissions (read/write for all)
        chmod 666 "$preset_file"
        log_message "Created new ReShadePreset.ini with proper permissions"
    else
        # File exists, just ensure it has proper permissions
        chmod 666 "$preset_file"
        log_message "ReShadePreset.ini already exists, updated permissions only"
    fi
    
    # Ensure ReShade.ini has proper permissions if it exists
    if [ -f "$game_path/ReShade.ini" ]; then
        chmod 666 "$game_path/ReShade.ini"
        log_message "Set proper permissions for ReShade.ini"
    fi
    
    # Create README file for Steam games
    local readme_file="$game_path/ReShade_README.txt"
    local game_name=$(basename "$(dirname "$game_path")" 2>/dev/null || basename "$game_path")
    
    # Check if AutoHDR was actually installed
    local autohdr_status=""
    if [ -f "$game_path/AutoHDR.addon${arch}" ]; then
        autohdr_status="- AutoHDR.addon$arch: AutoHDR addon (DirectX 10/11/12 compatible)"
    else
        case "$dll_override" in
            "dxgi"|"d3d11"|"d3d12")
                autohdr_status="- AutoHDR.addon$arch: Not installed (AutoHDR addon file missing)"
                ;;
            *)
                autohdr_status="- AutoHDR.addon$arch: Not compatible with $dll_override (requires DirectX 10/11/12)"
                ;;
        esac
    fi
    
    cat > "$readme_file" << EOF
ReShade for $game_name
------------------------------------
Installed with LetMeReShadeAll plugin for Steam

DLL Override: $dll_override
Architecture: $arch-bit
Game Directory: $game_path
$([ ! -z "$exact_exe_path" ] && echo "Exact Executable: $exact_exe_path")

Press HOME key in-game to open the ReShade overlay.

If shaders are not visible:
1. Open the ReShade overlay with HOME key
2. Go to Settings tab
3. Check paths for "Effect Search Paths" and "Texture Search Paths"
4. They should point to the ReShade_shaders folder in this game directory
5. If not, update them to: ".\\ReShade_shaders"

Shader preset files (.ini) will be saved in this game directory.

Files created:
- ReShade.ini: Main ReShade configuration (symlinked to global)
- ReShadePreset.ini: Preset configurations (auto-populated when you save presets)
- $dll_override.dll: ReShade DLL (symlinked)
- d3dcompiler_47.dll: DirectX shader compiler (symlinked)
- ReShade_shaders/: Shader files directory (symlinked)
$autohdr_status

Detection Method: $([ ! -z "$exact_exe_path" ] && echo "Steam Console Logs" || echo "Enhanced File Analysis / User Selected")

AutoHDR Compatibility:
- Compatible APIs: DXGI, D3D11, D3D12 (DirectX 10/11/12)
- Incompatible APIs: D3D9, D3D8, OpenGL32, DDraw, DInput8
- Current API: $dll_override $(case "$dll_override" in "dxgi"|"d3d11"|"d3d12") echo "(✅ AutoHDR Compatible)";; *) echo "(❌ AutoHDR Incompatible)";; esac)

Note: If ReShadePreset.ini already existed, your previous settings were preserved.
EOF
    
    # Set proper permissions for README (read/write for all)
    chmod 666 "$readme_file"
    log_message "Created ReShade_README.txt with proper permissions"
    
    log_message "Setup completed successfully"
    return 0
}

main() {
    local game_path="$1"
    local dll_override="${2:-dxgi}"

    log_message "Starting enhanced game manager with:"
    log_message "Game path: $game_path"
    log_message "DLL override: $dll_override"

    if [ ! -d "$RESHADE_PATH" ]; then
        log_message "Error: RESHADE_PATH does not exist: $RESHADE_PATH"
        echo "Error: ReShade path not found" >&2
        exit 1
    fi

    game_path="${game_path//\"}"  # Remove any quotes
    if [ ! -d "$game_path" ]; then
        log_message "Error: Invalid game path: $game_path"
        echo "Error: Invalid game path" >&2
        exit 1
    fi

    # Use enhanced detection method with proper error handling
    local detection_result
    detection_result=$(detect_game_arch_and_api_enhanced "$game_path")
    
    if [ -z "$detection_result" ]; then
        log_message "Error: Enhanced detection returned empty result"
        echo "Error: Could not detect game architecture or API" >&2
        exit 1
    fi
    
    local arch
    local detected_api
    arch=$(echo "$detection_result" | cut -d',' -f1)
    detected_api=$(echo "$detection_result" | cut -d',' -f2)
    
    # FIXED: Clean variable validation with fallback
    if [ -z "$arch" ] || [[ ! "$arch" =~ ^(32|64)$ ]]; then
        log_message "Error: Invalid architecture detected: '$arch'. Falling back to 64-bit"
        arch="64"
    fi
    
    if [ -z "$detected_api" ]; then
        log_message "Error: No API detected. Falling back to default based on architecture"
        if [ "$arch" = "32" ]; then
            detected_api="d3d9"
        else
            detected_api="dxgi"
        fi
    fi
    
    log_message "Parsed detection result - Architecture: $arch, API: $detected_api"
    
    # Use detected API when auto-detection is requested
    if [ "$dll_override" = "auto" ]; then
        dll_override="$detected_api"
        log_message "Auto-detection selected API: $dll_override"
    fi
    
    # FIXED: Validate dll_override is clean and supported
    local valid_apis=("d3d8" "d3d9" "d3d11" "d3d12" "dxgi" "opengl32" "ddraw" "dinput8")
    local api_valid=false
    for valid_api in "${valid_apis[@]}"; do
        if [ "$dll_override" = "$valid_api" ]; then
            api_valid=true
            break
        fi
    done
    
    if [ "$api_valid" = false ]; then
        log_message "Error: Invalid API selected: '$dll_override'. Falling back to default"
        if [ "$arch" = "32" ]; then
            dll_override="d3d9"
        else
            dll_override="dxgi"
        fi
        log_message "Using fallback API: $dll_override"
    fi
    
    log_message "Setting executable permissions for game directory"
    chmod -R u+w "$game_path" 2>/dev/null || log_message "Warning: Could not set write permissions"
    
    if setup_game_reshade "$game_path" "$dll_override" "$arch"; then
        # Update the WINEDLLOVERRIDES based on detected API
        local override_cmd="WINEDLLOVERRIDES=\"d3dcompiler_47=n;${dll_override}=n,b\" %command%"
        echo "Successfully installed ReShade using enhanced detection"
        
        # Check if AutoHDR was installed based on API compatibility
        local autohdr_message=""
        case "$dll_override" in
            "dxgi"|"d3d11"|"d3d12")
                if [ -f "$MAIN_PATH/AutoHDR_addons/AutoHDR.addon$arch" ]; then
                    autohdr_message="AutoHDR components included (DirectX 10/11/12 detected)"
                fi
                ;;
            *)
                autohdr_message="AutoHDR not included (requires DirectX 10/11/12, detected: ${dll_override})"
                ;;
        esac
        
        if [ ! -z "$autohdr_message" ]; then
            echo "$autohdr_message"
        fi
        
        echo "Detected architecture: $arch-bit"
        echo "Selected API: $dll_override"
        echo "Use this launch option: $override_cmd"
        echo "Press HOME key in-game to open ReShade interface"
        return 0
    else
        echo "Failed to install ReShade" >&2
        return 1
    fi
}

main "$@"
