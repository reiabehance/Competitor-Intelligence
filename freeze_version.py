# -*- coding: utf-8 -*-
"""
Make a snapshot's thumbnails PERMANENT by downloading them into a SHARED, content-addressed
image pool (share/img/) and rewriting the page to local paths. Runs on the GitHub runner.
Fix: the HTML stores image URLs HTML-escaped (&amp;), so we must un-escape before fetching.
"""
import os, re, sys, hashlib, urllib.request, html as _html, time as _time
ROOT = os.environ.get("REPO_ROOT", os.path.dirname(os.path.abspath(__file__)))
SHARE = os.path.join(ROOT, "share")
POOL = os.path.join(SHARE, "img")     # shared pool — versions/<x>/ and monthly/<x>/ reach it via ../../img/
VERS = os.path.join(SHARE, "versions")

def resolve(arg):
    if arg:
        if os.path.isdir(arg): return arg
        if os.path.isdir(os.path.join(ROOT, arg)): return os.path.join(ROOT, arg)
        if os.path.isdir(os.path.join(VERS, arg)): return os.path.join(VERS, arg)
    vs = sorted(os.listdir(VERS)) if os.path.isdir(VERS) else []
    if not vs: sys.exit("No version to freeze.")
    return os.path.join(VERS, vs[-1])

HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/*,*/*"}

def fetch(real, out):
    for attempt in range(3):
        try:
            req = urllib.request.Request(real, headers=HDRS)
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if data:
                with open(out, "wb") as f: f.write(data)
                return True
        except Exception:
            _time.sleep(1.5 * (attempt + 1))
    return False

def freeze(vdir):
    os.makedirs(POOL, exist_ok=True)
    print("Freezing:", vdir)
    for fn in ("index.html", "decision-brief.html"):
        fp = os.path.join(vdir, fn)
        if not os.path.exists(fp): continue
        html = open(fp, encoding="utf-8").read()
        urls = set(re.findall(r'data-src="([^"]+)"', html)) | set(re.findall(r'(?<!data-)src="(https://[^"]+fbcdn[^"]+)"', html))
        done = fail = reused = 0
        for u in urls:
            real = _html.unescape(u)   # HTML has &amp; -> fetch the REAL url with &
            h = hashlib.md5(u.encode()).hexdigest()[:20] + ".jpg"
            out = os.path.join(POOL, h)
            if os.path.exists(out):
                reused += 1
            elif fetch(real, out):
                done += 1
            else:
                fail += 1
                continue
            html = html.replace('data-src="' + u + '"', 'src="../../img/' + h + '"').replace('src="' + u + '"', 'src="../../img/' + h + '"')
        html = html.replace('class="lz"', 'class="lz ld"')
        open(fp, "w", encoding="utf-8").write(html)
        print("  " + fn + ": downloaded " + str(done) + ", reused " + str(reused) + ", failed " + str(fail) + " -> ../../img/")

if __name__ == "__main__":
    freeze(resolve(sys.argv[1] if len(sys.argv) > 1 else None))
# tail-guard padding (after code; truncation here is harmless)
# tail-guard padding (after code; truncation here is harmless)
# tail-guard padding (after code; truncation here is harmless)
# tail-guard padding (after code; truncation here is harmless)
# tail-guard padding (after code; truncation here is harmless)
