# GitHub Trending Report

Generate a static GitHub Trending report with README-based summaries and tags.

The scraper reads repositories from `https://github.com/trending`, fetches each repository README, summarizes the READMEs with `codex exec`, and writes static HTML and JSON files to `docs/`.

## What It Produces

- `docs/index.html` - archive page listing all generated reports
- `docs/YYYY-MM-DD.html` - dated static report
- `docs/YYYY-MM-DD.json` - dated report data

The generated HTML is self-contained and can be published directly with GitHub Pages.

## Requirements

- Python 3
- A working `codex` CLI installation
- Codex authentication configured for `codex exec`
- Network access to GitHub

Python dependencies are listed in `requirements.txt`.

## Setup

Use the repo virtual environment if it already exists:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Or create one first:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Generate A Report

Generate the default report, currently limited to 16 trending repositories:

```bash
.venv/bin/python scrape.py
```

Generate a smaller report:

```bash
.venv/bin/python scrape.py --limit 5
```

The command prints the report JSON and writes the static files into `docs/`.
After a successful run, it commits changed files in `docs/` and pushes them to GitHub.

Generate without pushing:

```bash
.venv/bin/python scrape.py --no-push
```

## Summarization

README summarization is handled in `summarizer.py`.

Current behavior:

- Uses `codex exec`.
- Uses the `gpt-5.4-mini` model.
- Runs Codex in a read-only sandbox.
- Batches README summaries instead of calling Codex once per repository.
- Keeps adding READMEs to a batch until the estimated prompt would exceed `300000` tokens.
- Sends the batched prompt through stdin to avoid command-line length limits.
- Parses `codex exec --json` usage events to record summary token usage.

The main tuning constants are:

```python
CODEX_MODEL = 'gpt-5.4-mini'
MAX_README_CHARS = 12000
MAX_BATCH_TOKENS = 300000
CODEX_TIMEOUT = 600
```

## Publish With GitHub Pages

Because the generated site lives in `docs/`, GitHub Pages can serve it directly.

1. Add a `.nojekyll` file:

```bash
touch docs/.nojekyll
```

2. Commit and push the generated files:

```bash
git add docs README.md
git commit -m "Publish static trending report"
git push
```

3. In GitHub, open:

```text
Settings -> Pages -> Build and deployment
```

4. Select:

```text
Source: Deploy from a branch
Branch: main
Folder: /docs
```

After GitHub Pages finishes publishing, the site should be available at:

```text
https://<username>.github.io/<repo-name>/
```

The homepage lists all generated reports. Each report is available at:

```text
https://<username>.github.io/<repo-name>/YYYY-MM-DD.html
```

After GitHub Pages is configured, each successful `scrape.py` run updates `docs/`, commits the generated files, and pushes to `origin main`. Use `--no-push` when testing locally.

## Project Structure

```text
github_scraper.py   Fetches GitHub Trending and repository README content.
summarizer.py       Batches README content and asks Codex for summaries/tags.
html_report.py      Renders the static HTML report.
scrape.py           Main CLI entrypoint for generating reports.
docs/               Generated static HTML and JSON output for GitHub Pages.
requirements.txt    Python dependencies.
TODO.TXT            Planned follow-up work.
```

## Troubleshooting

If imports fail, use the repo virtual environment:

```bash
.venv/bin/python scrape.py
```

If summaries fail, verify that `codex exec` works outside the script:

```bash
printf '%s' 'Return {"ok": true}' | codex exec --json --model gpt-5.4-mini --skip-git-repo-check --ephemeral --sandbox read-only -
```

If README fetching fails, check network access to GitHub and whether GitHub is rate-limiting the requests.
