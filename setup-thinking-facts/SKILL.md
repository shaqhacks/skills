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
next to the spinner while it works. The CLI reads custom strings from a setting
called **`spinnerTipsOverride`** in `~/.claude/settings.json` and rotates through
them randomly, and it only shows tips at all when the master toggle
**`spinnerTipsEnabled`** is on. So the way to show facts while Claude thinks is
not a running program or a hook — there is no hook that fires during thinking —
it is simply to fill `spinnerTipsOverride` with good facts and make sure
`spinnerTipsEnabled` is true. That is what the bundled script does.

The exact key names matter and have bitten this skill before: the CLI reads
`spinnerTipsOverride`, NOT a key named `spinnerTips`. Writing to `spinnerTips`
puts a tidy-looking block in settings.json that the CLI silently ignores, so the
facts never appear. Always go through the script — it writes the correct keys
and removes the dead `spinnerTips` key if an older run left one behind.

Because the spinner reads a fixed list from the config, the facts are gathered
**once at setup** and stored. To refresh them later, the user just runs this
skill again. Each tip should be short enough to fit a terminal line, since
anything wider gets cut off.

The setting shape the CLI actually reads (confirmed against the installed
binary — `spinnerTipsOverride: { tips: string[], excludeDefault?: boolean }`):

```json
{
  "spinnerTipsEnabled": true,
  "spinnerTipsOverride": {
    "tips": ["fact one", "fact two", "..."],
    "excludeDefault": true
  }
}
```

`excludeDefault: true` shows only the user's facts; `false` mixes them with the
built-in gerunds. Default to `true` — the user is here to replace the gerunds
with facts, so honor that unless they say they want to keep the originals too.

**The `Tip:` label is hardcoded.** The CLI renders every spinner tip as
`Tip: <your text>` — that "Tip:" prefix lives in the compiled binary and there is
no setting to rename it (and patching the binary is a non-starter: it breaks the
app's code signature and gets wiped on every update). So the only thing under our
control is the text *after* the label. To surface which subject a fact came from,
**embed the subject into the fact string itself** (see step 2), e.g. a tip of
`"Astronomy Fact — Venus's day is longer than its year."` renders as
`Tip: Astronomy Fact — Venus's day is longer than its year.` If a user asks to
replace the word "Tip," explain this honestly rather than promising something the
CLI won't do.

## Two display channels: the glowing verb vs. the dim tip

There are actually two places facts can go, and they look very different:

1. **The spinner verb** (`spinnerVerbs`) — the bright word that animates with a
   shimmer/glow (the "Discombobulating…" element). This is what users mean when
   they want facts that "glow," "pop," or are "more visible." It's rendered with
   the `claudeShimmer` effect, front and center. Schema:
   `spinnerVerbs: { mode: "append" | "replace", verbs: string[] }` — `replace`
   uses only your entries, `append` mixes them with the built-in gerunds. The
   catch: the verb shares one line with the "(esc to interrupt · 12s)" hint, so
   **verbs must be short** (aim for under ~60 characters). Long facts get clipped
   or wrap. The CLI appends its own "…", so don't add one.

2. **The tip line** (`spinnerTipsOverride`) — the secondary line rendered *dim*
   by design. Good for **longer, in-depth** facts that wouldn't fit the verb, but
   it never glows.

So short facts ↔ glowing verb, long facts ↔ dim tip. They're independent: you can
set one, the other, or both. A nice combo is short glowing facts as the verb
*plus* in-depth facts on the tip line — they won't match (each is chosen
independently), but both are interesting. Ask the user which they want when they
mention visibility/glow; default to short glowing verbs if they just want it to
stand out. Write verbs with the bundled script's `--target verbs` flag.

## The workflow

### 1. Get the subjects and the fact length

Settle two things before writing any facts: which subjects, and how long.

**Subjects — use a multi-select checkbox prompt.** If the user already named
their subjects ("history and astronomy"), use those and don't re-ask. Otherwise
present the menu as an interactive **multi-select** prompt (the `AskUserQuestion`
tool with `multiSelect: true`) so they can tick boxes rather than typing a list
back.

One hard constraint to respect: **`AskUserQuestion` allows at most 4 options per
question** — handing it a single ten-item list throws "Invalid tool parameters"
and the prompt never appears. So split the subjects across a few grouped
multi-select questions of up to four options each (the tool accepts several
questions in one call, shown together). A natural split is two groups, e.g.:

> **Science:** Astronomy/Space · Biology · Physics · Chemistry
> **Humanities & other:** History · Math · Geography · Art & Technology

Make clear in each question that they can pick several and that their choices
combine across the groups; the auto-provided "Other" option lets them name a
subject of their own. You can fold the length question (below) into the same call
as a final single-select question so the whole setup is one interaction.

**Fact length.** Then ask whether they want facts **short or in-depth** — people
differ on this and it changes how the facts read. A single-select question is
fine here (it's one choice, not many):

> Do you want short one-line facts, or longer in-depth ones?

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

### 2. Gather the facts — write them yourself, true and tight

This is the part that makes the result good or bad, so spend your effort here.
**Write the facts directly from your own knowledge — do not browse the web.**
That's a deliberate choice: setup should feel instant, and hitting the web for
each subject means a string of tool calls the user has to approve one by one,
which turns a 30-second task into a slog of permission prompts. You already know
far more genuinely interesting, accurate facts than a spinner needs, so just
write them. The cost is staleness, and the answer to staleness is that the pool
regenerates every time the user re-runs this skill — it's never the same list
twice — not a live network fetch.

(If the user *explicitly* asks for web-sourced or "look it up" facts, you can use
WebSearch/WebFetch — but that's opt-in, not the default. Don't reach for the web
on your own; it's the thing that made setup feel slow.)

**Write a generous pool — roughly 20–30 per subject.** The pool is what the
spinner rotates through, and the user asked for it not to feel like a tiny
static list, so err on the side of more. The spinner reads this fixed pool and
the user refreshes it by re-running this skill, so a big, varied pool is what
keeps the rotation from going stale between runs.

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

**Tag each fact with its subject.** Because the spinner's hardcoded `Tip:` label
can't be changed, prefix every fact with the subject it came from so the line
reads `Tip: <Subject> Fact — <the fact>`. Use a consistent format like
`"<Subject> Fact — "` (an em dash reads cleanly), and keep track of which subject
each fact belongs to as you write it. This adds ~15–20 characters, so leave a
little headroom under the length budget. If the user explicitly says they don't
want any subject label, skip the prefix and just write the bare facts.

Write the assembled pool to a JSON file as a flat array of strings (each already
carrying its subject prefix). **Use a unique filename** — never a fixed shared
path like `/tmp/thinking-facts.json`,
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
writes only the `spinnerTipsOverride` and `spinnerTipsEnabled` keys (and clears
the dead legacy `spinnerTips` key), and refuses to write if the existing file is
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
blanks/duplicates, and skips anything over the limit, then reports how many
entries it installed.

**To write the glowing spinner verbs** (the shimmering word, for short facts),
pass `--target verbs` with a small `--max-len` so they stay on one line:

```bash
python3 <skill-dir>/scripts/apply_spinner_tips.py \
  --facts-file "$VERBS" --target verbs --mode replace --max-len 70
```

`--target verbs` writes `spinnerVerbs` and leaves the tip keys untouched, so you
can set the glowing verbs and the dim in-depth tips in two separate calls (each
from its own facts file) to get the combined effect.

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
- how to undo it: remove the `spinnerTipsOverride` block from
  `~/.claude/settings.json` (or set `spinnerTipsEnabled` to false to keep the
  facts but hide them, or just restore the `.bak`).

Show them three or four sample facts from the pool so they get a taste of what
they'll see.

## Quality checklist

- If the user didn't name subjects, did I offer them as a multi-select checkbox
  prompt, split into groups of ≤4 options each (the tool's per-question limit)?
- Did I ask short vs. in-depth (and match the fact length + `--max-len` to it)?
- Did I write the facts from my own knowledge (no unprompted web browsing), so
  setup stayed fast and approval-free?
- Did I gather a generous pool (~20–30 per subject) so it doesn't feel static?
- Did I prefix each fact with its subject (`<Subject> Fact — …`), since the
  hardcoded `Tip:` label can't be renamed, unless the user opted out?
- If the user wanted facts to "glow"/stand out, did I write short ones to the
  spinner verb (`--target verbs`), not just the dim tip line?
- Are all facts things I'm confident are TRUE — no popular myths?
- Did I write facts to a UNIQUE filename (never a fixed shared path)?
- Are they varied and genuinely interesting, not the tired greatest-hits?
- Did I write through the script (with its backup), never by hand-editing JSON?
- Did I tell them it takes effect in a new session, how to refresh, and how to
  revert?
