---
name: setup-thinking-facts
description: >-
  Replace Claude Code's whimsical "thinking" spinner words (Discombobulating…,
  Frolicking…) with short, true facts that GLOW in the spinner — from subjects
  the user picks (history, space, biology, math, art, anything). Use this
  whenever the user wants to customize, change, or personalize what shows while
  Claude is thinking/working, wants trivia or facts on the spinner, wants to
  learn something while they wait, or says things like "change the thinking
  words," "show me facts while you think," "make the spinner show facts," or "I
  want history facts when you're working." It writes the facts into the
  spinnerVerbs setting (the bright, animated spinner word) and leaves the regular
  tips alone. This is a one-time SETUP task, not an ongoing behavior — run it,
  and the facts then show on their own in every new session.
---

# Setup Thinking Facts

## What this does and why it works this way

Claude Code draws a playful gerund ("Ruminating…", "Discombobulating…") next to
the spinner while it works, and that word **glows** with an animated shimmer
(internally `claudeShimmer`). The CLI builds that word from a setting called
**`spinnerVerbs`**, so the way to make your own facts glow there is simply to
fill `spinnerVerbs` with them. That is all this skill does — it writes one key
and nothing else.

We deliberately use the spinner *verb*, not the "Tip:" line. There are only two
places text can go, and they're very different:

- **The spinner verb** (`spinnerVerbs`) — bright, animated, glowing. This is what
  people mean when they want facts that "glow," "pop," or stand out. **But it's a
  single short line:** it shares its row with the live status, `(5s · ↓ 2.0k
  tokens · thinking)`, so a long fact gets clipped to fit. Keep facts short.
- **The tip line** (`spinnerTipsOverride`) — rendered *dim* grey by design, never
  glows, but can hold long facts that wrap. This skill leaves it alone so the
  user keeps Claude Code's normal tips.

Because "glowing" and "long" can't coexist (the glow lives only on the short
verb), this skill does exactly one thing: **short, glowing facts.** There is no
long / in-depth option and no length question — don't offer one. If a user asks
for long facts, explain honestly that only short facts can glow (longer text
would have to live on the dim, non-glowing tip line, which this skill leaves
alone) rather than promising glowing paragraphs the CLI can't render.

**About the trailing "…":** the spinner appends "…" to every word — that's why
the defaults read `Discombobulating…`. Your facts get the same "…". It is
decoration, not truncation: `Astronomy: Moon footprints last for eons…` is the
complete fact. (Real truncation only happens if the fact is too wide for the
terminal line — that's why we keep them short.) The "…" is baked into the CLI and
can't be removed without patching the binary, which is unsafe and undone on every
update.

The setting shape (`spinnerVerbs: { mode: "append" | "replace", verbs: [...] }`):

```json
{
  "spinnerVerbs": {
    "mode": "replace",
    "verbs": ["History: Nintendo was founded in 1889",
              "Astronomy: Saturn would float in water"]
  }
}
```

`mode: "replace"` shows only the user's facts as the glowing word; `"append"`
mixes them with the built-in gerunds. Default to `"replace"` — the user is here
to swap the gerunds for facts — unless they say they want to keep the originals
mixed in.

## The workflow

### 1. Get the subjects

If the user already named subjects ("history and astronomy"), use those and don't
re-ask. Otherwise present them as an interactive **multi-select** prompt (the
`AskUserQuestion` tool with `multiSelect: true`) so they can tick boxes rather
than typing a list back.

One hard constraint: **`AskUserQuestion` allows at most 4 options per question** —
a single ten-item list throws "Invalid tool parameters" and the prompt never
appears. So split the subjects across a few grouped multi-select questions of up
to four options each (the tool accepts several questions in one call, shown
together). A natural split is two groups, e.g.:

> **Science:** Astronomy/Space · Biology · Physics · Chemistry
> **Humanities & other:** History · Math · Geography · Art & Technology

Make clear in each question that they can pick several and that the choices
combine; the auto-provided "Other" option lets them name their own subject.

There's no need to ask about fact length — glowing facts are short by definition.

### 2. Write the facts — short, true, and glowing

This is the part that makes the result good or bad, so spend your effort here.
**Write the facts directly from your own knowledge — do not browse the web.** That
keeps setup instant: hitting the web for each subject means a string of tool
calls the user has to approve one by one, turning a 30-second task into a slog of
permission prompts. You already know more genuinely interesting, accurate facts
than a spinner needs, so just write them. They regenerate fresh every time the
user re-runs this skill, so the rotation never goes stale. (Only use WebSearch if
the user *explicitly* asks to source facts online.)

Hold every fact to this bar:

- **Short enough to fit the glowing line — aim for ~36 characters or less,**
  including the subject prefix. This is the constraint that bites: the verb
  shares its row with the live status, e.g. `(1m 30s · ↓ 145.2k tokens ·
  thinking)`, which can run ~35–40 columns. On a standard 80-column terminal that
  leaves only ~36 for the fact; anything longer gets clipped mid-word (the CLI
  truncates the line to the terminal width). So count the characters — prefix
  included — and keep each at/under ~36. Trim hard; favor the punchiest version
  of the fact. If a subject's natural phrasing won't fit, shorten the wording
  (abbreviate, drop filler) rather than letting it spill over.
- **Prefixed with its short subject tag, e.g. `History: …`, `Astronomy: …`.** Use
  the bare subject plus a colon (not "History Fact:") to save precious room. This
  tells the user which subject each glowing fact is from.
- **True and not a myth.** This is the whole game — a spinner of confidently-stated
  falsehoods is worse than the gerunds. Avoid the popular wrong ones (the Great
  Wall is not visible from space with the naked eye; we use far more than 10% of
  our brains; glass is not a slow liquid). When unsure, drop it.
- **Self-contained and surprising.** It should land without setup and make the
  user think "huh, neat." Concrete specifics beat vague claims — though at this
  length you're often distilling to the single striking core of the fact.
- **Varied within a subject**, and **clean** (safe-for-work, non-political,
  non-gory) — it shows constantly while they work.

**Gather a generous pool — roughly 20–30 per subject** so the rotation feels
alive rather than like a tiny static list.

Write the pool to a JSON file as a flat array of strings. **Use a unique
filename** — never a fixed shared path like `/tmp/facts.json`, since a re-run
would collide. Generate one with `mktemp`:

```bash
FACTS=$(mktemp -t thinking-facts.XXXXXX) ; echo "$FACTS"
# then write the JSON array of short, subject-prefixed facts to "$FACTS"
```

```json
["History: Nintendo was founded in 1889",
 "Astronomy: Venus's day outlasts its year",
 "Math: 0.999... exactly equals 1"]
```

(The script also accepts the array on stdin via `--stdin` if you'd rather not
create a file.)

### 3. Write it into the setting with the bundled script

Do **not** hand-edit `settings.json` — it holds the user's whole configuration
and a slip could corrupt it. Use the bundled script, which backs up the file,
writes only the `spinnerVerbs` key (leaving the tips untouched), and refuses to
write if the existing file is unparseable:

```bash
python3 <skill-dir>/scripts/apply_spinner_facts.py \
  --facts-file "$FACTS" --mode replace --max-len 36
```

Keep `--max-len` around 36 (for an 80-column terminal) so over-long facts are
dropped rather than clipped on the spinner line. The script reports how many it
dropped — if that number isn't zero, your facts are too long; rewrite them
shorter instead of shipping a thinned pool. Other flags: `--settings PATH` (default
`~/.claude/settings.json`), `--mode append` to mix with the built-in gerunds,
`--stdin` to pipe the facts, `--dry-run` to preview. The script cleans
whitespace, drops blanks/dupes/over-length entries, and reports how many it
installed.

### 4. Confirm and tell them what to expect

Report back plainly:
- which subjects you set up — **do not state a fact count.** A finite "42 facts"
  reads as a small fixed list when the intent is an open-ended, refreshable set.
- that it takes effect **in a new session** (the verb list is read at startup),
  so they should start a fresh `claude` to see it,
- that the facts **glow** in place of the gerunds, and the trailing "…" is the
  spinner's normal ellipsis (same as `Discombobulating…`), not a cutoff,
- that to pull a fresh batch later they just **re-run this skill**,
- that the regular Tip line is untouched,
- that the previous settings were backed up to `settings.json.bak`,
- how to undo it: remove the `spinnerVerbs` block from `~/.claude/settings.json`
  (or restore the `.bak`).

Show them three or four sample facts so they get a taste of what they'll see.

## Quality checklist

- If the user didn't name subjects, did I offer them as a multi-select checkbox
  prompt, split into groups of ≤4 options each (the tool's per-question limit)?
- Did I write the facts from my own knowledge (no unprompted web browsing), so
  setup stayed fast and approval-free?
- Is every fact **short (~36 chars or less, prefix included)** so it won't be
  clipped by the status text on an 80-column terminal, and prefixed with its
  subject
  (`History: …`), so it fits the glowing line without being clipped?
- Did I gather a generous pool (~20–30 per subject) so it doesn't feel static?
- Are all facts things I'm confident are TRUE — no popular myths?
- Did I write facts to a UNIQUE filename (never a fixed shared path)?
- Did I write through the script (with its backup), touching only `spinnerVerbs`
  and never hand-editing JSON or disturbing the tip line?
- Did I tell them it takes effect in a new session, that the "…" is normal, how
  to refresh, and how to revert?
