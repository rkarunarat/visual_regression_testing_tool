#!/usr/bin/env python3
"""Run visual regression tests in CI and emit PDF/HTML artifacts."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ci.runner import run_test_matrix
from config import BROWSERS, DEVICES, REGIONS
from reports.generator import generate_html_report, write_pdf_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


def _load_config(path: Path) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _config_from_env() -> dict | None:
    """Build a minimal config when STAGING_URL and PRODUCTION_URL are set."""
    staging = os.environ.get('STAGING_URL', '').strip()
    production = os.environ.get('PRODUCTION_URL', '').strip()
    if not staging or not production:
        return None

    return {
        'url_pairs': [{
            'name': os.environ.get('TEST_NAME', 'CI Test'),
            'staging_url': staging,
            'production_url': production,
        }],
        'browsers': [os.environ.get('BROWSER', 'Chrome')],
        'devices': [os.environ.get('DEVICE', 'Desktop')],
        'similarity_threshold': float(os.environ.get('SIMILARITY_THRESHOLD', '95')),
        'wait_time': int(os.environ.get('WAIT_TIME', '3')),
        'region': os.environ.get('REGION', 'Default'),
        'fail_on_regression': os.environ.get('FAIL_ON_REGRESSION', 'false').lower() in ('1', 'true', 'yes'),
    }


def _validate_config(config: dict):
    if not config.get('url_pairs'):
        raise ValueError("Config must include at least one url_pair")

    for browser in config.get('browsers', ['Chrome']):
        if browser not in BROWSERS:
            raise ValueError(f"Unknown browser: {browser}")

    for device in config.get('devices', ['Desktop']):
        if device not in DEVICES:
            raise ValueError(f"Unknown device: {device}")

    region = config.get('region', 'Default')
    if region != 'Default' and region not in REGIONS:
        raise ValueError(f"Unknown region: {region}")


def parse_args():
    parser = argparse.ArgumentParser(description='Run visual regression tests for CI')
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('ci/config.json'),
        help='Path to JSON config (default: ci/config.json)',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('artifacts'),
        help='Directory for PDF/HTML artifacts (default: artifacts)',
    )
    parser.add_argument(
        '--summary-pdf-only',
        action='store_true',
        help='Generate summary PDF only (default: full PDF with screenshots)',
    )
    parser.add_argument(
        '--fail-on-regression',
        action='store_true',
        help='Exit with code 1 when visual regressions are found (default: alert only)',
    )
    return parser.parse_args()


def _write_manifest(output_dir, run_id, results, pdf_name, failed, skipped):
    passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
    manifest = {
        'run_id': run_id,
        'total': len(results),
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'pdf': pdf_name,
        'html': 'index.html',
        'regressions_found': failed > 0,
        'status': 'issues_found' if failed > 0 else 'ok',
    }
    (output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main():
    args = parse_args()

    try:
        if args.config.exists():
            config = _load_config(args.config)
            logger.info("Loaded config from %s", args.config)
        else:
            config = _config_from_env()
            if config is None:
                logger.error(
                    "No config file at %s and STAGING_URL/PRODUCTION_URL env vars are not set.",
                    args.config,
                )
                return 2

        _validate_config(config)

        run_id = os.environ.get('RUN_ID') or f"ci_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting visual regression run: %s", run_id)
        results = asyncio.run(
            run_test_matrix(
                config['url_pairs'],
                config.get('browsers', ['Chrome']),
                config.get('devices', ['Desktop']),
                config.get('similarity_threshold', 95),
                config.get('wait_time', 3),
                config.get('region', 'Default'),
            ),
        )

        passed = sum(1 for r in results if r.get('is_match') and not r.get('is_skipped', False))
        failed = sum(1 for r in results if not r.get('is_match') and not r.get('is_skipped', False))
        skipped = sum(1 for r in results if r.get('is_skipped', False))
        logger.info("Finished: %s total, %s passed, %s failed, %s skipped", len(results), passed, failed, skipped)

        pdf_name = 'report-summary.pdf' if args.summary_pdf_only else 'report-full.pdf'
        pdf_path = write_pdf_report(
            results,
            run_id,
            output_dir / pdf_name,
            summary_only=args.summary_pdf_only,
        )
        logger.info("Wrote PDF: %s", pdf_path)

        html_path = generate_html_report(results, run_id, output_dir)
        logger.info("Wrote HTML report: %s", html_path)

        manifest = _write_manifest(output_dir, run_id, results, pdf_name, failed, skipped)

        fail_on_regression = (
            args.fail_on_regression or config.get('fail_on_regression', False)
        )
        if fail_on_regression and failed > 0:
            logger.error("Visual regressions detected (%s failed).", failed)
            return 1

        if failed > 0:
            logger.warning(
                "Visual regressions detected (%s failed). Reports were generated; job will not fail.",
                failed,
            )
        if skipped > 0:
            logger.warning("%s test(s) were skipped (capture/runtime issues).", skipped)

        return 0
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        return 2
    except Exception as e:
        logger.exception("Unexpected error during visual regression run: %s", e)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
