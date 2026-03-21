# GitHub Repository Intelligence Analyzer

> **C2SI WebiU — GSoC 2026 Pre-Task (Issue #541, Task 2)**

A tool that analyzes multiple GitHub repositories and generates structured
reports covering **activity**, **complexity**, and **learning difficulty**.

---

## Live Demo

🔗 **[Deployed URL — fill this in after deployment]**

---

## Features

- Accepts any GitHub repo URL or `owner/repo` shorthand
- Fetches real data from the GitHub REST API (stars, forks, languages, commits, contributors, PRs, issues, file count, dependency files)
- Computes custom **Activity Score** and **Complexity Score** (0–100 each)
- Classifies every repo as **Beginner / Intermediate / Advanced**
- Handles edge cases: missing data, dormant repos, empty contributor lists, API failures
- Minimizes API calls (caps paginated requests; uses a single token header)
- Generates both a **self-contained HTML report** and a machine-readable **JSON report**
- Ships a **Flask web app** deployable on Render / Railway in one click

---

## Scoring Formulas

### Activity Score (0–100)

Measures how actively the repo is developed over the past 90 days.

```
raw   = (commits_90d  × 0.40)   # commit cadence — strongest signal
      + (contributors × 0.30)   # sustained team engagement
      + (issues_closed × 0.20)  # responsiveness to problems
      + (prs_merged    × 0.10)  # code actually landing

score = min(raw, 100)
```

**Rationale:** Commits weighted highest (0.40) because they represent
real code work. Contributors weighted second (0.30) because solo repos
are inherently less sustainable. Issues and PRs weighted lower because
they can be absent in healthy research or library repos.

### Complexity Score (0–100)

Measures structural complexity of the codebase.

```
raw   = (file_count / 10     × 0.35)   # size proxy
      + (language_count × 5  × 0.40)   # polyglot breadth — strongest signal
      + (dep_file_count × 8  × 0.25)   # dependency surface area

score = min(raw, 100)
```

**Rationale:** Language diversity weighted highest (0.40) because a repo
mixing TypeScript + Python + Dockerfile + SCSS requires more breadth to
understand than a large single-language codebase. File count is a rough
size proxy; dependency files indicate how much third-party knowledge is
assumed.

### Difficulty Classification

```
Beginner     complexity ≤ 25  AND  contributors ≤ 10
Advanced     complexity ≥ 70  OR   contributors ≥ 100
Intermediate everything else
```

---

## Sample Output (5 Repositories)

| Repository | Activity | Complexity | Difficulty |
|---|---:|---:|---|
| c2siorg/Webiu | 100.0 | 19.9 | Intermediate |
| c2siorg/GDB-UI | 24.2 | 13.4 | Beginner |
| c2siorg/codelabz | 26.5 | 18.9 | Intermediate |
| tensorflow/tensorflow | 100.0 | 100.0 | Advanced |
| vuejs/vue | 33.2 | 22.3 | Advanced |

**Observations:**
- `c2siorg/Webiu` is classified **Intermediate** despite high activity because
  its complexity is low (only 4 languages, ~284 files) — it's active but
  accessible, making it a good GSoC entry point.
- `c2siorg/GDB-UI` is **Beginner**: small file count, 3 languages, fewer than
  10 contributors — the lowest barrier to entry in the C2SI ecosystem.
- `tensorflow/tensorflow` hits the ceiling on both scores (100/100). Its
  99,820 files across 8 languages, 4 dependency manifests, and 100+
  contributors make it unambiguously Advanced.
- `vuejs/vue` scores **Advanced** despite low recent activity (it's in
  maintenance mode — Vue 3 is the active branch) because its contributor
  count (100+) triggers the Advanced threshold.

Full JSON report: `reports/report.json`  
Full HTML report: `reports/report.html`

---

## Installation & Usage

### Prerequisites

- Python 3.11+
- (Optional but recommended) A GitHub Personal Access Token —
  raises rate limit from 60 to 5000 requests/hour.
  Generate one at https://github.com/settings/tokens (no special scopes needed).

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/repo-intelligence-analyzer
cd repo-intelligence-analyzer

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

### CLI — analyze specific repos

```bash
# Default: analyze the 5 sample repos
python main.py

# Analyze specific repos
python main.py c2siorg/Webiu vuejs/vue django/django

# Analyze from a file (one URL per line)
python main.py --repos-file my-repos.txt

# Skip HTML output, JSON only
python main.py --no-html
```

### Web App — run locally

```bash
python app.py
# Open http://localhost:8000
```

---

## Edge Case Handling

| Scenario | Handling |
|---|---|
| Repository not found (404) | Marked as error in report, analysis continues |
| GitHub API rate limit hit (403) | Waits for reset window automatically |
| No commits in 90 days | Activity score reflects zero; note added to report |
| No contributor data | contributor_count = 0; classified as Beginner by default |
| Git tree > 100k nodes | file_count may be 0 due to API truncation; noted |
| Network timeout | Request caught, error surfaced in report |
| Repo with no languages | language_count = 0; complexity still computed from other factors |

---

## Deployment (Render)

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Add environment variable: `GITHUB_TOKEN` = your token
7. Deploy

Alternatively, use the included `render.yaml` for one-click deploy.

---

## Project Structure

```
repo-intelligence-analyzer/
├── main.py              # CLI entrypoint
├── app.py               # Flask web application
├── requirements.txt
├── render.yaml          # Render deployment config
├── .env.example
├── reports/
│   ├── report.html      # Generated HTML report (sample included)
│   └── report.json      # Generated JSON report (sample included)
└── analyzer/
    ├── __init__.py
    ├── github_client.py # GitHub REST API client
    ├── pipeline.py      # Analysis pipeline (fetches + scores one repo)
    ├── scoring.py       # Scoring formulas and RepoMetrics dataclass
    └── reporter.py      # HTML and JSON report generators
```

---

## Limitations

- Commits are capped at 500 (5 pages × 100) to stay within rate limits without a token
- Contributor count is capped at 100 by the GitHub API
- PR count uses only the most recent 100 results
- File count uses the git tree API; repos with > 100k files may return 0
- Analysis of very large repos (tensorflow, linux) is slow without a token

---

## License

MIT
