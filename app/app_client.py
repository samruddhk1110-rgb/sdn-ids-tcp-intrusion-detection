#!/usr/bin/env python3
"""Concurrent legitimate TCP load client.
Usage: app_client.py <server_ip> <requests_per_client> <gap_seconds> [--clients N]
CSV output: timestamp,latency_ms,success,client_id
"""
import argparse, socket, threading, time, csv, sys

p = argparse.ArgumentParser()
p.add_argument('server_ip'); p.add_argument('requests', type=int); p.add_argument('gap', type=float)
p.add_argument('--clients', type=int, default=1, help='simultaneous independent TCP clients')
p.add_argument('--port', type=int, default=5000)
a = p.parse_args()
write_lock = threading.Lock()

def run(cid):
    for i in range(a.requests):
        start = time.time(); ok = 0
        try:
            with socket.create_connection((a.server_ip, a.port), timeout=2) as s:
                s.settimeout(2); s.sendall(('GET %d\n' % i).encode())
                ok = int(s.recv(256).startswith(b'OK'))
                s.sendall(b'BYE\n')
        except OSError:
            pass
        with write_lock:
            print('%.6f,%.2f,%d,%s' % (start, (time.time()-start)*1000, ok, cid), flush=True)
        time.sleep(a.gap)

threads = [threading.Thread(target=run, args=(i+1,)) for i in range(a.clients)]
for t in threads: t.start()
for t in threads: t.join()
