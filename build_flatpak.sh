#!/usr/bin/env bash
# Build, validate, and optionally bundle Media Downloader as a Flatpak.
set -Eeuo pipefail

readonly APP_ID="io.github.hmidani_abdelilah.Media_Downloader"
readonly RUNTIME_VERSION="25.08"
readonly CODECS_VERSION="25.08-extra"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly MANIFEST="$SCRIPT_DIR/flatpak/$APP_ID.json"
readonly WORK_DIR="$SCRIPT_DIR/.flatpak-build"
readonly BUILD_DIR="$WORK_DIR/build"
readonly STATE_DIR="$WORK_DIR/state"
readonly REPO_DIR="$WORK_DIR/repo"
readonly OUTPUT_DIR="$SCRIPT_DIR/dist-flatpak"
readonly ARCH="$(flatpak --default-arch 2>/dev/null || uname -m)"
readonly BUNDLE_FILE="$OUTPUT_DIR/$APP_ID-$ARCH.flatpak"

install_app=1
make_bundle=0
run_app=0
install_deps=1

usage() {
    cat <<'EOF'
Usage: ./build_flatpak.sh [OPTIONS]

Build Media Downloader from pinned sources using Flatpak Builder.
The default action builds, installs for the current user, and runs smoke tests.

Options:
  --bundle       Also create dist-flatpak/*.flatpak and its SHA-256 file
  --no-install   Build and export only; do not install or run smoke tests
  --run          Launch the graphical application after a successful build
  --no-deps      Do not install missing Flatpak runtime/SDK dependencies
  -h, --help     Show this help
EOF
}

for option in "$@"; do
    case "$option" in
        --bundle) make_bundle=1 ;;
        --no-install) install_app=0 ;;
        --run) run_app=1 ;;
        --no-deps) install_deps=0 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "error: unknown option: $option" >&2; usage >&2; exit 2 ;;
    esac
done

if (( run_app && ! install_app )); then
    echo "error: --run cannot be combined with --no-install" >&2
    exit 2
fi

for command_name in flatpak flatpak-builder appstreamcli desktop-file-validate sha256sum; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "error: required command not found: $command_name" >&2
        exit 1
    fi
done

if [[ ! -f "$MANIFEST" ]]; then
    echo "error: Flatpak manifest not found: $MANIFEST" >&2
    exit 1
fi

ensure_flathub_user_remote() {
    if ! flatpak remotes --user --columns=name | sed 's/[[:space:]]*$//' | grep -Fxq flathub; then
        echo "==> Adding the Flathub user remote"
        flatpak remote-add --user --if-not-exists flathub \
            https://dl.flathub.org/repo/flathub.flatpakrepo
    fi
}

ensure_ref() {
    local ref="$1"
    if flatpak info "$ref" >/dev/null 2>&1; then
        return
    fi
    if (( ! install_deps )); then
        echo "error: missing Flatpak dependency: $ref" >&2
        exit 1
    fi
    ensure_flathub_user_remote
    echo "==> Installing $ref for the current user"
    flatpak install --user --noninteractive -y flathub "$ref"
}

verify_desktop_integration() {
    local user_data_home="${XDG_DATA_HOME:-${HOME:?}/.local/share}"
    local export_root="$user_data_home/flatpak/exports/share"
    local desktop_entry="$export_root/applications/$APP_ID.desktop"
    local exported_icon="$export_root/icons/hicolor/512x512/apps/$APP_ID.png"
    local legacy_icon="$user_data_home/icons/hicolor/512x512/apps/$APP_ID.png"

    echo "==> Verifying desktop menu integration"
    if ! flatpak info --user "$APP_ID" >/dev/null 2>&1; then
        echo "error: $APP_ID was not installed for the current user" >&2
        exit 1
    fi
    if [[ ! -e "$desktop_entry" ]]; then
        echo "error: exported desktop entry not found: $desktop_entry" >&2
        exit 1
    fi
    if [[ ! -e "$exported_icon" ]]; then
        echo "error: exported application icon not found: $exported_icon" >&2
        exit 1
    fi
    if ! grep -Fqx "X-Flatpak=$APP_ID" "$desktop_entry"; then
        echo "error: exported desktop entry is not registered for $APP_ID" >&2
        exit 1
    fi

    if command -v update-desktop-database >/dev/null 2>&1; then
        if ! update-desktop-database "$export_root/applications"; then
            echo "warning: could not refresh the desktop entry cache" >&2
        fi
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        if ! gtk-update-icon-cache --force "$export_root/icons/hicolor" >/dev/null; then
            echo "warning: could not refresh the Flatpak icon cache" >&2
        fi
    fi

    if [[ -f "$legacy_icon" ]] && ! cmp -s "$legacy_icon" "$exported_icon"; then
        echo "warning: a different host icon may override the Flatpak icon:" >&2
        echo "         $legacy_icon" >&2
        echo "         Back it up or remove it, refresh the icon cache, then sign in again." >&2
    fi
    echo "Desktop entry and icon exports: OK"
}

echo "==> Validating desktop metadata"
desktop-file-validate \
    "$SCRIPT_DIR/flatpak/$APP_ID.desktop"
appstreamcli validate --no-net \
    "$SCRIPT_DIR/flatpak/$APP_ID.appdata.xml"

ensure_ref "org.freedesktop.Platform//$RUNTIME_VERSION"
ensure_ref "org.freedesktop.Sdk//$RUNTIME_VERSION"
ensure_ref "org.freedesktop.Platform.codecs-extra//$CODECS_VERSION"

mkdir -p "$WORK_DIR" "$OUTPUT_DIR"

builder_options=(
    --force-clean
    --user
    --repo="$REPO_DIR"
    --state-dir="$STATE_DIR"
)
if (( install_app )); then
    builder_options+=(--install -y)
fi

echo "==> Building $APP_ID ($ARCH)"
flatpak-builder "${builder_options[@]}" "$BUILD_DIR" "$MANIFEST"

if (( install_app )); then
    verify_desktop_integration
    echo "==> Running packaged dependency smoke tests"
    flatpak run --user --command=sh "$APP_ID" -c '
        set -eu
        cd /app/share/media-downloader
        python3 -c "from pathlib import Path; import tkinter, customtkinter, tkinterdnd2, yt_dlp, yt_dlp_ejs; import app; assert Path(app.__file__).resolve() == Path(\"/app/share/media-downloader/app.py\"); tcl = tkinter.Tcl(); tcl_library = Path(str(tcl.call(\"info\", \"library\"))); assert (tcl_library / \"init.tcl\").is_file(), tcl_library; assert Path(\"/app/lib/tk9.0/tk.tcl\").is_file(); patchlevel = tcl.call(\"info\", \"patchlevel\"); print(f\"Python/Tk dependencies: OK (Tcl {patchlevel})\")"
        qjs -e "console.log(\"QuickJS: OK\")" >/dev/null
        aria2c --version >/dev/null
        ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx264"
        ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "libx265"
    '
fi

if (( make_bundle )); then
    echo "==> Creating $BUNDLE_FILE"
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID" master
    sha256sum "$BUNDLE_FILE" > "$BUNDLE_FILE.sha256"
fi

echo "==> Flatpak build completed"
if (( install_app )); then
    echo "Run: flatpak run --user $APP_ID"
fi
if (( make_bundle )); then
    echo "Bundle: $BUNDLE_FILE"
fi

if (( run_app )); then
    exec flatpak run --user "$APP_ID"
fi
