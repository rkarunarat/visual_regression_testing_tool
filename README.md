# Visual Diff

A Streamlit-based visual regression tool that screenshots pairs of URLs across browsers/devices, compares images, and reports differences.

## Features

- URL pairs input (manual/CSV)
- Multi-browser and multi-device testing (Chrome recommended)
- Per-combo screenshots (staging/production) and visual diff
- Detailed Comparison UI: side-by-side, overlay with opacity, diff
- Results management: list, load, export ZIP, delete/cleanup
- Reports: Summary PDF (table) and Full PDF (SxP, overlay, diff per test)

## Dependencies

These reflect `requirements.txt`.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.49%2B-ff4b4b?logo=streamlit)
![Playwright](https://img.shields.io/badge/Playwright-1.55%2B-brightgreen)
![Pillow](https://img.shields.io/badge/Pillow-11.3%2B-9cf)
![NumPy](https://img.shields.io/badge/NumPy-2.3%2B-013243?logo=numpy&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.11%2B-5C3EE8?logo=opencv&logoColor=white)
![scikit-image](https://img.shields.io/badge/scikit--image-0.25%2B-F7931E)
![pandas](https://img.shields.io/badge/pandas-2.3%2B-150458?logo=pandas&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-4.1%2B-6aa84f)

Alternative stacks sometimes used elsewhere: Selenium, WebDriver Manager, ImageHash (not used here).

## Quick start

- Python 3.11+
- Install dependencies and Playwright browsers:

```
pip install -r requirements.txt
python -m playwright install chromium
```

- Run locally:

```
streamlit run app.py
```

## Folder structure

```
VisualDiff/
  app.py                  # Streamlit app
  browser_automation.py   # Playwright manager (internal)
  browser_manager.py      # Import alias for clarity
  image_comparison.py     # Comparator (internal)
  image_comparator.py     # Import alias for clarity
  result_manager.py       # Results persistence (internal)
  results_store.py        # Import alias for clarity
  config.py               # Browsers, devices, viewports
  utils.py                # UI/util helpers
  test_results/           # Saved runs: <test_id>/<browser>/<device>/
```

## Usage notes

- Start with Chrome. Firefox mobile/tablet emulation can be limited depending on environment.
- Results are stored under `test_results/<test_id>/<browser>/<device>/` with JSON + PNGs.
- Use Manage Test Runs to load, export, or delete runs.

## Production deployment

### Single host

```
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Put nginx in front and proxy to 127.0.0.1:8501.

### systemd service (Linux)

Create a venv, install deps, then a unit file:

```
[Unit]
Description=VisualDiff
After=network.target

[Service]
WorkingDirectory=/srv/visualdiff
ExecStart=/srv/visualdiff/.venv/bin/streamlit run /srv/visualdiff/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker (example)

Use python:3.11-slim, install requirements and `playwright install chromium`, expose 8501.

## Troubleshooting

- Firefox mobile/tablet: if runs fail, try Desktop only or use Chrome.
- Large pages: DecompressionBombWarning is handled; very tall mobile images are cropped in PDFs.
- If images don’t show after “Load Results”, the app loads them from disk automatically.
