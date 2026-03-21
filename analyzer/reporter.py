

import json
from datetime import datetime, timezone
from pathlib import Path
from analyzer.scoring import RepoMetrics, to_dict


# ── Difficulty badge colours ─────────────────────────────────────────────────
BADGE = {
    "Beginner":     ("🟢", "#22c55e", "#f0fdf4"),
    "Intermediate": ("🟡", "#f59e0b", "#fffbeb"),
    "Advanced":     ("🔴", "#ef4444", "#fef2f2"),
}


def _bar(value: float, color: str) -> str:
    pct = min(int(value), 100)
    return (
        f'<div style="background:#e5e7eb;border-radius:6px;height:10px;width:100%">'
        f'<div style="background:{color};width:{pct}%;height:10px;border-radius:6px"></div>'
        f'</div>'
    )


def _lang_pills(langs: dict) -> str:
    if not langs:
        return '<span style="color:#9ca3af;font-size:13px">—</span>'
    total = sum(langs.values()) or 1
    colors = ["#6366f1","#f59e0b","#10b981","#3b82f6","#ec4899","#8b5cf6","#14b8a6"]
    pills = []
    for i, (lang, bytes_) in enumerate(sorted(langs.items(), key=lambda x: -x[1])[:6]):
        pct = round(bytes_ / total * 100, 1)
        c = colors[i % len(colors)]
        pills.append(
            f'<span style="background:{c}18;color:{c};border:1px solid {c}44;'
            f'padding:2px 8px;border-radius:99px;font-size:12px;font-weight:600">'
            f'{lang} {pct}%</span>'
        )
    return " ".join(pills)


def _card(m: RepoMetrics) -> str:
    if m.fetch_error:
        return (
            f'<div style="border:1px solid #fca5a5;background:#fef2f2;border-radius:12px;'
            f'padding:24px;margin-bottom:20px">'
            f'<h3 style="margin:0 0 8px;color:#dc2626">{m.url}</h3>'
            f'<p style="color:#b91c1c;margin:0">⚠ {m.fetch_error}</p>'
            f'</div>'
        )

    emoji, accent, bg = BADGE.get(m.difficulty, ("⬜", "#6b7280", "#f9fafb"))

    dep_list = ", ".join(m.dep_files) if m.dep_files else "none detected"
    note_html = (
        f'<p style="margin:12px 0 0;font-size:12px;color:#9ca3af">⚠ {m.analysis_note}</p>'
        if m.analysis_note else ""
    )

    return f"""
<div style="border:1px solid {accent}55;background:{bg};border-radius:14px;
            padding:28px;margin-bottom:24px;box-shadow:0 2px 8px {accent}18">

  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:12px;margin-bottom:16px">
    <div>
      <h2 style="margin:0;font-size:20px;color:#111827">
        <a href="https://github.com/{m.owner}/{m.name}" target="_blank"
           style="color:#111827;text-decoration:none">
          {m.owner}/<strong>{m.name}</strong>
        </a>
      </h2>
      <p style="margin:4px 0 0;color:#6b7280;font-size:14px">{m.description or "No description"}</p>
    </div>
    <div style="text-align:right">
      <span style="background:{accent};color:#fff;padding:5px 14px;border-radius:99px;
                   font-size:13px;font-weight:700">{emoji} {m.difficulty}</span>
    </div>
  </div>

  <!-- Score bars -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:13px;font-weight:600;color:#374151">Activity Score</span>
        <span style="font-size:13px;font-weight:700;color:{accent}">{m.activity_score}/100</span>
      </div>
      {_bar(m.activity_score, accent)}
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:13px;font-weight:600;color:#374151">Complexity Score</span>
        <span style="font-size:13px;font-weight:700;color:{accent}">{m.complexity_score}/100</span>
      </div>
      {_bar(m.complexity_score, accent)}
    </div>
  </div>

  <!-- Stat grid -->
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));
              gap:10px;margin-bottom:16px">
    {"".join(
        f'<div style="background:#ffffff88;border:1px solid #e5e7eb;border-radius:8px;'
        f'padding:10px 14px">'
        f'<div style="font-size:11px;color:#9ca3af;font-weight:600;text-transform:uppercase'
        f';letter-spacing:.05em">{label}</div>'
        f'<div style="font-size:18px;font-weight:700;color:#111827;margin-top:2px">{value}</div>'
        f'</div>'
        for label, value in [
            ("⭐ Stars",       f"{m.stars:,}"),
            ("🍴 Forks",       f"{m.forks:,}"),
            ("👥 Contributors", f"{m.contributor_count}"),
            ("📝 Commits 90d", f"{m.commits_90d}"),
            ("✅ Issues 90d",  f"{m.issues_closed_90d}"),
            ("🔀 PRs 90d",     f"{m.prs_merged_90d}"),
            ("📄 Files",       f"{m.file_count:,}"),
            ("🌐 Languages",   f"{m.language_count}"),
        ]
    )}
  </div>

  <!-- Languages -->
  <div style="margin-bottom:12px">
    <span style="font-size:12px;font-weight:600;color:#6b7280;
                 text-transform:uppercase;letter-spacing:.05em">Languages: </span>
    {_lang_pills(m.languages)}
  </div>

  <!-- Dependency files -->
  <div>
    <span style="font-size:12px;font-weight:600;color:#6b7280;
                 text-transform:uppercase;letter-spacing:.05em">Dependency files: </span>
    <span style="font-size:13px;color:#374151">{dep_list}</span>
  </div>

  {note_html}
</div>
"""


def generate_html(results: list[RepoMetrics], output_path: str) -> None:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total        = len(results)
    errors       = sum(1 for r in results if r.fetch_error)
    ok           = total - errors

    difficulty_counts = {"Beginner": 0, "Intermediate": 0, "Advanced": 0}
    for r in results:
        if not r.fetch_error:
            difficulty_counts[r.difficulty] = difficulty_counts.get(r.difficulty, 0) + 1

    cards = "\n".join(_card(r) for r in results)

    summary_pills = "".join(
        f'<span style="background:{BADGE[d][1]};color:#fff;padding:6px 16px;'
        f'border-radius:99px;font-size:14px;font-weight:700;margin:4px">'
        f'{BADGE[d][0]} {d}: {n}</span>'
        for d, n in difficulty_counts.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GitHub Repository Intelligence Report</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f3f4f6; color: #1f2937; padding: 32px 16px; }}
    .container {{ max-width: 860px; margin: 0 auto; }}
    h1 {{ font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 6px; }}
    .meta {{ color: #6b7280; font-size: 14px; margin-bottom: 32px; }}
    .summary {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
                padding: 24px; margin-bottom: 32px; }}
    .formula {{ background: #1e1e2e; color: #cdd6f4; border-radius: 10px;
                padding: 20px 24px; margin-bottom: 32px; font-size: 13px;
                line-height: 1.7; white-space: pre-wrap; font-family: monospace; }}
    a {{ color: #6366f1; }}
  </style>
</head>
<body>
<div class="container">

  <h1>🔬 GitHub Repository Intelligence Report</h1>
  <p class="meta">Generated {generated_at} · {ok} repositories analyzed · {errors} error(s)</p>

  <div class="summary">
    <h2 style="font-size:16px;margin-bottom:12px;color:#374151">Summary</h2>
    <div style="display:flex;flex-wrap:wrap;gap:6px">{summary_pills}</div>
  </div>

  <div class="formula">── Scoring Formulas ──────────────────────────────────────────────────

Activity Score (0–100):
  raw = (commits_90d × 0.40) + (contributors × 0.30)
      + (issues_closed_90d × 0.20) + (prs_merged_90d × 0.10)
  score = min(raw, 100)

Complexity Score (0–100):
  raw = (file_count/10 × 0.35) + (language_count×5 × 0.40)
      + (dep_file_count×8 × 0.25)
  score = min(raw, 100)

Difficulty:
  Beginner     → complexity ≤ 25 AND contributors ≤ 10
  Advanced     → complexity ≥ 70 OR contributors ≥ 100
  Intermediate → everything else</div>

  {cards}

</div>
</body>
</html>
"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"\n  ✓  HTML report → {output_path}")


def generate_json(results: list[RepoMetrics], output_path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repositories": [to_dict(r) for r in results],
    }
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  ✓  JSON report → {output_path}")
