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
