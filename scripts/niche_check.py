#!/usr/bin/env python3
"""YouTube niche checker: is a niche OPEN or CROWDED right now? ($0, no API key)

Rule of thumb (r/YT_Faceless, pandich93/youtube-niche-finder):
  OPEN    = >=3 channels younger than 4 months with 1k+ subscribers and a recent median >=10k views.
  CROWDED = this week's uploads are mostly near zero views and several young channels keep uploading.

Per niche: each search phrase is read twice from public YouTube search pages:
  A) this month, sorted by views   (what works)
  B) this week, sorted by upload date (who is uploading right now)
Then every channel found: /about page (join date, subscribers);
for young channels (<= MAX_AGE_DAYS): last 15 uploads via yt-dlp (median views).

Usage: python3 niche_check.py OUT_DIR niches.json
niches.json: {"niche name": ["search phrase 1", "search phrase 2"], ...}
Optional env: GL=FR (search country; interface stays English so dates parse).
Personal research only. Reads public pages; keep it small and slow; respect YouTube's terms.
"""
import json, os, re, statistics, subprocess, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

TODAY = date.today()
MAX_AGE_DAYS = 120
SP_MONTH_VIEWS = "CAMSBAgEEAE%3D"   # sort=views, date=month, type=video
SP_WEEK_NEW = "CAISBAgDEAE%3D"      # sort=upload date, date=week, type=video
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/130 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            err = e
            time.sleep(2 + 3 * i)
    sys.stderr.write(f"FAIL {url}: {err}\n")
    return ""


def initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    return json.loads(m.group(1)) if m else {}


def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            else:
                yield from walk(v, key)
    elif isinstance(o, list):
        for x in o:
            yield from walk(x, key)


def num(s):
    if not s:
        return 0
    s = s.replace(",", "").strip()
    m = re.match(r"([\d.]+)\s*([KMB]?)", s)
    if not m:
        return 0
    return int(float(m.group(1)) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)])


def age_days(txt):
    """'3 days ago' / '2w ago' / 'Streamed 5 hours ago' -> days (float)."""
    if not txt:
        return None
    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year|s|m|h|d|w|mo|y)\b", txt.replace("ago", ""))
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    mult = {"second": 1/86400, "s": 1/86400, "minute": 1/1440, "m": 1/1440, "hour": 1/24, "h": 1/24,
            "day": 1, "d": 1, "week": 7, "w": 7, "month": 30, "mo": 30, "year": 365, "y": 365}[u]
    return n * mult


def text(o):
    if not o:
        return ""
    if "simpleText" in o:
        return o["simpleText"]
    return "".join(r.get("text", "") for r in o.get("runs", []))


GL = os.environ.get("GL", "")  # search country, e.g. FR, DE; interface stays English so dates parse


def search(q, sp):
    html = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q) + "&sp=" + sp
               + (f"&gl={GL}&hl=en" if GL else ""))
    out = []
    for v in walk(initial_data(html), "videoRenderer"):
        owner = (v.get("ownerText") or {}).get("runs") or [{}]
        cid = (((owner[0].get("navigationEndpoint") or {}).get("browseEndpoint")) or {}).get("browseId")
        dur = text(v.get("lengthText"))
        secs = 0
        for p in dur.split(":"):
            secs = secs * 60 + (int(p) if p.isdigit() else 0)
        out.append({"id": v.get("videoId"), "title": text(v.get("title")), "channel": owner[0].get("text"),
                    "channel_id": cid, "views": num(text(v.get("viewCountText"))),
                    "age_d": age_days(text(v.get("publishedTimeText"))), "dur": secs})
    return out


def about(cid):
    html = get(f"https://www.youtube.com/channel/{cid}/about")
    m = re.search(r'"joinedDateText":\{"content":"Joined ([A-Za-z]{3} \d{1,2}, \d{4})"', html)
    joined = datetime.strptime(m.group(1), "%b %d, %Y").date() if m else None
    s = re.search(r'"subscriberCountText":"([\d.,]+[KMB]?) subscriber', html)
    vc = re.search(r'"videoCountText":"([\d,]+) video', html)
    return {"channel_id": cid, "joined": joined.isoformat() if joined else None,
            "age_days": (TODAY - joined).days if joined else None,
            "subs": num(s.group(1)) if s else 0, "videos": num(vc.group(1)) if vc else None}


def recent_median(cid):
    """Median views of the newest uploads (videos tab, else shorts tab)."""
    for tab in ("videos", "shorts"):
        r = subprocess.run(["uvx", "yt-dlp", "--flat-playlist", "--ignore-errors", "--playlist-end", "15",
                            "-J", f"https://www.youtube.com/channel/{cid}/{tab}"],
                           capture_output=True, text=True, timeout=180)
        try:
            ents = json.loads(r.stdout).get("entries") or []
        except Exception:
            ents = []
        v = [e.get("view_count") or 0 for e in ents]
        if v:
            return {"tab": tab, "n": len(v), "median": int(statistics.median(v))}
    return {"tab": None, "n": 0, "median": 0}


def main():
    out, cfg = sys.argv[1], json.load(open(sys.argv[2]))
    os.makedirs(out, exist_ok=True)
    jobs = [(n, q, kind, sp) for n, qs in cfg.items() for q in qs
            for kind, sp in (("month_views", SP_MONTH_VIEWS), ("week_new", SP_WEEK_NEW))]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda j: (j, search(j[1], j[3])), jobs))
    vids = []
    for (n, q, kind, _), rows in res:
        for r in rows:
            vids.append({**r, "niche": n, "q": q, "kind": kind})
    json.dump(vids, open(f"{out}/videos.json", "w"), ensure_ascii=False, indent=1)
    cids = sorted({v["channel_id"] for v in vids if v["channel_id"]})
    print("videos", len(vids), "channels", len(cids), flush=True)
    with ThreadPoolExecutor(8) as ex:
        chans = {c["channel_id"]: c for c in ex.map(about, cids)}
    young = [c for c in chans.values() if c["age_days"] is not None and c["age_days"] <= MAX_AGE_DAYS]
    print("young channels", len(young), flush=True)
    with ThreadPoolExecutor(6) as ex:
        for c, m in zip(young, ex.map(lambda c: recent_median(c["channel_id"]), young)):
            c["recent"] = m
    json.dump(chans, open(f"{out}/channels.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
