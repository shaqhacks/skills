#!/usr/bin/env python3
"""Weekly rotation for facts-spinner.

Picks a fresh slice of the 500-fact bank and installs it on the spinner Tip line.
Meant to be run once a week by cron. The selection is deterministic per ISO week:
it changes every week but stays stable within a week (and across reruns), so the
spinner feels refreshed without needing the model or any network call.

It reuses apply_spinner_tips.py to do the actual settings write (backup + safety).
"""
import datetime
import json
import os
import random
import subprocess
import sys
import tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(SKILL, "data", "facts-bank.json")
APPLY = os.path.join(SKILL, "scripts", "apply_spinner_tips.py")
WINDOW = 150  # how many facts to show each week (the spinner rotates within these)


def main():
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)

    iso = datetime.date.today().isocalendar()
    seed = iso[0] * 100 + iso[1]  # stable within an ISO week, advances weekly
    rng = random.Random(seed)
    k = min(WINDOW, len(bank))
    week_slice = rng.sample(bank, k)

    fd, tmp = tempfile.mkstemp(prefix="facts-week-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(week_slice, f, ensure_ascii=False)
    try:
        subprocess.run(
            [sys.executable, APPLY, "--facts-file", tmp,
             "--max-len", "300", "--exclude-default", "true"],
            check=True,
        )
    finally:
        os.remove(tmp)

    print(f"facts-spinner: installed {k} of {len(bank)} facts for "
          f"ISO week {iso[0]}-W{iso[1]:02d} (seed {seed}).")


if __name__ == "__main__":
    main()
