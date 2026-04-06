from datetime import datetime

from stock_scanner.config import report_path


def create_empty_report() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Stock Scanner Report</title>

<style>
body {{
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    margin: 0;
}}

.header {{
    background: #1e2228;
    color: white;
    padding: 20px;
}}

.tabs {{
    display: flex;
    background: #2c313a;
}}

.tab {{
    padding: 15px 20px;
    cursor: pointer;
    color: white;
}}

.tab:hover {{
    background: #3a404a;
}}

.tab.active {{
    background: #4CAF50;
}}

.content {{
    display: none;
    padding: 30px;
}}

.content.active {{
    display: block;
}}

.section-box {{
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}}

th, td {{
    padding: 6px 10px;
}}

th {{
    text-align: right;
}}

td {{
    text-align: right;
}}

th:first-child,
td:first-child {{
    text-align: left;
}}
</style>

<script>
function openTab(tabId) {{
    var contents = document.getElementsByClassName("content");
    var tabs = document.getElementsByClassName("tab");

    for (var i = 0; i < contents.length; i++) {{
        contents[i].classList.remove("active");
        tabs[i].classList.remove("active");
    }}

    document.getElementById(tabId).classList.add("active");
    document.getElementById("tab-" + tabId).classList.add("active");
}}
</script>

</head>
<body>

<div class="header">
<h1>📊 Stock Scanner Report</h1>
<p>Data wygenerowania: {now}</p>
</div>

<div class="tabs">
<div class="tab active" id="tab-d1download" onclick="openTab('d1download')">Pobieranie GPW XTB</div>
<div class="tab" id="tab-d1analysis" onclick="openTab('d1analysis')">Analiza 1D</div>
<div class="tab" id="tab-m15download" onclick="openTab('m15download')">Pobieranie 15m</div>
<div class="tab" id="tab-m15analysis" onclick="openTab('m15analysis')">Analiza 15m</div>
<div class="tab" id="tab-m5download" onclick="openTab('m5download')">Pobieranie 5m</div>
<div class="tab" id="tab-m5analysis" onclick="openTab('m5analysis')">Analiza 5m</div>
</div>

<div id="d1download" class="content active">
<div class="section-box" id="d1download-content">
<!-- T1_DOWNLOAD -->
</div>
</div>

<div id="d1analysis" class="content">
<div class="section-box" id="d1analysis-content">
<!-- T1_FILTER -->
</div>
</div>

<div id="m15download" class="content">
<div class="section-box" id="m15download-content">
<!-- T2_DOWNLOAD -->
</div>
</div>

<div id="m15analysis" class="content">
<div class="section-box" id="m15analysis-content">
<!-- T2_FILTER -->
</div>
</div>

<div id="m5download" class="content">
<div class="section-box" id="m5download-content">
<!-- T3_DOWNLOAD -->
</div>
</div>

<div id="m5analysis" class="content">
<div class="section-box" id="m5analysis-content">
<!-- T3_FILTER -->
</div>
</div>

</body>
</html>
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    return str(report_path)
