"""PDF and HTML report generation (Streamlit-free)."""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

from utils import enrich_test_result, format_configured_viewport, safe_results_path, sanitize_filename

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    PDF_OK = True
except ImportError:
    PDF_OK = False
    A4 = canvas = cm = ImageReader = None


def build_report_filename(results, run_id, summary_only=True):
    """Build a sanitized PDF filename from results metadata."""
    total = len(results)
    passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    kind = 'summary' if summary_only else 'full'
    base = (
        f"VisualDiff_{run_id}_{total}tests_{passed}pass_{failed}fail_"
        f"{pass_rate:.0f}pr_{ts}_{kind}.pdf"
    )
    return sanitize_filename(base)


def _load_result_image(record, which, results_base=None):
    """Load a PIL image from memory or saved screenshot paths."""
    from PIL import Image as PILImage

    img = record.get(which)
    if img is not None:
        return img

    path_key = {
        'staging_screenshot': 'staging',
        'production_screenshot': 'production',
        'diff_image': 'diff',
    }.get(which, '')
    rel = record.get('screenshot_paths', {}).get(path_key)
    if rel and results_base is not None:
        fp = safe_results_path(results_base, rel)
        try:
            if fp and fp.exists():
                return PILImage.open(fp)
        except Exception:
            return None
    return None


def generate_pdf_report(results, run_id='run', summary_only=True, results_base=None):
    """Generate PDF bytes for a result set."""
    if not PDF_OK:
        raise RuntimeError("PDF generation requires reportlab")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    y = height - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Visual Regression Report")
    y -= 1.2 * cm
    c.setFont("Helvetica", 10)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(margin, y, f"Generated: {now}")
    y -= 0.7 * cm

    total = len(results)
    passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
    failed = sum(1 for r in results if not r.get('is_match') and not r.get('is_skipped', False))
    skipped = sum(1 for r in results if r.get('is_skipped', False))
    pass_rate = (passed / total * 100) if total > 0 else 0
    scored = [r.get('similarity_score', 0) for r in results if not r.get('is_skipped', False)]
    avg_similarity = (sum(scored) / len(scored)) if scored else 0
    browsers = sorted({r.get('browser', 'Unknown') for r in results})
    devices = sorted({r.get('device', 'Unknown') for r in results})

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Executive Summary")
    y -= 0.8 * cm
    c.setFont("Helvetica", 10)

    def draw_kv(label, value):
        nonlocal y
        c.drawString(margin, y, f"{label}:")
        c.drawString(margin + 4.5 * cm, y, str(value))
        y -= 0.6 * cm

    draw_kv("Run ID", run_id)
    draw_kv("Total Tests", total)
    draw_kv("Passed", passed)
    draw_kv("Failed", failed)
    draw_kv("Skipped", skipped)
    draw_kv("Pass Rate", f"{pass_rate:.1f}%")
    draw_kv("Average Similarity", f"{avg_similarity:.1f}%")
    draw_kv("Browsers", ", ".join(browsers) if browsers else "-")
    draw_kv("Devices", ", ".join(devices) if devices else "-")

    y -= 0.2 * cm
    c.line(margin, y, width - margin, y)
    y -= 0.6 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Tests (name | browser | device | score | status)")
    y -= 0.7 * cm
    c.setFont("Helvetica", 9)
    for r in results:
        if r.get('is_skipped', False):
            status = 'SKIP'
            score = 'N/A'
        else:
            status = 'PASS' if r.get('is_match') else 'FAIL'
            score = f"{r.get('similarity_score', 0):.1f}%"
        line = f"{r['test_name']} | {r['browser']} | {r['device']} | {score} | {status}"
        c.drawString(margin, y, line[:170])
        y -= 0.55 * cm
        if y < margin + 1.5 * cm:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 9)

    c.showPage()

    if summary_only:
        y = height - margin
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Summary Details")
        y -= 0.9 * cm
        c.setFont("Helvetica", 9)
        for r in results:
            status = 'SKIP' if r.get('is_skipped', False) else ('PASS' if r.get('is_match') else 'FAIL')
            score = 'N/A' if r.get('is_skipped', False) else f"{r.get('similarity_score', 0):.1f}%"
            line = f"{r['test_name']} | {r['browser']} | {r['device']} | {score} | {status}"
            c.drawString(margin, y, line[:170])
            y -= 0.55 * cm
            if y < margin + 1.0 * cm:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 9)
    else:
        from PIL import Image as PILImage
        from image_comparison import ImageComparator

        def draw_img_jpeg(pil_img, x, y_pos, max_w, max_h, quality=70):
            if not pil_img:
                return y_pos
            try:
                img = pil_img.convert('RGB')
                iw, ih = img.size
                scale = min(max_w / iw, max_h / ih, 1.0)
                dw, dh = int(iw * scale), int(ih * scale)
                if scale < 1.0:
                    img = img.resize((dw, dh), PILImage.Resampling.LANCZOS)
                buf = BytesIO()
                img.save(buf, format='JPEG', quality=quality, optimize=True)
                buf.seek(0)
                ir = ImageReader(buf)
                c.drawImage(ir, x, y_pos - dh, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                return y_pos - dh - 0.5 * cm
            except Exception:
                return y_pos

        comparator = ImageComparator()
        for idx, r in enumerate(results, 1):
            if idx > 1:
                c.showPage()
            y = height - margin
            c.setFont("Helvetica-Bold", 12)
            title = f"{idx}. {r['test_name']} - {r['browser']} ({r['device']})"
            c.drawString(margin, y, title)
            y -= 0.7 * cm
            c.setFont("Helvetica", 9)
            status = 'SKIP' if r.get('is_skipped', False) else ('PASS' if r.get('is_match') else 'FAIL')
            meta = f"Similarity: {r.get('similarity_score', 0):.1f}% | Status: {status}"
            c.drawString(margin, y, meta)
            y -= 0.5 * cm

            staging_img = _load_result_image(r, 'staging_screenshot', results_base)
            production_img = _load_result_image(r, 'production_screenshot', results_base)
            diff_img = r.get('diff_image') or _load_result_image(r, 'diff_image', results_base)

            overlay_img = None
            try:
                if staging_img is not None and production_img is not None:
                    overlay_img = comparator.create_overlay(staging_img, production_img, opacity=0.5)
            except Exception:
                overlay_img = None

            col_gap = 0.5 * cm
            col_w = (width - 2 * margin - col_gap) / 2
            row_h = (height - 5 * cm) / 3

            y1 = draw_img_jpeg(staging_img, margin, y, col_w, row_h)
            y2 = draw_img_jpeg(production_img, margin + col_w + col_gap, y, col_w, row_h)
            y = min(y1, y2)
            y = draw_img_jpeg(overlay_img, margin, y, width - 2 * margin, row_h, quality=65)
            y = draw_img_jpeg(diff_img, margin, y, width - 2 * margin, row_h, quality=65)

    c.save()
    buffer.seek(0)
    return buffer.read()


def _slugify(*parts):
    raw = "_".join(str(p) for p in parts)
    slug = re.sub(r'[^A-Za-z0-9_-]+', '_', raw).strip('_')
    return slug[:120] or 'test'


def _save_image(img, path: Path):
    if img is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='PNG')
    return True


def _status_label(result):
    if result.get('is_skipped', False):
        return 'Skipped', 'skip'
    if result.get('is_match'):
        return 'Pass', 'pass'
    return 'Fail', 'fail'


def generate_html_report(results, run_id, output_dir):
    """Write index.html and comparison images to output_dir."""
    output_dir = Path(output_dir)
    images_dir = output_dir / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)

    from image_comparison import ImageComparator

    comparator = ImageComparator()
    prepared = []

    for index, result in enumerate(results, 1):
        enrich_test_result(result)
        slug = _slugify(index, result.get('test_name'), result.get('browser'), result.get('device'))
        paths = {}

        staging = result.get('staging_screenshot')
        production = result.get('production_screenshot')
        diff = result.get('diff_image')

        if _save_image(staging, images_dir / f"{slug}_staging.png"):
            paths['staging'] = f"images/{slug}_staging.png"
        if _save_image(production, images_dir / f"{slug}_production.png"):
            paths['production'] = f"images/{slug}_production.png"
        if _save_image(diff, images_dir / f"{slug}_diff.png"):
            paths['diff'] = f"images/{slug}_diff.png"

        overlay = None
        try:
            if staging is not None and production is not None:
                overlay = comparator.create_overlay(staging, production, opacity=0.5)
        except Exception:
            overlay = None
        if _save_image(overlay, images_dir / f"{slug}_overlay.png"):
            paths['overlay'] = f"images/{slug}_overlay.png"

        status_text, status_class = _status_label(result)
        prepared.append({
            'index': index,
            'slug': slug,
            'paths': paths,
            'status_text': status_text,
            'status_class': status_class,
            'result': result,
        })

    total = len(results)
    passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
    failed = sum(1 for r in results if not r.get('is_match') and not r.get('is_skipped', False))
    skipped = sum(1 for r in results if r.get('is_skipped', False))
    pass_rate = (passed / total * 100) if total > 0 else 0
    scored = [r.get('similarity_score', 0) for r in results if not r.get('is_skipped', False)]
    avg_similarity = (sum(scored) / len(scored)) if scored else 0
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary_json = {
        'run_id': run_id,
        'generated_at': generated_at,
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'pass_rate': round(pass_rate, 1),
        'average_similarity': round(avg_similarity, 1),
    }
    (output_dir / 'summary.json').write_text(json.dumps(summary_json, indent=2), encoding='utf-8')

    cards_html = []
    for item in prepared:
        r = item['result']
        paths = item['paths']
        vp = format_configured_viewport(r)
        similarity = 'N/A' if r.get('is_skipped', False) else f"{r.get('similarity_score', 0):.1f}%"

        def img_block(path_key, label):
            rel = paths.get(path_key)
            if not rel:
                return f'<div class="panel empty"><p>{html.escape(label)} not available</p></div>'
            return (
                f'<div class="panel"><h4>{html.escape(label)}</h4>'
                f'<img src="{html.escape(rel)}" alt="{html.escape(label)}" loading="lazy"></div>'
            )

        side_by_side = ''
        if paths.get('staging') or paths.get('production'):
            side_by_side = (
                '<div class="grid two">'
                f'{img_block("staging", "Staging")}'
                f'{img_block("production", "Production")}'
                '</div>'
            )

        overlay_block = ''
        if paths.get('overlay'):
            overlay_block = (
                '<div class="view view-overlay">'
                f'{img_block("overlay", "Overlay (50% staging)")}'
                '</div>'
            )

        diff_block = ''
        if paths.get('diff'):
            diff_block = (
                '<div class="view view-diff">'
                f'{img_block("diff", "Difference")}'
                '<p class="hint">Red areas indicate visual differences.</p>'
                '</div>'
            )

        cards_html.append(f"""
        <article class="test-card" id="test-{item['index']}">
          <header>
            <h2>{item['index']}. {html.escape(r.get('test_name', 'Test'))}</h2>
            <span class="badge {item['status_class']}">{html.escape(item['status_text'])}</span>
          </header>
          <div class="meta">
            <span><strong>Browser:</strong> {html.escape(r.get('browser', '-'))}</span>
            <span><strong>Device:</strong> {html.escape(r.get('device', '-'))}</span>
            <span><strong>Viewport:</strong> {html.escape(vp)}</span>
            <span><strong>Similarity:</strong> {html.escape(similarity)}</span>
          </div>
          <div class="urls">
            <div><strong>Staging:</strong> <a href="{html.escape(r.get('staging_url', ''))}" target="_blank" rel="noopener">{html.escape(r.get('staging_url', ''))}</a></div>
            <div><strong>Production:</strong> <a href="{html.escape(r.get('production_url', ''))}" target="_blank" rel="noopener">{html.escape(r.get('production_url', ''))}</a></div>
          </div>
          <div class="tabs" role="tablist">
            <button class="tab active" data-target="test-{item['index']}-side">Side by Side</button>
            <button class="tab" data-target="test-{item['index']}-overlay">Overlay</button>
            <button class="tab" data-target="test-{item['index']}-diff">Difference</button>
          </div>
          <div class="view view-side active" id="test-{item['index']}-side">{side_by_side or '<p class="empty">No screenshots available.</p>'}</div>
          <div class="view view-overlay-pane" id="test-{item['index']}-overlay">{overlay_block or '<p class="empty">Overlay not available.</p>'}</div>
          <div class="view view-diff-pane" id="test-{item['index']}-diff">{diff_block or '<p class="empty">Diff not available.</p>'}</div>
        </article>
        """)

    rows_html = []
    for item in prepared:
        r = item['result']
        similarity = 'N/A' if r.get('is_skipped', False) else f"{r.get('similarity_score', 0):.1f}%"
        rows_html.append(
            f"<tr><td><a href=\"#test-{item['index']}\">{html.escape(r.get('test_name', ''))}</a></td>"
            f"<td>{html.escape(r.get('browser', ''))}</td>"
            f"<td>{html.escape(r.get('device', ''))}</td>"
            f"<td>{html.escape(similarity)}</td>"
            f"<td><span class=\"badge {item['status_class']}\">{html.escape(item['status_text'])}</span></td></tr>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visual Regression Report - {html.escape(run_id)}</title>
  <style>
    :root {{
      --green: #2f855a;
      --green-dark: #276749;
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --border: #e5e7eb;
      --pass: #def7ec;
      --fail: #fde8e8;
      --skip: #edf2f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header.page-header {{
      background: var(--card);
      border-left: 4px solid var(--green);
      padding: 1.5rem 2rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 2px rgba(0,0,0,.05);
    }}
    header.page-header h1 {{ margin: 0 0 .25rem; font-size: 1.6rem; }}
    header.page-header p {{ margin: 0; color: var(--muted); }}
    main {{ max-width: 1400px; margin: 0 auto; padding: 0 1.5rem 2rem; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .metric {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem;
    }}
    .metric .label {{ color: var(--muted); font-size: .85rem; }}
    .metric .value {{ font-size: 1.4rem; font-weight: 700; color: var(--green-dark); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 2rem;
    }}
    th, td {{ padding: .75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ background: #f3f4f6; font-size: .85rem; text-transform: uppercase; letter-spacing: .03em; }}
    .test-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }}
    .test-card header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: .75rem;
    }}
    .test-card h2 {{ margin: 0; font-size: 1.15rem; }}
    .meta, .urls {{ display: flex; flex-wrap: wrap; gap: .75rem 1.25rem; margin-bottom: .75rem; font-size: .92rem; }}
    .urls {{ flex-direction: column; gap: .35rem; word-break: break-all; }}
    .badge {{
      display: inline-block;
      padding: .2rem .6rem;
      border-radius: 999px;
      font-size: .8rem;
      font-weight: 700;
    }}
    .badge.pass {{ background: var(--pass); color: #03543f; }}
    .badge.fail {{ background: var(--fail); color: #9b1c1c; }}
    .badge.skip {{ background: var(--skip); color: #4a5568; }}
    .tabs {{ display: flex; gap: .5rem; margin: 1rem 0; flex-wrap: wrap; }}
    .tab {{
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      padding: .45rem .9rem;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }}
    .tab.active {{ background: var(--green); color: #fff; border-color: var(--green); }}
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    .grid.two {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
    }}
    .panel {{
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      background: #fff;
    }}
    .panel h4 {{ margin: 0; padding: .6rem .8rem; background: #f9fafb; border-bottom: 1px solid var(--border); }}
    .panel img {{ width: 100%; height: auto; display: block; }}
    .panel.empty, .empty {{ color: var(--muted); padding: 1rem; }}
    .hint {{ color: var(--muted); font-size: .85rem; margin: .5rem 0 0; }}
    a {{ color: var(--green-dark); }}
  </style>
</head>
<body>
  <header class="page-header">
    <h1>Visual Regression Report</h1>
    <p>Run <strong>{html.escape(run_id)}</strong> · Generated {html.escape(generated_at)}</p>
  </header>
  <main>
    <section class="metrics">
      <div class="metric"><div class="label">Total</div><div class="value">{total}</div></div>
      <div class="metric"><div class="label">Passed</div><div class="value">{passed}</div></div>
      <div class="metric"><div class="label">Failed</div><div class="value">{failed}</div></div>
      <div class="metric"><div class="label">Skipped</div><div class="value">{skipped}</div></div>
      <div class="metric"><div class="label">Pass Rate</div><div class="value">{pass_rate:.1f}%</div></div>
      <div class="metric"><div class="label">Avg Similarity</div><div class="value">{avg_similarity:.1f}%</div></div>
    </section>

    <table>
      <thead>
        <tr><th>Test</th><th>Browser</th><th>Device</th><th>Similarity</th><th>Status</th></tr>
      </thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>

    <section id="comparisons">
      <h2>Detailed Comparisons</h2>
      {''.join(cards_html)}
    </section>
  </main>
  <script>
    document.querySelectorAll('.test-card').forEach(card => {{
      const tabs = card.querySelectorAll('.tab');
      const views = card.querySelectorAll('.view, .view-overlay-pane, .view-diff-pane');
      tabs.forEach(tab => {{
        tab.addEventListener('click', () => {{
          tabs.forEach(t => t.classList.remove('active'));
          views.forEach(v => v.classList.remove('active'));
          tab.classList.add('active');
          const target = card.querySelector('#' + tab.dataset.target);
          if (target) target.classList.add('active');
        }});
      }});
    }});
  </script>
</body>
</html>
"""

    index_path = output_dir / 'index.html'
    index_path.write_text(page, encoding='utf-8')
    return index_path


def write_pdf_report(results, run_id, output_path, summary_only=False, results_base=None):
    """Generate and write a PDF report to disk."""
    pdf_bytes = generate_pdf_report(results, run_id, summary_only=summary_only, results_base=results_base)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return output_path
