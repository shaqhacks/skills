#!/usr/bin/env python3
"""Safely write a pool of fact strings into Claude Code's spinnerVerbs setting.

The CLI renders the bright, shimmering spinner word (the "Discombobulating…"
element) from the `spinnerVerbs` key, shape
`{"mode": "append"|"replace", "verbs": [...]}`. Putting facts there makes them
glow with the `claudeShimmer` animation. This skill only ever writes that key —
it deliberately leaves the dim "Tip:" line at Claude Code's defaults.

Why this is a script and not inline edits: settings.json holds the user's whole
Claude Code configuration. A naive write could clobber unrelated keys or corrupt
the file. This reads the existing JSON, changes ONLY the spinnerVerbs key, writes
a .bak first, and refuses to proceed if the existing file isn't parseable — so a
malformed settings file fails loudly instead of being silently destroyed.

Usage:
  apply_spinner_facts.py --facts-file facts.json [options]

Options:
  --settings PATH     Target settings file (default: ~/.claude/settings.json)
  --facts-file PATH   JSON array of fact strings to install (required unless --stdin)
  --stdin             Read the JSON array of facts from stdin instead of a file
  --mode MODE         'replace' (default) shows only your facts as the spinner
                      word; 'append' mixes them with Claude Code's built-in verbs
  --max-len N         Drop any fact longer than N chars (default: 36). The verb
                      shares its line with the live status text (time + token
                      count), so on an 80-column terminal facts over ~36 chars get
                      clipped — keep them short.
  --dry-run           Print what would be written without modifying the file

Exit codes: 0 ok, 1 usage/IO error, 2 existing settings unparseable (no write).
"""
import argparse
import json
import os
import shutil
import sys


def load_facts(args):
    raw = sys.stdin.read() if args.stdin else open(args.facts_file, encoding="utf-8").read()
    data = json.loads(raw)
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise ValueError("facts must be a JSON array of strings")
    return data


def clean(facts, max_len):
    """Normalize whitespace, drop empties/dupes/over-length, preserve order."""
    seen, out, dropped = set(), [], []
    for f in facts:
        t = " ".join(f.split())  # collapse internal whitespace/newlines
        if not t:
            continue
        if len(t) > max_len:
            dropped.append(t)
            continue
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
    return out, dropped


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--settings", default=os.path.expanduser("~/.claude/settings.json"))
    p.add_argument("--facts-file")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--mode", choices=["replace", "append"], default="replace")
    p.add_argument("--max-len", type=int, default=36)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.facts_file and not args.stdin:
        p.error("provide --facts-file or --stdin")

    try:
        facts = load_facts(args)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR reading facts: {e}", file=sys.stderr)
        return 1

    facts, dropped = clean(facts, args.max_len)
    if not facts:
        print("ERROR: no valid facts after cleaning", file=sys.stderr)
        return 1

    # Read existing settings. A parse failure must NOT lead to a write.
    path = os.path.expanduser(args.settings)
    settings = {}
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, encoding="utf-8") as f:
                settings = json.load(f)
            if not isinstance(settings, dict):
                raise ValueError("settings root is not a JSON object")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"ERROR: {path} is not valid JSON ({e}). Refusing to overwrite. "
                  f"Fix or remove it, then re-run.", file=sys.stderr)
            return 2

    # The CLI handles append/replace against its built-in verbs natively, so just
    # hand it {mode, verbs}. We touch ONLY spinnerVerbs — the dim Tip: line is
    # left at the user's existing/default configuration on purpose.
    settings["spinnerVerbs"] = {"mode": args.mode, "verbs": facts}
    rendered = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(rendered)
        print(f"[dry-run] {len(facts)} verbs (mode={args.mode}), "
              f"dropped {len(dropped)} over-length", file=sys.stderr)
        return 0

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Wrote {len(facts)} glowing spinner facts to {path} "
          f"via spinnerVerbs (mode={args.mode}).")
    if os.path.exists(path + ".bak"):
        print(f"Previous settings backed up to {path}.bak")
    if dropped:
        print(f"Skipped {len(dropped)} fact(s) longer than {args.max_len} chars "
              f"(would be clipped on the spinner line).")
    print("Takes effect in a NEW Claude Code session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
