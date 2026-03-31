"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Pytest wrapper for QML component tests.
Allows QML tests to be run as part of the regular pytest suite.

Usage:
    pytest test_qml_components.py -v
    pytest test_qml_components.py -v -k "float_param"
    pytest test_qml_components.py -v -k "TestQmlTestHelper"

Note: Tests require Qt runtime and will be skipped if unavailable.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent


# ====================
# Qt Environment Check
# ====================

def _can_run_qt_tests() -> bool:
    """Check if Qt environment is available for testing."""
    try:
        from PySide6.QtCore import QCoreApplication
        # Check for display (X11/Wayland) or offscreen platform
        platform = os.environ.get("QT_QPA_PLATFORM", "")
        if platform == "offscreen":
            return True
        # Try to detect display
        display = os.environ.get("DISPLAY", "")
        wayland = os.environ.get("WAYLAND_DISPLAY", "")
        # macOS doesn't need DISPLAY
        if sys.platform == "darwin":
            return True
        return bool(display or wayland or platform)
    except ImportError:
        return False


SKIP_REASON = "Qt environment not available (no display or PySide6)"
HAS_QT = _can_run_qt_tests()


# ====================
# QML Test Discovery
# ====================

def get_qml_test_files() -> list[Path]:
    """Find all QML test files in the test directory.

    Returns
    -------
    list[Path]
        Sorted list of QML test file paths.
    """
    return sorted(SCRIPT_DIR.glob("test_*.qml"))


# ====================
# QML Component Tests
# ====================

@pytest.fixture(scope="module")
def qml_test_environment():
    """Ensure the QML test environment is properly configured."""
    original_platform = os.environ.get("QT_QPA_PLATFORM")
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    yield

    # Restore original platform setting
    if original_platform is None:
        os.environ.pop("QT_QPA_PLATFORM", None)
    else:
        os.environ["QT_QPA_PLATFORM"] = original_platform


@pytest.mark.skipif(not HAS_QT, reason=SKIP_REASON)
@pytest.mark.parametrize(
    "test_file",
    get_qml_test_files(),
    ids=lambda p: p.stem  # Use filename without extension as test ID
)
def test_qml_component(test_file: Path, qml_test_environment):
    """Run a QML component test file via the test runner.

    Parameters
    ----------
    test_file : Path
        Path to the QML test file to execute.
    qml_test_environment : fixture
        Fixture ensuring proper QML test environment setup.
    """
    runner_script = SCRIPT_DIR / "run_qml_tests.py"

    env = os.environ.copy()
    if "QT_QPA_PLATFORM" not in env:
        env["QT_QPA_PLATFORM"] = "offscreen"

    result = subprocess.run(
        [
            sys.executable,
            str(runner_script),
            "--test", test_file.name,
            "--timeout", "60000"
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(SCRIPT_DIR)
    )

    # Print output for debugging
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    assert result.returncode == 0, f"QML test '{test_file.name}' failed with exit code {result.returncode}"


def test_all_qml_tests_discovered():
    """Verify that QML test files are discovered."""
    test_files = get_qml_test_files()
    assert len(test_files) > 0, "No QML test files found"

    # Verify expected test files exist
    expected_tests = [
        "test_uncertain_param_field.qml",
        "test_float_param_field.qml",
        "test_param_fields.qml",
        "test_num_list_param_field.qml",
        "test_float_nullable_param_field.qml",
        "test_readonly_parameter.qml",
        "test_file_selector.qml",
        "test_directory_selector.qml",
    ]

    found_names = [f.name for f in test_files]
    for expected in expected_tests:
        assert expected in found_names, f"Expected test file '{expected}' not found"


# ====================
# QmlTestHelper Unit Tests
# ====================

@pytest.fixture
def qml_helper():
    """Create a QmlTestHelper instance that persists for the test duration.

    This fixture ensures the helper and its Qt objects stay alive throughout
    the test, preventing 'C++ object already deleted' errors.
    """
    from helprgui.hygu.tests.test_interaction.qml_test_helper import QmlTestHelper
    helper = QmlTestHelper()
    yield helper
    # Helper and its Qt objects will be cleaned up after test completes


@pytest.mark.skipif(not HAS_QT, reason=SKIP_REASON)
class TestQmlTestHelper:
    """Unit tests for the QmlTestHelper class."""

    def test_helper_creation(self, qml_helper):
        """Test that QmlTestHelper can be instantiated."""
        assert qml_helper is not None
        assert qml_helper.field is None  # No field created yet

    def test_create_deterministic_field(self, qml_helper):
        """Test creating a deterministic field."""
        field = qml_helper.create_deterministic_field()

        assert field is not None
        assert qml_helper.get_input_type() == "det"

    def test_create_uniform_field(self, qml_helper):
        """Test creating a uniform distribution field."""
        field = qml_helper.create_uniform_field()

        assert field is not None
        assert qml_helper.get_input_type() == "uni"
        assert qml_helper.is_field_visible("lower")
        assert qml_helper.is_field_visible("upper")
        assert not qml_helper.is_field_visible("mean")

    def test_set_subparam(self, qml_helper):
        """Test setting sub-parameter values."""
        qml_helper.create_deterministic_field()

        qml_helper.set_subparam("value", "75.0")

        # Check value was updated
        val = float(qml_helper.get_field_value())
        assert abs(val - 75.0) < 0.1

    def test_validation_events_recorded(self, qml_helper):
        """Test that validation events are recorded."""
        qml_helper.create_uniform_field()  # lower=40, upper=60
        qml_helper.clear_validation_events()

        # Set invalid lower bound
        qml_helper.set_subparam("lower", "70")  # > upper

        # Should have recorded validation event
        assert qml_helper.get_validation_event_count() > 0

    def test_distribution_switching(self, qml_helper):
        """Test switching between distribution types by creating new fields."""
        # Create fields of each type to test distribution detection
        # (Switching distributions on existing field can cause Qt lifecycle issues)
        qml_helper.create_deterministic_field()
        assert qml_helper.get_input_type() == "det"

        qml_helper.create_uniform_field()
        assert qml_helper.get_input_type() == "uni"

        qml_helper.create_normal_field()
        assert qml_helper.get_input_type() == "nor"

        qml_helper.create_truncated_normal_field()
        assert qml_helper.get_input_type() == "tnor"

    def test_field_visibility_normal(self, qml_helper):
        """Test field visibility for normal distribution."""
        qml_helper.create_normal_field()
        assert qml_helper.is_field_visible("mean")
        assert qml_helper.is_field_visible("std")
        assert not qml_helper.is_field_visible("lower")
        assert not qml_helper.is_field_visible("mu")

    def test_field_visibility_truncated_normal(self, qml_helper):
        """Test field visibility for truncated normal distribution."""
        qml_helper.create_truncated_normal_field()
        assert qml_helper.is_field_visible("mean")
        assert qml_helper.is_field_visible("std")
        assert qml_helper.is_field_visible("lower")
        assert qml_helper.is_field_visible("upper")

    def test_field_visibility_lognormal(self, qml_helper):
        """Test field visibility for lognormal distribution."""
        qml_helper.create_lognormal_field()
        assert qml_helper.is_field_visible("mu")
        assert qml_helper.is_field_visible("sigma")
        assert not qml_helper.is_field_visible("mean")

    def test_field_visibility_beta(self, qml_helper):
        """Test field visibility for beta distribution."""
        qml_helper.create_beta_field()
        assert qml_helper.is_field_visible("alpha")
        assert qml_helper.is_field_visible("beta")
        assert not qml_helper.is_field_visible("mean")
        assert not qml_helper.is_field_visible("lower")

    def test_num_field_pressure(self, qml_helper):
        """Test creating pressure NumFormField."""
        qml_helper.create_pressure_field()
        assert qml_helper.get_num_unit_type() == "pres"
        assert abs(float(qml_helper.get_num_value()) - 50.0) < 0.1

    def test_num_field_temperature(self, qml_helper):
        """Test creating temperature NumFormField."""
        qml_helper.create_temperature_field()
        assert qml_helper.get_num_unit_type() == "temp"
        assert abs(float(qml_helper.get_num_value()) - 300.0) < 0.1

    def test_int_field_creation(self, qml_helper):
        """Test creating IntFormField instances."""
        qml_helper.create_sample_count_field()

        assert qml_helper.get_int_label() == "Sample Count"
        assert qml_helper.get_int_value() == "50"

    def test_bool_field_enabled(self, qml_helper):
        """Test creating enabled BoolFormField."""
        qml_helper.create_enabled_field()
        assert qml_helper.get_bool_value() is True

    def test_bool_field_debug(self, qml_helper):
        """Test creating debug BoolFormField."""
        qml_helper.create_debug_field()
        assert qml_helper.get_bool_value() is False

    def test_choice_field_creation(self, qml_helper):
        """Test creating ChoiceFormField instances."""
        qml_helper.create_study_type_field()

        assert qml_helper.get_choice_value() == "det"
        assert qml_helper.get_choice_index() == 0

        qml_helper.set_choice_by_index(1)
        assert qml_helper.get_choice_value() == "prb"

    def test_string_field_creation(self, qml_helper):
        """Test creating StringFormField instances."""
        qml_helper.create_name_field()

        assert qml_helper.get_string_label() == "Analysis Name"
        assert qml_helper.get_string_value() == "Test Analysis"

    def test_num_list_field_creation(self, qml_helper):
        """Test creating NumListFormField instances."""
        qml_helper.create_cycle_times_field()

        assert qml_helper.get_num_list_label() == "Cycle Times"
        assert qml_helper.get_num_list_count() == 5

    def test_nullable_field(self, qml_helper):
        """Test nullable NumFormField functionality."""
        qml_helper.create_nullable_float_field()

        assert qml_helper.get_num_is_null() is False

        qml_helper.set_num_null()
        assert qml_helper.get_num_is_null() is True

        qml_helper.set_num_value("50.0")
        assert qml_helper.get_num_is_null() is False
