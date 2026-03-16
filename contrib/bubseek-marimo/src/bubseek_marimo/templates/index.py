# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo"]
# ///

"""Bubseek Insights index — browse runtime notebooks and open the dashboard."""

# marimo.App (for directory scanner)
import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    insights_dir = Path(__file__).resolve().parent
    return insights_dir, mo


@app.cell
def _(insights_dir):
    notebooks = sorted(
        [path for path in insights_dir.glob("*.py") if path.name not in {"dashboard.py", "index.py"}],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return (notebooks,)


@app.cell
def _(mo, notebooks):
    hero = mo.md(
        """
<div style="padding: 1.1rem 1.2rem; border: 1px solid #d9e6ea; border-radius: 18px; background:
linear-gradient(135deg, #f8fbfc 0%, #f2f7f8 55%, #ffffff 100%);">
  <div style="font-size: 1.8rem; font-weight: 700; color: #17363b;">Bubseek Insights</div>
  <div style="margin-top: 0.45rem; color: #48656a;">Open the async dashboard, inspect generated notebooks, and treat the workspace as a live analysis gallery.</div>
</div>
"""
    )

    links = [
        "- [Open dashboard](/?file=dashboard.py)",
    ]
    if notebooks:
        links.append("")
        links.append("## Generated notebooks")
        links.extend(f"- [{path.stem}](/?file={path.name})" for path in notebooks)
    else:
        links.extend(["", "No generated notebooks yet. Use the dashboard to ask Bub for one."])

    page = mo.vstack([hero, mo.md("\n".join(links))], gap=1.0)
    page  # noqa: B018
    return (page,)


if __name__ == "__main__":
    app.run()
