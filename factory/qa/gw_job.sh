#!/usr/bin/env bash
# Run one free-gateway job and wait for its result.
# Usage: factory/qa/gw_job.sh <job-id> <ops.json file>   -> prints gw/out/<job-id>.json
set -e
cd /home/claude/planner
ID="$1"; OPS="$2"
python3 -c "import json,sys;json.dump({'id':sys.argv[1],'ops':json.load(open(sys.argv[2]))},open('gw/jobs/'+sys.argv[1]+'.json','w'))" "$ID" "$OPS"
git add "gw/jobs/$ID.json"
git commit -q -m "gw job $ID

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git pull -q --rebase origin main && git push -q origin main 2>/dev/null
for i in $(seq 1 40); do
  sleep 10
  git fetch -q origin main
  if git cat-file -e "origin/main:gw/out/$ID.json" 2>/dev/null; then
    git pull -q --rebase origin main
    cat "gw/out/$ID.json"; exit 0
  fi
done
echo "TIMEOUT waiting for gw/out/$ID.json" >&2; exit 1
