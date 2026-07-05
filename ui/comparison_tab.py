"""Detailed side-by-side comparison tab."""
import streamlit as st

from ui.deps import ImageComparator, PDF_OK, PLAYWRIGHT_DEVICE_MAP
from ui.export import build_pdf_filename, generate_pdf
from ui.helpers import load_image_from_result
from ui.theme import render_page_header, status_chip
from utils import resize_image_for_display


def detailed_comparison_tab():
    """Provide side-by-side, overlay, and diff visualizations per test."""
    render_page_header(
        "Detailed Comparison",
        "Inspect screenshots side-by-side, overlay views, and visual diffs.",
    )

    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first!")
        return

    test_options = []
    for i, result in enumerate(st.session_state.test_results):
        label = f"{result['test_name']} - {result['browser']} ({result['device']})"
        test_options.append((label, i))

    selected_test = st.selectbox(
        "Select test for detailed comparison:",
        options=range(len(test_options)),
        format_func=lambda x: test_options[x][0],
    )

    if selected_test is not None:
        result = st.session_state.test_results[selected_test]

        st.markdown('<div class="vrt-sticky-top">', unsafe_allow_html=True)
        top_left, top_right = st.columns([3, 2])
        with top_left:
            st.markdown("**Staging URL**")
            st.write(f"{result.get('staging_url', 'N/A')}")
            st.markdown("**Production URL**")
            st.write(f"{result.get('production_url', 'N/A')}")
        with top_right:
            st.markdown("**Generate Report**")
            col_a, col_b = st.columns(2)
            with col_a:
                if PDF_OK and st.button("Summary PDF", key="btn_pdf_summary_top"):
                    pdf_bytes = generate_pdf(summary_only=True)
                    st.download_button(
                        label="Download Summary PDF",
                        data=pdf_bytes,
                        file_name=build_pdf_filename(summary_only=True),
                        mime="application/pdf",
                        key="dl_pdf_summary_top",
                    )
                elif not PDF_OK:
                    st.button("Summary PDF (Unavailable)", disabled=True, key="btn_pdf_summary_top_disabled")
            with col_b:
                if PDF_OK and st.button("Full PDF", key="btn_pdf_full_top"):
                    pdf_bytes = generate_pdf(summary_only=False)
                    st.download_button(
                        label="Download Full PDF",
                        data=pdf_bytes,
                        file_name=build_pdf_filename(summary_only=False),
                        mime="application/pdf",
                        key="dl_pdf_full_top",
                    )
                elif not PDF_OK:
                    st.button("Full PDF (Unavailable)", disabled=True, key="btn_pdf_full_top_disabled")
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Similarity Score", f"{result['similarity_score']:.1f}%")
        with col2:
            st.metric("Status", "Pass" if result['is_match'] else "Fail")
        with col3:
            device = result['device']
            device_model = PLAYWRIGHT_DEVICE_MAP.get(device)
            device_display = (
                f"{device} ({device_model})"
                if device_model and device_model != device
                else device
            )
            vp = f"{result.get('viewport_width', '?')}x{result.get('viewport_height', '?')}"
            st.caption("Browser / Device")
            st.markdown(
                f"<div style='font-size:1.15rem;font-weight:600;line-height:1.3;"
                f"word-break:break-word;color:#0f172a;'>{result['browser']} / "
                f"{device_display} @ {vp}</div>",
                unsafe_allow_html=True,
            )

        comparison_mode = st.radio(
            "Comparison Mode:",
            ["Side by Side", "Overlay", "Difference Only"],
            horizontal=True,
        )

        device_model = PLAYWRIGHT_DEVICE_MAP.get(result['device'], result['device'])
        vp_cfg = f"{result.get('viewport_width', '?')}x{result.get('viewport_height', '?')}"
        rt = result.get('production_runtime_metrics') or result.get('staging_runtime_metrics') or {}
        vp_rt = (
            f"{rt.get('innerWidth', '?')}x{rt.get('innerHeight', '?')}@"
            f"{rt.get('devicePixelRatio', '?')}"
            if rt else "-"
        )
        status = 'PASS' if result['is_match'] else 'FAIL'
        st.markdown(
            status_chip(f"Browser: {result['browser']}")
            + status_chip(f"Device: {device_model}")
            + status_chip(f"Viewport cfg: {vp_cfg}")
            + status_chip(f"Viewport rt: {vp_rt}")
            + status_chip(f"Status: {status}"),
            unsafe_allow_html=True,
        )

        if comparison_mode == "Side by Side":
            st.markdown('<div class="vrt-image-panel">', unsafe_allow_html=True)
            staging_loaded = load_image_from_result(result, 'staging_screenshot')
            production_loaded = load_image_from_result(result, 'production_screenshot')

            if staging_loaded is None and production_loaded is None:
                st.info("No screenshots available for this test.")
            elif staging_loaded is not None and production_loaded is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Staging")
                    img = resize_image_for_display(staging_loaded, max_width=1200, max_height=1600)
                    st.image(img, use_container_width=True)
                    st.caption(result.get('staging_url', 'URL not available'))
                with col2:
                    st.subheader("Production")
                    img = resize_image_for_display(production_loaded, max_width=1200, max_height=1600)
                    st.image(img, use_container_width=True)
                    st.caption(result.get('production_url', 'URL not available'))
            else:
                available_label = "Staging" if staging_loaded is not None else "Production"
                available_url = (
                    result.get('staging_url')
                    if staging_loaded is not None
                    else result.get('production_url')
                )
                available_img = staging_loaded if staging_loaded is not None else production_loaded
                st.subheader(available_label)
                img = resize_image_for_display(available_img, max_width=1400, max_height=1600)
                st.image(img, use_container_width=True)
                st.caption(available_url or 'URL not available')
            st.markdown('</div>', unsafe_allow_html=True)

        elif comparison_mode == "Overlay":
            st.subheader("Overlay Comparison")
            staging_loaded = load_image_from_result(result, 'staging_screenshot')
            production_loaded = load_image_from_result(result, 'production_screenshot')
            if staging_loaded is not None and production_loaded is not None:
                opacity = st.slider("Staging Opacity", 0.0, 1.0, 0.5, 0.1)
                with st.spinner("Generating overlay..."):
                    try:
                        comparator = ImageComparator()
                        overlay_image = comparator.create_overlay(
                            staging_loaded, production_loaded, opacity,
                        )
                        overlay_resized = resize_image_for_display(
                            overlay_image, max_width=1400, max_height=900,
                        )
                        st.image(overlay_resized, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating overlay: {e}")
            else:
                st.error("Both staging and production screenshots are required for overlay comparison")

        elif comparison_mode == "Difference Only":
            st.subheader("Visual Differences")
            diff_loaded = load_image_from_result(result, 'diff_image')
            if diff_loaded is None:
                staging_loaded = load_image_from_result(result, 'staging_screenshot')
                production_loaded = load_image_from_result(result, 'production_screenshot')
                if staging_loaded is not None and production_loaded is not None:
                    with st.spinner("Computing visual diff..."):
                        try:
                            comparator = ImageComparator()
                            diff_loaded = comparator.create_difference_image(
                                staging_loaded, production_loaded,
                            )
                        except Exception as e:
                            st.error(f"Error generating difference image: {e}")
                            diff_loaded = None
            if diff_loaded is not None:
                img = resize_image_for_display(diff_loaded, max_width=1600, max_height=1600)
                st.image(img, use_container_width=True)
                st.caption("Red areas indicate differences between staging and production")
            else:
                st.info("No differences detected or difference image not available")
