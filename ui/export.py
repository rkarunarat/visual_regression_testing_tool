"""Export results to ZIP and generate PDF reports."""
from io import BytesIO
import zipfile

import streamlit as st

from reports.generator import build_report_filename, generate_pdf_report
from ui.deps import PDF_OK, ResultManager
from utils import safe_results_path


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
    return build_report_filename(
        st.session_state.get('test_results', []),
        st.session_state.get('current_test_id') or 'run',
        summary_only=summary_only,
    )


def generate_pdf(summary_only=True):
    """Generate a PDF report from current session results."""
    if not PDF_OK:
        st.error("PDF generation is not available due to missing dependencies.")
        return b""
    try:
        return generate_pdf_report(
            st.session_state.get('test_results', []),
            st.session_state.get('current_test_id') or 'run',
            summary_only=summary_only,
            results_base=ResultManager().results_dir,
        )
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return b""
