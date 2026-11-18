#!/bin/bash
# Usage: scripts/run.sh <normal|scan|flood|multi> [on|off]
cd "$(dirname "$0")/.." || exit 1
SCEN=${1:?usage: scripts/run.sh normal|scan|flood|multi [on|off]}; MODE=${2:-on}
mkdir -p results
source "${RYU_VENV:-$HOME/ryuenv}/bin/activate" || { echo 'ryuenv not found'; exit 1; }
sudo mn -c >/dev/null 2>&1
# Keep each run's data isolated; old outputs are retained under timestamped archive.
STAMP=$(date +%Y%m%d_%H%M%S); mkdir -p "results/archive/$STAMP"
for f in results/detections.csv results/flowstats.csv results/client_*.csv results/attack_*.log; do
  [ -f "$f" ] && mv "$f" "results/archive/$STAMP/"
done
IDS_MODE=$MODE ryu-manager --ofp-tcp-listen-port 6653 controller/ids.py > "results/ryu_${SCEN}_${MODE}.log" 2>&1 & RP=$!
trap 'kill $RP 2>/dev/null' EXIT
for i in $(seq 1 30); do ss -ltn | grep -q ':6653 ' && break; sleep .5; done
if ! ss -ltn | grep -q ':6653 '; then echo 'Ryu did not start; inspect results/ryu log'; exit 1; fi
echo "Ryu running (IDS_MODE=$MODE). Starting $SCEN demo."
sudo python3 topology/topo.py --demo "$SCEN"
echo '---- controller detections ----'; grep BLOCKED "results/ryu_${SCEN}_${MODE}.log" || echo '(none)'
echo 'Dashboard: results/dashboard.html'
