#!/usr/bin/env python3
"""Build an offline, self-contained HTML dashboard from project CSV/log outputs."""
import csv, json, os, glob, html, statistics, sys
from collections import Counter, defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,'results')
OUT=os.path.join(RES,'dashboard.html')
def read_csv(path):
    try:
        with open(path,newline='') as f: return list(csv.DictReader(f))
    except (OSError, csv.Error): return []
def num(v):
    try:return float(v)
    except (TypeError,ValueError):return 0.0
def esc(v):return html.escape(str(v))

dets=read_csv(os.path.join(RES,'detections.csv')); stats=read_csv(os.path.join(RES,'flowstats.csv'))
clients=[]
for path in glob.glob(os.path.join(RES,'client_*.csv')):
    try:
        with open(path,newline='') as f:
            for row in csv.reader(f):
                if len(row)>=3:
                    clients.append({'timestamp':row[0],'latency_ms':row[1],'success':row[2], 'client_id':row[3] if len(row)>3 else '1'})
    except OSError: pass
scenarios=[]
for path in glob.glob(os.path.join(RES,'attack_*.log')):
    name=os.path.basename(path).replace('attack_','').replace('.log',''); lines=open(path,errors='ignore').read().splitlines()
    probes=[]; start=end=0
    for line in lines:
        if line.startswith('ATTACK_START'): start=num(line.split()[-1])
        elif line.startswith('ATTACK_END'): end=num(line.split()[-1])
        else:
            x=line.split(',')
            if len(x)==3: probes.append({'time':num(x[0]),'port':int(num(x[1])),'success':int(num(x[2]))})
    scenarios.append({'scenario':name,'start':start,'end':end,'sent':len(probes),'success':sum(x['success'] for x in probes)})
lat=[num(x.get('latency_ms')) for x in clients]; ok=sum(int(num(x.get('success'))) for x in clients); total=len(clients)
source_counts=Counter(x.get('src','unknown') for x in dets); rule_counts=Counter(x.get('rule','unknown') for x in dets)
attack_counts=Counter({x['scenario']:x['sent'] for x in scenarios})
outcome_counts=Counter({'Successful':ok,'Failed':max(0,total-ok)})
latest=defaultdict(dict)
for r in stats: latest[r.get('src','unknown')]=r

def table(headers, rows):
    return '<table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def bar_svg(items, title):
    maxv=max([v for _,v in items]+[1]); width=660; row=34; h=48+row*len(items)
    out=['<svg viewBox="0 0 %d %d" role="img" aria-label="%s">'%(width,h,esc(title))]
    for i,(label,val) in enumerate(items):
        y=28+i*row; w=int(420*val/maxv)
        out.append('<text x="8" y="%d" class="barlabel">%s</text>'%(y+14,esc(label[:22])))
        out.append('<rect x="190" y="%d" width="%d" height="18" rx="5" class="bar"/>'%(y,w))
        out.append('<text x="%d" y="%d" class="barvalue">%s</text>'%(198+w,y+14,esc(val)))
    return ''.join(out)+'</svg>'

cards=[('TCP requests',total),('Successful requests',ok),('Success rate','%.1f%%'%(100*ok/total if total else 0)),('IDS blocks',len(dets)),('Flow-stat samples',len(stats)),('Mean latency','%.1f ms'%(sum(lat)/len(lat) if lat else 0))]
card_html=''.join('<div class="card"><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>' for k,v in cards)
det_rows=[[r.get('block_time',''),r.get('src',''),r.get('rule',''),r.get('detect_ms',''),r.get('response_ms',''),r.get('packet_ins','')] for r in dets]
stat_rows=[[r.get('time',''),r.get('src',''),r.get('flows',''),r.get('packets',''),r.get('bytes','')] for r in stats[-100:]]
scen_rows=[[x['scenario'],x['sent'],x['success']] for x in scenarios]
client_rows=[[r.get('client_id','1'),r.get('timestamp',''),r.get('latency_ms',''), 'Success' if int(num(r.get('success'))) else 'Failed'] for r in clients[-100:]]
html_doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SDN TCP Security Dashboard</title><style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121d30;--line:#26364f;--muted:#9fb0c8;--text:#edf4ff;--accent:#5eead4}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,Segoe UI,sans-serif}header{padding:34px max(22px,calc((100% - 1180px)/2));background:linear-gradient(120deg,#142b48,#102039);border-bottom:1px solid var(--line)}h1{margin:0;font-size:30px}header p,.muted{color:var(--muted)}main{max-width:1180px;margin:26px auto;padding:0 20px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}.card span{display:block;color:var(--muted);font-size:13px}.card strong{font-size:26px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}.panel{margin-top:18px;overflow:auto}h2{font-size:18px;margin:0 0 12px}table{width:100%;border-collapse:collapse;font-size:13px;white-space:nowrap}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line)}th{color:var(--accent);font-weight:600}tr:last-child td{border:0}svg{width:100%;height:auto}.bar{fill:#2dd4bf}.barlabel,.barvalue{fill:var(--text);font:12px system-ui}.barvalue{fill:var(--muted)}.pill{display:inline-block;background:#123c3b;color:#8df5e5;padding:4px 9px;border-radius:99px;font-size:12px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:24px}}</style></head><body><header><h1>SDN TCP Security Dashboard</h1><p>Live-lab evidence · intrusion detection · controlled TCP traffic · switch flow statistics</p><span class="pill">Offline report · generated from results CSV/logs</span></header><main><section class="cards">'''+card_html+'''</section><div class="grid"><section class="panel"><h2>Detections by rule</h2>'''+bar_svg(list(rule_counts.items()),'Detections by rule')+'''</section><section class="panel"><h2>Detections by source IP</h2>'''+bar_svg(list(source_counts.items()),'Detections by source IP')+'''</section><section class="panel"><h2>Attack attempts by host</h2>'''+bar_svg(list(attack_counts.items()),'Attack attempts by host')+'''</section><section class="panel"><h2>Legitimate request outcomes</h2>'''+bar_svg(list(outcome_counts.items()),'Legitimate request outcomes')+''' </section></div><section class="panel"><h2>Attack test summary</h2>'''+table(['Scenario','Probes / attempts','Successful TCP connects'],scen_rows)+'''</section><section class="panel"><h2>Detection and response events</h2>'''+table(['Time','Source IP','Rule','Detection ms','Response ms','Packet-ins'],det_rows)+'''</section><section class="panel"><h2>Legitimate client requests (latest 100)</h2>'''+table(['Client','Timestamp','Latency ms','Result'],client_rows)+'''</section><section class="panel"><h2>OpenFlow statistics (latest 100 samples)</h2>'''+table(['Time','Source IP','Flows','Packets','Bytes'],stat_rows)+'''<p class="muted">Note: statistics are controller polling snapshots. Empty tables mean the corresponding run/log has not produced data yet. This report is generated locally and requires no internet connection.</p></section></main></body></html>'''
os.makedirs(RES,exist_ok=True)
with open(OUT,'w') as f:f.write(html_doc)
print('Dashboard written: '+OUT)
