from config import report_path

def update_XT_down_section(results, place):

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()

    content_html = "<h2>Download X tier data results</h2>"

    for key, tickers in results.items():
        content_html += f"<h3>{key} ({len(tickers)})</h3><ul>"
        for t in tickers:
            content_html += f"<li>{t}</li>"
        content_html += "</ul>"

    html = html.replace(place, content_html)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)