# Project Overview: GitHub Repository Intelligence Analyzer

## Live Demo

[Live Demo](https://github-repository-intelligence-analyzer-production.up.railway.app/)

## Introduction

The **GitHub Repository Intelligence Analyzer** is a tool developed as a GSoC 2026 Pre-Task (C2SI WebiU, Issue #541, Task 2). It is designed to analyze multiple GitHub repositories and generate structured reports covering their activity, complexity, and learning difficulty. The project provides both a Command Line Interface (CLI) and a Flask web application, making it accessible for both automated analysis and interactive use.

## Motivation

Understanding the barrier to entry and the health of open-source projects can be challenging for new contributors, organizations, and maintainers. This tool automates the evaluation of repositories, classifying them into Beginner, Intermediate, and Advanced difficulty levels. This helps prospective contributors find projects that match their skill level and availability.

## Core Features

- **Comprehensive Data Fetching:** Retrieves real data directly from the GitHub REST API, including commit history, pull requests, issues, contributor count, languages, and dependency files.
- **Custom Scoring Metrics:**
    - **Activity Score (0-100):** Measures recent development cadence incorporating commits (strongest signal), contributors, merged PRs, and closed issues over the past 90 days.
    - **Complexity Score (0-100):** Evaluates the structural complexity using proxy metrics like file size, polyglot breadth, and dependency surface area.
- **Difficulty Classification:** Automatically classifies a repository based on defined thresholds for Beginner, Intermediate, or Advanced difficulty.
- **Robustness:** Handles common edge cases seamlessly, such as missing data, hit rate limits, dormant repositories, and repositories with extensive file structures.

## Architecture

The project is structured into modular components:

- **CLI (`main.py`):** Accepts GitHub repository URLs or shorthands to perform analysis quickly from the terminal.
- **Web App (`app.py`):** A Flask-based web application providing a user-friendly interface. It's ready to be deployed on platforms like Render or Railway.
- **Analyzer Module (`analyzer/`):** Contains the core logic:
    - `github_client.py`: API interactions.
    - `pipeline.py`: Coordinates fetching and scoring.
    - `scoring.py`: Mathematical models for activity and complexity.
    - `reporter.py`: Generates machine-readable (JSON) and human-readable (HTML) reports.

## Artifact Deliverables

The tool produces consistent output for consumption:

- **JSON Reports:** For machine analysis and integrations.
- **HTML Reports:** Self-contained visualization showcasing metrics and classifications.

## Scoring Formulas

### Activity Score (0–100)

Measures how actively the repo is developed over the past 90 days.

```text
raw   = (commits_90d  × 0.40)   # commit cadence — strongest signal
      + (contributors × 0.30)   # sustained team engagement
      + (issues_closed × 0.20)  # responsiveness to problems
      + (prs_merged    × 0.10)  # code actually landing

score = min(raw, 100)
```

**Rationale:** Commits weighted highest (0.40) because they represent real code work. Contributors weighted second (0.30) because solo repos are inherently less sustainable. Issues and PRs weighted lower because they can be absent in healthy research or library repos.

### Complexity Score (0–100)

Measures structural complexity of the codebase.

```text
raw   = (file_count / 10     × 0.35)   # size proxy
      + (language_count × 5  × 0.40)   # polyglot breadth — strongest signal
      + (dep_file_count × 8  × 0.25)   # dependency surface area

score = min(raw, 100)
```

**Rationale:** Language diversity weighted highest (0.40) because a repo mixing TypeScript + Python + Dockerfile + SCSS requires more breadth to understand than a large single-language codebase. File count is a rough size proxy; dependency files indicate how much third-party knowledge is assumed.

### Difficulty Classification

```text
Beginner     complexity ≤ 25  AND  contributors ≤ 10
Advanced     complexity ≥ 70  OR   contributors ≥ 100
Intermediate everything else
```

## Installation & Usage

### Prerequisites

- Python 3.11+
- (Optional but recommended) A GitHub Personal Access Token — raises rate limit from 60 to 5000 requests/hour. Generate one at https://github.com/settings/tokens.

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/repo-intelligence-analyzer
cd repo-intelligence-analyzer

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GITHUB_TOKEN if you have one
```

### CLI — Analyze Specific Repos

```bash
# Default: analyze the sample repos embedded in the code
python main.py

# Analyze specific repos
python main.py c2siorg/Webiu vuejs/vue django/django

# Analyze from a file (one URL per line)
python main.py --repos-file my-repos.txt

# Skip HTML output, JSON only
python main.py --no-html
```

### Web App — Run Locally

```bash
python app.py
# Open http://localhost:8000
```
