#!/bin/bash
# Ensure a display is available for the Tkinter GUI.
# Prefer Wayland, fall back to X11/XWayland.
if [ -z "$WAYLAND_DISPLAY" ] && [ -d "$XDG_RUNTIME_DIR" ] && [ -S "$XDG_RUNTIME_DIR/wayland-0" ]; then
    export WAYLAND_DISPLAY=wayland-0
fi
if [ -z "$DISPLAY" ]; then
    for d in 1 0; do
        if [ -S "/tmp/.X11-unix/X$d" ]; then
            export DISPLAY=":$d"
            break
        fi
    done
fi
exec python3 /app/share/media-downloader/app.py "$@"
