# Réia — Competitor Intelligence (auto-publishing)

This repo scrapes competitor Facebook ads, builds the creative-intelligence breakdown, freezes the monthly archive's thumbnails so they never expire, and publishes everything to a permanent GitHub Pages link — **on its own, every 5 days**. No clicks after setup.

What gets published: `share/index.html` (the history hub) → links to each version's breakdown + the frozen monthly archives.

---

## One-time setup (all in your browser — ~15 minutes)

### 1. Copy your Apify API token
- Go to **console.apify.com** → click your avatar → **Settings** → **API & Integrations**.
- Copy the **Personal API token** (a long string). Keep it handy.

### 2. Create the GitHub repository
- Go to **github.com** → top-right **+** → **New repository**.
- Name it `reia-competitor-intel`.
- **Visibility:** choose **Public** (free GitHub Pages needs a public repo). ⚠️ Public means the code and scraped data are visible to anyone who finds the repo. If you need it private, GitHub Pages on a private repo requires **GitHub Pro** (~$4/mo) — pick Private + later upgrade if so.
- Click **Create repository**.

### 3. Upload the 9 flat files (no folders to worry about)
On the new empty repo page, click **“uploading an existing file”**, then drag in ALL of these at once (they all sit at the top level of the `reia-github` folder — just select them and drag):
`pipeline.py`, `classify.py`, `render.py`, `build_share.py`, `freeze_version.py`, `page_urls.json`, `recommendations2.json`, `README.md`, `.gitignore`
Then **Commit changes**.

### 3b. Add the one workflow file (the only thing that needs a folder path)
- Click **Add file → Create new file**.
- In the filename box, type exactly: `.github/workflows/weekly.yml` — typing the `/` slashes makes GitHub create the folders for you automatically.
- Open the `weekly.yml` card I shared, copy ALL of its contents, paste into the editor.
- **Commit changes.**

### 4. Add your Apify token as a secret
- Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
- Name: `APIFY_TOKEN`   ·   Value: paste your token   ·   **Add secret**.

### 5. Turn on GitHub Pages
- Repo → **Settings** → **Pages** → under **Build and deployment**, set **Source = GitHub Actions**. (Nothing else to fill in.)

### 6. Run it the first time
- Repo → **Actions** tab → if asked, click **“I understand my workflows, enable them.”**
- Click **“Réia Weekly Competitor Intel”** → **Run workflow** → **Run workflow**.
- It takes ~10–15 minutes (it scrapes all 56 brands, builds, and freezes images).

### 7. Get your permanent link
- When the run finishes (green check), go to **Settings → Pages** — your live URL is shown, like:
  `https://<your-username>.github.io/reia-competitor-intel/`
- That is the link you share with the team. It updates itself every 5 days from now on.

---

## Good to know
- **Cost:** each run scrapes ~5,000–6,000 ads via Apify (~$4–5/run, ~$25/mo at this cadence). Apify bills your account.
- **Schedule:** runs every 5 days (`cron: 0 6 */5 * *`). Change the cron in `.github/workflows/weekly.yml` to adjust. You can also hit **Run workflow** any time.
- **History:** every run is frozen under `share/versions/<date>/`; each month's final state is frozen with permanent images under `share/monthly/<YYYY-MM>/`. Nothing is ever overwritten.
- **What this does NOT do:** the weekly email draft, the Excel "Bible", and the Decision Brief are still produced by your Cowork assistant's scheduled task. Keep that running for those; this repo handles the live shareable breakdown + archive.
- **To change the brand list:** edit `config/page_urls.json` and commit — the next run picks it up.
