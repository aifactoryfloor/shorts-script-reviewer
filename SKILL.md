---
name: youtube-niche-checker
description: "Check if a YouTube niche is open or crowded, $0."
when_to_use: "Use before you start a new YouTube channel or series and want to know if new channels are breaking through in a niche right now, or if it is crowded with tiny channels making the same video. Triggers: check my niche, is this niche saturated, is this niche crowded, find a niche, should I start a channel about X."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [youtube, niche, research, faceless, new-channel]
    related_skills: []
---

# YouTube Niche Checker

From the AI Factory Floor experiment "a new channel from zero". Free, no API key, no paid tools.

Top videos tell you what worked. This week's uploads tell you what's waiting for you.

## When to Use

- You are about to pick a niche or format for a new channel.
- An AI (or a guru) just told you "this niche is hot" and you want to check it before you make a single video.

## Requirements

- Python 3.9+ and `uv` (the script runs `uvx yt-dlp` to read channel uploads). No pip installs, no API key.
- About 1-2 minutes for 3 niches. Keep runs small: it reads public YouTube pages.

## Steps

1. Write `niches.json`: each niche gets 2 search phrases a viewer would type (English, plain words).
   See `examples/niches.json`.
2. Run the scan:
   `python3 scripts/niche_check.py out niches.json`
3. Build the report:
   `python3 scripts/niche_report.py out > report.md`
4. Read the verdicts:
   - **OPEN** - at least 3 channels younger than 4 months already have 1k+ subscribers and a recent median of 10k+ views.
   - **OPEN (but many tiny uploaders)** - winners exist, but most of this week's uploads sit under 100 views.
   - **BORDERLINE** - 1-2 young winners. Not enough to call it.
   - **CLOSED** - only old channels grow. New ones are not breaking through.
   - **CROWDED** - most of this week's uploads are under 100 views, and several young channels keep uploading.
5. **Open every young winner by hand.** This is the step the script cannot do. Check:
   - Is it really your niche? (A "survive" map search once returned 5 zombie-story channels out of 6.)
   - Is it really the language you think? (YouTube auto-translates titles; English channels showed up as French and German winners.)
   - Is it one lucky video or a steady channel? Look at the last 10 uploads.
   Drop the wrong ones with `EXCLUDE_IDS="UC...,UC..." python3 scripts/niche_report.py out`.
6. Pick a niche only after step 5. Then look at what the winners do NOT cover yet.

## Options

- `GL=FR` / `GL=DE` - search as a viewer from that country.
- `LANG_FILTER=fr|de` - winners must title their videos in that language.
- `ALLOW_NONLATIN=1` - keep channels with non-Latin titles (skipped by default).

## Pitfalls

- It is a screening rule, not a census. One search page is a sample.
- Search shows demand, not the recommendation feed. Shock and story formats can grow from recommendations with weak search numbers.
- A big "top of month" median means the topic works for someone. It does not mean it works for a new channel.
- The thresholds (120 days, 1k subs, 10k median, 60% under 100 views) are starting points. Change them in the scripts if your niche is smaller.

## Verification

The report lists every young winner with a link. If you did not open them, you did not finish the check.
