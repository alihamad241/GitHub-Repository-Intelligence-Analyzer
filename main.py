#!/usr/bin/env python3
"""
GitHub Repository Intelligence Analyzer
========================================
Analyzes GitHub repositories and generates activity, complexity,
and learning difficulty reports.

Usage:
  python main.py                          # analyze default 5 repos
  python main.py owner/repo [...]        # analyze specific repos
  python main.py --repos repos.txt       # read URLs from a file

Environment:
  GITHUB_TOKEN  (optional but recommended — raises rate limit to 5000/hr)
"""

import argparse
import os
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from analyzer.github_client import GitHubClient
from analyzer.pipeline import analyze_repo
from analyzer.reporter import generate_html, generate_json

DEFAULT_REPOS = [
    "c2siorg/Webiu",
    "c2siorg/GDB-UI",
    "c2siorg/codelabz",
    "tensorflow/tensorflow",
    "vuejs/vue",
]


def parse_args():
    p = argparse.ArgumentParser(
        description="GitHub Repository Intelligence Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "repos", nargs="*",
        help="GitHub repo URLs or owner/repo shorthands to analyze",
    )
    p.add_argument(
        "--repos-file", metavar="FILE",
        help="Text file with one repo URL per line",
    )
    p.add_argument(
        "--out-dir", default="reports",
        help="Directory to write report files (default: reports/)",
    )
    p.add_argument(
        "--no-html", action="store_true",
        help="Skip HTML report generation",
    )
    p.add_argument(
        "--no-json", action="store_true",
        help="Skip JSON report generation",
    )
    return p.parse_args()


def collect_repos(args) -> list[str]:
    repos = list(args.repos)
    if args.repos_file:
        path = Path(args.repos_file)
        if not path.exists():
            print(f"✗ File not found: {args.repos_file}", file=sys.stderr)
            sys.exit(1)
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                repos.append(line)
    if not repos:
        print("No repos specified — using default 5 repositories.\n")
        repos = DEFAULT_REPOS
    return repos


def main():
    args   = parse_args()
    repos  = collect_repos(args)
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    token = os.getenv("GITHUB_TOKEN")
    if token:
        print(f"✓ GitHub token found — rate limit: 5000 req/hr\n")
    else:
        print("⚠  No GITHUB_TOKEN found — using unauthenticated API (60 req/hr)\n"
              "   Set GITHUB_TOKEN in .env or environment for faster analysis.\n")

    client  = GitHubClient(token)
    results = []

    print(f"Analyzing {len(repos)} repositories...")
    print("=" * 56)

    for url in repos:
        result = analyze_repo(client, url)
        results.append(result)

    print("\n" + "=" * 56)
    print(f"\nGenerating reports in {outdir}/...")

    if not args.no_html:
        generate_html(results, str(outdir / "report.html"))
    if not args.no_json:
        generate_json(results, str(outdir / "report.json"))

    # ── Console summary table ────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print(f"{'Repository':<30} {'Activity':>8} {'Complexity':>10} {'Difficulty':<14}")
    print("─" * 72)
    for r in results:
        if r.fetch_error:
            print(f"{r.url:<30} {'ERROR':>8} {'':>10} {r.fetch_error:<14}")
        else:
            name = f"{r.owner}/{r.name}"
            print(f"{name:<30} {r.activity_score:>8} {r.complexity_score:>10} {r.difficulty:<14}")
    print("─" * 72)
    print("\nDone.\n")


if __name__ == "__main__":
    main()
