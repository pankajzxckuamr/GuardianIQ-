import markdown
import sys
import os
import re

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        h1, h2, h3, h4 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1rem;
        }}
        table th, table td {{
            padding: 8px 13px;
            border: 1px solid #dfe2e5;
        }}
        table tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        blockquote {{
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0 0 16px 0;
            background-color: #f9f9f9;
        }}
        code {{
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        }}
        .alert-box {{
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 4px;
            border-left: 4px solid;
            background-color: #f8f9fa;
        }}
        .alert-note {{ border-color: #0969da; }}
        .alert-warning {{ border-color: #bf8700; }}
        .alert-danger {{ border-color: #cf222e; }}
        
        @media print {{
            body {{
                padding: 0;
                max-width: 100%;
            }}
            table {{
                page-break-inside: auto;
            }}
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            h1, h2, h3 {{
                page-break-after: avoid;
            }}
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""

def replace_github_alerts(text):
    # Basic regex to catch Github style alerts and convert them to simple styled divs
    text = re.sub(r'> \[!NOTE\]\n> (.*?)\n', r'<div class="alert-box alert-note"><b>NOTE:</b> \1</div>\n', text)
    text = re.sub(r'> \[!WARNING\]\n> (.*?)\n', r'<div class="alert-box alert-warning"><b>WARNING:</b> \1</div>\n', text)
    text = re.sub(r'> \[!CAUTION\]\n> (.*?)\n', r'<div class="alert-box alert-danger"><b>CAUTION:</b> \1</div>\n', text)
    text = re.sub(r'> \[!IMPORTANT\]\n> (.*?)\n', r'<div class="alert-box alert-note"><b>IMPORTANT:</b> \1</div>\n', text)
    return text

def md_to_html(md_path, html_path):
    if not os.path.exists(md_path):
        print(f"Error: Could not find file {md_path}")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = replace_github_alerts(text)

    # Convert markdown to html (enabling tables and extra styling)
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code'])

    # Format the full html page
    title = os.path.basename(md_path).replace('.md', '')
    full_html = HTML_TEMPLATE.format(title=title, content=html_content)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"Successfully generated HTML: {html_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_html.py <input.md> <output.html>")
        sys.exit(1)
    
    md_to_html(sys.argv[1], sys.argv[2])
