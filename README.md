# YouTube Niche Checker (free skill)

Is a YouTube niche open for a new channel, or crowded with tiny channels making the same video?
$0, no API key. From the AI Factory Floor video "a new channel from zero".

## Install
- **Claude Code:** `git clone https://github.com/abdullinaleksandr78-create/shorts-script-reviewer ~/.claude/skills/youtube-niche-checker`, then ask: "check my niche".
- **Hermes Agent:** `git clone https://github.com/abdullinaleksandr78-create/shorts-script-reviewer ~/.hermes/skills/youtube-niche-checker`.
- **No agent?** Code -> Download ZIP, then run the two commands below yourself.

## Run
```
python3 scripts/niche_check.py out examples/niches.json
python3 scripts/niche_report.py out > report.md
```
Needs Python 3.9+ and [uv](https://docs.astral.sh/uv/) (for `uvx yt-dlp`).

## Files
- `SKILL.md` - the rules: verdicts, the manual check, pitfalls.
- `scripts/niche_check.py` - reads public YouTube search and channel pages.
- `scripts/niche_report.py` - turns the scan into an OPEN / CROWDED table.
- `examples/niches.json` - sample input.

Personal research only. It reads public pages; keep runs small and respect YouTube's terms.

Looking for the Shorts Script Reviewer from the first video? It is in the `v1-shorts-script-reviewer` branch.

License: MIT.
