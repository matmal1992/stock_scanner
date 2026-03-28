from config import report_path


def update_down_section(results, location, tier):

    content_html = f"<h2>Download {tier} - tier data results</h2>"

    for key, tickers in results.items():
        content_html += f"<h3>{key} ({len(tickers)})</h3><ul>"
        for t in tickers:
            content_html += f"<li>{t}</li>"
        content_html += "</ul>"

    write_section(location, content_html)


def build_filter_stats_html(stats):

    if stats is None:
        return ""

    total = stats["total"]

    html = "<h3>Filter diagnostics</h3>"
    html += "<ul>"
    html += f"<li>Total scanned: {total}</li>"
    html += f"<li>Passed filter: {stats['passed']}</li>"
    html += "</ul>"
    html += "<h4>Fail reasons</h4>"
    html += "<ul>"

    for key, value in stats["fails"].items():

        pct = (value / total * 100) if total else 0
        html += f"<li>{key}: {value} ({pct:.1f}%)</li>"

    html += "</ul>"

    return html


def write_section(location, content_html):

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace(str(location), content_html)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)


def update_filter_section(results, location, columns, stats=None):

    stats_html = build_filter_stats_html(stats)

    content_html = f"""

{stats_html}

<table style="border-collapse:collapse; width:100%;">
<tr style="background:#eee;">
"""

    for col_name, _ in columns:
        content_html += f"<th>{col_name}</th>"

    content_html += "</tr>"

    for i, (ticker, metrics) in enumerate(results, start=1):
        content_html += "<tr>"
        for _, value_fn in columns:
            value = value_fn(i, ticker, (metrics))
            content_html += f"<td>{value}</td>"
        content_html += "</tr>"

    content_html += "</table>"
    content_html += f"<p><b>Znaleziono: {len(results)} spółek</b></p>"

    write_section(location, content_html)
