# CleanSRT — free SRT cleaner (demo script)

Clean the SRT you already have, then export a clean SRT + a `chapters.txt`
for your video description. No AI rewriting, no upload, no account:
a single deterministic Python script that runs offline on your own machine.

```bash
python3 clean_srt.py messy.srt clean.srt before-after.txt counts.json
```

## What it does

| Rule | Detail |
|---|---|
| Fillers removed | Standalone `um`, `uh`, `erm`, `you know`, filler `like` |
| Repeats collapsed | `the the` → `the`, `I, I, I` → `I` |
| Re-wrapped | Max 37 chars / line, max 2 lines per cue (Premiere rule) |
| Timestamps fixed | Cues sorted by start time; overlaps trimmed to next start − 1 ms |
| HTML stripped | `<font>`, `<b>` and friends removed |
| Tidied | Whitespace normalised, sentence starts capitalised |

Timestamps are never changed except for overlap trimming. Meaningful
`like` is kept (e.g. "a low number like f-eleven").

## Try it on the samples

```bash
python3 clean_srt.py samples/01-podcast-small-business_original.srt out.srt out-ba.txt out-counts.json
diff out.srt samples/01-podcast-small-business_cleaned.srt   # no output = identical
```

Across the three samples (58 cues): 124 filler words removed, 9 repeats
collapsed, 58 cues re-wrapped, 13 timestamp issues fixed, 12 HTML tags
stripped. `samples/` also has the matching `chapters.txt` for each file
(`00:00 Title` format, ready to paste into a YouTube description).

> The three sample transcripts are synthetic files written for this demo,
> not any real creator's transcript. The counts above are real counts from
> running this script on them.

## The full desktop tool (pre-sale)

This script is the free core. The full offline desktop app — batch
cleaning, chapter export, and a GUI instead of the command line — is in
pre-sale: **$19 early-bird** (regular $39), full refund if it never ships.

👉 https://lzhorizon4.gumroad.com/l/rsmqd

## Files

- `clean_srt.py` — the cleaner (Python 3, standard library only)
- `CLEANING_RULES.md` — the six rules, exactly, with counting definitions
- `samples/` — 3 messy originals, their cleaned outputs, and chapters

## License

MIT — see `LICENSE`.
