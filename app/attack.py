#!/usr/bin/env python3
"""Controlled TCP scan/connection-rate test generator for the isolated Mininet lab."""
import argparse, socket, time

def probe(ip, port, timeout):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.settimeout(timeout)
    try: return s.connect_ex((ip,port)) == 0
    except OSError: return False
    finally: s.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['scan','flood']); ap.add_argument('target')
    ap.add_argument('--port',type=int,default=5000); ap.add_argument('--lo',type=int,default=1); ap.add_argument('--hi',type=int,default=1024)
    ap.add_argument('--rate',type=float,default=None); ap.add_argument('--duration',type=float,default=10); ap.add_argument('--timeout',type=float,default=.3)
    a=ap.parse_args(); rate=a.rate or (50 if a.mode=='scan' else 100)
    start=time.time(); print('ATTACK_START %.6f' % start,flush=True); nxt=start; port=a.lo
    while time.time()-start<a.duration:
        p=port if a.mode=='scan' else a.port
        if a.mode=='scan': port=a.lo if port>=a.hi else port+1
        t=time.time(); ok=probe(a.target,p,a.timeout)
        print('%.6f,%d,%d' % (t,p,int(ok)),flush=True)
        nxt+=1.0/rate
        if nxt>time.time(): time.sleep(nxt-time.time())
    print('ATTACK_END %.6f' % time.time(),flush=True)
if __name__=='__main__': main()
