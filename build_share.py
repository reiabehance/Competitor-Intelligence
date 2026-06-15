# -*- coding: utf-8 -*-
# Versioned share archive: each render -> its own dated snapshot (never overwritten),
# a monthly copy, and a regenerated history hub (share/index.html) linking everything.
import json, os, shutil, datetime, html, glob
import os as _os
BASE=_os.environ.get("REPO_ROOT", _os.path.dirname(_os.path.abspath(__file__)))
SHARE=BASE+"/share"; VERS=SHARE+"/versions"; MON=SHARE+"/monthly"
os.makedirs(VERS,exist_ok=True); os.makedirs(MON,exist_ok=True)
BREAK=BASE+"/reports/Reia-Competitor-Creative-Breakdown.html"
BRIEF=BASE+"/reports/Reia-WEEKLY-Decision-Brief.html"
stats=json.load(open(BASE+"/data/assets/stats6.json"))
now=datetime.datetime.now()
stamp=now.strftime("%Y-%m-%d_%H%M"); ym=now.strftime("%Y-%m"); nice=now.strftime("%d %b %Y, %H:%M")
monthname=now.strftime("%B %Y")

# 1) save this version (frozen snapshot)
vdir=VERS+"/"+stamp; os.makedirs(vdir,exist_ok=True)
shutil.copy(BREAK, vdir+"/index.html")
if os.path.exists(BRIEF): shutil.copy(BRIEF, vdir+"/decision-brief.html")

# 2) monthly snapshot (latest state of the month)
mdir=MON+"/"+ym; os.makedirs(mdir,exist_ok=True)
shutil.copy(BREAK, mdir+"/index.html")
if os.path.exists(BRIEF): shutil.copy(BRIEF, mdir+"/decision-brief.html")

# 3) append to manifest (append-only history; dedupe by stamp)
MF=SHARE+"/manifest.json"
man=[]
if os.path.exists(MF):
    try: man=json.load(open(MF))
    except: man=[]
man=[m for m in man if m.get("stamp")!=stamp]
man.append({"stamp":stamp,"nice":nice,"ym":ym,"monthname":monthname,"has_brief":os.path.exists(BRIEF),
            "unique":stats["unique"],"brands":stats["brands"],"winning":stats["winning"],
            "losing":stats["losing"],"newly":stats["newly"]})
man.sort(key=lambda m:m["stamp"], reverse=True)
json.dump(man, open(MF,"w"), indent=2)

# 4) regenerate history hub (share/index.html), grouped by month
from collections import OrderedDict
by=OrderedDict()
for m in man: by.setdefault(m["monthname"],[]).append(m)
latest=man[0]
CSS="""
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@400;500;600&family=Lora&display=swap');
:root{--maroon:#7B0017;--ink:#15150e;--line:#e6dccb;--gold:#b78b2e;--cream:#FFFAF1;--win:#3f8f4f;--lose:#c47d2a;--new:#3a6098;}
*{box-sizing:border-box}body{margin:0;background:#f3ecdf;color:var(--ink);font-family:'Lora',Georgia,serif;line-height:1.5}
.top{background:var(--maroon);color:#fff;padding:22px 26px;box-shadow:0 2px 12px rgba(0,0,0,.18)}
.top .tt{font-family:'Cormorant Garamond',serif;font-size:1.9rem;font-weight:700;letter-spacing:.5px}
.top .ts{font-family:'Poppins',sans-serif;font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;opacity:.85;margin-bottom:4px}
.wrap{max-width:1060px;margin:0 auto;padding:28px 22px 80px}
.latest{background:linear-gradient(100deg,#7B0017,#9a142e);color:#fff;border-radius:16px;padding:22px 24px;margin:8px 0 26px;box-shadow:0 8px 24px rgba(123,0,23,.25)}
.latest .lab{font-family:'Poppins',sans-serif;font-size:.6rem;letter-spacing:.16em;text-transform:uppercase;color:#ffd9a8}
.latest h2{font-family:'Cormorant Garamond',serif;font-size:1.7rem;margin:4px 0 10px;border:none;color:#fff}
.latest a.btn{display:inline-block;background:#fff;color:var(--maroon);font-family:'Poppins',sans-serif;font-weight:600;font-size:.8rem;padding:9px 18px;border-radius:24px;text-decoration:none;margin-top:6px}
.kpis{display:flex;flex-wrap:wrap;gap:18px;margin-top:6px;font-family:'Poppins',sans-serif;font-size:.74rem}
.kpis b{font-family:'Cormorant Garamond',serif;font-size:1.5rem;display:block;color:#fff}
h2.mh{font-family:'Cormorant Garamond',serif;color:var(--maroon);font-size:1.5rem;border-bottom:2px solid var(--maroon);padding-bottom:5px;margin:34px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 2px 10px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:8px}
.card .d{font-family:'Cormorant Garamond',serif;font-size:1.25rem;font-weight:700;color:var(--ink)}
.card .s{font-family:'Poppins',sans-serif;font-size:.7rem;color:#7a6a60;display:flex;flex-wrap:wrap;gap:4px 12px}
.card .s i{font-style:normal}.card .s .w{color:var(--win)}.card .s .l{color:var(--lose)}.card .s .n{color:var(--new)}
.card .links{display:flex;gap:8px;margin-top:4px}
.card a{font-family:'Poppins',sans-serif;font-size:.72rem;font-weight:500;text-decoration:none;color:var(--maroon);background:#faf4ea;border:1px solid var(--line);padding:6px 12px;border-radius:20px}
.card a:hover{background:var(--maroon);color:#fff}
.monthlink{font-family:'Poppins',sans-serif;font-size:.66rem;color:#8a7c6c;margin-left:10px}
.foot{margin-top:40px;font-size:.76rem;color:#8a7a70;border-top:1px solid var(--line);padding-top:14px}
"""
def kpis(m):
    return (f'<div class="kpis"><span><b>{m["unique"]:,}</b>placements</span><span><b>{m["brands"]}</b>brands</span>'
            f'<span><b>{m["winning"]:,}</b>winning</span><span><b>{m["losing"]:,}</b>short-run</span><span><b>{m["newly"]:,}</b>newly</span></div>')
B=[]
B.append('<div class="top"><div class="ts">Weekly Competitor Creative Intelligence · version history</div><div class="tt">RÉIA — Competitor Intelligence Archive</div></div><div class="wrap">')
_lbrief=(f'<a class="btn" style="background:rgba(255,255,255,.16);color:#fff" href="versions/{latest["stamp"]}/decision-brief.html">Decision brief →</a>' if latest.get("has_brief") else '')
B.append(f'<div class="latest"><div class="lab">Latest snapshot</div><h2>{html.escape(latest["nice"])}</h2>{kpis(latest)}'
         f'<div><a class="btn" href="versions/{latest["stamp"]}/index.html">Open the breakdown →</a> {_lbrief}</div></div>')
for monthname,items in by.items():
    ymv=items[0]["ym"]
    B.append(f'<h2 class="mh">{html.escape(monthname)} <span class="monthlink"><a style="color:#8a7c6c" href="monthly/{ymv}/index.html">month\'s latest →</a></span></h2><div class="grid">')
    for m in items:
        briefl=f'<a href="versions/{m["stamp"]}/decision-brief.html">Brief</a>' if m.get("has_brief") else ''
        B.append(f'<div class="card"><div class="d">{html.escape(m["nice"])}</div>'
                 f'<div class="s"><i>{m["unique"]:,} placements</i><i>{m["brands"]} brands</i><i class="w">{m["winning"]:,} win</i><i class="l">{m["losing"]:,} short</i><i class="n">{m["newly"]:,} new</i></div>'
                 f'<div class="links"><a href="versions/{m["stamp"]}/index.html">Breakdown</a>{briefl}</div></div>')
    B.append('</div>')
B.append(f'<div class="foot">{len(man)} versions archived · each snapshot is frozen at capture time. Monthly folders hold the final state of each month. EF/VVS floor applies to all Réia creative.</div></div>')
OUT="<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'><title>Réia — Competitor Intelligence Archive</title><style>"+CSS+"</style></head><body>"+''.join(B)+"</body></html>"
open(SHARE+"/index.html","w",encoding="utf-8").write(OUT)
print("Saved version",stamp,"| month",ym,"| total versions:",len(man))
print("Hub:",len(OUT),"chars")
