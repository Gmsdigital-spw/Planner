#!/usr/bin/env bash
# Run at the start of every phase. Then send the zip to Grayson as a file.
# usage: scripts/backup.sh agency|office  (run from the repo root)
set -euo pipefail
STAMP=$(TZ=America/Chicago date +%F_%H%M)
NAME=${1:?usage: backup.sh agency|office}
mkdir -p backups
zip -qr "backups/${NAME}_backup_${STAMP}.zip" . -x "backups/*" ".git/*" "node_modules/*" "*.mp4" "*.wav" "*.mp3" "gw/out/files/*" "listing-photos/*" "prints/*" "pins/*" "social/20*" "office/studio/media/*" "office/studio/out/*"
echo "backups/${NAME}_backup_${STAMP}.zip"
