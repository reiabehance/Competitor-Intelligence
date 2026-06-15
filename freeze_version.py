# -*- coding: utf-8 -*-
"""
Make a saved snapshot's thumbnails PERMANENT: download every thumbnail into the snapshot's
own /img folder and rewrite the page to local paths -> self-contained, never expires.

Runs on the GitHub runner (downloading is allowed there) or on your own computer.
Usage:
  python freeze_version.py <abs_or_rel_dir>   # freeze that folder (e.g. share/monthly/2026-06)
  python freeze_version.py <stamp>            # freeze share/versions/<stamp>
  python freeze_version.py                    # freeze the newest version
"""
import os, re, sys, hashlib, urllib.request
ROOT = os.environ.get("REPO_ROOT", os.path.dirname(os.path.abspath(__file__)))
SHARE = os.path.join(ROOT, "share")
VERS = os.path.join(SHARE, "versions")

def resolve(arg):
    if arg:
        if os.path.isdir(arg):
            return arg
        if os.path.isdir(os.path.join(ROOT, arg)):
            return os.path.join(ROOT, arg)
        if os.path.isdir(os.path.join(VERS, arg)):
            return os.path.join(VERS, arg)
    vs = sorted(os.listdir(VERS)) if os.path.isdir(VERS) else []
    if not vs:
        sys.exit("No version to freeze.")
    return os.path.join(VERS, vs[-1])

def freeze(vdir):
    print("Freezing:", vdir)
    for fn in ("index.html", "decision-brief.html"):
        fp = os.path.join(vdir, fn)
        if not os.path.exists(fp):
            continue
        html = open(fp, encoding="utf-8").read()
        imgdir = os.path.join(vdir, "img"); os.makedirs(imgdir, exist_ok=True)
        urls = set(re.findall(r'data-src="([^"]+)"', html)) | set(re.findall(r'(?<!data-)src="(https://[^"]+fbcdn[^"]+)"', html))
        done = fail = 0
        for u in urls:
            h = hashlib.md5(u.encode()).hexdigest()[:16] + ".jpg"
            out = os.path.join(imgdir, h)
            if not os.path.exists(out):
                try:
                    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": ""})
                    with urllib.request.urlopen(req, timeout=30) as r, open(out, "wb") as f:
                        f.write(r.read())
                    done += 1
                except Exception:
                    f