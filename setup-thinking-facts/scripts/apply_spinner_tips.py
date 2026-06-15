#!/usr/bin/env python3
"""Safely merge a pool of fact strings into Claude Code's spinner-tips setting.

The CLI reads custom spinner tips from the `spinnerTipsOverride` key (shape:
{"tips": [...], "excludeDefault": bool}) and gates the whole feature behind the
`spinnerTipsEnabled` master toggle. This script writes BOTH: it fills
spinnerTipsOverride with the facts and sets spinnerTipsEnabled:true so the tips
actually appear. (An earlier version wrote a key named `spinnerTips`, which the
CLI does not read — so the facts never showed. This script also removes that
dead legacy key when it finds it.)

Why this is a script and not inline edits: settings.json holds the user's whole
Claude Code configuration. A naive write could clobber unrelated keys or corrupt
the file. This reads the existing JSON, changes ONLY the spinner-tip keys, writes
a .bak first, and refuses to proceed if the existing file isn't parseable —
so a malformed settings file fails loudly instead of being silently destroyed.

Usage:
  apply_spinner_tips.py --facts-file facts.json [options]

Options:
  --settings PATH     Target settings file (default: ~/.claude/settings.json)
  --facts-file PATH   JSON array of fact strings to install (required unless --stdin)
  --stdin             Read the JSON array of facts from stdin instead of a file
  --mode MODE         'replace' (default) overwrites the tip pool; 'append' adds
                      to whatever tips are already configured (deduped)
  --exclude-default BOOL  'true' (default) shows ONLY your facts; 'false' mixes
                          them with Claude Code's built-in spinner gerunds
  --max-len N         Drop/flag any fact longer than N chars (default: 160) so
                      tips fit the spinner line instead of being truncated
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
    p.add_argument("--target", choices=["tips", "verbs"], default="tips",
                   help="'tips' = the dim Tip: line (spinnerTipsOverride); "
                        "'verbs' = the bright glowing spinner word (spinnerVerbs)")
    p.add_argument("--exclude-default", default="true")
    p.add_argument("--max-len", type=int, default=160)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.facts_file and not args.stdin:
        p.error("provide --facts-file or --stdin")
    exclude_default = str(args.exclude_default).strip().lower() in ("1", "true", "yes")

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

    if args.target == "verbs":
        # The bright, shimmering spinner word (the "Discombobulating…" element).
        # The CLI handles append/replace against its built-in verbs natively, so
        # just hand it {mode, verbs}. These share the spinner line with the
        # "(esc to interrupt)" hint, so keep them short (use a small --max-len).
        settings["spinnerVerbs"] = {"mode": args.mode, "verbs": facts}
        target_desc = f"spinnerVerbs (mode={args.mode})"
    else:
        if args.mode == "append":
            existing = []
            cur = settings.get("spinnerTipsOverride")
            if isinstance(cur, dict) and isinstance(cur.get("tips"), list):
                existing = [t for t in cur["tips"] if isinstance(t, str)]
            facts, _ = clean(existing + facts, args.max_len)
        # The CLI reads custom tips from spinnerTipsOverride and only shows them
        # when spinnerTipsEnabled is on, so write both. Drop the dead legacy
        # 'spinnerTips' key if a prior version left one behind.
        settings.pop("spinnerTips", None)
        settings["spinnerTipsOverride"] = {"tips": facts, "excludeDefault": exclude_default}
        settings["spinnerTipsEnabled"] = True
        target_desc = f"spinnerTipsOverride (excludeDefault={exclude_default}, spinnerTipsEnabled=true)"
    rendered = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(rendered)
        print(f"[dry-run] {len(facts)} entries -> {target_desc}, "
              f"dropped {len(dropped)} over-length", file=sys.stderr)
        return 0

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Wrote {len(facts)} entries to {path} via {target_desc}.")
    if os.path.exists(path + ".bak"):
        print(f"Previous settings backed up to {path}.bak")
    if dropped:
        print(f"Skipped {len(dropped)} fact(s) longer than {args.max_len} chars.")
    print("Takes effect in a NEW Claude Code session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
