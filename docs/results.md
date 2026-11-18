# Measured results (Demo 1)

Environment: Ubuntu VM, Mininet 2.3.0, Open vSwitch 3.7.1, Ryu 4.34, one run per case. Attack from h1 for 10 s starting at
t = 5 s; legitimate client h2 sends 100 requests over about 23 s. Numbers are copied from the demo output
(`scripts/summarize.py`).

## IDS on

| Scenario | Rule | Detection | Response | End-to-end | Attacker probes | Succeeded | Probes OK after block | Controller packet-ins at block | Legit success | Legit p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| Normal | none | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 100% (100 req) | 137.9 ms |
| Scan | R2_PORT_SCAN | 214.4 ms | 0.12 ms | 219.5 ms | 41 | 0 | 0 | 155 | 100% (38 req) | 80.9 ms |
| Flood | R1_HIGH_CONN_RATE | 296.2 ms | 0.13 ms | 302.3 ms | 61 | 30 | 0 | 255 | 100% (38 req) | 95.5 ms |

Switch state after the attack: `priority=100,ip,nw_src=10.0.0.1 actions=drop` with `n_packets=30`; ping from h1 to the server: 100% loss.

## IDS off (static baseline)

| Scenario | Attacker probes | Succeeded | Drop rule | h1 ping to server | Legit success | Legit p95 |
|---|---|---|---|---|---|---|
| Scan | 500 | 0 | none | 0% loss | 100% (42 req) | 84.5 ms |
| Flood | 1000 | 1000 | none | 0% loss | 100% (41 req) | 76.9 ms |

## Comparison

| Metric | Static (off) | SDN-IDS (on) | Change |
|---|---|---|---|
| Scan probes sent in 10 s | 500 | 41 | -92% |
| Flood connections completed in 10 s | 1000 | 30 | -97% |
| Attacker reachability after attack | full | none | blocked |

## Interpretation and caveats

* Detection times match what the rules predict (11 ports at 50 probes/s is about 0.22 s; 31 connections at 100/s is about 0.31 s).
  The controller reacts as soon as the rule allows, and the flow-mod is built and sent in about 0.1 ms.
* The scan "succeeded: 0" in both modes because the 500 probes covered ports 1-500 and the only open port is 5000.
  The comparison metric for the scan is therefore probes sent, not probes succeeded.
* The legitimate client reached 100% in both modes: these attacks do not overload an 8-worker server. The demonstrated
  benefit is containment and reduced load, not improved legitimate latency. Overload scenarios (slow-connection attack,
  two simultaneous attackers) are Demo 2 work.
* The normal run's p95 latency (137.9 ms) is higher than in the other runs. The cause was not investigated; VM scheduling
  and a cold start are plausible. Averages over repeated runs are planned for Demo 2.
* One run per case in a VM: treat timings as indicative, not statistically established.


# Final demo results (measured) (scripts/run.sh multi vs scripts/run.sh multi off)

Two attackers (h1, h4) flood the server for 10 s while five concurrent legitimate clients run on h2. One run per case.

| Metric | Static switch (IDS off) | SDN-IDS (on) |
|---|---|---|
| Connection attempts per attacker (h1 / h4) | 885 / 885 | 176 / 177 |
| Connections that succeeded per attacker | 885 / 885 | 150 / 150 |
| Drop flows on the switch | none | 2 (priority 100, hard timeout 60 s) |
| Attacker reachability after attack | ping 0% loss | ping 100% loss |
| Detection time (R1), h4 / h1 | n/a | 1820.5 ms / 1850.4 ms |
| Response time (rule fires to flow-mod sent) | n/a | 0.13 ms / 0.20 ms |
| Legitimate requests succeeded (h2, 5 clients) | 200 of 200 (100%) | 200 of 200 (100%) |
| Legitimate source blocked (false positive) | n/a | none |

Both attackers are detected independently and blocked by source IP. h2 is never blocked. Legitimate success is 100% in both modes because the 8-worker server is not overloaded; the measured benefit is containment of the attackers and about 80% fewer packets reaching the server.

*Threshold note:* R1 was raised from 30 to 150 connections per 5 s window. With five concurrent clients, h2 alone produced about 75 connections per window and was wrongly blocked at the old value. The cost is slower detection (about 1.8 s instead of about 0.3 s in the single-client Demo 1 run).

