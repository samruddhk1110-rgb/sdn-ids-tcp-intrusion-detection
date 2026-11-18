# Final demo runbook

## One-command demo

From the project root on the Ubuntu VM:

```bash
scripts/run.sh multi
```

This starts Ryu, creates the four-host Mininet topology, starts the TCP server on h3, launches five concurrent legitimate clients from h2, and starts two simultaneous connection-rate test generators from h1 and h4. The IDS should detect the two sources independently and install two priority-100 source-IP drop rules. The script then generates `results/dashboard.html`.

Open the dashboard locally:

```bash
xdg-open results/dashboard.html
```

No internet/CDN is needed for the dashboard.

## Focused test sequence

```bash
scripts/run.sh normal    # concurrent legitimate traffic; check no IDS blocks
scripts/run.sh scan      # h1 port-scan rule R2
scripts/run.sh flood     # h1 TCP connection-rate rule R1
scripts/run.sh multi     # h1 + h4 simultaneous attackers, plus legitimate load
scripts/run.sh multi off # same multi-host traffic with IDS disabled (baseline)
```

Every run moves the previous CSV and attack logs into `results/archive/<timestamp>/`, so the dashboard shows the current run rather than mixing old measurements. The Ryu log is named `results/ryu_<scenario>_<mode>.log`.

## What to point out in the dashboard

- KPI cards: legitimate request count, successes, success percentage, IDS blocks, flow-stat samples and mean latency.
- Detection chart/table: which source was blocked, which rule fired, detection time and response time.
- Attack summary: number of attempts and successful TCP connects per attacker.
- Client table: per-client request latency and success/failure.
- OpenFlow statistics: source, active connection flows, packet count and byte count from controller polling.

## Host roles

| Host | Address | Role |
|---|---|---|
| h1 | 10.0.0.1 | Controlled attacker 1 |
| h2 | 10.0.0.2 | Five concurrent legitimate TCP clients |
| h3 | 10.0.0.3 | Multi-worker TCP server |
| h4 | 10.0.0.4 | Controlled attacker 2 (used by `multi`) |

## Important interpretation

The two attacker processes run concurrently and are tracked independently by source IP. A source-specific block should not block h2's legitimate requests. `IDS_MODE=off` is the static-switch baseline; it intentionally installs no IDS drop rules. Flow statistics are periodic polling snapshots, so they are not a packet-by-packet trace. Run only inside the isolated Mininet lab.

## If the dashboard looks empty

Check `results/ryu_<scenario>_<mode>.log`, `results/server.log`, and `results/attack_h1.log` / `results/attack_h4.log`. Confirm Ryu started before Mininet and that `sudo mn -c` ran first. Then rerun the scenario.
