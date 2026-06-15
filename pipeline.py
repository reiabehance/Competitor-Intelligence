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
LIMIT_PER_SOURCE = 200

def _get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode())

def _post(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def run_scrape():
    if not TOKEN:
        sys.exit("APIFY_TOKEN env var is not set — add it as a GitHub Actions secret.")
    cfg = json.load(open(os.path.join(CFG, "page_urls.json"), encoding="utf-8"))
    tmpl = cfg["url_template"]
    urls = [{"url": tmpl.replace("{COUNTRY}", p["country"]).replace("{PAGE_ID}", p["page_id"])} for p in cfg["pages"]]
    inp = {"urls": urls, "limitPerSource": LIMIT_PER_SOURCE,
           "scrapePageAds.activeStatus": "active", "scrapePageAds.sortBy": "impressions_desc",
           "runTag": "github_" + datetime.date.today().isoformat()}
    print(f"Starting Apify scrape of {len(urls)} brands ...")
    run = _post(f"{API}/acts/{ACTOR}/runs?token={TOKEN}", inp)["data"]
    run_id = run["id"]
    while True:
        time.sleep(10)
        st = _get(f"{API}/actor-runs/{run_id}?token={TOKEN}")["data"]
        print("  status:", st["status"], "| items so far: checking...")
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
    print(f"Fetched {len(items)} ads.")
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
                    "start_date", "end_date", "is_active", "ad_library_url", "publisher_platform"])
        for it in items:
            if it.get("error") or not it.get("ad_library_url"):
                continue
            link = it["ad_library_url"]
            snap = it.get("snapshot") or {}
            body = snap.get("body")
            body_text = body.get("text") if isinstance(body, dict) else (body or "")
            pp = it.get("publisher_platform") or []
            pp = ";".join(pp) if isinstance(pp, list) else str(pp or "")
            w.writerow([snap.get("page_name") or it.get("page_name") or "", snap.get("display_format") or "",
                        snap.get("cta_text") or "", snap.get("title") or "", body_text or "",
                        it.get("start_date_formatted") or "", it.get("end_date_formatted") or "",
                        it.get("is_active"), link, pp])
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
    # The current weekly version keeps live CDN images (fresh during its active window) to keep the repo lean.
    ym = datetime.datetime.now().strftime("%Y-%m")
    monthly_dir = os.path.join(ROOT, "share", "monthly", ym)
    if os.path.isdir(monthly_dir):
        run("freeze_version.py", monthly_dir)
    print("\nPipeline complete.")
