from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


def md_to_pdf(md_path: str, pdf_path: Optional[str] = None) -> str:
    md_file = Path(md_path)
    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    if pdf_path is None:
        pdf_path = str(md_file.with_suffix(".pdf"))

    return _try_weasyprint(str(md_file), pdf_path) \
        or _try_pandoc(str(md_file), pdf_path) \
        or _try_fallback_pdf(str(md_file), pdf_path)


def _md_to_html_simple(md_text: str) -> str:
    import html as html_mod
    escaped = html_mod.escape(md_text)
    html_lines = []
    in_code = False
    for line in escaped.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html_lines.append(line)
            continue
        if stripped.startswith("#### "):
            html_lines.append(f"<h4>{stripped[5:]}</h4>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("> "):
            html_lines.append(f"<blockquote><p>{stripped[2:]}</p></blockquote>")
        elif stripped.startswith("- "):
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("| "):
            html_lines.append(line)
        elif stripped == "---":
            html_lines.append("<hr>")
        elif stripped == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif;
          max-width: 800px; margin: 2em auto; padding: 0 1em;
          line-height: 1.6; font-size: 11pt; }}
  h1 {{ font-size: 1.6em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
  h2 {{ font-size: 1.3em; color: #2c3e50; }}
  h3 {{ font-size: 1.1em; color: #34495e; }}
  pre {{ background: #f5f5f5; padding: 1em; border-radius: 4px; overflow-x: auto; }}
  code {{ font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 9pt; }}
  blockquote {{ border-left: 3px solid #ccc; margin: 0; padding: 0 1em; color: #666; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
  th {{ background: #f0f0f0; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
  a {{ color: #2980b9; text-decoration: none; }}
</style></head><body>
{''.join(html_lines)}
</body></html>"""
    return html


def _try_weasyprint(md_path: str, pdf_path: str) -> Optional[str]:
    try:
        import weasyprint
        from markdown import markdown
        with open(md_path) as f:
            md_text = f.read()
        html_text = markdown(md_text, extensions=["extra", "codehilite", "tables"])
        weasyprint.HTML(string=html_text).write_pdf(pdf_path)
        return pdf_path
    except ImportError:
        return None
    except Exception as e:
        print(f"  weasyprint failed: {e}", file=sys.stderr)
        return None


def _try_pandoc(md_path: str, pdf_path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["pandoc", md_path, "-o", pdf_path, "--pdf-engine=xelatex"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and Path(pdf_path).exists():
            return pdf_path
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _try_fallback_pdf(md_path: str, pdf_path: str) -> str:
    md_file = Path(md_path)
    html = _md_to_html_simple(md_file.read_text())
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
    except ImportError:
        try:
            import fpdf
            pdf = fpdf.FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            try:
                pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
                pdf.set_font("DejaVu", "", 10)
            except RuntimeError:
                pdf.set_font("Helvetica", "", 10)
            for line in md_file.read_text().split("\n"):
                pdf.cell(0, 6, line[:90], new_x="LMARGIN", new_y="NEXT")
            pdf.output(pdf_path)
        except Exception:
            html_path = str(md_file.with_suffix(".html"))
            Path(html_path).write_text(html)
            if not Path(pdf_path).exists():
                pdf_path = html_path
    return pdf_path
