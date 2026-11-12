# Polaarts Skills

Agent skills by [@polaarts](https://github.com/polaarts). Each skill is a self-contained folder
under [`skills/`](skills/) with its own `SKILL.md`, scripts, references and tests.

| Skill | What it does |
|---|---|
| [talk-to-article](skills/talk-to-article/) | Turns a recorded talk into a technical blog-style article with screenshots, as one HTML page per talk. |

## Install a skill

With the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add polaarts/skills@<skill-name>
```

Or copy its folder into your skills folder:

```bash
git clone --depth 1 https://github.com/polaarts/skills /tmp/polaarts-skills
cp -R /tmp/polaarts-skills/skills/<skill-name> ~/.claude/skills/
```

Each skill's README lists its requirements and usage.

## Repository layout

```
skills/<skill-name>/   # one folder per skill: SKILL.md, README.md, scripts/, references/, tests/
site/                  # the catalog site (site/index.html) and one page per skill (site/skills/<name>/)
```

The catalog reads the skill list from this repository through the GitHub API, so a new folder
under `skills/` shows up there without editing the site. Its card uses the skill's `SKILL.md`
frontmatter: `name`, `description`, `license`, and the optional `metadata` fields `version`,
`category`, `platforms` and `summary` (add `-es` / `-pt` variants such as `summary-es` to
translate the card).

## Development

Every skill runs its tests from its own folder; CI runs them all on Linux, macOS and Windows:

```bash
cd skills/talk-to-article && python3 -m unittest discover tests
```

## License

[MIT](LICENSE)
