# -*- coding: utf-8 -*-
"""
Réia weekly competitor-intel pipeline — STANDALONE (runs on GitHub Actions).
Scrapes every brand in config/page_urls.json via the Apify REST API, extracts the data,
then runs classify -> render -> build_share -> freeze. No MCP / no Cowork needed.
Requires env var APIFY_TOKEN (set as a GitHub Actions secret).
"""
import os, sys, json, time, csv, subprocess, urllib.request, urllib.parse, datetime

ROOT = os.environ.get("REPO_ROOT", os.path.dirname(os.path.abspath(__file__)))
CFG  = ROOT
RAW  = os.path.join(ROOT, "data", "raw")
ASSETS = os.path.join(ROOT, "data", "assets")
REPORTS = os.path.join(ROOT, "reports")
for d in (RAW, ASSETS, REPORTS):
    os.makedirs(d, exist_ok=True)

TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
ACTOR = "curious_coder~facebook-ads-library-scraper"
API = "https://api.apify.com/v2"
DIRECT_LIMIT = 1000   # ~100% coverage for DIRECT competitors (+ Réia) — captures every active ad
REST_LIMIT = 200      # cap for adjacent + inspiration brands (cost control)

def _get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode())

def _post(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def _run_actor(pages, limit, tmpl):
    if not pages:
        return []
    urls = [{"url": tmpl.replace("{COUNTRY}", p["country"]).replace("{PAGE_ID}", p["page_id"])} for p in pages]
    inp = {"urls": urls, "scrapePageAds.activeStatus": "active", "scrapePageAds.sortBy": "impressions_desc",
           "runTag": "github_" + datetime.date.today().isoformat()}
    if limit:
        inp["limitPerSource"] = limit
    print(f"  scraping {len(pages)} pages (limit={limit or 'ALL'}) ...")
    run = _post(f"{API}/acts/{ACTOR}/runs?token={TOKEN}", inp)["data"]
    rid = run["id"]
    while True:
        time.sleep(10)
        st = _get(f"{API}/actor-runs/{rid}?token={TOKEN}")["data"]
        if st["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    if st["status"] != "SUCCEEDED":
        sys.exit("Apify run did not succeed: " + st["status"])
    ds = st["defaultDatasetId"]
    items, offset = [], 0
    while True:
        chunk = _get(f"{API}/datasets/{ds}/items?token={TOKEN}&clean=true&limit=1000&offset={offset}")
        if not chunk:
            break
        items.extend(chunk)
        offset += len(chunk)
        if len(chunk) < 1000:
            break
    return items

def run_scrape():
    if not TOKEN:
        sys.exit("APIFY_TOKEN env var is not set — add it as a GitHub Actions secret.")
    cfg = json.load(open(os.path.join(CFG, "page_urls.json"), encoding="utf-8"))
    tmpl = cfg["url_template"]
    direct = [p for p in cfg["pages"] if (p.get("seg") or "").lower() in ("direct", "self")]
    rest   = [p for p in cfg["pages"] if (p.get("seg") or "").lower() not in ("direct", "self")]
    print(f"Scraping {len(direct)} direct/self at 100% + {len(rest)} adjacent/inspiration at cap {REST_LIMIT} ...")
    items = _run_actor(direct, DIRECT_LIMIT, tmpl) + _run_actor(rest, REST_LIMIT, tmpl)
    print(f"Fetched {len(items)} ads total.")
    return items

def best_img(snap):
    for arr, key in [("images", "resized_image_url"), ("images", "original_image_url"),
                     ("videos", "video_preview_image_url"), ("cards", "resized_image_url"),
                     ("cards", "original_image_url"), ("cards", "video_preview_image_url"),
                     ("extra_images", "resized_image_url")]:
        a = snap.get(arr) or []
        if isinstance(a, list) and a and isinstance(a[0], dict) and a[0].get(key):
            return a[0][key]
    return None

def extract(items):
    # one fresh complete scrape -> one CSV + img map + collation map
    csv_path = os.path.join(RAW, "latest_scrape.csv")
    img_map, coll_map = {}, {}
    rows = 0
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["page_name", "display_format", "cta_text", "title", "body_text",
                    "start_date", "end_date", "is_active", "ad_library_url", "publisher_platform", "has_video", "page_id"])
        for it in items:
            if it.get("error") or not it.get("ad_library_url"):
                continue
            link = it["ad_library_url"]
            snap = it.get("snapshot") or {}
            body = snap.get("body")
            body_text = body.get("text") if isinstance(body, dict) else (body or "")
            pp = it.get("publisher_platform") or []
            pp = ";".join(pp) if isinstance(pp, list) else str(pp or "")
            # Detect VIDEO regardless of display_format — DCO/DPA dynamic ads can carry video creative.
            vids = snap.get("videos") or []
            cards = snap.get("cards") or []
            has_video = "1" if (snap.get("display_format") == "VIDEO"
                or any(isinstance(v, dict) and (v.get("video_sd_url") or v.get("video_hd_url") or v.get("video_preview_image_url")) for v in vids)
                or any(isinstance(c, dict) and (c.get("video_sd_url") or c.get("video_hd_url")) for c in cards)) else ""
            w.writerow([snap.get("page_name") or it.get("page_name") or "", snap.get("display_format") or "",
                        snap.get("cta_text") or "", snap.get("title") or "", body_text or "",
                        it.get("start_date_formatted") or "", it.get("end_date_formatted") or "",
                        it.get("is_active"), link, pp, has_video,
                        str(it.get("page_id") or snap.get("page_id") or "")])
            rows += 1
            im = best_img(snap)
            if im:
                img_map[link] = im
            if it.get("collation_id"):
                coll_map[link] = str(it["collation_id"])
    json.dump(img_map, open(os.path.join(ASSETS, "run_img.json"), "w"))
    json.dump(coll_map, open(os.path.join(ASSETS, "collation_map.json"), "w"))
    # static dep needed by render
    src = os.path.join(CFG, "recommendations2.json")
    if os.path.exists(src):
        json.dump(json.load(open(src, encoding="utf-8")), open(os.path.join(ASSETS, "recommendations2.json"), "w"), ensure_ascii=False)
    print(f"Wrote CSV ({rows} rows), {len(img_map)} thumbnails, {len(coll_map)} collation ids.")

def run(script, *args):
    env = dict(os.environ, REPO_ROOT=ROOT)
    print(f"\n>>> {script} {' '.join(args)}")
    subprocess.check_call([sys.executable, os.path.join(ROOT, script), *args], env=env)
if __name__ == "__main__":
    items = run_scrape()
    extract(items)
    run("classify.py")
    run("render.py")
    run("build_share.py")
    # Freeze the MONTHLY archive so its thumbnails are permanent (the historical record).
    ym = datetime.datetime.now().strftime("%Y-%m")
    monthly_dir = os.path.join(ROOT, "share", "monthly", ym)
    if os.path.isdir(monthly_dir):
        run("freeze_version.py", monthly_dir)
    print("\nPipeline complete.")
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
# padding line 34 — guards the file tail against OneDrive sync tru