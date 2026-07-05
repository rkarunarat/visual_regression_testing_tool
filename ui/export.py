"""Export results to ZIP and generate PDF reports."""
from datetime import datetime
from io import BytesIO
import zipfile

import streamlit as st

from ui.deps import (
    A4,
    ImageComparator,
    ImageReader,
    PDF_OK,
    ResultManager,
    canvas,
    cm,
)
from utils import safe_results_path, sanitize_filename


def export_selected_runs(run_ids, result_manager):
    """Write selected test_results/<run_id> trees into a single ZIP file."""
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for run_id in run_ids:
                run_dir = result_manager.results_dir / run_id
                if run_dir.exists():
                    for file_path in run_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = f"{run_id}/{file_path.relative_to(run_dir)}"
                            zip_file.write(file_path, arc_name)

        zip_buffer.seek(0)
        data = zip_buffer.read()
        st.download_button(
            label="Download Selected Runs",
            data=data,
            file_name="selected_test_runs.zip",
            mime="application/zip",
        )
        st.success("Export prepared! Use the button above to download.")

    except Exception as e:
        st.error(f"Error exporting runs: {e}")


def export_results(df):
    """Export current results as CSV plus associated screenshots into ZIP."""
    try:
        result_manager = ResultManager()
        results_base = result_manager.results_dir
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr("test_results.csv", csv_buffer.getvalue())

            for i, result in enumerate(st.session_state.test_results):
                test_folder = f"test_{i+1}_{result['test_name']}_{result['browser']}_{result['device']}"
                test_folder = test_folder.replace(" ", "_").replace("/", "_")

                staging_img = result.get('staging_screenshot')
                if staging_img is not None:
                    staging_bytes = BytesIO()
                    staging_img.save(staging_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/staging.png", staging_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('staging'):
                    try:
                        p = safe_results_path(results_base, result['screenshot_paths']['staging'])
                        if p and p.exists():
                            zip_file.write(p, f"{test_folder}/staging.png")
                    except Exception:
                        pass

                production_img = result.get('production_screenshot')
                if production_img is not None:
                    production_bytes = BytesIO()
                    production_img.save(production_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/production.png", production_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('production'):
                    try:
                        p = safe_results_path(results_base, result['screenshot_paths']['production'])
                        if p and p.exists():
                            zip_file.write(p, f"{test_folder}/production.png")
                    except Exception:
                        pass

                diff_img = result.get('diff_image')
                if diff_img is not None:
                    diff_bytes = BytesIO()
                    diff_img.save(diff_bytes, format='PNG')
                    zip_file.writestr(f"{test_folder}/diff.png", diff_bytes.getvalue())
                elif result.get('screenshot_paths', {}).get('diff'):
                    try:
                        p = safe_results_path(results_base, result['screenshot_paths']['diff'])
                        if p and p.exists():
                            zip_file.write(p, f"{test_folder}/diff.png")
                    except Exception:
                        pass

        zip_buffer.seek(0)
        data = zip_buffer.read()
        st.download_button(
            label="Download Results (ZIP)",
            data=data,
            file_name="visual_regression_results.zip",
            mime="application/zip",
        )
        st.success("Results exported successfully!")

    except Exception as e:
        st.error(f"Error exporting results: {str(e)}")


def build_pdf_filename(summary_only=True):
    """Build a sanitized PDF filename from current session results."""
    results = st.session_state.get('test_results', [])
    total = len(results)
    passed = sum(1 for r in results if r.get('is_match'))
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    test_id = st.session_state.get('current_test_id') or 'run'
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    kind = 'summary' if summary_only else 'full'
    base = (
        f"VisualDiff_{test_id}_{total}tests_{passed}pass_{failed}fail_"
        f"{pass_rate:.0f}pr_{ts}_{kind}.pdf"
    )
    return sanitize_filename(base)


def generate_pdf(summary_only=True):
    """Generate a PDF report from current session results."""
    if not PDF_OK:
        st.error("PDF generation is not available due to missing dependencies.")
        return b""
    try:
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

        results = st.session_state.get('test_results', [])
        total = len(results)
        passed = sum(1 for r in results if r.get('is_match'))
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        avg_similarity = (sum(r.get('similarity_score', 0) for r in results) / total) if total > 0 else 0
        browsers = sorted({r.get('browser', 'Unknown') for r in results})
        devices = sorted({r.get('device', 'Unknown') for r in results})
        run_id = st.session_state.get('current_test_id') or 'N/A'

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
            line = (
                f"{r['test_name']} | {r['browser']} | {r['device']} | "
                f"{r['similarity_score']:.1f}% | {'PASS' if r['is_match'] else 'FAIL'}"
            )
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
                line = (
                    f"{r['test_name']} | {r['browser']} | {r['device']} | "
                    f"{r['similarity_score']:.1f}% | {'PASS' if r['is_match'] else 'FAIL'}"
                )
                c.drawString(margin, y, line[:170])
                y -= 0.55 * cm
                if y < margin + 1.0 * cm:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", 9)
        else:
            from PIL import Image as PILImage

            def _load_img(record, which):
                img = record.get(which)
                if img is not None:
                    return img
                path_key = (
                    'staging' if which == 'staging_screenshot'
                    else 'production' if which == 'production_screenshot'
                    else 'diff'
                )
                p = record.get('screenshot_paths', {}).get(path_key)
                if p:
                    fp = safe_results_path(ResultManager().results_dir, p)
                    try:
                        if fp and fp.exists():
                            return PILImage.open(fp)
                    except Exception:
                        return None
                return None

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
                meta = (
                    f"Similarity: {r['similarity_score']:.1f}% | "
                    f"Status: {'PASS' if r['is_match'] else 'FAIL'}"
                )
                c.drawString(margin, y, meta)
                y -= 0.5 * cm

                staging_img = _load_img(r, 'staging_screenshot')
                production_img = _load_img(r, 'production_screenshot')
                diff_img = r.get('diff_image') or _load_img(r, 'diff_image')

                try:
                    is_mobile = 'mobile' in str(r.get('device', '')).lower()
                    if is_mobile:
                        vp_h = r.get('viewport_height') or 0
                        crop_h = int(2.5 * vp_h) if vp_h else 2400

                        def _crop_tall(img):
                            if img is None:
                                return None
                            w, h = img.size
                            if h > crop_h:
                                return img.crop((0, 0, w, crop_h))
                            return img

                        staging_img = _crop_tall(staging_img)
                        production_img = _crop_tall(production_img)
                        diff_img = _crop_tall(diff_img)
                except Exception:
                    pass

                overlay_img = None
                try:
                    if staging_img is not None and production_img is not None:
                        overlay_img = comparator.create_overlay(staging_img, production_img, opacity=0.5)
                except Exception:
                    overlay_img = None

                col_gap = 0.5 * cm
                col_w = (width - 2 * margin - col_gap) / 2
                row_h = (height - 5 * cm) / 3

                y1 = y
                y1 = draw_img_jpeg(staging_img, margin, y1, col_w, row_h)
                y2 = y
                y2 = draw_img_jpeg(production_img, margin + col_w + col_gap, y2, col_w, row_h)
                y = min(y1, y2)

                y = draw_img_jpeg(overlay_img, margin, y, width - 2 * margin, row_h, quality=65)
                y = draw_img_jpeg(diff_img, margin, y, width - 2 * margin, row_h, quality=65)

                c.setFont("Helvetica-Oblique", 8)
                c.drawString(
                    margin, y,
                    "Guidance: In overlay, verify key regions align (header, nav, CTAs, forms). "
                    "In diff, red shows changes.",
                )

        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return b""
