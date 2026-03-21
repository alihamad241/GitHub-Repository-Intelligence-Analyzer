"""
Analysis pipeline — ties GitHub client + scoring engine together.
"""

import re
from analyzer.github_client import GitHubClient
from analyzer.scoring import RepoMetrics, score


def parse_repo_url(url: str) -> tuple[str, str] | None:
    """Accept github.com/owner/repo or owner/repo shorthand."""
    url = url.strip().rstrip("/")
    patterns = [
        r"github\.com/([^/]+)/([^/]+)",
        r"^([^/]+)/([^/]+)$",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1), m.group(2).removesuffix(".git")
    return None


def analyze_repo(client: GitHubClient, url: str) -> RepoMetrics:
    m = RepoMetrics(url=url)

    parsed = parse_repo_url(url)
    if not parsed:
        m.fetch_error = "Could not parse repository URL"
        return m

    owner, name = parsed
    m.owner = owner
    m.name  = name

    print(f"\n  Fetching {owner}/{name}...")

    # ── Core repo data ──────────────────────────────────────────────────────
    repo = client.get_repo(owner, name)
    if repo is None:
        m.fetch_error = "Repository not found or inaccessible"
        return m

    m.description    = repo.get("description") or ""
    m.stars          = repo.get("stargazers_count", 0)
    m.forks          = repo.get("forks_count", 0)
    m.open_issues    = repo.get("open_issues_count", 0)
    m.watchers       = repo.get("watchers_count", 0)
    m.size_kb        = repo.get("size", 0)
    m.default_branch = repo.get("default_branch", "main")

    # ── Languages ───────────────────────────────────────────────────────────
    print(f"    → languages", end="", flush=True)
    langs = client.get_languages(owner, name)
    m.languages      = langs
    m.language_count = len(langs)
    print(f" ({m.language_count})", flush=True)

    # ── Contributors ────────────────────────────────────────────────────────
    print(f"    → contributors", end="", flush=True)
    contribs = client.get_contributors(owner, name)
    m.contributor_count = len(contribs)
    print(f" ({m.contributor_count})", flush=True)

    # ── Commits (last 90 days) ───────────────────────────────────────────────
    print(f"    → commits (90d)", end="", flush=True)
    m.commits_90d = client.get_commits_since(owner, name, days=90)
    print(f" ({m.commits_90d})", flush=True)

    # ── Closed issues (last 90 days) ────────────────────────────────────────
    print(f"    → closed issues (90d)", end="", flush=True)
    m.issues_closed_90d = client.get_issues_closed_since(owner, name, days=90)
    print(f" ({m.issues_closed_90d})", flush=True)

    # ── Merged PRs (last 90 days) ────────────────────────────────────────────
    print(f"    → merged PRs (90d)", end="", flush=True)
    m.prs_merged_90d = client.get_prs_merged_since(owner, name, days=90)
    print(f" ({m.prs_merged_90d})", flush=True)

    # ── File count ──────────────────────────────────────────────────────────
    print(f"    → file count", end="", flush=True)
    m.file_count = client.get_file_count(owner, name, m.default_branch)
    print(f" ({m.file_count})", flush=True)

    # ── Dependency files ────────────────────────────────────────────────────
    print(f"    → dependency files", end="", flush=True)
    m.dep_files = client.get_dep_files(owner, name, m.default_branch)
    print(f" ({', '.join(m.dep_files) or 'none'})", flush=True)

    # ── Edge case notes ─────────────────────────────────────────────────────
    notes = []
    if m.commits_90d == 0:
        notes.append("no commits in 90 days (archived or dormant)")
    if m.contributor_count == 0:
        notes.append("no contributor data (repo may be private or empty)")
    if m.file_count == 0:
        notes.append("file count unavailable (git tree fetch failed)")
    m.analysis_note = "; ".join(notes)

    # ── Compute scores ───────────────────────────────────────────────────────
    score(m)

    print(f"  ✓  activity={m.activity_score}  complexity={m.complexity_score}  "
          f"difficulty={m.difficulty}")
    print(f"     rate limit remaining: {client.rate_limit_remaining}")

    return m
