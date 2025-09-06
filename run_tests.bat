@echo off
REM Visual Regression Testing Tool - Test Runner (Windows)
REM Runs the functionality test suite before deployment

echo.
echo ============================================================
echo VISUAL REGRESSION TESTING TOOL - TEST RUNNER
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Check if test file exists
if not exist "test_functionality.py" (
    echo ❌ test_functionality.py not found
    exit /b 1
)

echo ℹ️ Running functionality tests...

REM Run the test suite
python test_functionality.py

REM Capture exit code
if errorlevel 1 (
    echo.
    echo ============================================================
    echo TESTS FAILED
    echo ============================================================
    echo ❌ Some tests failed. Please fix issues before deploying.
    exit /b 1
) else (
    echo.
    echo ============================================================
    echo TESTS PASSED
    echo ============================================================
    echo ✅ All tests passed! Ready for deployment.
    echo.
    echo ℹ️ You can now:
    echo   1. Deploy locally: docker-compose up -d
    echo   2. Push to repository: git add . ^&^& git commit -m "message" ^&^& git push
)
