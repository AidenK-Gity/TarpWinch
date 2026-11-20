"""
Turns a Markdown doc into a printable PDF with headless Chrome (the v3 guide PDF was made the same way).
Usage: python tools/md_to_pdf.py "V4/docs/Pool Cover Winch v4 Build Guide.md"   (needs: pip install markdown)
Writes the PDF next to the .md file.
"""
import os
import subprocess
import sys
import tempfile
import markdown

CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
CSS = """
@page { size: Letter; margin: 0.7in 0.75in; }
body { font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 22pt; margin: 0 0 4pt; } h2 { font-size: 14pt; margin: 18pt 0 6pt; border-bottom: 1px solid #ddd; padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 4pt 6pt; text-align: left; vertical-align: top; } th { background: #f3f3f3; }
code { font-family: Consolas, monospace; font-size: 9.5pt; background: #f4f4f4; padding: 0 2pt; }
pre { background: #f4f4f4; padding: 6pt; font-size: 9pt; white-space: pre-wrap; }
li { margin: 2pt 0; }
"""


def main(md_path):
    md_path = os.path.abspath(md_path)
    text = open(md_path, encoding="utf-8").read()
    title = text.splitlines()[0].lstrip("# ").strip()
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    html = "<!doctype html><html><head><meta charset='utf-8'><title>%s</title><style>%s</style></head><body>%s</body></html>" % (title, CSS, body)
    pdf = os.path.splitext(md_path)[0] + ".pdf"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp = f.name
    chrome = next(c for c in CHROME if os.path.exists(c))
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + pdf, "file:///" + tmp.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(tmp)
    print("wrote", pdf)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
