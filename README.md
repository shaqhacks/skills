# skills

A collection of [Claude Code](https://claude.com/claude-code) skills.

## Skills

### `coding-mentor`
Turns coding work into active learning instead of passive delegation. While
writing or changing code, Claude explains the reasoning and tradeoffs in a
strictly technical register and pauses at genuine decision points to ask you a
question — so your engineering judgment stays sharp instead of atrophying.
Dials back automatically when you say you're in a hurry.

### `setup-thinking-facts`
Replaces Claude Code's whimsical "thinking" spinner words (Discombobulating…,
Frolicking…) with true, interesting facts from subjects you pick — history,
biology, math, astronomy, and more. It gathers fresh facts from the web and
writes them into your `spinnerTips` setting. Run it, pick your subjects and
whether you want short or in-depth facts, then start a new session to see them.

## Installing a skill

Each top-level folder is a self-contained skill. To install one globally (so
it's available in every Claude Code session on your machine), copy its folder
into `~/.claude/skills/`:

```bash
git clone https://github.com/shaqhacks/skills.git
cp -R skills/coding-mentor ~/.claude/skills/
cp -R skills/setup-thinking-facts ~/.claude/skills/
```

Skills are picked up at the start of a new session. Invoke one explicitly with
`/coding-mentor` or `/setup-thinking-facts`, or let it trigger automatically
based on its description.

## License

[MIT](./LICENSE)
