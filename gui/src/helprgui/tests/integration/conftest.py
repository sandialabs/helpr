"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Pytest configuration for integration tests.
"""
import pytest


def pytest_addoption(parser):
    """Add command-line option to regenerate golden files."""
    try:
        parser.addoption(
            "--regenerate-golden",
            action="store_true",
            default=False,
            help="Regenerate golden reference files instead of comparing against them"
        )
    except ValueError:
        # Option already added by another conftest.py
        pass


def pytest_configure(config):
    """Set the global regenerate flag based on command line option."""
    if config.getoption("--regenerate-golden"):
        from . import test_parameter_preparation
        test_parameter_preparation.set_regenerate_mode(True)


@pytest.fixture
def regenerate_golden(request):
    """Fixture to check if --regenerate-golden was passed."""
    return request.config.getoption("--regenerate-golden")
