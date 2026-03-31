"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Pytest configuration and fixtures for regression tests.
"""
import pytest
from pathlib import Path


def pytest_addoption(parser):
    """Add custom command line options for regression tests."""
    try:
        parser.addoption(
            "--regenerate-golden",
            action="store_true",
            default=False,
            help="Regenerate golden snapshot files instead of comparing against them"
        )
    except ValueError:
        # Option already added by another conftest.py
        pass


def pytest_configure(config):
    """Configure test session based on command line options."""
    if config.getoption("--regenerate-golden", default=False):
        # Set the regeneration mode in the golden snapshots module
        from . import test_golden_snapshots
        test_golden_snapshots.set_regenerate_mode(True)


@pytest.fixture
def regenerate_golden(request) -> bool:
    """Fixture to check if golden files should be regenerated."""
    return request.config.getoption("--regenerate-golden")


@pytest.fixture
def golden_dir() -> Path:
    """Path to the golden snapshot files directory."""
    return Path(__file__).parent / "golden"
