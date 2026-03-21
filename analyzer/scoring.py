"""
Scoring Engine
==============

All formulas are documented here so they can be explained in the submission.

─── Activity Score (0–100) ────────────────────────────────────────────────────
Measures how actively the repo is being developed over the past 90 days.

  raw = (commits_90d  × 0.40)   # commit cadence is the strongest signal
      + (contributors × 0.30)   # team size indicates sustained effort
      + (issues_closed × 0.20)  # issue resolution shows responsiveness
      + (prs_merged    × 0.10)  # PR merges confirm code is landing

  score = min(raw, 100)  # cap at 100

Rationale: commits weighted highest because they represent actual code work;
contributors weighted second because solo projects are inherently less active;
issues and PRs weighted lower since they can be gamed or absent in small repos.

─── Complexity Score (0–100) ──────────────────────────────────────────────────
Measures the structural complexity of the codebase.

  raw = (file_count      / 10   × 0.35)   # file count is the strongest proxy
      + (language_count  × 5    × 0.40)   # polyglot repos are harder to grok
      + (dep_file_count  × 8    × 0.25)   # dependency surface area adds risk

  score = min(raw, 100)

Rationale: language diversity weighted highest because a repo mixing e.g.
TypeScript + SCSS + Python + Dockerfile requires more breadth to understand
than a large single-language codebase.

─── Learning Difficulty Classification ────────────────────────────────────────
Based on both complexity and contributor count (signal for community/docs quality):

  Beginner     complexity ≤ 25  AND  contributors ≤ 10
  Advanced     complexity ≥ 70  OR   contributors ≥ 100
  Intermediate everything else

─── Limitations ───────────────────────────────────────────────────────────────
- Commits capped at 500 (5 pages × 100) to stay within unauthenticated rate limits
- File count is exact only for repos whose git tree has < 100,000 nodes
- Contributor count is capped at 100 by the API (sufficient for classification)
- PR and issue counts use only the most recent 100 results
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RepoMetrics:
    # Identity
    owner: str = ""
    name: str = ""
    url: str = ""
    description: str = ""
    default_branch: str = "main"
    # Raw GitHub numbers
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    size_kb: int = 0
    # Collected metrics
    commits_90d: int = 0
    contributor_count: int = 0
    issues_closed_90d: int = 0
    prs_merged_90d: int = 0
    language_count: int = 0
    languages: dict = field(default_factory=dict)
    file_count: int = 0
    dep_files: list = field(default_factory=list)
    # Computed scores
    activity_score: float = 0.0
    complexity_score: float = 0.0
    difficulty: str = ""
    # Meta
    fetch_error: Optional[str] = None
    analysis_note: str = ""


def compute_activity(m: RepoMetrics) -> float:
    raw = (
        m.commits_90d       * 0.40 +
        m.contributor_count * 0.30 +
        m.issues_closed_90d * 0.20 +
        m.prs_merged_90d    * 0.10
    )
    return round(min(raw, 100.0), 1)


def compute_complexity(m: RepoMetrics) -> float:
    raw = (
        (m.file_count     / 10) * 0.35 +
        (m.language_count * 5)  * 0.40 +
        (len(m.dep_files) * 8)  * 0.25
    )
    return round(min(raw, 100.0), 1)


def classify_difficulty(m: RepoMetrics) -> str:
    c = m.complexity_score
    n = m.contributor_count
    if c <= 25 and n <= 10:
        return "Beginner"
    if c >= 70 or n >= 100:
        return "Advanced"
    return "Intermediate"


def score(m: RepoMetrics) -> RepoMetrics:
    m.activity_score   = compute_activity(m)
    m.complexity_score = compute_complexity(m)
    m.difficulty       = classify_difficulty(m)
    return m


def to_dict(m: RepoMetrics) -> dict:
    d = asdict(m)
    # Flatten dep_files list to a readable string for JSON/HTML
    d["dep_files_str"] = ", ".join(m.dep_files) if m.dep_files else "none detected"
    return d
