#!/usr/bin/env python3
"""Four-host Mininet demo: h1/h4 controlled attackers, h2 multi-client load, h3 server."""
import argparse, os, time
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP=os.path.join(ROOT,'app'); RES=os.path.join(ROOT,'results')

def build():
    net=Mininet(controller=None,switch=OVSSwitch,autoSetMacs=True)
    net.addController('c0',controller=RemoteController,ip='127.0.0.1',port=6653)
    sw=net.addSwitch('s1',protocols='OpenFlow13')
    for name,ip in [('h1','10.0.0.1'),('h2','10.0.0.2'),('h3','10.0.0.3'),('h4','10.0.0.4')]: net.addLink(net.addHost(name,ip=ip+'/24'),sw)
    return net

def run_demo(net,scenario):
    h1,h2,h3,h4=net.get('h1','h2','h3','h4'); sw=net.get('s1'); os.makedirs(RES,exist_ok=True)
    client=os.path.join(RES,'client_%s.csv'%scenario); attacks=[]
    print('\n[1/5] Starting TCP server on h3 (multi-worker TCP socket server)')
    h3.cmd('python3 %s/app_server.py > %s/server.log 2>&1 &'%(APP,RES)); time.sleep(1)
    print('[2/5] Connectivity check'); net.pingAll()
    clients=5 if scenario in ('normal','multi','scan','flood') else 5
    print('[3/5] Starting %d simultaneous legitimate TCP clients from h2'%clients)
    h2.sendCmd('python3 %s/app_client.py 10.0.0.3 40 0.3 --clients %d > %s'%(APP,clients,client))
    time.sleep(3)
    if scenario in ('scan','flood','multi'):
        mode='scan' if scenario=='scan' else 'flood'
        attackers=[(h1,'h1','10.0.0.1')]
        if scenario=='multi': attackers.append((h4,'h4','10.0.0.4'))
        print('[4/5] Launching controlled %s traffic from %s'%(mode,', '.join(x[1] for x in attackers)))
        for host,name,ip in attackers:
            path=os.path.join(RES,'attack_%s.log'%name); attacks.append(path)
            host.sendCmd('python3 %s/attack.py %s 10.0.0.3 --duration 10 > %s'%(APP,mode,path))
        for host,_,_ in attackers: host.waitOutput()
        print('Switch drop-flow entries:')
        flows=sw.cmd('ovs-ofctl -O OpenFlow13 dump-flows s1')
        print('\n'.join(x.strip() for x in flows.splitlines() if 'priority=100' in x) or '(none)')
        for host,name,_ in attackers: print('%s reachability check: %s'%(name,host.cmd('ping -c 1 -W 1 10.0.0.3 | tail -2').strip()))
    h2.waitOutput()
    print('[5/5] Generating offline HTML dashboard')
    os.system('python3 %s/scripts/dashboard.py %s'%(ROOT,RES))
    print('Open results/dashboard.html in a browser.')
    h3.cmd("pkill -f 'app_server.py'")

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--demo',choices=['normal','scan','flood','multi']); a=ap.parse_args()
    setLogLevel('info'); net=build(); net.start()
    try: run_demo(net,a.demo) if a.demo else CLI(net)
    finally: net.stop()
