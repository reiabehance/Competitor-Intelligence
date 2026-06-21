# -*- coding: utf-8 -*-
import csv, json, re, glob, os, hashlib
from datetime import date
from collections import defaultdict, Counter
import os
BASE=os.environ.get("REPO_ROOT", os.path.dirname(os.path.abspath(__file__)))
today=date.today()
TODAY=today.isoformat()
MIN_ADS=4
# collation map (stable creative id) + the append-only "seen" ledger for NEW / weeks-running tracking
try: COLL=json.load(open(BASE+"/data/assets/collation_map.json"))
except Exception: COLL={}
try: SEEN=json.load(open(BASE+"/data/seen.json"))
except Exception: SEEN={}
try: RUNIMG=json.load(open(BASE+"/data/assets/run_img.json"))
except Exception: RUNIMG={}
PREV_KEYS=set(SEEN.keys())   # which creatives existed BEFORE this run -> anything not here is NEW

def stable_key(x):
    """A creative id that SURVIVES weekly re-scrapes (the ad link/id changes each scrape, so we must
    key on CONTENT, not the link). Priority: Meta collation_id -> brand+message hash -> image filename."""
    cid=COLL.get(x["link"])
    if cid: return str(cid)   # Meta collation_id is already stable across scrapes — keep as-is (preserves existing reviews)
    t=re.sub(r'\d+',' ',re.sub(r'\W+',' ',(x.get("copy") or ""))).strip().lower()[:90]
    if len(t)>=10: return "t_"+hashlib.md5(((x.get("brand") or "")+"|"+t).encode()).hexdigest()[:16]
    u=RUNIMG.get(x["link"]); fn=u.split("?")[0].rsplit("/",1)[-1] if u else x["link"]
    return "i_"+hashlib.md5(fn.encode()).hexdigest()[:16]

def days(s):
    try:
        y,m,d=s.split(" ")[0].split("-");return max(0,(today-date(int(y),int(m),int(d))).days)
    except: return None

# brand-name normalisation: (substring in lowercased page_name) -> canonical. Order matters (check specific first).
NORM=[
 ("reiadiamonds","Réia (self)"),
 ("mia by tanishq","Mia by Tanishq"),("candere","Candere"),("kalyan jewellers","Kalyan"),
 ("tanishq","Tanishq"),
 ("house of quadri","House of Quadri"),("quadri","House of Quadri"),
 ("onya","Onya"),("aukera","Aukera"),("wondr","Wondr"),("jewelbox","Jewelbox"),
 ("beyon","BEYON (Titan)"),("caratlane","CaratLane"),("truecarat","Truecarat"),
 ("fiona","Fiona"),("limelight","Limelight"),
 ("brilliant earth","Brilliant Earth"),("cullen","Cullen"),("blue nile","Blue Nile"),
 ("malabar gold","Malabar"),("joyalukkas","Joyalukkas"),("joy alukkas","Joyalukkas"),
 ("zoya","Zoya"),("tyaani","Tyaani"),("giva","GIVA"),("mookuthi","Mookuthi"),
 ("grassroot by anita dongre","Anita Dongre"),("anita dongre","Anita Dongre"),
 ("bombae","Bombae"),("bombay shaving","Bombay Shaving"),("suta","Suta"),("moxie","Moxie"),("gully labs","Gully Labs"),
 ("forest essentials","Forest Essentials"),("the whole truth","The Whole Truth"),("whole truth","The Whole Truth"),
 ("the sleep company","The Sleep Company"),("fizzy goblet","Fizzy Goblet"),("hidesign","Hidesign"),
 ("pant project","Pant Project"),("william penn","William Penn"),("charles & keith","Charles & Keith"),
 ("charles keith","Charles & Keith"),("nappa dori","Nappa Dori"),("frido","Frido"),("go desi","GO DESi"),
 ("gaurav gupta","Gaurav Gupta"),("shantnu","Shantnu & Nikhil"),("shantanu","Shantnu & Nikhil"),
 ("tarun tahiliani","Tarun Tahiliani"),("amit aggarwal","Amit Aggarwal"),("jaipur watch","Jaipur Watch Co"),
 ("cartier","Cartier"),("gucci","Gucci"),("armani","Armani"),("bally","Bally"),("birkenstock","Birkenstock"),
 ("levis","Levi's"),("levi's","Levi's"),("nike","Nike"),("hrx","HRX"),("cult.fit","Cult.fit"),("cultsport","Cultsport"),
 ("bluestone","BlueStone"),
 ("sabyasachi","Sabyasachi"),("raw mango","Raw Mango"),("behno","Behno"),("kay by katrina","Kay by Katrina"),
 ("huda","Huda Beauty"),("tridia","Tridia"),("avira","Avira"),("solitario","Solitario"),
]
NOISE=["matrimony","swiggy","amazon","flipkart","nykaa","sephora","myntra","adobe","american express","cashkaro",
 "propert","realty","real estate","makeup studio","beauty school","beauty salon","academy","pearl academy",
 " school"," church","sermon","ministr","drama","reelshow","top shows","kukufm","kuku fm","pocket fm"," moj",
 "glasafe","nif global","nifrajkot","nifglobal"," mall","interiors","developers","spices"," foods","kitchen",
 "icecream","ice cream","perfumes","lifespaces","grandeur","cholesterol","health support","fitline","usee shop",
 "idall","shopzilo","basico","iide","investor","franchise india","gullak","tata neu","jewellery guide",
 "bag studio","slikk","vrtti","xokatoz","gobbleright","chukde","kpra","creamka","adi.hyderabad","anasa",
 "zira","keyafoods","upalas","nusara","mycityevents","letsmoderate","urban forest","hibbs","melliphant",
 "fil-am","day trip","caasie","contactout","richmond dinh","way of the hunter","prager","culture kings",
 "manisha jewellers","maharashtra-jewellers","raj ratan","elista","diatoms","velora","seodre","vellismith",
 "house of legacy","rented kart","shoppers stop","monarch","prime commercial","dr batra","window world",
 "total sports","jazz lesson","jay hoggard","luminosity","john ross","allan bratton","sunflowerly","colonial theatre",
 "northeast comiccon","palos verdes","compressport","henson","ritual oils","blue note","city folk","cityfolk",
 "weaverville","marsh family","raising happy","brut india","lush house","jacob allen","allen james","mantra propert",
 "gnh","a dot by","best free","best app","short tv","story tv","freedrama","dramabox","drama time","drama honey",
 "vinci thrill","new york irish","secret of vitality","akrithi","floating tiger","athenese","mayo clinic",
 "blue dahlia","dr mm raza","innocence","sirius","krishniah","angara","kripalani","chirag","jain parash",
 "thangamayil","mbees","emori","mantra diamond","mantradiamond","rlx","pure jewels","new age","hbh","silver by twc",
 "darjewellery","diamondlady","firefly","avaidens","secret","indiatv","gujarati","bitespeed","mila victoria",
 "fyva","hok makeup","elevateglow","shopaarel","pankh","glamour beauty","uk international","makeup studio",
 "high design","investor","mall of faridabad","pacific mall","imm outlet","slikk",
 "jared","krupa jain","escape plan","country delight","jewelers",
 "cult equipment","cultfit","offcult","gold's gym","golds gym","tata cliq","ajiogram","ladia","emara",
 "buy original gemstones","jaison james","american health","tata cliq fashion",
 "wishlink","oyeitem","pink window","isha jaiswal","bernardo","nishchiti","surbhishukla","tarinimanchanda",
 "theriyakohli","tanisha haryani","nikita_khanna","ganeshunwired","vikash gupta","sanjana","aknksha","nishliving",
 "precisely peri","coversbyaastha","athena katoanga","georgia wellman"]

def canon(name):
    low=(name or "").strip().lower()
    if not low: return None
    for k in NOISE:
        if k in low: return None
    if low=="cult": return "Cult.fit"
    for sub,disp in NORM:
        if sub in low: return disp
    # auto-include unknown brand: use cleaned page name (drop city suffixes)
    base=re.split(r' - | – |\|', name.strip())[0].strip()
    return base

SEG={ # canonical -> (group, tagclass, tagtext)  groups: 0 self, 1 DIRECT competitor, 2 ADJACENT jewellery, 3 INSPIRATION only
 "Réia (self)":(0,"self","YOUR BRAND"),
 "Onya":(1,"critical","DIRECT · same city (Bangalore)"),"House of Quadri":(1,"rival","DIRECT · lab-grown"),
 "Aukera":(1,"rival","DIRECT · lab-grown"),"Wondr":(1,"rival","DIRECT · lab-grown"),"Jewelbox":(1,"rival","DIRECT · lab-grown"),
 "BEYON (Titan)":(1,"rival","DIRECT · Titan lab-grown"),
 "Truecarat":(1,"rival","DIRECT · lab-grown"),"Fiona":(1,"rival","DIRECT · lab-grown"),"Limelight":(1,"rival","DIRECT · lab-grown"),
 "GIVA":(1,"rival","DIRECT · D2C lab-grown/silver"),
 "CaratLane":(2,"natural","ADJACENT · Tata (lab+natural)"),"BlueStone":(2,"natural","ADJACENT · D2C fine jewellery"),
 "Cult.fit":(3,"d2c","INSPIRATION · fitness"),
 "Brilliant Earth":(1,"global","DIRECT · global (US)"),"Cullen":(1,"global","DIRECT · global (AU)"),"Blue Nile":(1,"global","DIRECT · global (US)"),
 "Tanishq":(2,"natural","ADJACENT · natural/gold"),"Mia by Tanishq":(2,"natural","ADJACENT · natural everyday"),
 "Kalyan":(2,"natural","ADJACENT · natural/gold"),"Candere":(2,"natural","ADJACENT · online (Kalyan)"),
 "Malabar":(2,"natural","ADJACENT · natural/gold"),"Joyalukkas":(2,"natural","ADJACENT · natural/gold"),
 "Zoya":(2,"natural","ADJACENT · Tata luxury"),"Tyaani":(2,"natural","ADJACENT · polki/KJo"),"Mookuthi":(2,"natural","ADJACENT · contemporary"),
 # global luxury / D2C — INSPIRATION only (creative mechanics, NOT competitors)
 "Cartier":(3,"d2c","INSPIRATION · global luxury jewellery"),"Gucci":(3,"d2c","INSPIRATION · luxury fashion"),
 "Levi's":(3,"d2c","INSPIRATION · apparel"),"Birkenstock":(3,"d2c","INSPIRATION · footwear"),
 "Sabyasachi":(3,"d2c","INSPIRATION · couture"),"Raw Mango":(3,"d2c","INSPIRATION · couture / textiles"),
 "Behno":(3,"d2c","INSPIRATION · fashion (New York)"),"Kay by Katrina":(3,"d2c","INSPIRATION · beauty (NOT jewellery)"),
 "Huda Beauty":(3,"d2c","INSPIRATION · beauty"),
 # India lab-grown DIRECT (added but no active ads captured this cycle — placeholders if they surface)
 "Tridia":(1,"rival","DIRECT · lab-grown"),"Avira":(1,"rival","DIRECT · lab-grown"),"Solitario":(1,"rival","DIRECT · lab-grown"),
}
# ---- CONFIG-DRIVEN brand map: page_urls.json is the single place to add/manage competitors ----
SEGMAP={"self":(0,"self","YOUR BRAND"),"direct":(1,"rival","DIRECT competitor"),
        "adjacent":(2,"natural","ADJACENT jewellery"),"inspiration":(3,"d2c","INSPIRATION only — not a competitor")}
PAGEMAP={}   # page_id -> {brand,group,tag,tagtext,country}
try:
    _cfg=json.load(open(os.path.join(BASE,"page_urls.json"),encoding="utf-8"))
    for _p in _cfg.get("pages",[]):
        _g=SEGMAP.get((_p.get("seg") or "inspiration").lower(),SEGMAP["inspiration"])
        PAGEMAP[str(_p["page_id"])]={"brand":_p["brand"],"group":_g[0],"tag":_g[1],"tagtext":_g[2],"country":_p.get("country","ALL")}
except Exception as _e:
    print("page_urls.json not loaded (fallback to hardcoded SEG):",_e)
BRANDINFO={}  # canonical brand -> {group,tag,tagtext,page_id,country}; filled while reading rows
def seg(b):
    if b in BRANDINFO:
        i=BRANDINFO[b]; return (i["group"],i["tag"],i["tagtext"])
    return SEG.get(b,(3,"d2c","INSPIRATION only — not a competitor"))

def category(copy, title, fmt):
    t=((title or "")+" "+(copy or "")).lower()
    if "{{product" in t or (not t.strip() and fmt in("DCO","DPA")): return "Product / Catalogue"
    rules=[
     ("Offer / Discount", r"% off|flat \d|off on making|making charge|value addition|110%|buy \d|exchange|old gold|discount|sale is live|upto \d|₹\d+ off|starting ₹|starting rs|deal|save \d"),
     ("Festival / Seasonal", r"akshaya|diwali|valentine|festive|festival|wedding season|raksha"),
     ("Education", r"explained|what to check|lab.?grown|vs natural|certified|igi|clarity|\bcut\b|learn|myth|difference|cvd|hpht|ef colour|vvs|how to|guide|what makes|things to know"),
     ("Proposal / Emotional", r"propos|she said yes|the big question|forever|love story|her ring|will you|big day|romantic|fall for you|anniversary|gift"),
     ("Co-creation / Custom", r"custom|design(ed)? with|personali|your names|your date|your story|vision|sketch|bespoke|built from|made for you|design lab|your style|made to order"),
     ("Social Proof", r"\d{3}\+|customers chose|loved by thousands|bestseller|reviews|most.loved|chose this|rated|trusted by"),
     ("Store launch / Footfall", r"now open|grand opening|visit us|visit our|arrived at|new store|get directions|store|boutique|launch"),
     ("UGC / Testimonial", r"comment .* for|story time|my hair|obsessed|i tried|ily |@\w+|#fyp|#foryou|tried a bunch|go.?to|honest review"),
     ("Everyday / Lifestyle", r"everyday|every day|worn because|self|treat yourself|stack|layer|9kt|lightweight|out of office|daily|comfort"),
     ("Cultural / Heritage", r"heritage|tradition|motif|ghungroo|temple|desi|india's love|dance|kantha|handcrafted|artisan|craft"),
     ("Brand film", r"follow the feeling|an ode|meet [a-z]+\.|unrushed|let things land|introducing|new collection"),
    ]
    for name,pat in rules:
        if re.search(pat, t): return name
    if fmt=="VIDEO": return "Brand / Product video"
    return "Product / Catalogue"

bylink={}
for rf in sorted(glob.glob(BASE+"/data/raw/*.csv")):
    try:
        for r in csv.DictReader(open(rf,encoding="utf-8")):
            link=r.get("ad_library_url","")
            if not link: continue
            pid=str(r.get("page_id","") or "").strip()
            if pid and pid in PAGEMAP:                 # tracked brand (config-driven, by page id)
                info=PAGEMAP[pid]; b=info["brand"]
                BRANDINFO[b]={"group":info["group"],"tag":info["tag"],"tagtext":info["tagtext"],"page_id":pid,"country":info["country"]}
            elif pid:                                   # an ad from a page we don't track (collab / branded content) -> skip
                continue
            else:                                       # legacy CSV with no page_id column -> fall back to name matching
                b=canon(r.get("page_name",""))
                if not b: continue
            copy=(r.get("body_text","") or "").strip()
            cur=bylink.get(link)
            if cur and len(cur["copy"])>=len(copy): continue
            bylink[link]={"brand":b,"fmt":(r.get("display_format","") or ""),"title":(r.get("title","") or ""),
                "copy":copy,"start":(r.get("start_date","") or "")[:10],"link":link,"hasvid":(r.get("has_video","") or "")}
    except Exception as e:
        print("skip",rf,e)
rows=list(bylink.values())
for x in rows:
    dd=days(x["start"]); x["dd"]=dd
    x["media"]="Reel" if (x.get("hasvid")=="1" or x["fmt"]=="VIDEO") else "Static"
    x["status"]=("Winning" if dd>=14 else "Losing" if dd>=7 else "Newly") if dd is not None else "?"
    x["cat"]=category(x["copy"],x["title"],x["fmt"])
    x["ckey"]=stable_key(x)                              # content-stable creative id (review/save key, survives weekly runs)
# --- update the append-only seen ledger: first-seen date + how many runs each creative has appeared in ---
for x in rows:
    if x["status"]=="?": continue
    k=x["ckey"]
    if k in SEEN:
        if SEEN[k].get("last")!=TODAY: SEEN[k]["runs"]=SEEN[k].get("runs",1)+1
        SEEN[k]["last"]=TODAY
    else:
        SEEN[k]={"first":TODAY,"last":TODAY,"runs":1}
    x["new"]=(k not in PREV_KEYS)                         # first appearance ever = NEW this week
    x["weeks"]=SEEN[k]["runs"]; x["first"]=SEEN[k]["first"]
try: json.dump(SEEN, open(BASE+"/data/seen.json","w"))
except Exception as _se: print("seen ledger save skipped:",_se)

# brand totals, keep >=MIN_ADS OR any tracked brand (in page_urls.json / hardcoded)
bc=Counter(x["brand"] for x in rows if x["status"]!="?")
known=set(BRANDINFO.keys())|set(SEG.keys())|set(disp for _,disp in NORM)
keep=[b for b,n in bc.items() if n>=MIN_ADS or b in known]
KEYS=["WR","WS","LR","LS","NR","NS"]
KM={("Winning","Reel"):"WR",("Winning","Static"):"WS",("Losing","Reel"):"LR",("Losing","Static"):"LS",("Newly","Reel"):"NR",("Newly","Static"):"NS"}
buckets=defaultdict(lambda:{k:[] for k in KEYS})
for x in rows:
    if x["status"]=="?" or x["brand"] not in keep: continue
    buckets[x["brand"]][KM[(x["status"],x["media"])]].append(x)

# order brands: by segment group, then ad count desc
order=sorted(keep, key=lambda b:(seg(b)[0], -bc[b]))
brk={}; insight={}; meta={}
for b in order:
    v=buckets[b]
    brk[b]={k:[{"cat":a["cat"],"dd":a["dd"],"fmt":a["fmt"],"copy":(a["title"] or a["copy"])[:150],"link":a["link"],
                "ckey":a.get("ckey",a["link"]),"new":a.get("new",False),"weeks":a.get("weeks",1),"first":a.get("first","")}
              for a in sorted(v[k],key=lambda a:-(a["dd"] if a["dd"] is not None else 0))] for k in KEYS}
    g,tc,tt=seg(b); _bi=BRANDINFO.get(b,{})
    meta[b]={"group":g,"tag":tc,"tagtext":tt,"total":bc[b],"page_id":_bi.get("page_id",""),"country":_bi.get("country","ALL")}
    winners=v["WR"]+v["WS"]
    if winners:
        topcat=Counter(a["cat"] for a in winners).most_common(1)[0][0]
        insight[b]=f"Wins on {topcat} · {len(v['WR'])} winning reels, {len(v['WS'])} winning statics"
    else:
        insight[b]=f"No 2-week survivors captured · {len(v['NR'])+len(v['NS'])} newly launched"
json.dump({"brk":brk,"insight":insight,"meta":meta,"order":order}, open(BASE+"/data/assets/breakdown6.json","w"), ensure_ascii=False)
sW=sum(1 for x in rows if x["status"]=="Winning" and x["brand"] in keep)
sL=sum(1 for x in rows if x["status"]=="Losing" and x["brand"] in keep)
sN=sum(1 for x in rows if x["status"]=="Newly" and x["brand"] in keep)
uniq=sum(bc[b] for b in keep)
json.dump({"unique":uniq,"winning":sW,"losing":sL,"newly":sN,"brands":len(keep)}, open(BASE+"/data/assets/stats6.json","w"))
GN={0:"Réia",1:"Direct competitors",2:"Adjacent jewellery",3:"Inspiration only"}
try:
    print("brands kept:",len(keep),"| unique ads:",uniq,"| W",sW,"L",sL,"N",sN)
    for _grp in range(4):
        _bs=[b for b in order if seg(b)[0]==_grp]
        print("  ["+GN[_grp]+"] "+str(len(_bs))+": "+", ".join(b+"("+str(bc[b])+")" for b in _bs))
except Exception as _pe:
    print("summary print skipped:", _pe)
# --- end of classify.py ---  (padding below guards against editor/sync tail-truncation)
# pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad
# pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad
# pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad pad
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
# padding line 18 