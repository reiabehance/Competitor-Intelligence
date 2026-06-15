# -*- coding: utf-8 -*-
import json, html, os, re
from collections import defaultdict, Counter
import os as _os
BASE=_os.environ.get("REPO_ROOT", _os.path.dirname(_os.path.abspath(__file__)))
A=BASE+"/data/assets/"
d=json.load(open(A+"breakdown6.json")); brk=d["brk"]; insight=d["insight"]; meta=d["meta"]; order=d["order"]
rec=json.load(open(A+"recommendations2.json")); stats=json.load(open(A+"stats6.json"))
IMG={}
for f in os.listdir(A):
    if f.endswith(".json") and "img" in f:
        try: IMG.update(json.load(open(A+f)))
        except: pass
for f in ["dataset1_creatives.json","dataset2_creatives.json"]:
    if os.path.exists(A+f):
        for a in json.load(open(A+f)):
            if a.get("link") and a.get("image"): IMG.setdefault(a["link"],a["image"])

CATCOL={"Offer / Discount":"#b23b3b","Festival / Seasonal":"#b5732a","Education":"#2f5d2f","Proposal / Emotional":"#7B0017",
"Co-creation / Custom":"#5d3a7a","Social Proof":"#2f4d7a","Store launch / Footfall":"#7a6a16","UGC / Testimonial":"#2f7d6a",
"Everyday / Lifestyle":"#7a5e16","Cultural / Heritage":"#8a4a2a","Brand film":"#444","Product / Catalogue":"#9a8f80","Brand / Product video":"#666"}
TWIST={
"Proposal / Emotional":"Run real Bangalore-couple proposal reels — hijack the hook with 'Designed with her, in her hands in 7 days.'",
"Co-creation / Custom":"Don't claim co-creation — prove it. Film the 7-day build: sketch -> CAD -> EF/VVS stone -> finished ring.",
"Education":"Own a NAMED asset: the 'Réia Clarity Code' (EF/VVS + lab-grown explained). Beat generic 'what to check'.",
"UGC / Testimonial":"Real customers + 'Comment RÉIA for a design consult' to farm warm DMs.",
"Offer / Discount":"Do NOT match the discount. Counter with value-transparency — 'What Rs X actually buys' — win on trust.",
"Everyday / Lifestyle":"Self-purchase angle: 'Worn because you chose you' — everyday EF/VVS bands.",
"Social Proof":"'Chosen by N couples this month' — most-loved custom ring, with real review quotes.",
"Store launch / Footfall":"Turn store ads into experience invites: 'Design your ring with us in Jayanagar — ready in 7 days.'",
"Cultural / Heritage":"Named, limited South-Indian motif drops — modern temple-inspired rings sold as identity.",
"Festival / Seasonal":"Festival = proposal season. Pair the festive hook with the 7-day delivery guarantee.",
"Brand film":"A founder-led 'why Réia' film — substance over gloss; 7-day + EF/VVS as the brand spine.",
"Product / Catalogue":"Don't lead with catalogue — retarget only. Replace hero spend with process/story video.",
"Brand / Product video":"Convert plain product video into PROCESS video — show the ring being made in 7 days.",
}
COLLATION={}
try: COLLATION=json.load(open(A+"collation_map.json"))
except: pass
def chip(c): return f'<span class="cat" style="background:{CATCOL.get(c,"#777")}">{html.escape(c)}</span>'
def imgtag(u,extra=""): return f'<img class="lz" data-src="{html.escape(u)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" alt=""{extra}>'
def ckey(a):
    """Collapse the SAME creative into one card. Priority:
       1) Meta's collation_id — authoritative 'these ads are the same creative' grouping;
       2) message with numbers/prices stripped — collapses DPA price/product variants of one template;
       3) image filename — last resort for distinct stills."""
    cid=COLLATION.get(a["link"])
    if cid: return ("c",cid)
    t=re.sub(r'\d+',' ',re.sub(r'\W+',' ',(a.get("copy") or ""))).strip().lower()[:90]
    if len(t)>=10: return ("t",t)
    u=IMG.get(a["link"]); fn=u.split("?")[0].rsplit("/",1)[-1] if u else None
    return ("i",fn or a["link"])
def dedupe(ads):
    seen={}; ordk=[]
    for a in sorted(ads,key=lambda x:-(x["dd"] if x["dd"] is not None else 0)):
        k=ckey(a)
        if k not in seen:
            seen[k]={**a,"_n":1}; ordk.append(k)
        else:
            seen[k]["_n"]+=1
            # upgrade representative to one that HAS a thumbnail (keeps the card from showing "no preview")
            if (a["link"] in IMG) and (seen[k]["link"] not in IMG):
                n=seen[k]["_n"]; seen[k]={**a,"_n":n}
    return [seen[k] for k in ordk]
BKT={"WR":("win","Reel"),"WS":("win","Static"),"LR":("lose","Reel"),"LS":("lose","Static"),"NR":("new","Reel"),"NS":("new","Static")}
def brand_uniq(b):
    allads=[]
    for k in ["WR","WS","LR","LS","NR","NS"]:
        st,med=BKT[k]
        for a in brk[b][k]: allads.append({**a,"_st":st,"_med":med})
    return dedupe(allads)
def _nbadge(a): return f'<span class="ntag" title="Same creative running as {a["_n"]} ad placements">x{a["_n"]}</span>' if a.get("_n",1)>1 else ''
def thumb(a,big=False):
    u=IMG.get(a["link"]); m=a.get("_med") or ("Reel" if a.get("fmt")=="VIDEO" else "Static")
    cls="th big" if big else "th"
    inner=imgtag(u) if u else '<div class="noimg">no preview</div>'
    return (f'<a class="{cls}" href="{html.escape(a["link"])}" target="_blank" rel="noopener" title="{html.escape((a.get("cat") or "")+" · "+(a.get("copy") or ""))}">'
            f'{inner}<span class="thm">{m[0]}</span>{_nbadge(a)}<span class="thd">{a.get("dd","?")}d</span></a>')

GN={0:"Réia — your own ads",1:"Direct competitors",2:"Adjacent jewellery (category context)",3:"Creative inspiration — NOT competitors"}
GSUB={0:"self-audit",1:"India + global lab-grown / custom-engagement brands — your real rivals",2:"natural &amp; gold incumbents — they chase jewellery/wedding spend, not lab-grown engagement",3:"non-jewellery D2C &amp; luxury — we borrow their creative MECHANICS only; NOT competitors"}
def aid(b): return "c-"+re.sub(r'[^a-z0-9]','',b.lower())
def adlib(b):
    pid=str(meta.get(b,{}).get("page_id") or ""); c=meta.get(b,{}).get("country") or "ALL"
    return f'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={c}&search_type=page&view_all_page_id={pid}' if pid else ""
def bstats(b):
    v=brk[b]
    w=len(v["WR"])+len(v["WS"]); l=len(v["LR"])+len(v["LS"]); n=len(v["NR"])+len(v["NS"])
    reels=len(v["WR"])+len(v["LR"])+len(v["NR"]); statics=len(v["WS"])+len(v["LS"])+len(v["NS"])
    tot=w+l+n
    allads=v["WR"]+v["WS"]+v["LR"]+v["LS"]+v["NR"]+v["NS"]
    top=Counter(a["cat"] for a in allads).most_common(1)[0][0] if allads else "—"
    wr=round(100*w/tot) if tot else 0
    return dict(w=w,l=l,n=n,reels=reels,statics=statics,tot=tot,top=top,wr=wr)
S={b:bstats(b) for b in order}
U={b:len(brand_uniq(b)) for b in order}
maxtot=max(s["tot"] for s in S.values()) or 1
print("loaded",len(order),"brands; IMG",len(IMG))

# ---------- Réia vs the field ----------
reia=S.get("Réia (self)",{"tot":0,"w":0,"wr":0}); rtot=reia["tot"]; rwr=reia["wr"]; rcre=U.get("Réia (self)",0)
g1=[b for b in order if meta[b]["group"]==1]
def med(xs):
    xs=sorted(xs); return xs[len(xs)//2] if xs else 0
medtot=med([S[b]["tot"] for b in g1]); medwr=round(sum(S[b]["wr"] for b in g1)/len(g1)) if g1 else 0; medcre=med([U[b] for b in g1])
be=S.get("Brilliant Earth",{"tot":0,"wr":0}); becre=U.get("Brilliant Earth",0)
def vcard(title,you,rival,best,unit,take,bestlabel="Brilliant Earth"):
    mx=max(you,rival,best,1)
    def row(lab,val,cls):
        w=int(100*val/mx)
        return f'<div class="vbrow {cls}"><span class="vbl">{lab}</span><span class="vbbar"><i style="width:{w}%"></i></span><span class="vbn">{val}{unit}</span></div>'
    return (f'<div class="vscard"><div class="vsq">{title}</div><div class="vsbars">'
            +row("Réia (you)",you,"you")+row("Typical rival",rival,"rival")+row(f"Best · {bestlabel}",best,"best")
            +f'</div><div class="vstake">{take}</div></div>')
vspanel=('<h2 id="vsfield">Réia vs the field — at a glance</h2>'
 '<div class="note">Three questions, three answers. Maroon = you, grey = the typical direct rival, gold = the best-in-class benchmark.</div>'
 '<div class="vsgrid">'
 +vcard("How much are you publishing?",rtot,medtot,be["tot"],"","You publish the least of the serious players. Scale to a steady weekly cadence.")
 +vcard("How much of it works? (win-rate)",rwr,medwr,be["wr"],"%","Win-rate = % of ads still live after 2 weeks. Let winners run instead of churning.")
 +vcard("How many distinct creatives?",rcre,medcre,becre,"","Variety of ideas in-market. You need more shots on goal, not more repeats.")
 +'</div>')

# ---------- Overview matrix ----------
def mixbar(s):
    tot=s["tot"] or 1
    ww=round(150*s["w"]/tot); lw=round(150*s["l"]/tot); nw=max(0,150-ww-lw)
    return (f'<span class="mix" title="Winning {s["w"]} · Short-run {s["l"]} · Newly {s["n"]}">'
            f'<i class="mw" style="width:{ww}px"></i><i class="ml" style="width:{lw}px"></i><i class="mn" style="width:{nw}px"></i></span>')
SEGTOT=defaultdict(lambda:{"plc":0,"cre":0,"n":0})
for b in order:
    g=meta[b]["group"]; SEGTOT[g]["plc"]+=S[b]["tot"]; SEGTOT[g]["cre"]+=U[b]; SEGTOT[g]["n"]+=1
rows=[]; lastg=None; rk=0
for b in order:
    g=meta[b]["group"]; s=S[b]
    if g!=lastg:
        t=SEGTOT[g]; rk=0
        rows.append(f'<tr class="seg"><td colspan="6"><span class="segname">{GN[g]}</span><span class="segmeta">{t["n"]} brands · {t["cre"]} creatives · {t["plc"]} live placements</span></td></tr>')
        lastg=g
    rk+=1; barw=int(100*s["tot"]/maxtot); rc=' reia' if b=="Réia (self)" else ''
    _al=adlib(b); _alink=(f' <a class="metalink" href="{_al}" target="_blank" rel="noopener" title="Cross-check this brand on Meta Ad Library">↗ Meta</a>' if _al else '')
    rows.append(f'<tr class="{rc}" data-brand="{html.escape(b.lower())}"><td class="bcell"><span class="rk">{rk}</span><a class="brandlink" href="#{aid(b)}">{html.escape(b)}</a>{_alink}</td>'
      f'<td class="volcell"><span class="volbar"><i style="width:{barw}%"></i></span><b class="vn">{s["tot"]}</b></td>'
      f'<td class="crecell"><b>{U[b]}</b></td>'
      f'<td class="mixcell">{mixbar(s)}<span class="mixn"><b class="wc">{s["w"]}</b> <b class="lc">{s["l"]}</b> <b class="nc">{s["n"]}</b></span></td>'
      f'<td class="wrcell"><span class="wrbar"><i style="width:{s["wr"]}%"></i></span><b>{s["wr"]}%</b></td>'
      f'<td>{chip(s["top"])}</td></tr>')
matrix=('<div class="mxlegend"><span><b>Live placements</b> = every active ad</span><span><b>Creatives</b> = distinct ads (duplicates collapsed)</span>'
 '<span class="lk"><i class="sw mw"></i>Winning 2+wk <i class="sw ml"></i>Short-run 1–2wk <i class="sw mn"></i>Newly &lt;1wk</span></div>'
 '<div class="matrixwrap"><table class="mx"><thead><tr><th>Brand</th><th>Live placements</th><th>Creatives</th><th>Status mix (win / short / new)</th><th>Win-rate</th><th>Top theme</th></tr></thead><tbody>'
 +''.join(rows)+'</tbody></table></div>')
dl=sorted([(b,S[b]["tot"]) for b in g1],key=lambda x:-x[1])[:3]
lead_txt=", ".join(f"{b.split(' (')[0]} {n}" for b,n in dl)
gap=(f'<div class="gap"><b>Where Réia lags:</b> you run <b>{rtot} live placements</b> ({reia.get("w",0)} winning, {rwr}% win-rate). '
  f'Direct rivals run far more — {lead_txt}. Benchmark <b>Brilliant Earth runs {be["tot"]} at ~{be["wr"]}% win-rate</b>. '
  f'<b>The gap is volume + consistency, not strategy.</b> You are already in the right themes — scale a steady cadence and let winners run.</div>')
print("vs+matrix built; rows",len(rows))

# ---------- Brand-by-brand (show ALL creatives — no caps) ----------
def catblocks(winners):
    by=defaultdict(list)
    for a in winners: by[a["cat"]].append(a)
    out=[]
    for c in sorted(by,key=lambda c:-len(by[c])):
        ads=by[c]
        nR=sum(1 for a in ads if a.get("fmt")=="VIDEO"); nS=len(ads)-nR
        thumbs=''.join(thumb(a) for a in ads)
        tw=TWIST.get(c,"Adapt this theme to Réia's 7-day + EF/VVS positioning.")
        out.append(f'<div class="catblock"><div class="cath">{chip(c)}<span class="catn">{len(ads)} creative{"s" if len(ads)!=1 else ""} · {nR}R / {nS}S</span></div>'
                   f'<div class="thumbs">{thumbs}</div><div class="twist"><span class="tl">RÉIA TWIST</span> {html.escape(tw)}</div></div>')
    return '\n'.join(out) or '<div class="empty">No winning creatives captured this cycle.</div>'
def gallery(ads,cls,lab):
    if not ads: return ''
    return f'<div class="galsec"><div class="galh {cls}">{lab} — {len(ads)} creatives</div><div class="gallery">{"".join(thumb(a) for a in ads)}</div></div>'
def cap(label,val,cls=""): return f'<span class="cap {cls}">{label} <b>{val}</b></span>'
sections=[]; lastg=None
for b in order:
    g=meta[b]["group"]; s=S[b]; m=meta[b]
    if g!=lastg:
        sections.append(f'<div class="seghead" id="seg{g}"><span>{GN[g]}</span><small>{GSUB[g]}</small></div>'); lastg=g
    uniq=brand_uniq(b)
    winners=[a for a in uniq if a["_st"]=="win"]; losers=[a for a in uniq if a["_st"]=="lose"]; newlies=[a for a in uniq if a["_st"]=="new"]
    tagh=f'<span class="btag {m["tag"]}">{html.escape(m["tagtext"])}</span>'
    caps=(cap("Live placements",s["tot"],"t")+cap("Creatives",U[b],"cre")+cap("✓ Winning",s["w"],"w")+cap("◴ Short-run",s["l"],"l")+cap("✦ Newly",s["n"],"n")
        +cap("Win-rate",f'{s["wr"]}%')+f'<span class="cap th">Top theme <b>{html.escape(s["top"])}</b></span>')
    if winners: head="What’s WINNING — by theme (with the Réia twist)"; blocks=catblocks(winners)
    else: head="No 2-week winners yet — current bets (newly launched)"; blocks=catblocks(newlies) if newlies else '<div class="empty">No active creatives captured.</div>'
    _al=adlib(b); _albtn=(f'<a class="metabtn" href="{_al}" target="_blank" rel="noopener">↗ Verify on Meta Ad Library</a>' if _al else '')
    sections.append(f'<section class="comp" id="{aid(b)}" data-brand="{html.escape(b.lower())}"><div class="comph"><h3>{html.escape(b)} {tagh}</h3>'
      f'<div class="caps">{caps}</div>{_albtn}<div class="insight">{html.escape(insight.get(b,""))}</div></div>'
      f'<div class="winhead">{head}</div>{blocks}'
      f'{gallery(losers,"lose","◴ Losing / short-run (1–2 wks)") if winners else ""}'
      f'{gallery(newlies,"new","✦ Newly launched (<1 wk)") if winners else ""}</section>')
PMAP={p[0].split(" · ")[0]:p[0].split(" · ")[1] for p in rec["personas"]}
def pchip(p): return f'<span class="per">{html.escape(p)} · {html.escape(PMAP.get(p,""))}</span>'
def ochip(o): return f'<span class="out">{html.escape(o)}</span>'
reels='\n'.join(f'<div class="rc reel"><div class="rch">{html.escape(t)}</div><div class="badges">{pchip(p)}{ochip(o)}<span class="fmtb">Reel</span></div><p class="hook">{html.escape(hook)}</p><div class="rcref"><b>Ref:</b> {html.escape(rb)} — {html.escape(rt)} <a href="https://www.facebook.com/ads/library/?id={html.escape(rl)}" target="_blank" rel="noopener">view ↗</a></div></div>' for (t,p,o,fmt,rb,rt,rl,hook) in rec["reels"])
stat='\n'.join(f'<div class="rc stat"><div class="rch">{html.escape(t)}</div><div class="badges">{pchip(p)}{ochip(o)}<span class="fmtb">{html.escape(ty)}</span></div><p class="hook">{html.escape(idea)}</p><div class="rcref"><b>Ref:</b> {html.escape(rb)} — {html.escape(rt)} <a href="https://www.facebook.com/ads/library/?id={html.escape(rl)}" target="_blank" rel="noopener">view ↗</a></div></div>' for (t,p,o,ty,rb,rt,rl,idea) in rec["statics"])
personarows='\n'.join(f'<tr><td><b>{html.escape(a)}</b></td><td>{html.escape(bb)}</td><td>{html.escape(c)}</td></tr>' for (a,bb,c) in rec["personas"])
print("sections built:",len([x for x in sections if x.startswith("<section")]))

CSS="""
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Poppins:wght@400;500;600&family=Lora:ital@0;1&display=swap');
:root{--maroon:#7B0017;--ink:#15150e;--line:#e6dccb;--gold:#b78b2e;--cream:#FFFAF1;--win:#3f8f4f;--lose:#c47d2a;--new:#3a6098;--paper:#f3ecdf;}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'Lora',Georgia,serif;line-height:1.5;}
a{color:inherit;}
.top{position:sticky;top:0;z-index:60;background:rgba(123,0,23,.98);color:#fff;padding:11px 20px;box-shadow:0 2px 12px rgba(0,0,0,.18);}
.top .tt{font-family:'Cormorant Garamond',serif;font-size:1.4rem;font-weight:700;letter-spacing:.5px;}
.top .nav{margin-top:7px;white-space:nowrap;overflow-x:auto;font-family:'Poppins',sans-serif;font-size:.64rem;}
.top .nav a{display:inline-block;background:rgba(255,255,255,.14);padding:3px 9px;border-radius:20px;margin-right:5px;text-decoration:none;}
.top .nav a:hover{background:#fff;color:var(--maroon);}
.wrap{max-width:1280px;margin:0 auto;padding:26px 22px 90px;}
.hero h1{font-family:'Cormorant Garamond',serif;font-size:2.9rem;color:var(--maroon);margin:6px 0 4px;font-weight:700;letter-spacing:.3px;}
.hero .k{font-family:'Poppins',sans-serif;font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);}
.hero .sub{font-style:italic;color:#6b5b52;margin-bottom:8px;}
.statrow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0;}
@media(max-width:680px){.statrow{grid-template-columns:repeat(2,1fr);}}
.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.05);}
.stat .n{font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:700;color:var(--maroon);}
.stat.s2 .n{color:var(--win);}.stat.s4 .n{color:var(--new);}
.stat .l{font-family:'Poppins',sans-serif;font-size:.6rem;letter-spacing:.05em;text-transform:uppercase;color:#9a8a80;margin-top:3px;}
h2{font-family:'Cormorant Garamond',serif;font-size:1.95rem;color:var(--maroon);border-bottom:2px solid var(--maroon);padding-bottom:5px;margin:50px 0 10px;font-weight:700;}
.note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:0 12px 12px 0;padding:13px 17px;margin:12px 0;font-size:.9rem;box-shadow:0 1px 4px rgba(0,0,0,.04);}
/* vs field */
.vsgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:14px 0;}
@media(max-width:900px){.vsgrid{grid-template-columns:1fr;}}
.vscard{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 4px 16px rgba(0,0,0,.07);}
.vsq{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:700;color:var(--ink);margin-bottom:12px;}
.vbrow{display:flex;align-items:center;gap:10px;margin:9px 0;font-family:'Poppins',sans-serif;font-size:.74rem;}
.vbl{width:108px;flex:none;color:#6b5f54;}
.vbbar{flex:1;height:14px;background:#ece3d4;border-radius:7px;overflow:hidden;}
.vbbar i{display:block;height:100%;border-radius:7px;background:#cdбcaa;}
.vbrow.you .vbl{color:var(--maroon);font-weight:600;}.vbrow.you .vbbar i{background:linear-gradient(90deg,#7B0017,#a83048);}
.vbrow.rival .vbbar i{background:#b9ab93;}
.vbrow.best .vbbar i{background:linear-gradient(90deg,#b78b2e,#d8b25a);}
.vbn{width:46px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;font-family:'Poppins',sans-serif;}
.vstake{margin-top:12px;padding-top:10px;border-top:1px dashed var(--line);font-size:.82rem;font-style:italic;color:#6b5b52;}
/* matrix */
.mxlegend{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;margin:8px 2px 10px;font-family:'Poppins',sans-serif;font-size:.66rem;color:#6b5f54;}
.mxlegend b{color:var(--maroon);font-weight:600;}
.mxlegend .lk{display:flex;align-items:center;gap:6px;}
.sw{display:inline-block;width:11px;height:11px;border-radius:3px;}
.mw,.sw.mw{background:var(--win);}.ml,.sw.ml{background:var(--lose);}.mn,.sw.mn{background:var(--new);}
.matrixwrap{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 4px 18px rgba(0,0,0,.07);}
.searchwrap{margin:6px 0 14px;display:flex;align-items:center;gap:12px;}
#brandsearch{flex:1;max-width:520px;font-family:'Poppins',sans-serif;font-size:.9rem;padding:11px 16px;border:1px solid var(--line);border-radius:24px;background:#fff;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.05);outline:none;}
#brandsearch:focus{border-color:var(--maroon);box-shadow:0 0 0 3px rgba(123,0,23,.12);}
#searchcount{font-family:'Poppins',sans-serif;font-size:.72rem;color:#8a7c6c;}
.metalink{font-family:'Poppins',sans-serif;font-size:.6rem;font-weight:500;color:#2f4d7a;background:#eef2f8;border:1px solid #d8e0ee;border-radius:9px;padding:1px 7px;text-decoration:none;margin-left:8px;white-space:nowrap;}
.metalink:hover{background:#2f4d7a;color:#fff;}
.metabtn{display:inline-block;font-family:'Poppins',sans-serif;font-size:.66rem;font-weight:600;color:#fff;background:#2f4d7a;border-radius:20px;padding:6px 14px;text-decoration:none;margin:2px 0 8px;}
.metabtn:hover{background:#23395c;}
table.mx{border-collapse:separate;border-spacing:0;width:100%;font-size:.9rem;}
table.mx thead th{position:sticky;top:50px;z-index:5;background:var(--maroon);color:#fff;font-family:'Poppins',sans-serif;font-weight:500;font-size:.66rem;letter-spacing:.04em;text-transform:uppercase;text-align:left;padding:11px 14px;}
table.mx tbody td{padding:11px 14px;border-bottom:1px solid #efe7d9;vertical-align:middle;}
table.mx tbody tr:hover td{background:#fbf6ec;}
table.mx tbody tr.reia td{background:#fff2cf !important;box-shadow:inset 4px 0 0 var(--maroon);}
table.mx tr.seg td{background:#2a0a10;color:#fff;padding:9px 14px;border-bottom:none;}
.segname{font-family:'Cormorant Garamond',serif;font-size:1.15rem;font-weight:700;letter-spacing:.3px;}
.segmeta{font-family:'Poppins',sans-serif;font-size:.62rem;text-transform:uppercase;letter-spacing:.06em;opacity:.72;margin-left:12px;}
.bcell{white-space:nowrap;}.bcell .rk{display:inline-block;width:20px;color:#b3a690;font-size:.78rem;font-variant-numeric:tabular-nums;}
.bcell .brandlink{font-weight:600;color:var(--ink);text-decoration:none;border-bottom:1px dotted #c9bca8;}
.bcell .brandlink:hover{color:var(--maroon);}
.volcell,.wrcell,.mixcell,.crecell{white-space:nowrap;}
.volbar{display:inline-block;height:11px;width:108px;border-radius:6px;background:#ece3d4;vertical-align:middle;overflow:hidden;}
.volbar i{display:block;height:100%;background:linear-gradient(90deg,#7B0017,#a83048);}
.vn{margin-left:9px;font-variant-numeric:tabular-nums;}
.crecell b{color:#5d3a7a;font-size:1rem;font-variant-numeric:tabular-nums;}
.mix{display:inline-block;width:150px;height:13px;border-radius:7px;overflow:hidden;background:#ece3d4;vertical-align:middle;}
.mix i{display:inline-block;height:100%;vertical-align:top;}
.mixn{margin-left:9px;font-size:.78rem;font-variant-numeric:tabular-nums;}
.mixn .wc{color:var(--win);}.mixn .lc{color:var(--lose);}.mixn .nc{color:var(--new);}
.wrbar{display:inline-block;height:9px;width:58px;border-radius:5px;background:#ece3d4;vertical-align:middle;overflow:hidden;}
.wrbar i{display:block;height:100%;background:var(--win);}
.wrcell b{margin-left:8px;font-variant-numeric:tabular-nums;}
.gap{background:var(--maroon);color:#fff;border-radius:14px;padding:18px 22px;margin:14px 0;font-size:1rem;box-shadow:0 8px 22px rgba(123,0,23,.24);}
.gap b{color:#ffd9a8;}
/* sections */
.seghead{background:linear-gradient(100deg,#7B0017,#9a142e);color:#fff;border-radius:13px;padding:14px 20px;margin:44px 0 14px;box-shadow:0 6px 18px rgba(123,0,23,.22);}
.seghead span{font-family:'Cormorant Garamond',serif;font-size:1.55rem;font-weight:700;}
.seghead small{display:block;font-family:'Poppins',sans-serif;font-size:.66rem;letter-spacing:.04em;text-transform:uppercase;opacity:.82;margin-top:2px;}
.comp{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:14px 0;box-shadow:0 3px 14px rgba(0,0,0,.06);}
.comph h3{font-family:'Cormorant Garamond',serif;font-size:1.9rem;color:var(--maroon);margin:0 0 8px;font-weight:700;}
.btag{font-family:'Poppins',sans-serif;font-size:.56rem;letter-spacing:.05em;text-transform:uppercase;padding:3px 9px;border-radius:11px;vertical-align:middle;margin-left:8px;background:#efe2c4;color:#7a5e16;}
.btag.critical{background:#7B0017;color:#fff;}.btag.rival{background:#b23b3b;color:#fff;}.btag.global{background:#2f4d7a;color:#fff;}.btag.natural{background:#2f5d2f;color:#fff;}.btag.d2c{background:#5d3a7a;color:#fff;}.btag.self{background:var(--gold);color:#1a1a12;}
.caps{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 10px;}
.cap{font-family:'Poppins',sans-serif;font-size:.66rem;color:#6b5f54;background:#faf5ec;border:1px solid var(--line);border-radius:9px;padding:5px 11px;}
.cap b{color:var(--ink);font-size:.82rem;}
.cap.t b{color:var(--maroon);}.cap.cre b{color:#5d3a7a;}.cap.w b{color:var(--win);}.cap.l b{color:var(--lose);}.cap.n b{color:var(--new);}
.insight{font-style:italic;color:#6b5b52;font-size:.9rem;}
.winhead{font-family:'Poppins',sans-serif;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin:14px 0 8px;}
.catblock{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0;background:#fffdf8;}
.cath{display:flex;align-items:center;gap:10px;margin-bottom:9px;flex-wrap:wrap;}
.cat{font-family:'Poppins',sans-serif;font-size:.62rem;font-weight:500;color:#fff;padding:3px 10px;border-radius:11px;letter-spacing:.02em;}
.catn{font-family:'Poppins',sans-serif;font-size:.68rem;color:#8a7c6c;}
.thumbs,.gallery{display:flex;flex-wrap:wrap;gap:8px;}
.th{position:relative;width:104px;height:104px;border-radius:10px;overflow:hidden;border:1px solid var(--line);background:#efe7d8;text-decoration:none;display:block;flex:none;box-shadow:0 1px 4px rgba(0,0,0,.06);transition:box-shadow .15s,transform .15s;}
.th:hover{box-shadow:0 8px 20px rgba(0,0,0,.2);transform:translateY(-2px);}
.th img{width:100%;height:100%;object-fit:cover;display:block;}
.th img.lz{opacity:0;transition:opacity .35s;background:#efe7d8;}
.th img.lz.ld{opacity:1;}
.th .noimg{display:flex;align-items:center;justify-content:center;width:100%;height:100%;font-family:'Poppins',sans-serif;font-size:.58rem;color:#a89a88;text-align:center;padding:4px;}
.th .thm{position:absolute;top:5px;left:5px;background:rgba(21,21,14,.78);color:#fff;font-family:'Poppins',sans-serif;font-size:.56rem;font-weight:600;width:16px;height:16px;line-height:16px;text-align:center;border-radius:5px;}
.th .thd{position:absolute;bottom:5px;left:5px;background:rgba(21,21,14,.74);color:#fff;font-family:'Poppins',sans-serif;font-size:.56rem;padding:1px 6px;border-radius:6px;}
.ntag{position:absolute;top:5px;right:5px;background:rgba(42,10,16,.92);color:#ffd9a8;font-family:'Poppins',sans-serif;font-size:.58rem;font-weight:700;padding:2px 6px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.3);}
.more{display:flex;align-items:center;justify-content:center;width:104px;height:104px;border-radius:10px;border:1px dashed #c9bca8;color:#8a7c6c;font-family:'Poppins',sans-serif;font-size:.72rem;background:#faf5ec;}
.twist{margin-top:9px;font-size:.86rem;background:#fcf6ea;border-left:3px solid var(--gold);padding:8px 12px;border-radius:0 8px 8px 0;}
.tl{font-family:'Poppins',sans-serif;font-size:.58rem;font-weight:600;letter-spacing:.06em;color:var(--gold);margin-right:6px;}
.galsec{margin:12px 0;}
.galh{font-family:'Poppins',sans-serif;font-size:.66rem;letter-spacing:.05em;text-transform:uppercase;padding:5px 0;color:#8a7c6c;border-top:1px solid var(--line);margin-top:8px;}
.galh.lose{color:var(--lose);}.galh.new{color:var(--new);}
.empty{font-size:.84rem;color:#a89a88;font-style:italic;padding:8px 0;}
.rcgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}
@media(max-width:760px){.rcgrid{grid-template-columns:1fr;}}
.rc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 15px;box-shadow:0 2px 8px rgba(0,0,0,.05);border-top:3px solid var(--maroon);}
.rc.stat{border-top-color:var(--new);}
.rch{font-family:'Cormorant Garamond',serif;font-size:1.18rem;font-weight:700;color:var(--ink);margin-bottom:6px;}
.badges{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:6px;}
.per,.out,.fmtb{font-family:'Poppins',sans-serif;font-size:.58rem;padding:2px 8px;border-radius:9px;}
.per{background:#efe2c4;color:#7a5e16;}.out{background:#e3ecdf;color:#2f5d2f;}.fmtb{background:#eee;color:#555;}
.hook{font-size:.88rem;margin:6px 0;}
.rcref{font-size:.74rem;color:#8a7c6c;border-top:1px solid var(--line);padding-top:6px;margin-top:6px;}
.hsub{font-family:'Poppins',sans-serif;font-size:.7rem;color:#9a8a80;font-weight:400;}
table.per{border-collapse:collapse;width:100%;font-size:.86rem;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.05);}
table.per td{border:1px solid var(--line);padding:8px 11px;vertical-align:top;}
.foot{margin-top:34px;font-size:.76rem;color:#8a7a70;border-top:1px solid var(--line);padding-top:14px;}
@media print{.top{position:static;}table.mx thead th{position:static;}.comp,.catblock,.vscard,.matrixwrap,.th,.rc,.seghead{break-inside:avoid;box-shadow:none;}body{background:#fff;}}
"""
CSS=CSS.replace("#cdбcaa","#cdbcaa")
nav='<a href="#vsfield">Réia vs field</a> <a href="#overview">Overview</a> '+' '.join(f'<a href="#{aid(b)}">{html.escape(b.split(" (")[0])}</a>' for b in order)+' <a href="#recos">★ Recos</a>'
B=[]
B.append('<div class="top"><div class="tt">RÉIA · Competitor &amp; Category Creative Intelligence</div><div class="nav">'+nav+'</div></div><div class="wrap">')
B.append(f'<div class="hero"><div class="k">Holistic creative breakdown · {stats["brands"]} brands · 12 June 2026</div><h1>Where Réia stands — and what every brand is winning on</h1><div class="sub">Read it top to bottom: how you compare, the full brand matrix, then each brand\'s winning creatives with the Réia twist.</div></div>')
B.append(f'<div class="statrow"><div class="stat"><div class="n">{stats["brands"]}</div><div class="l">Brands tracked</div></div><div class="stat"><div class="n">{stats["unique"]}</div><div class="l">Live placements</div></div><div class="stat s2"><div class="n">{stats["winning"]}</div><div class="l">Winning 2+wk</div></div><div class="stat s4"><div class="n">{stats["losing"]+stats["newly"]}</div><div class="l">Short-run + new</div></div></div>')
B.append(vspanel)
B.append('<h2 id="overview">Overview — every brand at a glance</h2>')
B.append('<div class="searchwrap"><input id="brandsearch" type="search" placeholder="🔎  Search a competitor… (filters the table and the brand sections)" autocomplete="off"><span id="searchcount"></span></div>')
B.append('<div class="note"><b>How to read this:</b> the <b>Live placements</b> bar shows raw ad volume; <b>Creatives</b> is the distinct-ad count after we collapse duplicates; the <b>Status mix</b> bar shows what share is Winning (2+ wks), Short-run (1–2 wks) or Newly (&lt;1 wk); <b>Win-rate</b> = % surviving 2+ weeks. Click any brand to jump to its creatives.</div>')
B.append(matrix); B.append(gap)
B.append('<h2>Brand-by-brand creative breakdown</h2><div class="note" style="border-left-color:var(--maroon)">Each thumbnail is one distinct creative — a <b>x N</b> badge means that creative runs as N separate placements. Use the search box to jump to a brand; click <b>↗ Verify on Meta Ad Library</b> in any brand to cross-check against the live source.</div>'+''.join(sections))
B.append(f'<h2 id="recos">20 Reel recommendations <span class="hsub">(persona + output)</span></h2><div class="rcgrid">{reels}</div>')
B.append(f'<h2>20 Static recommendations <span class="hsub">(persona + output)</span></h2><div class="rcgrid">{stat}</div>')
B.append(f'<h2>Personas</h2><table class="per"><tr><td><b>Persona</b></td><td><b>Who</b></td><td><b>Output target</b></td></tr>{personarows}</table>')
B.append(f'<div class="foot">{stats["brands"]} brands · {stats["unique"]} live placements · {len(IMG)} thumbnails · creatives de-duplicated via Meta collation_id. Auto-published from GitHub. EF/VVS floor applies to all Réia creative.</div></div>')
LAZY="<script>(function(){function go(){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var im=e.target;if(im.dataset.src){im.src=im.dataset.src;im.removeAttribute('data-src');im.addEventListener('load',function(){im.classList.add('ld');});im.addEventListener('error',function(){im.classList.add('ld');});}io.unobserve(im);}});},{rootMargin:'900px 0px'});document.querySelectorAll('img.lz[data-src]').forEach(function(im){io.observe(im);});}if('IntersectionObserver' in window){go();}else{document.querySelectorAll('img.lz[data-src]').forEach(function(im){im.src=im.dataset.src;im.classList.add('ld');});}window.addEventListener('beforeprint',function(){document.querySelectorAll('img.lz[data-src]').forEach(function(im){im.src=im.dataset.src;});});})();</script>"
SEARCH="<script>(function(){var inp=document.getElementById('brandsearch');if(!inp)return;var cnt=document.getElementById('searchcount');function f(){var q=inp.value.trim().toLowerCase();var n=0;document.querySelectorAll('table.mx tbody tr[data-brand]').forEach(function(r){var hit=!q||r.getAttribute('data-brand').indexOf(q)>-1;r.style.display=hit?'':'none';if(hit)n++;});document.querySelectorAll('table.mx tbody tr.seg').forEach(function(s){s.style.display=q?'none':'';});document.querySelectorAll('section.comp[data-brand]').forEach(function(s){s.style.display=(!q||s.getAttribute('data-brand').indexOf(q)>-1)?'':'none';});document.querySelectorAll('.seghead').forEach(function(s){s.style.display=q?'none':'';});cnt.textContent=q?(n+' match'+(n==1?'':'es')):'';}inp.addEventListener('input',f);})();</script>"
OUT="<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'><meta name=referrer content=no-referrer><title>Reia Competitor Intelligence</title><style>"+CSS+"</style></head><body>"+''.join(B)+LAZY+SEARCH+"</body></html>"
open(BASE+"/reports/Reia-Competitor-Creative-Breakdown.html","w",encoding="utf-8").write(OUT)
print("WROTE", len(OUT), "chars")
# padding line 1 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 2 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 3 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 4 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 5 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 6 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 7 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 8 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 9 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 10 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 11 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 12 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 13 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 14 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 15 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 16 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 17 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 18 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 19 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 20 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 21 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 22 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 23 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 24 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 25 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 26 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 27 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 28 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 29 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 30 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 31 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 32 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 33 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 34 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 35 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 36 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 37 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 38 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 39 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 40 — guards the file tail against OneDrive sync truncation; safe to ignore
