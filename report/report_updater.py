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

    html = html.replace(location, content_html)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

def update_filter_section(results, location, tier, stats):

    # stats_html = build_filter_stats_html(stats)

    content_html = f"""
<h2>Filter {tier} - tier data results</h2>

{build_filter_stats_html(stats)}

<table style="border-collapse:collapse; width:100%;">
<tr style="background:#eee;">
<th>Ticker</th>
<th>20D Return</th>
<th>R² Trend</th>
<th>ATR %</th>
<th>Turnover</th>
<th>Compression</th>
</tr>
"""

    for ticker, m in results:
        content_html += f"""
<tr>
<td>{ticker}</td>
<td>{m['ret_20d']:.2%}</td>
<td>{m['trend_r2']:.2f}</td>
<td>{m['atr_pct']:.2%}</td>
<td>{m['avg_turnover']:,.0f}</td>
<td>{m['compression_ratio']:.2f}</td>
</tr>
"""

    content_html += "</table>"
    content_html += f"<p><b>Znaleziono: {len(results)} spółek</b></p>"
    write_section(location, content_html)

def update_2T_filter_section(results, location, tier):

    content_html = f"""
<h2>Filter {tier} - intraday confirmation</h2>

<table style="border-collapse:collapse; width:100%;">
<tr style="background:#eee;">
<th>Ticker</th>
<th>1D Return</th>
<th>R² Trend</th>
<th>Volume Ratio</th>
<th>Compression</th>
<th>Dist From High</th>
</tr>
"""

    for ticker, m in results:
        content_html += f"""
<tr>
<td>{ticker}</td>
<td>{m['ret_1d']:.2%}</td>
<td>{m['trend_r2']:.2f}</td>
<td>{m['vol_ratio']:.2f}</td>
<td>{m['compression_ratio']:.2f}</td>
<td>{m['dist_from_high']:.2%}</td>
</tr>
"""

    content_html += "</table>"
    content_html += f"<p><b>Znaleziono: {len(results)} spółek</b></p>"
    write_section(location, content_html)

def update_3T_filter_section(results, location, tier):

    content_html = f"""
<h2>Filter {tier} - breakout candidates</h2>

<th>Rank</th>
<th>Ticker</th>
<th>Score</th>
<th>Compression</th>
<th>Dist From High</th>
<th>Volume Ratio</th>
<th>R² Trend</th>
<th>ATR</th>
"""

    for i, (ticker, m) in enumerate(results, start=1):
        content_html += f"""
<tr>
<td>{i}</td>
<td>{ticker}</td>
<td>{m['score']:.2f}</td>
<td>{m['compression_ratio']:.2f}</td>
<td>{m['dist_from_high']:.2%}</td>
<td>{m['vol_ratio']:.2f}</td>
<td>{m['trend_r2']:.2f}</td>
<td>{m['atr14']:.3f}</td>
</tr>
"""

    content_html += "</table>"
    content_html += f"<p><b>Znaleziono: {len(results)} spółek</b></p>"
    write_section(location, content_html)