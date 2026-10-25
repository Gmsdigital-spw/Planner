#!/bin/sh
# Build the final PDF: draw -> centre fields (post.py) -> Lora fonts in fields (tools/acro_font.py)
set -e
D=$(dirname "$0")
python3 "$D/build.py" /tmp/cab_raw.pdf
python3 "$D/post.py" /tmp/cab_raw.pdf /tmp/cab_post.pdf
python3 /home/claude/planner/tools/acro_font.py /tmp/cab_post.pdf "$D/pink-cabana-birthday-invitation.pdf"
