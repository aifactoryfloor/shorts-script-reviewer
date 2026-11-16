#!/usr/bin/env python3
"""Verdict table OPEN / CROWDED from OUT_DIR/videos.json + channels.json (made by niche_check.py).
Usage: python3 niche_report.py OUT_DIR > report.md
Env: EXCLUDE_IDS="UCxxx,UCyyy" to drop channels you checked by hand (wrong audience/topic);
     LANG_FILTER=fr|de to require winners whose titles are in that language;
     ALLOW_NONLATIN=1 to keep channels with non-Latin titles.
"""
import json, os, re, statistics, sys
from collections import defaultdict

d = sys.argv[1]
vids = json.load(open(f"{d}/videos.json"))
chans = json.load(open(f"{d}/channels.json"))
MAXAGE = 120
EXCLUDE = {c.strip(): "excluded by hand" for c in os.environ.get("EXCLUDE_IDS", "").split(",") if c.strip()}
if os.environ.get("ALLOW_NONLATIN"):
    NONLATIN = re.compile(r"[\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\u0600-\u06FF\uAC00-\uD7AF]")
else:
  NONLATIN = re.compile(r"[^\x00-\u024F\u2000-\u206F\u20A0-\u20CF\u2100-\u214F\U0001F000-\U0001FFFF]")

LANG = os.environ.get("LANG_FILTER", "")  # fr / de: winners must title videos in this language
STOP = {
 "fr": r"\b(le|la|les|des|du|une|est|qui|pour|dans|avec|pas|sur|ce|au|aux|et|il|elle|ils)\b|[éèêàçùœ]",
 "de": r"\b(der|die|das|und|ist|nicht|ein|eine|mit|wie|warum|was|den|dem|für|auf|im|zu|von|sich)\b|[äöüß]",
}
EN = r"\b(the|of|and|is|how|why|what|you|this|in|to|with)\b"


def lang_ok(titles):
    t = " ".join(titles).lower()
    return len(re.findall(STOP[LANG], t)) > len(re.findall(EN, t))


def med(xs):
    return int(statistics.median(xs)) if xs else 0

by = defaultdict(list)
for v in vids:
    by[v["niche"]].append(v)

rows = []
for n, vs in by.items():
    mv = [v for v in vs if v["kind"] == "month_views"]
    wk = [v for v in vs if v["kind"] == "week_new" and v["age_d"] is not None and v["age_d"] >= 2]
    wk_views = [v["views"] for v in wk]
    wk_zero = sum(1 for x in wk_views if x < 100)
    cids = {v["channel_id"] for v in vs if v["channel_id"]}
    young, winners, newbies = [], [], 0
    for c in cids:
        ch = chans.get(c) or {}
        a = ch.get("age_days")
        if a is None or a > MAXAGE:
            continue
        young.append(ch)
        rm = (ch.get("recent") or {}).get("median", 0)
        titles = [v["title"] or "" for v in vs if v["channel_id"] == c]
        if c in EXCLUDE or any(NONLATIN.search(t) for t in titles):
            continue
        if LANG and not lang_ok(titles):
            continue
        if ch.get("subs", 0) >= 1000 and rm >= 10000:
            winners.append(ch)
    # young channels uploading this week
    wk_young = {v["channel_id"] for v in wk if ((chans.get(v["channel_id"]) or {}).get("age_days") or 9999) <= MAXAGE}
    mv_young_hits = [v for v in mv if ((chans.get(v["channel_id"]) or {}).get("age_days") or 9999) <= MAXAGE and v["views"] >= 10000]
    nw = len(winners)
    ok = [ch for ch in young if (ch.get("recent") or {}).get("median", 0) >= 1000]
    share_ok = len(ok) / len(young) if young else None
    zero_share = wk_zero / len(wk_views) if wk_views else None
    if nw >= 3 and zero_share is not None and zero_share >= 0.6:
        verdict = "OPEN (but many tiny uploaders)"
    elif nw >= 3:
        verdict = "OPEN"
    elif nw >= 1:
        verdict = "BORDERLINE"
    elif zero_share is not None and zero_share >= 0.6 and len(wk_young) >= 3:
        verdict = "CROWDED"
    else:
        verdict = "CLOSED (only old channels grow)"
    rows.append(dict(niche=n, verdict=verdict, month_med=med([v["views"] for v in mv]), n_month=len(mv),
                     wk_n=len(wk_views), wk_med=med(wk_views), zero_share=zero_share,
                     young=len(young), wk_young=len(wk_young), winners=winners, young_hits=mv_young_hits,
                     share_ok=share_ok))

order = {"OPEN": 0, "OPEN (but many tiny uploaders)": 0.5, "BORDERLINE": 1, "CLOSED (only old channels grow)": 2, "CROWDED": 3}
rows.sort(key=lambda r: (order[r["verdict"]], -len(r["winners"]), -r["month_med"]))

print(f"# Niche check: {d}\n")
print("Rule: OPEN = >=3 channels younger than 4 months with 1k+ subs and recent median >=10k views. "
      "CROWDED = >=60% of this week's uploads (2-7 days old) under 100 views and >=3 young channels uploading.\n")
print("| niche | verdict | young winners | median, top of month | this week: median / share <100 | young channels found (uploading this week) | young with median >=1k |")
print("|---|---|---|---|---|---|---|")
for r in rows:
    zs = f"{r['zero_share']*100:.0f}%" if r["zero_share"] is not None else "—"
    so = f"{r['share_ok']*100:.0f}%" if r["share_ok"] is not None else "—"
    print(f"| {r['niche']} | **{r['verdict']}** | {len(r['winners'])} | {r['month_med']:,} | {r['wk_med']:,} / {zs} (n={r['wk_n']}) | {r['young']} ({r['wk_young']}) | {so} |".replace(",", " "))

print("\nExcluded by hand: " + (", ".join(EXCLUDE) or "none") + ". Channels with non-Latin titles are skipped unless ALLOW_NONLATIN=1.")
print("\n## Young winners (channel <=120 days, 1k+ subs, median >=10k). OPEN EVERY ONE BEFORE YOU TRUST IT.\n")
print("| niche | channel | age, days | subscribers | recent median | tab |")
print("|---|---|---|---|---|---|")
for r in rows:
    for c in sorted(r["winners"], key=lambda c: -c["recent"]["median"]):
        name = next((v["channel"] for v in vids if v["channel_id"] == c["channel_id"]), c["channel_id"])
        print(f"| {r['niche']} | [{name}](https://www.youtube.com/channel/{c['channel_id']}) | {c['age_days']} | {c['subs']:,} | {c['recent']['median']:,} | {c['recent']['tab']} |".replace(",", " "))
