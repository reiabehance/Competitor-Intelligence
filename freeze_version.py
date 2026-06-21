# -*- coding: utf-8 -*-
"""
Make a snapshot's thumbnails PERMANENT by downloading them into a SHARED, content-addressed
image pool (share/img/) and rewriting the page to local paths. The shared pool means the same
creative is stored once no matter how many versions use it -> images never expire AND the repo
stays small. Runs on the GitHub runner (downloading allowed there) or locally.

Usage:
  python freeze_version.py <dir>     # freeze that folder (e.g. share/monthly/2026-06)
  python freeze_version.py <stamp>   # freeze share/versions/<stamp>
  python freeze_version.py           # freeze the newest version
"""
import os, re, sys, hashlib, urllib.request
ROOT = os.environ.get("REPO_ROOT", os.path.dirname(os.path.abspath(__file__)))
SHARE = os.path.join(ROOT, "share")
POOL = os.path.join(SHARE, "img")     # shared pool — both versions/<x>/ and monthly/<x>/ reach it via ../../img/
VERS = os.path.join(SHARE, "versions")

def resolve(arg):
    if arg:
        if os.path.isdir(arg): return arg
        if os.path.isdir(os.path.join(ROOT, arg)): return os.path.join(ROOT, arg)
        if os.path.isdir(os.path.join(VERS, arg)): return os.path.join(VERS, arg)
    vs = sorted(os.listdir(VERS)) if os.path.isdir(VERS) else []
    if not vs: sys.exit("No version to freeze.")
    return os.path.join(VERS, vs[-1])

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
            h = hashlib.md5(u.encode()).hexdigest()[:20] + ".jpg"
            out = os.path.join(POOL, h)
            if os.path.exists(out):
                reused += 1
            else:
                try:
                    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": ""})
                    with urllib.request.urlopen(req, timeout=30) as r, open(out, "wb") as f:
                        f.write(r.read())
                    done += 1
                except Exception:
                    fail += 1
                    continue
            html = html.replace(f'data-src="{u}"', f'src="../../img/{h}"').replace(f'src="{u}"', f'src="../../img/{h}"')
        html = html.replace('class="lz"', 'class="lz ld"')
        open(fp, "w", encoding="utf-8").write(html)
        print(f"  {fn}: downloaded {done}, reused {reused}, failed {fail} -> ../../img/")

if __name__ == "__main__":
    freeze(resolve(sys.argv[1] if len(sys.argv) > 1 else None))
# padding line 1 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 2 — guards the file tail against OneDrive sync truncation; safe to ignore
# padding line 3 — guards the file tail against OneDrive sync truncation; safe to ignore
