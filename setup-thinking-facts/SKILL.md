---
name: setup-thinking-facts
description: >-
  Replace Claude Code's "thinking" filler with interesting, true facts shown on
  the "Tip:" line beneath the spinner — from subjects the user picks (history,
  space, biology, math, art, anything), in short or in-depth form. Use this
  whenever the user wants to customize, change, or personalize what shows while
  Claude is thinking/working, wants trivia or facts while they wait, wants to
  learn something during pauses, or says things like "change the thinking words,"
  "show me facts while you think," "put facts in the spinner," or "I want history
  facts when you're working." It writes the facts into the spinnerTipsOverride
  setting and leaves the glowing spinner word at its defaults. This is a one-time
  SETUP task, not an ongoing behavior — run it, and the facts then show on their
  own in every new session.
---

# Setup Thinking Facts

## What this does and why it works this way

Claude Code shows a short helpful "Tip:" line beneath the spinner while it works.
The CLI reads custom strings for that line from a setting called
**`spinnerTipsOverride`** in `~/.claude/settings.json`, and only shows them when
the master toggle **`spinnerTipsEnabled`** is on. So the way to show facts while
Claude thinks is not a running program or a hook — there is no hook that fires
during thinking — it is simply to fill `spinnerTipsOverride` with good facts and
make sure `spinnerTipsEnabled` is true. That is what the bundled script does.

The exact key name matters and has bitten this skill before: the CLI reads
`spinnerTipsOverride`, **not** a key named `spinnerTips`. Writing to `spinnerTips`
puts a tidy-looking block in settings.json that the CLI silently ignores, so the
facts never appear. Always go through the script — it writes the correct keys.

This skill puts facts on the **Tip line** and leaves the bright, glowing spinner
word ("Discombobulating…") at Claude Code's defaults. (We tried putting facts in
the glowing word instead; it's eye-catching but it's a single short line that
shares space with the status text and clips longer facts, so the Tip line — which
has room to wrap — is the better home for real facts.) The script clears any
leftover `spinnerVerbs` override from that experiment so the default gerunds come
back.

Because the spinner reads a fixed list from the config, the facts are gathered
**once at setup** and stored. To refresh them later, the user just runs this
skill again.

The setting shape the CLI reads
(`spinnerTipsOverride: { tips: string[], excludeDefault?: boolean }`):

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
built-in tips. Default to `true` — the user is here to see their facts — unless
they say they want to keep the originals too.

## The workflow

### 1. Get the subjects and the fact length

Settle two things before writing any facts: which subjects, and how long.

**Subjects — use a multi-select checkbox prompt.** If the user already named their
subjects ("history and astronomy"), use those and don't re-ask. Otherwise present
the menu as an interactive **multi-select** prompt (the `AskUserQuestion` tool
with `multiSelect: true`) so they can tick boxes rather than typing a list back.

One hard constraint: **`AskUserQuestion` allows at most 4 options per question** —
a single ten-item list throws "Invalid tool parameters" and the prompt never
appears. So split the subjects across a few grouped multi-select questions of up
to four options each (the tool accepts several questions in one call, shown
together). A natural split is two groups, e.g.:

> **Science:** Astronomy/Space · Biology · Physics · Chemistry
> **Humanities & other:** History · Math · Geography · Art & Technology

Make clear in each question that they can pick several and that the choices
combine; the auto-provided "Other" option lets them name their own subject.

**Fact length.** Then ask whether they want facts **short or in-depth** — people
differ on this and the Tip line can hold either. A single-select question is fine
here (it's one choice):

> Do you want short one-line facts, or longer in-depth ones?

- **Short** — a single tight sentence (~120 characters). Compact and quick to
  read. A safe default if they don't care.
- **In-depth** — two or three sentences (up to ~280 characters) that use the extra
  room to explain *why* the fact is interesting. The Tip line wraps to fit, so
  length is fine; just don't pad.

You can fold both into one `AskUserQuestion` call (the subject groups plus the
length question) so setup is a single interaction.

### 2. Gather the facts — true, varied, and the right length

This is the part that makes the result good or bad, so spend your effort here.
**Write the facts directly from your own knowledge — do not browse the web.** That
keeps setup instant: hitting the web for each subject means a string of tool
calls the user has to approve one by one, turning a quick task into a slog of
permission prompts. You already know more genuinely interesting, accurate facts
than a spinner needs, so just write them. They regenerate fresh every time the
user re-runs this skill, so the rotation never goes stale. (Only use WebSearch if
the user *explicitly* asks to source facts online.)

**Gather a generous pool — roughly 20–30 per subject** so the rotation feels
alive rather than like a tiny static list.

Hold every fact to this bar:

- **The right length for their choice.** Short: a single sentence, ~120 chars.
  In-depth: two or three sentences, up to ~280 chars, using the extra room to
  explain why it's interesting, not to pad. Either way, tighten "It is a
  little-known fact that…" down to the fact itself.
- **Prefixed with its subject**, e.g. `History Fact — …`, `Astronomy Fact — …`,
  so the reader knows where each fact comes from. (An em dash reads cleanly.)
- **True and not a myth.** This is the whole game — a spinner of confidently-stated
  falsehoods is worse than the defaults. Avoid the popular wrong ones (the Great
  Wall is not visible from space with the naked eye; we use far more than 10% of
  our brains; glass is not a slow liquid). When unsure, drop it.
- **Self-contained and surprising.** It should land without setup and make the
  user think "huh, neat." Concrete numbers and specifics beat vague claims.
- **Varied within a subject** (don't give twenty facts about the same battle), and
  **clean** (safe-for-work, non-political, non-gory) — it shows constantly.

Write the pool to a JSON file as a flat array of strings. **Use a unique
filename** — never a fixed shared path like `/tmp/facts.json`, since a re-run
would collide. Generate one with `mktemp`:

```bash
FACTS=$(mktemp -t thinking-facts.XXXXXX) ; echo "$FACTS"
# then write the JSON array of subject-prefixed facts to "$FACTS"
```

```json
["Astronomy Fact — A day on Venus is longer than its year.",
 "History Fact — Honey found in 3,000-year-old Egyptian tombs was still edible."]
```

(The script also accepts the array on stdin via `--stdin`.)

### 3. Write it into the setting with the bundled script

Do **not** hand-edit `settings.json` — it holds the user's whole configuration and
a slip could corrupt it. Use the bundled script, which backs up the file, writes
only the Tip-line keys (and clears any leftover glowing-word override), and
refuses to write if the existing file is unparseable:

```bash
python3 <skill-dir>/scripts/apply_spinner_tips.py \
  --facts-file "$FACTS" \
  --exclude-default true \
  --max-len 140         # use 300 for in-depth mode so longer facts aren't dropped
```

Set `--max-len` to match the chosen length: ~140 for short, ~300 for in-depth
(otherwise the script drops the longer in-depth facts as too long). Other flags:
`--settings PATH` (default `~/.claude/settings.json`), `--mode append` to add to
an existing pool, `--stdin` to pipe the facts, `--dry-run` to preview. The script
cleans whitespace, drops blanks/dupes/over-length entries, and reports how many
it installed.

### 4. Confirm and tell them what to expect

Report back plainly:
- which subjects and which length (short / in-depth) you set up — **do not state a
  fact count.** A finite "42 facts" reads as a small fixed list when the intent is
  an open-ended, refreshable set.
- that it takes effect **in a new session** (the list is read at startup), so they
  should start a fresh `claude` to see it,
- that the facts show on the **Tip line** beneath the spinner; the glowing word
  stays Claude Code's normal gerunds,
- that to pull a fresh batch later they just **re-run this skill**,
- that the previous settings were backed up to `settings.json.bak`,
- how to undo it: remove the `spinnerTipsOverride` block from
  `~/.claude/settings.json` (or set `spinnerTipsEnabled` to false, or restore the
  `.bak`).

Show them three or four sample facts so they get a taste of what they'll see.

## Quality checklist

- If the user didn't name subjects, did I offer them as a multi-select checkbox
  prompt, split into groups of ≤4 options each (the tool's per-question limit)?
- Did I ask short vs. in-depth, and match the fact length + `--max-len` to it?
- Did I write the facts from my own knowledge (no unprompted web browsing), so
  setup stayed fast and approval-free?
- Did I gather a generous pool (~20–30 per subject) so it doesn't feel static?
- Did I prefix each fact with its subject (`History Fact — …`)?
- Are all facts things I'm confident are TRUE — no popular myths?
- Did I write facts to a UNIQUE filename (never a fixed shared path)?
- Did I write through the script (with its backup), never by hand-editing JSON?
- Did I tell them it takes effect in a new session, how to refresh, and how to
  revert?
