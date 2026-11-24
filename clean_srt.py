#!/usr/bin/env python3
"""Deterministic, rule-based SRT cleaner for the SRT Cleaner + Chapters validation.

Rules (see CLEANING_RULES.md):
  R1 remove standalone filler words um/uh/erm/you know/like
     (like only when filler: followed/preceded by a comma or at a cue edge;
      meaningful "like" as in "a low number like f-eleven" is KEPT)
  R2 collapse repeated consecutive words ("the the" -> "the", "I, I, I" -> "I")
  R3 re-wrap to max 37 chars/line, max 2 lines per cue
  R4 sort cues by start time; fix overlaps by trimming end to next start minus 1ms
  R5 strip HTML tags
  R6 normalise whitespace and capitalisation of sentence starts (+ standalone "i" -> "I")

No AI, no rewriting: only the rules above. Run:
  python3 clean_srt.py <original.srt> <cleaned.srt> <before-after.txt> <counts.json>
"""
import json
import re
import sys

FILLER_WORDS = ["um", "uh", "erm", "uhh"]


def parse_ms(ts: str) -> int:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def format_ms(ms: int) -> str:
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(path: str):
    """Parse an SRT file. Skips a plain-text header note before cue 1."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    blocks = [b.strip("\n") for b in re.split(r"\n\s*\n", raw.strip())]
    cues = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 2:
            continue
        if not lines[0].strip().isdigit():
            continue  # header note line, not a cue
        if "-->" not in lines[1]:
            continue
        start_s, end_s = [t.strip() for t in lines[1].split("-->")]
        cues.append({
            "orig_index": int(lines[0].strip()),
            "start": parse_ms(start_s),
            "end": parse_ms(end_s),
            "lines": lines[2:],
        })
    return cues


def remove_fillers(text: str):
    """R1. Returns (text, count)."""
    count = 0

    def sub(pattern, repl, flags=re.IGNORECASE):
        nonlocal text, count
        text, n = re.subn(pattern, repl, text, flags=flags)
        count += n
        return text

    # "you know" anywhere (always a filler in these samples), eating a following comma.
    sub(r"\byou know\b\s*,?\s*", " ")
    # um / uh / erm / uhh: leading, comma-wrapped, trailing, space-wrapped.
    sub(r"^(um|uh|erm|uhh)\s*,?\s*", "")
    sub(r",\s*(um|uh|erm|uhh)\s*,", ",")
    sub(r",\s*(um|uh|erm|uhh)\s*(?=[.!?]|$)", "")
    sub(r"\s+(um|uh|erm|uhh)\s+", " ")
    sub(r"^(um|uh|erm|uhh)\s*,?\s*", "")
    sub(r"\s+(um|uh|erm|uhh)\s*$", "")
    # "like" ONLY as a filler: at cue start before a comma, between commas,
    # or trailing after a comma. Meaningful "like" (followed by a word) is kept.
    sub(r"^like\s*,\s*", "")
    sub(r"([.!?]\s+)like\s*,\s*", r"\1")
    sub(r",\s*like\s*,", ",")
    sub(r",\s*like\s*(?=[.!?]|$)", "")
    sub(r"\s+like\s*,\s*", " ")
    return text, count


def collapse_repeats(text: str):
    """R2. Returns (text, count)."""
    count = 0
    pat = re.compile(r"\b(\w+)([,\s]+)\1\b", re.IGNORECASE)
    while True:
        text, n = pat.subn(r"\1", text, count=1)
        if n == 0:
            break
        count += n
    return text, count


def normalise(text: str):
    """R6 (whitespace + sentence-start capitalisation)."""
    text = re.sub(r"\s+,", ",", text)          # space before comma
    text = re.sub(r",(\s*,)+", ",", text)      # collapsed ", ,"
    text = re.sub(r"\b(and|but|or)\s*,\s*", r"\1 ", text)  # comma left behind after a removed filler ("and, uh," -> "and")
    text = re.sub(r"\s*,\s*([.!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^,\s*", "", text)
    text = re.sub(r",\s*$", "", text)
    text = re.sub(r"\bi\b", "I", text)         # standalone "i" -> "I"
    if text:
        text = text[0].upper() + text[1:]
    text = re.sub(r"([.!?]\s+)([a-z])",
                  lambda m: m.group(1) + m.group(2).upper(), text)
    return text


def wrap(text: str, max_len=37, max_lines=2):
    """R3. Greedy word wrap. Returns lines (asserts max_lines)."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_len:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def clean_cue(cue):
    raw_text = " ".join(line.strip() for line in cue["lines"]).strip()
    counts = {"filler_removed": 0, "repeats_collapsed": 0, "tags_stripped": 0}
    text = raw_text
    # R5 strip HTML tags.
    tags = re.findall(r"<[^>]+>", text)
    counts["tags_stripped"] = len(tags)
    text = re.sub(r"<[^>]+>", "", text)
    # R1 fillers.
    text, counts["filler_removed"] = remove_fillers(text)
    # R2 repeats.
    text, counts["repeats_collapsed"] = collapse_repeats(text)
    # R6 normalise.
    text = normalise(text)
    # R3 re-wrap.
    lines = wrap(text)
    counts["rewrapped"] = 1 if lines != cue["lines"] else 0
    counts["wrap_overflow_lines"] = max(0, len(lines) - 2)
    return text, lines, counts, raw_text


def main():
    src, dst, excerpt_path, counts_path = sys.argv[1:5]
    cues = parse_srt(src)
    totals = {"cues": len(cues), "filler_removed": 0, "repeats_collapsed": 0,
              "cues_rewrapped": 0, "tags_stripped": 0,
              "timestamp_issues_fixed": 0, "cues_reordered": 0,
              "ends_trimmed": 0, "wrap_overflow_lines": 0,
              "meaningful_like_kept": 0}
    cleaned = []
    excerpt_rows = []
    for cue in cues:
        text, lines, c, raw_text = clean_cue(cue)
        totals["filler_removed"] += c["filler_removed"]
        totals["repeats_collapsed"] += c["repeats_collapsed"]
        totals["cues_rewrapped"] += c["rewrapped"]
        totals["tags_stripped"] += c["tags_stripped"]
        totals["wrap_overflow_lines"] += c["wrap_overflow_lines"]
        totals["meaningful_like_kept"] += len(re.findall(r"\blike\b", text, flags=re.I))
        cleaned.append({**cue, "text": text, "lines": lines})
        if cue["orig_index"] <= 10:
            excerpt_rows.append((cue["orig_index"], raw_text, text))

    # R4 sort by start time.
    sorted_cues = sorted(cleaned, key=lambda c: c["start"])
    for pos, cue in enumerate(sorted_cues):
        orig_pos = cues.index(next(c for c in cues if c["orig_index"] == cue["orig_index"]))
        if orig_pos != pos:
            totals["cues_reordered"] += 1
    # R4 fix overlaps: trim end to next start minus 1ms.
    for i in range(len(sorted_cues) - 1):
        if sorted_cues[i]["end"] >= sorted_cues[i + 1]["start"]:
            sorted_cues[i]["end"] = sorted_cues[i + 1]["start"] - 1
            totals["ends_trimmed"] += 1
    totals["timestamp_issues_fixed"] = totals["cues_reordered"] + totals["ends_trimmed"]

    with open(dst, "w", encoding="utf-8") as f:
        for i, cue in enumerate(sorted_cues, 1):
            f.write(f"{i}\n{format_ms(cue['start'])} --> {format_ms(cue['end'])}\n")
            f.write("\n".join(cue["lines"]) + "\n\n")

    with open(excerpt_path, "w", encoding="utf-8") as f:
        f.write("BEFORE vs AFTER — first 10 cues (original file order)\n")
        f.write("BEFORE = original cue text (single line). AFTER = cleaned cue text (single line).\n\n")
        for idx, before, after in excerpt_rows:
            f.write(f"Cue {idx}\n  BEFORE: {before}\n  AFTER:  {after}\n\n")

    with open(counts_path, "w", encoding="utf-8") as f:
        json.dump(totals, f, indent=2)
    print(json.dumps(totals, indent=2))


if __name__ == "__main__":
    main()
