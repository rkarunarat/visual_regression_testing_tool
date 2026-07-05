"""Test execution: single tests, parallel/sequential runs."""
import asyncio
import logging
import os
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import streamlit as st

from ui.session import request_nav
from ui.deps import (
    BrowserManager,
    ImageComparator,
    ResultManager,
    PLAYWRIGHT_DEVICE_MAP,
    VIEWPORT_CONFIGS,
)
from ui.helpers import (
    build_skipped_result,
    get_optimal_worker_count,
    is_rancher_desktop,
    is_wsl_environment,
    should_use_parallel_processing,
)

logger = logging.getLogger(__name__)


async def run_single_test(url_pair, browser, device, similarity_threshold, wait_time, selected_region):
    """Run one test case and return a result record with images/metrics."""
    browser_manager = None
    try:
        if st.session_state.get('stop_testing', False):
            logger.info(
                "Test %s (%s, %s) skipped - tests stopped by user",
                url_pair['name'], browser, device,
            )
            return None

        browser_manager = BrowserManager()
        viewport = VIEWPORT_CONFIGS[device]
        region = selected_region if selected_region != "Default" else None
        logger.info("Taking screenshots for %s with region: %s", url_pair['name'], region)

        staging_capture = await browser_manager.take_screenshot(
            url_pair['staging_url'], browser, viewport, wait_time,
            device_name=device, return_metrics=True, region=region,
        )
        production_capture = await browser_manager.take_screenshot(
            url_pair['production_url'], browser, viewport, wait_time,
            device_name=device, return_metrics=True, region=region,
        )

        staging_screenshot, staging_metrics = (
            staging_capture if isinstance(staging_capture, tuple) else (staging_capture, {})
        )
        production_screenshot, production_metrics = (
            production_capture if isinstance(production_capture, tuple) else (production_capture, {})
        )

        if not staging_screenshot or not production_screenshot:
            logger.warning(
                "Failed to capture screenshots for %s (%s, %s)",
                url_pair['name'], browser, device,
            )
            return None

        comparator = ImageComparator()
        comparison_result = comparator.compare_images(
            staging_screenshot, production_screenshot, similarity_threshold,
        )

        result = {
            'test_name': url_pair['name'],
            'browser': browser,
            'device': device,
            'device_model': PLAYWRIGHT_DEVICE_MAP.get(device, device),
            'staging_url': url_pair['staging_url'],
            'production_url': url_pair['production_url'],
            'similarity_score': comparison_result['similarity_score'],
            'is_match': comparison_result['is_match'],
            'staging_screenshot': staging_screenshot,
            'production_screenshot': production_screenshot,
            'diff_image': comparison_result['diff_image'],
            'timestamp': datetime.now().isoformat(),
            'viewport_width': viewport.get('width'),
            'viewport_height': viewport.get('height'),
            'staging_runtime_metrics': staging_metrics,
            'production_runtime_metrics': production_metrics,
            'region': selected_region if selected_region != "Default" else None,
        }

        logger.info(
            "Successfully completed test %s (%s, %s) - Similarity: %.2f%%",
            url_pair['name'], browser, device, comparison_result['similarity_score'],
        )
        return result

    except Exception as e:
        logger.error("Error in test %s (%s, %s): %s", url_pair['name'], browser, device, e)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())
        return None
    finally:
        if browser_manager is not None:
            try:
                await browser_manager.cleanup()
            except Exception as cleanup_error:
                logger.warning("Error during browser cleanup: %s", cleanup_error)


def run_single_test_sync(url_pair, browser, device, similarity_threshold, wait_time, selected_region):
    """Synchronous wrapper for run_single_test to use with ThreadPoolExecutor."""
    return asyncio.run(
        run_single_test(url_pair, browser, device, similarity_threshold, wait_time, selected_region),
    )


def run_tests(url_pairs, browsers, devices, similarity_threshold, wait_time, selected_region):
    """Execute the selected test matrix and persist results incrementally."""
    total_tests = len(url_pairs) * len(browsers) * len(devices)
    if total_tests == 0:
        st.warning("No valid browser/device combinations to run.")
        st.session_state.test_running = False
        return

    logger.info("Test configuration validated! Starting execution of %s tests...", total_tests)
    st.success("**Test configuration validated!** Starting execution...")

    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("**Initializing...** Setting up browsers and test environment...")

    start_time = datetime.now()
    timing_text = st.empty()
    current_test = 0
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    m_completed = metrics_col1.empty()
    m_passed = metrics_col2.empty()
    m_failed = metrics_col3.empty()
    m_skipped = metrics_col4.empty()
    passed_count = 0
    failed_count = 0
    skipped_count = 0

    result_manager = ResultManager()
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_test_id = test_id
    results = []

    try:
        use_parallel = should_use_parallel_processing()
        worker_count = get_optimal_worker_count()

        if use_parallel and total_tests > 1:
            logger.info("Starting parallel execution with %s workers...", worker_count)
            status_text.text("**Starting parallel execution...** Launching multiple browser instances...")

            env_info = ""
            if is_wsl_environment():
                env_info = " (WSL Environment)"
            elif is_rancher_desktop():
                env_info = " (Docker Environment)"
            elif platform.system() == "Windows":
                if os.path.exists('C:\\.dockerenv') or os.environ.get('CONTAINER'):
                    env_info = " (Docker on Windows)"
                else:
                    env_info = " (Windows Local)"
            elif platform.system() == "Linux":
                if os.path.exists('/.dockerenv') or os.environ.get('CONTAINER'):
                    env_info = " (Docker on Linux)"
                else:
                    env_info = " (Linux Local)"
            elif platform.system() == "Darwin":
                if os.path.exists('/.dockerenv') or os.environ.get('CONTAINER'):
                    env_info = " (Docker on macOS)"
                else:
                    env_info = " (macOS Local)"

            logger.info(
                "Environment detection: WSL=%s, Docker=%s, Platform=%s",
                is_wsl_environment(), is_rancher_desktop(), platform.system(),
            )
            logger.info(
                "Parallel Processing Enabled: Running tests with %s workers%s",
                worker_count, env_info,
            )
            st.info(
                f"**Parallel Processing Enabled**: Running tests with {worker_count} "
                f"workers for faster execution{env_info}",
            )

            test_tasks = [
                (url_pair, browser, device)
                for url_pair in url_pairs
                for browser in browsers
                for device in devices
            ]

            logger.info("Executing %s tests in parallel with %s workers...", total_tests, worker_count)
            status_text.text(f"**Executing {total_tests} tests in parallel** with {worker_count} workers...")

            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                future_to_task = {
                    executor.submit(
                        run_single_test_sync, url_pair, browser, device,
                        similarity_threshold, wait_time, selected_region,
                    ): (url_pair, browser, device)
                    for url_pair, browser, device in test_tasks
                }

                for future in as_completed(future_to_task):
                    if st.session_state.stop_testing:
                        logger.info("Tests stopped by user")
                        status_text.text("Tests stopped by user")
                        st.session_state.test_running = False
                        st.session_state.tests_started = False
                        for f in future_to_task:
                            if not f.done():
                                f.cancel()
                        return

                    url_pair, browser, device = future_to_task[future]
                    current_test += 1
                    progress = current_test / total_tests
                    progress_bar.progress(int(progress * 100))

                    elapsed = (datetime.now() - start_time).total_seconds()
                    if 1 < current_test < total_tests:
                        avg_time = elapsed / (current_test - 1)
                        remaining = (total_tests - current_test) * avg_time
                        timing_text.text(f"Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")
                    else:
                        timing_text.text(f"Elapsed: {elapsed:.1f}s")

                    logger.info(
                        "Completed %s on %s (%s)... (%s/%s)",
                        url_pair['name'], browser, device, current_test, total_tests,
                    )
                    status_text.text(
                        f"Completed {url_pair['name']} on {browser} ({device})... "
                        f"({current_test}/{total_tests})",
                    )

                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            result_manager.save_result(test_id, result)
                            if result.get('is_match'):
                                passed_count += 1
                                logger.info(
                                    "PASS: %s - %s %s (Similarity: %.1f%%)",
                                    url_pair['name'], browser, device, result['similarity_score'],
                                )
                            else:
                                failed_count += 1
                                logger.info(
                                    "FAIL: %s - %s %s (Similarity: %.1f%%)",
                                    url_pair['name'], browser, device, result['similarity_score'],
                                )
                        else:
                            skipped_result = build_skipped_result(
                                url_pair, browser, device, selected_region,
                            )
                            results.append(skipped_result)
                            result_manager.save_result(test_id, skipped_result)
                            skipped_count += 1

                        st.session_state.test_results = results.copy()
                        m_completed.metric("Completed", f"{current_test}/{total_tests}")
                        m_passed.metric("Passed", passed_count)
                        m_failed.metric("Failed", failed_count)
                        m_skipped.metric("Skipped", skipped_count)

                    except Exception as e:
                        st.error(f"Error in parallel test execution: {e}")
                        skipped_count += 1
        else:
            logger.info("Starting sequential execution... Running tests one by one...")
            status_text.text("**Starting sequential execution...** Running tests one by one...")

            for url_pair in url_pairs:
                for browser in browsers:
                    for device in devices:
                        if st.session_state.stop_testing:
                            logger.info("Tests stopped by user")
                            status_text.text("Tests stopped by user")
                            st.session_state.test_running = False
                            st.session_state.tests_started = False
                            return

                        current_test += 1
                        progress = current_test / total_tests
                        progress_bar.progress(int(progress * 100))

                        logger.info(
                            "Test %s/%s: %s - %s %s",
                            current_test, total_tests, url_pair['name'], browser, device,
                        )
                        status_text.text(
                            f"**Test {current_test}/{total_tests}**: "
                            f"{url_pair['name']} - {browser} {device}",
                        )
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if 1 < current_test < total_tests:
                            avg_time = elapsed / (current_test - 1)
                            remaining = (total_tests - current_test) * avg_time
                            timing_text.text(f"Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")
                        else:
                            timing_text.text(f"Elapsed: {elapsed:.1f}s")

                        status_text.text(
                            f"Testing {url_pair['name']} on {browser} ({device})... "
                            f"({current_test}/{total_tests})",
                        )

                        result = asyncio.run(
                            run_single_test(
                                url_pair, browser, device,
                                similarity_threshold, wait_time, selected_region,
                            ),
                        )

                        if result:
                            results.append(result)
                            result_manager.save_result(test_id, result)
                            if result.get('is_match'):
                                passed_count += 1
                                logger.info(
                                    "PASS: %s - %s %s (Similarity: %.1f%%)",
                                    url_pair['name'], browser, device, result['similarity_score'],
                                )
                            else:
                                failed_count += 1
                                logger.info(
                                    "FAIL: %s - %s %s (Similarity: %.1f%%)",
                                    url_pair['name'], browser, device, result['similarity_score'],
                                )
                        else:
                            skipped_result = build_skipped_result(
                                url_pair, browser, device, selected_region,
                            )
                            results.append(skipped_result)
                            result_manager.save_result(test_id, skipped_result)
                            skipped_count += 1

                        st.session_state.test_results = results.copy()
                        m_completed.metric("Completed", f"{current_test}/{total_tests}")
                        m_passed.metric("Passed", passed_count)
                        m_failed.metric("Failed", failed_count)
                        m_skipped.metric("Skipped", skipped_count)

        st.session_state.test_results = results
        progress_bar.progress(100)
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info("All tests completed successfully in %.1f seconds!", total_time)
        status_text.text("All tests completed successfully!")
        timing_text.text(f"Total time: {total_time:.1f}s")

        if len(results) > 0:
            passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
            failed = sum(1 for r in results if not r.get('is_match') and not r.get('is_skipped', False))
            scored = [r['similarity_score'] for r in results if not r.get('is_skipped', False)]
            avg_similarity = sum(scored) / len(scored) if scored else 0

            logger.info(
                "Results Summary: %s passed, %s failed, %s skipped | Average similarity: %.1f%%",
                passed, failed, skipped_count, avg_similarity,
            )
            st.success(f"Completed {len(results)} tests successfully in {total_time:.1f} seconds!")
            st.success(
                f"**Results Summary**: {passed} passed, {failed} failed, {skipped_count} skipped | "
                f"Average similarity: {avg_similarity:.1f}%",
            )

            with st.expander("Quick Results Summary", expanded=True):
                for i, result in enumerate(results, 1):
                    status = "Pass" if result['is_match'] else "Fail"
                    st.write(
                        f"**Test {i}**: {result['test_name']} - {result['browser']} "
                        f"({result['device']}) - {status} - {result['similarity_score']:.1f}%",
                    )

            st.toast("Tests complete!", icon="🎉")
        else:
            st.warning("Tests completed but no results were generated. Please check your URLs and try again.")

    except Exception as e:
        st.error(f"Error during testing: {str(e)}")
    finally:
        st.session_state.test_running = False
        st.session_state.tests_started = False
        results = st.session_state.get('test_results') or []
        if results and not st.session_state.get('stop_testing') and not st.session_state.get('cleanup_needed'):
            passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
            failed = sum(1 for r in results if not r.get('is_match') and not r.get('is_skipped', False))
            skipped = sum(1 for r in results if r.get('is_skipped', False))
            request_nav("Results")
            st.session_state.banner_message = (
                f"Completed {len(results)} tests — {passed} passed, {failed} failed, "
                f"{skipped} skipped. Review results below."
            )
            st.session_state.banner_type = "success"
            st.rerun()
