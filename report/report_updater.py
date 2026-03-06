from config import report_path

def update_down_section(results, location, tier):

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()

    content_html = f"<h2>Download {tier} - tier data results</h2>"

    for key, tickers in results.items():
        content_html += f"<h3>{key} ({len(tickers)})</h3><ul>"
        for t in tickers:
            content_html += f"<li>{t}</li>"
        content_html += "</ul>"

    html = html.replace(location, content_html)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)


def update_filter_section(results, location, tier):

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()

    content_html = f"<h2>Filter {tier} - tier data results</h2>"

    for key, tickers in results.items():
        content_html += f"<h3>{key} ({len(tickers)})</h3><ul>"
        for t in tickers:
            content_html += f"<li>{t}</li>"
        content_html += "</ul>"

    html = html.replace(location, content_html)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)