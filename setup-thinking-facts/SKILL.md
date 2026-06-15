---
name: setup-thinking-facts
description: >-
  Replace Claude Code's whimsical "thinking" spinner words (Discombobulating…,
  Frolicking…) with interesting, true one-sentence facts from subjects the user
  picks — history, biology, math, astronomy, science, art, anything. Use this
  whenever the user wants to customize, change, or personalize what shows while
  Claude is thinking/working, wants trivia or facts on the spinner, wants to
  learn something while they wait, or says things like "change the thinking
  words," "show me facts while you think," "replace the spinner text," or "I want
  history facts when you're working." It gathers fresh facts for the chosen
  subjects and writes them into the spinnerTips setting safely. This is a
  one-time SETUP task, not an ongoing behavior — run it, and the facts then show
  on their own in every new session.
---

# Setup Thinking Facts

## What this does and why it works this way

Claude Code draws those playful gerunds ("Ruminating…", "Discombobulating…")
next to the spinner while it works. The CLI reads the candidate strings from a
setting called **`spinnerTips`** in `~/.claude/settings.json` and rotates
through them randomly. So the way to show facts while Claude thinks is not a
running program or a hook — there is no hook that fires during thinking — it is
simply to fill `spinnerTips` with good facts. That is what this skill does.

Because the spinner reads a fixed list from the config, the facts are gathered
**once at setup** (fresh from the web) and stored. To refresh them later, the
user just runs this skill again. Each tip must be short — roughly one sentence —
because anything wider than the terminal line gets cut off.

The setting shape (verified against the installed CLI):

```json
{
  "spinnerTips": {
    "tips": ["fact one", "fact two", "..."],
    "excludeDefault": true
  }
}
```

`excludeDefault: true` shows only the user's facts; `false` mixes them with the
built-in gerunds. Default to `true` — the user is here to replace the gerunds
with facts, so honor that unless they say they want to keep the originals too.

## The workflow

### 1. Get the subjects and the fact length

This is a real conversation — ask, then wait for the answer. Two things to
settle before gathering anything:

**Subjects.** If the user already named subjects ("history and astronomy"), use
those and don't re-ask. If they didn't, present a menu and let them pick — a
numbered list is easiest to answer:

> Which subjects would you like facts from? Pick any number of these, or name
> your own:
> 1. History   2. Astronomy/Space   3. Biology   4. Math
> 5. Physics   6. Chemistry   7. Geography   8. Art
> 9. Technology   10. Language/Words

**Fact length.** Ask whether they want them **short or in-depth** — people differ
on this and it changes how the facts read:

> And do you want short one-line facts, or longer in-depth ones?

- **Short** — a single tight sentence (~120 characters). Fits the spinner line
  cleanly. This is the safe default if they don't care.
- **In-depth** — two or three sentences (up to ~280 characters) with a bit more
  explanation. Worth flagging honestly: the spinner is a *one-line* element, so
  longer facts may wrap or get clipped depending on terminal width. Offer it,
  but tell them they may want to see how it looks and can re-run for short if
  it's too cramped.

One default worth keeping silent: replace the gerunds entirely
(`excludeDefault: true`) unless they say they want to keep the originals mixed
in. Don't interrogate them on it.

### 2. Gather the facts — fresh, true, and tight

This is the part that makes the result good or bad, so spend your effort here.
For each subject, pull genuinely interesting facts. **Prefer the web**
(WebSearch / WebFetch) so they're fresh and sourced rather than the same dozen
facts everyone has seen; if web tools are unavailable, fall back to your own
knowledge, but stay strictly to things you are confident are true.

**Gather a generous pool — roughly 20–30 per subject.** The pool is what the
spinner rotates through, and the user asked for it not to feel like a tiny
static list, so err on the side of more. There's no live re-fetching: the
spinner reads this fixed pool, and the user refreshes it by re-running this
skill. A big, varied pool is what keeps it from going stale.

Hold every fact to this bar:

- **True and not a myth.** This is the whole game — a spinner full of
  confidently-stated falsehoods is worse than the gerunds. Actively avoid the
  popular ones that are wrong (the Great Wall is *not* visible from space with
  the naked eye; we use far more than 10% of our brains; glass is *not* a slow
  liquid). When unsure, drop it rather than ship a maybe.
- **The right length for their choice.** Short mode: a single sentence, ~120
  characters. In-depth mode: two or three sentences, up to ~280 characters,
  using the extra room to explain *why* the fact is interesting, not to pad.
  Either way, tighten "It is a little-known fact that…" down to the fact itself.
- **Self-contained and surprising.** It should land without setup and make the
  user think "huh, neat." Concrete numbers and specifics beat vague claims.
- **Varied within a subject.** Don't give twenty facts about the same battle or
  the same animal. Spread across the subject.
- **Clean.** Safe-for-work, non-political, non-gory. This shows up constantly
  while they work; keep it delightful, not jarring.

Write the assembled pool to a JSON file as a flat array of strings. **Use a
unique filename** — never a fixed shared path like `/tmp/thinking-facts.json`,
because two runs (or a re-run) would overwrite each other's facts mid-flight.
Generate a unique name, e.g. with `mktemp`:

```bash
FACTS=$(mktemp -t thinking-facts.XXXXXX) ; echo "$FACTS"
# then write the JSON array to "$FACTS"
```

```json
["Honey found in 3,000-year-old Egyptian tombs was still edible.",
 "A day on Venus is longer than its year.",
 "The '+' and '=' keys share a key because Robert Recorde invented '=' in 1557."]
```

(If you'd rather not create a file at all, the script also accepts the array on
stdin via `--stdin`, which sidesteps the collision entirely.)

### 3. Write it into the setting with the bundled script

Do **not** hand-edit `settings.json` — it holds the user's whole configuration
and a slip could corrupt it. Use the bundled script, which backs up the file,
changes only the `spinnerTips` key, and refuses to write if the existing file is
unparseable:

```bash
python3 <skill-dir>/scripts/apply_spinner_tips.py \
  --facts-file "$FACTS" \
  --exclude-default true \
  --max-len 140         # use 300 for in-depth mode so longer facts aren't dropped
```

Set `--max-len` to match the chosen length: ~140 for short, ~300 for in-depth
(otherwise the script will skip the longer in-depth facts as too long). Other
flags: `--settings PATH` (default `~/.claude/settings.json`), `--mode append` to
add to an existing pool instead of replacing it, `--stdin` to pipe the facts
instead of a file, `--dry-run` to preview. The script cleans whitespace, drops
blanks/duplicates, and skips anything over the limit, then reports how many tips
it installed.

### 4. Confirm and tell them what to expect

Report back plainly:
- which subjects and which length (short / in-depth) you set up — **do not state
  a fact count.** The user doesn't need a number, and a finite "42 facts" reads
  as a small fixed list when the intent is an open-ended, refreshable set. The
  script prints a count to its own output; that's for you, not for the reply.
- that it takes effect **in a new session** (the spinner list is read at
  startup), so they should start a fresh `claude` to see it,
- that there's no live re-fetch — to pull a brand-new batch later, just **re-run
  this skill**; the big pool keeps the rotation from feeling repetitive in the
  meantime,
- if they chose in-depth: that longer facts may wrap or clip on a narrow
  terminal, and they can re-run for short if it looks cramped,
- that the previous settings were backed up to `settings.json.bak`,
- how to undo it: remove the `spinnerTips` block from `~/.claude/settings.json`
  (or restore the `.bak`).

Show them three or four sample facts from the pool so they get a taste of what
they'll see.

## Quality checklist

- If the user didn't name subjects, did I show the menu and let them pick?
- Did I ask short vs. in-depth (and match the fact length + `--max-len` to it)?
- Did I gather a generous pool (~20–30 per subject) so it doesn't feel static?
- Are all facts things I'm confident are TRUE — no popular myths?
- Did I write facts to a UNIQUE filename (never a fixed shared path)?
- Are they varied and genuinely interesting, not the tired greatest-hits?
- Did I write through the script (with its backup), never by hand-editing JSON?
- Did I tell them it takes effect in a new session, how to refresh, and how to
  revert?
