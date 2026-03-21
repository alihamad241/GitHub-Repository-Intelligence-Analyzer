"""
Web interface for the analyzer — deployable on Render / Railway / Fly.io.

Routes:
  GET  /           → homepage with form
  POST /analyze    → run analysis, return HTML report inline
  GET  /report     → serve the last generated static report
  GET  /health     → health check for deployment platforms
"""

import os
import threading
from pathlib import Path
from flask import Flask, request, render_template_string, jsonify, redirect, url_for

import sys
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from analyzer.github_client import GitHubClient
from analyzer.pipeline import analyze_repo
from analyzer.reporter import generate_html, generate_json

app = Flask(__name__)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Simple in-memory lock so concurrent requests don't collide
_lock = threading.Lock()

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GitHub Repository Intelligence Analyzer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #f3f4f6; min-height: 100vh; display: flex;
           align-items: center; justify-content: center; padding: 24px; }
    .card { background: #fff; border-radius: 16px; padding: 40px;
            max-width: 640px; width: 100%;
            box-shadow: 0 4px 24px rgba(0,0,0,.08); }
    h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 6px; }
    p.sub { color: #6b7280; font-size: 14px; margin-bottom: 28px; }
    label { display: block; font-size: 13px; font-weight: 600; color: #374151;
            margin-bottom: 6px; }
    textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 8px;
               padding: 12px; font-size: 14px; font-family: monospace;
               resize: vertical; min-height: 140px; outline: none; }
    textarea:focus { border-color: #6366f1; box-shadow: 0 0 0 3px #6366f115; }
    button { background: #6366f1; color: #fff; border: none; border-radius: 8px;
             padding: 12px 28px; font-size: 15px; font-weight: 600;
             cursor: pointer; margin-top: 16px; width: 100%; }
    button:hover { background: #4f46e5; }
    button:disabled { background: #a5b4fc; cursor: not-allowed; }
    .note { margin-top: 20px; font-size: 12px; color: #9ca3af;
            border-top: 1px solid #f3f4f6; padding-top: 16px; }
    .example { font-size: 12px; color: #9ca3af; margin-top: 6px; }
    .spinner { display: none; }
    .loading .spinner { display: inline-block; }
    .loading .btn-text { display: none; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spin { display: inline-block; animation: spin 1s linear infinite; }
    .error { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px;
             padding: 16px; color: #dc2626; font-size: 14px; margin-top: 16px; }
  </style>
</head>
<body>
<div class="card">
  <h1>🔬 Repo Intelligence Analyzer</h1>
  <p class="sub">Built for C2SI WebiU GSoC 2026 Pre-Task · Issue #541</p>

  {% if error %}
  <div class="error">{{ error }}</div>
  {% endif %}

  <form method="POST" action="/analyze" id="form">
    <label for="repos">GitHub Repository URLs (one per line)</label>
    <textarea id="repos" name="repos" placeholder="c2siorg/Webiu
c2siorg/GDB-UI
tensorflow/tensorflow
vuejs/vue
django/django">{{ default_repos }}</textarea>
    <p class="example">Accepts: owner/repo  or  https://github.com/owner/repo</p>
    <button type="submit" id="btn">
      <span class="btn-text">Analyze Repositories</span>
      <span class="spinner"><span class="spin">⏳</span> Analyzing (may take ~30s)...</span>
    </button>
  </form>

  <div class="note">
    No GitHub token configured — using unauthenticated API (60 req/hr).
    Keep the list to ≤ 3 repos for reliability without a token.
  </div>
</div>
<script>
  document.getElementById("form").addEventListener("submit", function() {
    var btn = document.getElementById("btn");
    btn.disabled = true;
    btn.classList.add("loading");
  });
</script>
</body>
</html>
"""

DEFAULT_REPOS_TEXT = "\n".join([
    "c2siorg/Webiu",
    "c2siorg/GDB-UI",
    "c2siorg/codelabz",
    "tensorflow/tensorflow",
    "vuejs/vue",
])


@app.route("/")
def index():
    return render_template_string(INDEX_HTML,
                                  error=None,
                                  default_repos=DEFAULT_REPOS_TEXT)


@app.route("/analyze", methods=["POST"])
def analyze():
    raw = request.form.get("repos", "").strip()
    if not raw:
        return render_template_string(INDEX_HTML,
                                      error="Please enter at least one repository.",
                                      default_repos="")

    repo_list = [line.strip() for line in raw.splitlines()
                 if line.strip() and not line.startswith("#")]

    if len(repo_list) > 10:
        return render_template_string(INDEX_HTML,
                                      error="Maximum 10 repositories per request.",
                                      default_repos=raw)

    token   = os.getenv("GITHUB_TOKEN")
    client  = GitHubClient(token)
    results = []

    with _lock:
        for url in repo_list:
            results.append(analyze_repo(client, url))

    html_path = str(REPORTS_DIR / "report.html")
    json_path = str(REPORTS_DIR / "report.json")
    generate_html(results, html_path)
    generate_json(results, json_path)

    return Path(html_path).read_text(encoding="utf-8")


@app.route("/report")
def report():
    html_path = REPORTS_DIR / "report.html"
    if not html_path.exists():
        return redirect(url_for("index"))
    return html_path.read_text(encoding="utf-8")


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
