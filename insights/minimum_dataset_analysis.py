# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo"]
# ///

"""Iris Dataset Analysis — Full embedded data, English, mixed text and figures."""
# marimo.App (for directory scanner)

import marimo as mo

app = mo.App(width="full")


@app.cell
def _():
    import marimo as mo

    def _row(sl, sw, pl, pw, sp):
        return {"sepal_length": sl, "sepal_width": sw, "petal_length": pl, "petal_width": pw, "species": sp}

    # Full Iris dataset (150 samples, 50 per species) — embedded, no external fetch
    iris_data = [
        _row(5.1, 3.5, 1.4, 0.2, "Setosa"),
        _row(4.9, 3.0, 1.4, 0.2, "Setosa"),
        _row(4.7, 3.2, 1.3, 0.2, "Setosa"),
        _row(4.6, 3.1, 1.5, 0.2, "Setosa"),
        _row(5.0, 3.6, 1.4, 0.2, "Setosa"),
        _row(5.4, 3.9, 1.7, 0.4, "Setosa"),
        _row(4.6, 3.4, 1.4, 0.3, "Setosa"),
        _row(5.0, 3.4, 1.5, 0.2, "Setosa"),
        _row(4.4, 2.9, 1.4, 0.2, "Setosa"),
        _row(4.9, 3.1, 1.5, 0.1, "Setosa"),
        _row(5.4, 3.7, 1.5, 0.2, "Setosa"),
        _row(4.8, 3.4, 1.6, 0.2, "Setosa"),
        _row(4.8, 3.0, 1.4, 0.1, "Setosa"),
        _row(4.3, 3.0, 1.1, 0.1, "Setosa"),
        _row(5.8, 4.0, 1.2, 0.2, "Setosa"),
        _row(5.7, 4.4, 1.5, 0.4, "Setosa"),
        _row(5.4, 3.9, 1.3, 0.4, "Setosa"),
        _row(5.1, 3.5, 1.4, 0.3, "Setosa"),
        _row(5.7, 3.8, 1.7, 0.3, "Setosa"),
        _row(5.1, 3.8, 1.5, 0.3, "Setosa"),
        _row(5.4, 3.4, 1.7, 0.2, "Setosa"),
        _row(5.1, 3.7, 1.5, 0.4, "Setosa"),
        _row(4.6, 3.6, 1.0, 0.2, "Setosa"),
        _row(5.1, 3.3, 1.7, 0.5, "Setosa"),
        _row(4.8, 3.4, 1.9, 0.2, "Setosa"),
        _row(5.0, 3.0, 1.6, 0.2, "Setosa"),
        _row(5.0, 3.4, 1.6, 0.4, "Setosa"),
        _row(5.2, 3.5, 1.5, 0.2, "Setosa"),
        _row(5.2, 3.4, 1.4, 0.2, "Setosa"),
        _row(4.7, 3.2, 1.6, 0.2, "Setosa"),
        _row(4.8, 3.1, 1.6, 0.2, "Setosa"),
        _row(5.4, 3.4, 1.5, 0.4, "Setosa"),
        _row(5.2, 4.1, 1.5, 0.1, "Setosa"),
        _row(5.5, 4.2, 1.4, 0.2, "Setosa"),
        _row(4.9, 3.1, 1.5, 0.1, "Setosa"),
        _row(5.0, 3.2, 1.2, 0.2, "Setosa"),
        _row(5.5, 3.5, 1.3, 0.2, "Setosa"),
        _row(4.9, 3.1, 1.5, 0.1, "Setosa"),
        _row(4.4, 3.0, 1.3, 0.2, "Setosa"),
        _row(5.1, 3.4, 1.5, 0.2, "Setosa"),
        _row(5.0, 3.5, 1.3, 0.3, "Setosa"),
        _row(4.5, 2.3, 1.3, 0.3, "Setosa"),
        _row(4.4, 3.2, 1.3, 0.2, "Setosa"),
        _row(5.0, 3.5, 1.6, 0.6, "Setosa"),
        _row(5.1, 3.8, 1.9, 0.4, "Setosa"),
        _row(4.8, 3.0, 1.4, 0.3, "Setosa"),
        _row(5.1, 3.8, 1.6, 0.2, "Setosa"),
        _row(4.6, 3.2, 1.4, 0.2, "Setosa"),
        _row(5.3, 3.7, 1.5, 0.2, "Setosa"),
        _row(5.0, 3.3, 1.4, 0.2, "Setosa"),
        _row(7.0, 3.2, 4.7, 1.4, "Versicolor"),
        _row(6.4, 3.2, 4.5, 1.5, "Versicolor"),
        _row(6.9, 3.1, 4.9, 1.5, "Versicolor"),
        _row(5.5, 2.3, 4.0, 1.3, "Versicolor"),
        _row(6.5, 2.8, 4.6, 1.5, "Versicolor"),
        _row(5.7, 2.8, 4.5, 1.3, "Versicolor"),
        _row(6.3, 3.3, 4.7, 1.6, "Versicolor"),
        _row(4.9, 2.4, 3.3, 1.0, "Versicolor"),
        _row(6.6, 2.9, 4.6, 1.3, "Versicolor"),
        _row(5.2, 2.7, 3.9, 1.4, "Versicolor"),
        _row(5.0, 2.0, 3.5, 1.0, "Versicolor"),
        _row(5.9, 3.0, 4.2, 1.5, "Versicolor"),
        _row(6.0, 2.2, 4.0, 1.0, "Versicolor"),
        _row(6.1, 2.9, 4.7, 1.4, "Versicolor"),
        _row(5.6, 2.9, 3.6, 1.3, "Versicolor"),
        _row(6.7, 3.1, 4.4, 1.4, "Versicolor"),
        _row(5.6, 3.0, 4.5, 1.5, "Versicolor"),
        _row(5.8, 2.7, 4.1, 1.0, "Versicolor"),
        _row(6.2, 2.2, 4.5, 1.5, "Versicolor"),
        _row(5.6, 2.5, 3.9, 1.1, "Versicolor"),
        _row(5.9, 3.2, 4.8, 1.8, "Versicolor"),
        _row(6.1, 2.8, 4.0, 1.3, "Versicolor"),
        _row(6.3, 2.5, 4.9, 1.5, "Versicolor"),
        _row(6.1, 2.8, 4.7, 1.2, "Versicolor"),
        _row(6.4, 2.9, 4.3, 1.3, "Versicolor"),
        _row(6.6, 3.0, 4.4, 1.4, "Versicolor"),
        _row(6.8, 2.8, 4.8, 1.4, "Versicolor"),
        _row(6.7, 3.0, 5.0, 1.7, "Versicolor"),
        _row(6.0, 2.9, 4.5, 1.5, "Versicolor"),
        _row(5.7, 2.6, 3.5, 1.0, "Versicolor"),
        _row(5.5, 2.4, 3.8, 1.1, "Versicolor"),
        _row(5.5, 2.4, 3.7, 1.0, "Versicolor"),
        _row(5.8, 2.7, 3.9, 1.2, "Versicolor"),
        _row(6.0, 2.7, 5.1, 1.6, "Versicolor"),
        _row(5.4, 3.0, 4.5, 1.5, "Versicolor"),
        _row(6.0, 3.4, 4.5, 1.6, "Versicolor"),
        _row(6.7, 3.1, 4.7, 1.5, "Versicolor"),
        _row(6.3, 2.3, 4.4, 1.3, "Versicolor"),
        _row(5.6, 3.0, 4.1, 1.3, "Versicolor"),
        _row(5.5, 2.5, 4.0, 1.3, "Versicolor"),
        _row(5.5, 2.6, 4.4, 1.2, "Versicolor"),
        _row(6.1, 3.0, 4.6, 1.4, "Versicolor"),
        _row(5.8, 2.6, 4.0, 1.2, "Versicolor"),
        _row(5.0, 2.3, 3.3, 1.0, "Versicolor"),
        _row(5.6, 2.7, 4.2, 1.3, "Versicolor"),
        _row(5.7, 3.0, 4.2, 1.2, "Versicolor"),
        _row(5.7, 2.9, 4.2, 1.3, "Versicolor"),
        _row(6.2, 2.9, 4.3, 1.3, "Versicolor"),
        _row(5.1, 2.5, 3.0, 1.1, "Versicolor"),
        _row(5.7, 2.8, 4.1, 1.3, "Versicolor"),
        _row(6.3, 3.3, 6.0, 2.5, "Virginica"),
        _row(5.8, 2.7, 5.1, 1.9, "Virginica"),
        _row(7.1, 3.0, 5.9, 2.1, "Virginica"),
        _row(6.3, 2.9, 5.6, 1.8, "Virginica"),
        _row(6.5, 3.0, 5.8, 2.2, "Virginica"),
        _row(7.6, 3.0, 6.6, 2.1, "Virginica"),
        _row(4.9, 2.5, 4.5, 1.7, "Virginica"),
        _row(7.3, 2.9, 6.3, 1.8, "Virginica"),
        _row(6.7, 2.5, 5.8, 1.8, "Virginica"),
        _row(7.2, 3.6, 6.1, 2.5, "Virginica"),
        _row(6.5, 3.2, 5.1, 2.0, "Virginica"),
        _row(6.4, 2.7, 5.3, 1.9, "Virginica"),
        _row(6.8, 3.0, 5.5, 2.1, "Virginica"),
        _row(5.7, 2.5, 5.0, 2.0, "Virginica"),
        _row(5.8, 2.8, 5.1, 2.4, "Virginica"),
        _row(6.4, 3.2, 5.3, 2.3, "Virginica"),
        _row(6.5, 3.0, 5.5, 1.8, "Virginica"),
        _row(7.7, 3.8, 6.7, 2.2, "Virginica"),
        _row(7.7, 2.6, 6.9, 2.3, "Virginica"),
        _row(6.0, 2.2, 5.0, 1.5, "Virginica"),
        _row(6.9, 3.2, 5.7, 2.3, "Virginica"),
        _row(5.6, 2.8, 4.9, 2.0, "Virginica"),
        _row(7.7, 2.8, 6.7, 2.0, "Virginica"),
        _row(6.3, 2.7, 4.9, 1.8, "Virginica"),
        _row(6.7, 3.3, 5.7, 2.1, "Virginica"),
        _row(7.2, 3.2, 6.0, 1.8, "Virginica"),
        _row(6.2, 2.8, 4.8, 1.8, "Virginica"),
        _row(6.1, 3.0, 4.9, 1.8, "Virginica"),
        _row(6.4, 2.8, 5.6, 2.1, "Virginica"),
        _row(7.2, 3.0, 5.8, 1.6, "Virginica"),
        _row(7.4, 2.8, 6.1, 1.9, "Virginica"),
        _row(7.9, 3.8, 6.4, 2.0, "Virginica"),
        _row(6.4, 2.8, 5.6, 2.2, "Virginica"),
        _row(6.3, 2.8, 5.1, 1.5, "Virginica"),
        _row(6.1, 2.6, 5.6, 1.4, "Virginica"),
        _row(7.7, 3.0, 6.1, 2.3, "Virginica"),
        _row(6.3, 3.4, 5.6, 2.4, "Virginica"),
        _row(6.4, 3.1, 5.5, 1.8, "Virginica"),
        _row(6.0, 3.0, 4.8, 1.8, "Virginica"),
        _row(6.9, 3.1, 5.4, 2.1, "Virginica"),
        _row(6.7, 3.1, 5.6, 2.4, "Virginica"),
        _row(6.9, 3.1, 5.1, 2.3, "Virginica"),
        _row(5.8, 2.7, 5.1, 1.9, "Virginica"),
        _row(6.8, 3.2, 5.9, 2.3, "Virginica"),
        _row(6.7, 3.3, 5.7, 2.5, "Virginica"),
        _row(6.7, 3.0, 5.2, 2.3, "Virginica"),
        _row(6.3, 2.5, 5.0, 1.9, "Virginica"),
        _row(6.5, 3.0, 5.2, 2.0, "Virginica"),
        _row(6.2, 3.4, 5.4, 2.3, "Virginica"),
        _row(5.9, 3.0, 5.1, 1.8, "Virginica"),
    ]
    return (iris_data, mo)


@app.cell
def _(iris_data, mo):
    _n = len(iris_data)
    _counts = {}
    for _r in iris_data:
        _counts[_r["species"]] = _counts.get(_r["species"], 0) + 1
    _avgs = {}
    for _k in ["sepal_length", "sepal_width", "petal_length", "petal_width"]:
        _avgs[_k] = sum(_r[_k] for _r in iris_data) / _n
    _max_c = max(_counts.values())
    _pal = {"Setosa": "#e11d48", "Versicolor": "#0891b2", "Virginica": "#4f46e5"}
    _default_fill = "#64748b"
    _lines = []
    _y = 28
    for _s, _c in _counts.items():
        _w = int((_c / _max_c) * 180)
        _lines.append(
            f'<text x="8" y="{_y}" font-size="12" fill="#334155">{_s}</text>'
            f'<rect x="95" y="{_y - 12}" rx="4" width="{_w}" height="18" fill="{_pal.get(_s, _default_fill)}"/>'
            f'<text x="{100 + _w}" y="{_y}" font-size="11" fill="#0f172a">{_c}</text>'
        )
        _y += 32
    _svg_intro = f'<svg width="280" height="{_y + 8}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f8fafc"/><text x="8" y="16" font-size="12" font-weight="bold" fill="#1e293b">Species count</text>{"".join(_lines)}</svg>'
    intro = mo.vstack(
        [
            mo.md(
                "# Iris Dataset Analysis\n\n"
                "Classic **Fisher's Iris** dataset: 150 samples (50 per species), 4 numeric features. "
                "Data is **fully embedded** in this notebook — no external fetch."
            ),
            mo.hstack(
                [
                    mo.md(
                        f"**Dataset overview**  \n"
                        f"Samples: **{_n}**  \n"
                        f"Features: sepal length/width, petal length/width (cm)  \n"
                        f"Species: **{', '.join(f'{s} ({c})' for s, c in _counts.items())}**  \n"
                        f"Overall means: sepal length {_avgs['sepal_length']:.2f}, petal length {_avgs['petal_length']:.2f}."
                    ),
                    mo.Html(_svg_intro),
                ],
                widths=[0.55, 0.45],
                gap=1.0,
            ),
        ],
        gap=0.75,
    )
    return (intro,)


@app.cell
def _(iris_data, mo):
    _caption = mo.md(" *Table: first 20 rows of the embedded dataset (150 rows total).*")
    data_section = mo.vstack(
        [
            mo.md("## Data preview"),
            mo.ui.table(iris_data[:20], label="Iris (first 20)", selection=None),
            _caption,
        ],
        gap=0.5,
    )
    return (data_section,)


@app.cell
def _(iris_data, mo):
    _colors = {"Setosa": "#e11d48", "Versicolor": "#0891b2", "Virginica": "#4f46e5"}
    _pl = [r["petal_length"] for r in iris_data]
    _pw = [r["petal_width"] for r in iris_data]
    _min_pl, _max_pl = min(_pl), max(_pl)
    _min_pw, _max_pw = min(_pw), max(_pw)

    def _s(v, lo, hi, a, b):
        return a + (v - lo) / (hi - lo) * (b - a) if hi != lo else a

    _pts = []
    for _r in iris_data:
        _x = _s(_r["petal_length"], _min_pl, _max_pl, 50, 420)
        _y = _s(_r["petal_width"], _max_pw, _min_pw, 35, 300)
        _pts.append(
            f'<circle cx="{_x:.1f}" cy="{_y:.1f}" r="5" fill="{_colors.get(_r["species"], "#999")}" stroke="white" stroke-width="1" opacity="0.85"/>'
        )
    _leg = "".join(
        f'<circle cx="{60 + _i * 130}" cy="318" r="4" fill="{_c}"/><text x="{70 + _i * 130}" y="322" font-size="10" fill="#334155">{_s}</text>'
        for _i, (_s, _c) in enumerate(_colors.items())
    )
    _svg = f'<svg width="480" height="340" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f8fafc"/><text x="160" y="18" font-size="13" font-weight="bold" fill="#1e293b">Petal length vs width</text><line x1="50" y1="300" x2="430" y2="300" stroke="#cbd5e1" stroke-width="1"/><line x1="50" y1="35" x2="50" y2="300" stroke="#cbd5e1" stroke-width="1"/><text x="50" y="315" font-size="9" fill="#64748b">{_min_pl:.1f}</text><text x="415" y="315" font-size="9" fill="#64748b">{_max_pl:.1f}</text><text x="220" y="332" font-size="10" fill="#334155">Petal length (cm)</text><text x="18" y="300" font-size="9" fill="#64748b">{_min_pw:.1f}</text><text x="18" y="40" font-size="9" fill="#64748b">{_max_pw:.1f}</text>{"".join(_pts)}{_leg}</svg>'
    scatter_block = mo.vstack(
        [
            mo.md(
                "## Petal dimensions\n\nPetal length and width separate **Setosa** (small petals) from the other two species; **Versicolor** and **Virginica** overlap but remain partly separable."
            ),
            mo.Html(_svg),
        ],
        gap=0.5,
    )
    return (scatter_block,)


@app.cell
def _(iris_data, mo):
    _by_species = {"Setosa": [], "Versicolor": [], "Virginica": []}
    for _r in iris_data:
        _by_species[_r["species"]].append(_r)
    _means = {}
    for _sp, _rows in _by_species.items():
        if _rows:
            _means[_sp] = {
                f: sum(_x[f] for _x in _rows) / len(_rows)
                for f in ["sepal_length", "sepal_width", "petal_length", "petal_width"]
            }
    _fnames = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    _labels = ["Sepal length", "Sepal width", "Petal length", "Petal width"]
    _cols = {"Setosa": "#e11d48", "Versicolor": "#0891b2", "Virginica": "#4f46e5"}
    _bars = []
    _x0 = 55
    for _i, _f in enumerate(_fnames):
        _g = f'<text x="{_x0 + _i * 105 + 8}" y="268" font-size="9" fill="#334155">{_labels[_i].replace(" ", "&#8203;")}</text>'
        for _j, _sp in enumerate(["Setosa", "Versicolor", "Virginica"]):
            _v = _means[_sp][_f]
            _ht = int((_v / 8) * 200)
            _g += f'<rect x="{_x0 + _i * 105 + _j * 22}" y="{248 - _ht}" width="18" height="{_ht}" fill="{_cols[_sp]}" rx="2"/>'
        _bars.append(_g)
    _leg2 = "".join(
        f'<rect x="{380 + _i * 65}" y="14" width="10" height="10" fill="{_c}" rx="1"/><text x="{393 + _i * 65}" y="22" font-size="9" fill="#334155">{_s}</text>'
        for _i, (_s, _c) in enumerate(_cols.items())
    )
    _svg2 = f'<svg width="480" height="290" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f8fafc"/><text x="140" y="18" font-size="13" font-weight="bold" fill="#1e293b">Mean feature value by species (cm)</text><line x1="45" y1="248" x2="45" y2="48" stroke="#cbd5e1" stroke-width="1"/><line x1="45" y1="248" x2="430" y2="248" stroke="#cbd5e1" stroke-width="1"/>{"".join(_bars)}{_leg2}</svg>'
    means_block = mo.vstack(
        [
            mo.md(
                "## Feature means by species\n\nAll four features differ across species; petal dimensions show the largest gaps and are most useful for classification."
            ),
            mo.Html(_svg2),
        ],
        gap=0.5,
    )
    return (means_block,)


@app.cell
def _(data_section, intro, means_block, mo, scatter_block):
    _summary = mo.md(
        "## Summary\n\n"
        "- **Setosa** is linearly separable (small petals).  \n"
        "- **Versicolor** and **Virginica** overlap; classification is harder but still feasible.  \n"
        "- The dataset is well-suited for teaching classification (e.g. KNN, SVM, decision trees) and exploratory visualization.  \n"
        "---  \n"
        "*Visualizations use inline SVG; the full 150-row dataset is embedded in this notebook.*"
    )
    page = mo.vstack(
        [
            intro,
            data_section,
            mo.hstack([scatter_block, means_block], widths=[0.5, 0.5], gap=1.0),
            _summary,
        ],
        gap=1.5,
    )
    page  # noqa: B018  # last expression for marimo display
    return (page,)


if __name__ == "__main__":
    app.run()
