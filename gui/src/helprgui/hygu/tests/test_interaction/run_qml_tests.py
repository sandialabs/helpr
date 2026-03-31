#!/usr/bin/env python
"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

QML Test Runner - Executes QML component tests with Python backend support.

Usage:
    cd repo/gui/src/helprgui/hygu/tests/test_interaction
    python run_qml_tests.py [--visible] [--test <test_file.qml>] [--all]

Options:
    --visible       Show the test window (default: headless with offscreen)
    --test FILE     Run specific test file (default: test_uncertain_param_field.qml)
    --all           Run all test_*.qml files in the directory

Environment:
    Set QT_QPA_PLATFORM=offscreen for headless CI execution.
"""
import argparse
import os
import sys
from pathlib import Path

# Add parent paths for imports
script_dir = Path(__file__).parent
hygu_dir = script_dir.parent.parent
gui_src_dir = hygu_dir.parent
sys.path.insert(0, str(gui_src_dir))

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from helprgui.hygu.tests.test_interaction.qml_test_helper import QmlTestHelper
from helprgui.hygu.forms.fields_probabilistic import UncertainFormField


def setup_qml_types():
    """Register custom QML types."""
    # UncertainFormField is already registered via QmlElement decorator
    pass


def run_tests(test_file: str, visible: bool = False, timeout: int = 30000) -> int:
    """Run QML tests and return exit code.

    Parameters
    ----------
    test_file : str
        Path to QML test file
    visible : bool
        If True, show test window; if False, run headless
    timeout : int
        Test timeout in milliseconds

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure)
    """
    # Set offscreen platform for headless execution
    if not visible and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QGuiApplication(sys.argv)

    # Create QML engine
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()

    # Create and expose test helper
    tester = QmlTestHelper()
    ctx.setContextProperty("tester", tester)

    # Add import paths for hygu components
    ui_path = hygu_dir / "ui"
    engine.addImportPath(str(ui_path.parent))
    engine.addImportPath(str(gui_src_dir))

    # Track test completion
    test_result = {"completed": False, "exit_code": 1}

    def on_object_created(obj, url):
        if obj is None:
            print(f"ERROR: Failed to load QML file: {url}")
            test_result["exit_code"] = 1
            app.quit()

    def check_tests_complete():
        """Check if tests are complete by inspecting root object."""
        objects = engine.rootObjects()
        if objects:
            root = objects[0]
            # Check for testsComplete flag
            tests_complete = root.property("testsComplete")

            if tests_complete:
                tests_run = root.property("testsRun")
                tests_passed = root.property("testsPassed")
                tests_failed = root.property("testsFailed")

                print(f"\nTests completed: {tests_passed}/{tests_run} passed")
                if tests_failed and tests_failed > 0:
                    print(f"FAILURES: {tests_failed}")
                    test_result["exit_code"] = 1
                else:
                    test_result["exit_code"] = 0
                test_result["completed"] = True

                if not visible:
                    # Give a moment for final output then quit
                    QTimer.singleShot(500, app.quit)

    engine.objectCreated.connect(on_object_created)

    # Load QML test file
    test_path = Path(test_file)
    if not test_path.is_absolute():
        test_path = script_dir / test_file

    if not test_path.exists():
        print(f"ERROR: Test file not found: {test_path}")
        return 1

    print(f"Loading test file: {test_path}")
    engine.load(QUrl.fromLocalFile(str(test_path)))

    if not engine.rootObjects():
        print("ERROR: No root objects created")
        return 1

    # Set up periodic check for test completion (for headless mode)
    if not visible:
        check_timer = QTimer()
        check_timer.timeout.connect(check_tests_complete)
        check_timer.start(500)

        # Timeout timer
        def on_timeout():
            if not test_result["completed"]:
                print(f"ERROR: Test timeout after {timeout}ms")
                test_result["exit_code"] = 1
                app.quit()

        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(on_timeout)
        timeout_timer.start(timeout)

    # Run event loop
    exit_code = app.exec()

    return test_result["exit_code"] if test_result["completed"] else exit_code


def get_all_test_files() -> list[str]:
    """Find all test_*.qml files in the script directory."""
    test_files = []
    for f in script_dir.glob("test_*.qml"):
        # Skip validation test which uses QtTest framework
        if "validation" not in f.name:
            test_files.append(f.name)
    return sorted(test_files)


def run_all_tests(visible: bool = False, timeout: int = 30000) -> int:
    """Run all test files and return combined exit code.

    Note: Due to Qt application lifecycle, each test file must run in a
    separate process. This function spawns subprocesses for each test.
    """
    import subprocess

    test_files = get_all_test_files()
    if not test_files:
        print("ERROR: No test files found")
        return 1

    print("=" * 50)
    print("Running all QML test files")
    print("=" * 50)
    print(f"Found {len(test_files)} test files:")
    for tf in test_files:
        print(f"  - {tf}")
    print()

    total_passed = 0
    total_failed = 0
    failed_files = []

    for test_file in test_files:
        print("-" * 50)
        print(f"Running: {test_file}")
        print("-" * 50)

        cmd = [sys.executable, __file__, "--test", test_file]
        if visible:
            cmd.append("--visible")
        cmd.extend(["--timeout", str(timeout)])

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode == 0:
            total_passed += 1
        else:
            total_failed += 1
            failed_files.append(test_file)

        print()

    print("=" * 50)
    print("COMBINED RESULTS")
    print("=" * 50)
    print(f"Test files passed: {total_passed}/{len(test_files)}")
    if failed_files:
        print(f"Failed files:")
        for f in failed_files:
            print(f"  - {f}")
        return 1

    print("ALL TEST FILES PASSED")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run QML component tests")
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Show test window instead of running headless"
    )
    parser.add_argument(
        "--test",
        default="test_uncertain_param_field.qml",
        help="QML test file to run (default: test_uncertain_param_field.qml)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Test timeout in milliseconds (default: 30000)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all test_*.qml files"
    )

    args = parser.parse_args()

    # Run all tests if --all flag is set
    if args.all:
        exit_code = run_all_tests(visible=args.visible, timeout=args.timeout)
        sys.exit(exit_code)

    # Run single test file
    print("=" * 50)
    print("HELPR QML Component Test Runner")
    print("=" * 50)
    print(f"Test file: {args.test}")
    print(f"Visible: {args.visible}")
    print(f"Timeout: {args.timeout}ms")
    print()

    exit_code = run_tests(
        test_file=args.test,
        visible=args.visible,
        timeout=args.timeout
    )

    print()
    if exit_code == 0:
        print("=" * 50)
        print("ALL TESTS PASSED")
        print("=" * 50)
    else:
        print("=" * 50)
        print("TESTS FAILED")
        print("=" * 50)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
