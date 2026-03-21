"""
GitHub API client with rate-limit awareness and graceful fallbacks.
Uses unauthenticated requests (60 req/hr) by default.
Set GITHUB_TOKEN in .env for 5000 req/hr.
"""

import os
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        self._remaining = None

    def _get(self, path: str, params: dict = None) -> dict | list | None:
        url = f"{self.BASE}{path}"
        try:
            r = self.session.get(url, params=params, timeout=15)
            self._remaining = int(r.headers.get("X-RateLimit-Remaining", 999))

            if r.status_code == 404:
                return None
            if r.status_code == 403:
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset - time.time(), 1)
                print(f"  ⚠  Rate limited. Waiting {int(wait)}s...")
                time.sleep(wait)
                return self._get(path, params)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  ✗  Request failed for {path}: {e}")
            return None

    def get_repo(self, owner: str, repo: str) -> dict | None:
        return self._get(f"/repos/{owner}/{repo}")

    def get_languages(self, owner: str, repo: str) -> dict:
        result = self._get(f"/repos/{owner}/{repo}/languages")
        return result if isinstance(result, dict) else {}

    def get_contributors(self, owner: str, repo: str) -> list:
        result = self._get(f"/repos/{owner}/{repo}/contributors",
                           params={"per_page": 100, "anon": "true"})
        return result if isinstance(result, list) else []

    def get_commits_since(self, owner: str, repo: str, days: int = 90) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        count = 0
        page = 1
        while True:
            data = self._get(f"/repos/{owner}/{repo}/commits",
                             params={"since": since, "per_page": 100, "page": page})
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            count += len(data)
            if len(data) < 100:
                break
            page += 1
            if page > 5:   # cap at 500 commits to save rate limit
                break
        return count

    def get_issues_closed_since(self, owner: str, repo: str, days: int = 90) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        data = self._get(f"/repos/{owner}/{repo}/issues",
                         params={"state": "closed", "since": since,
                                 "per_page": 100})
        if not isinstance(data, list):
            return 0
        # filter out pull requests (GitHub includes them in /issues)
        return sum(1 for i in data if "pull_request" not in i)

    def get_prs_merged_since(self, owner: str, repo: str, days: int = 90) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        data = self._get(f"/repos/{owner}/{repo}/pulls",
                         params={"state": "closed", "per_page": 100})
        if not isinstance(data, list):
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(
            1 for p in data
            if p.get("merged_at") and
            datetime.fromisoformat(p["merged_at"].replace("Z", "+00:00")) > cutoff
        )

    def get_file_count(self, owner: str, repo: str, default_branch: str) -> int:
        """Estimate file count from git tree (truncated at 100k nodes)."""
        data = self._get(f"/repos/{owner}/{repo}/git/trees/{default_branch}",
                         params={"recursive": "1"})
        if not data or not isinstance(data, dict):
            return 0
        tree = data.get("tree", [])
        return sum(1 for node in tree if node.get("type") == "blob")

    def get_dep_files(self, owner: str, repo: str, default_branch: str) -> list[str]:
        """Check which dependency/manifest files exist."""
        candidates = [
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
            "pom.xml", "build.gradle", "Gemfile", "go.mod", "Cargo.toml",
            "composer.json", "setup.py", "setup.cfg",
        ]
        found = []
        for f in candidates:
            r = self._get(f"/repos/{owner}/{repo}/contents/{f}")
            if r and isinstance(r, dict) and r.get("type") == "file":
                found.append(f)
        return found

    @property
    def rate_limit_remaining(self) -> int:
        return self._remaining or 0
