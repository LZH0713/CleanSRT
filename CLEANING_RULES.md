# Cleaning rules — SRT Cleaner + Chapters validation

Deterministic, rule-based cleaning only. No AI rewriting, no rewording, no
summarising. The cleaner is `clean_srt.py` in this folder; run it with:

```
python3 clean_srt.py <original.srt> <cleaned.srt> <before-after.txt> <counts.json>
```

## R1 — Remove standalone filler words
Remove `um`, `uh`, `erm`/`uhh`, the phrase `you know`, and `like` **only when
it is a standalone filler**: at the start of a cue before a comma, between
commas, or trailing after a comma. `like` inside a meaningful phrase is
**kept** — e.g. "a low number like f-one-point-eight" and "fixed costs like
rent" survive (2 kept in file 02, 2 kept in file 03). `so` is not in the R1
list, so no standalone `so` filler was used in the samples.

## R2 — Collapse repeated consecutive words
`the, the` -> `the`; `I, I, I` -> `I`; `really, really` -> `really`;
`check, check` -> `check`. Matching is case-insensitive and works across a
comma or a space. Each single collapse counts as 1.

## R3 — Re-wrap to the Premiere rule
Greedy word wrap: max **37 characters per line**, max **2 lines per cue**.
"Cues re-wrapped" counts cues whose line layout changed vs the original.
No cue overflowed 2 lines after cleaning (wrap_overflow_lines = 0 in all
three files). No words are dropped to fit; samples were written so cleaned
cues fit within 2 x 37 chars.

## R4 — Fix timestamps
Sort cues by start time, then fix overlaps by trimming the earlier cue's
end time to the next cue's start minus 1 ms. "Timestamp issues fixed" =
cues reordered by the sort + cue ends trimmed. No start times are changed.

## R5 — Strip HTML tags
Remove all `<...>` tags (`<font ...>`, `</font>`, `<b>`, `</b>`). "Tags
stripped" counts opening + closing tags separately (each file has 2 tags
with open + close = 4).

## R6 — Normalise whitespace and capitalisation
Collapse multiple spaces, drop spaces before commas, collapse `, ,` to `,`,
drop a comma left behind after a removed filler (`and, uh,` -> `and`),
capitalise the first letter of each cue, capitalise after `.`/`!`/`?`, and
turn standalone `i` into `I`. Proper-noun capitalisation is NOT fixed
(out of scope for R6).

## Counting definitions
- filler_removed: each matched filler token/phrase (R1).
- repeats_collapsed: each single collapse step (R2).
- cues_rewrapped: cues whose line layout changed (R3).
- timestamp_issues_fixed: reordered cues + trimmed ends (R4).
- tags_stripped: each `<...>` tag removed (R5).
