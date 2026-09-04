#!/bin/sh
set -eu

cd /app/share/media-downloader
exec python3 app.py "$@"
