"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Golden snapshot tests for UncertainField serialization.
These tests compare current behavior against known-good reference files.

Usage:
    # Run tests comparing against existing golden files
    pytest test_golden_snapshots.py -v

    # Regenerate golden files (do this BEFORE refactoring)
    pytest test_golden_snapshots.py --regenerate-golden
"""
import json
import unittest
from pathlib import Path

from ...models.fields_probabilistic import UncertainField
from ...utils.distributions import Distributions, Uncertainties
from ...utils.units_of_measurement import Pressure, Temperature, Distance


GOLDEN_DIR = Path(__file__).parent / "golden"


def _save_golden(filename: str, data: dict):
    """Save data to golden file."""
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    filepath = GOLDEN_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _load_golden(filename: str) -> dict:
    """Load data from golden file."""
    filepath = GOLDEN_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Golden file not found: {filepath}\n"
            f"Run with --regenerate-golden to create it."
        )
    with open(filepath, 'r') as f:
        return json.load(f)


# Global flag for regeneration mode (set by conftest.py)
_REGENERATE_GOLDEN = False


def set_regenerate_mode(value: bool):
    """Set whether to regenerate golden files."""
    global _REGENERATE_GOLDEN
    _REGENERATE_GOLDEN = value


class TestGoldenDeterministic(unittest.TestCase):
    """Golden tests for deterministic distribution."""

    def test_deterministic_pressure_mpa(self):
        """Deterministic pressure field in MPa."""
        field = UncertainField(
            'Test Pressure',
            value=50.0,
            distr=Distributions.det,
            min_value=0,
            max_value=100,
            unit_type=Pressure,
            unit='mpa'
        )

        result = field.to_dict()
        filename = "deterministic_pressure_mpa.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenNormal(unittest.TestCase):
    """Golden tests for normal distribution."""

    def test_normal_pressure_mpa_aleatory(self):
        """Normal distribution with aleatory uncertainty."""
        field = UncertainField(
            'Test Pressure',
            value=50.0,
            distr=Distributions.nor,
            mean=50.0,
            std=10.0,
            min_value=0,
            max_value=100,
            uncertainty=Uncertainties.ale,
            unit_type=Pressure,
            unit='mpa'
        )

        result = field.to_dict()
        filename = "normal_pressure_mpa_aleatory.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)

    def test_normal_temperature_k_epistemic(self):
        """Normal distribution with epistemic uncertainty and temperature."""
        field = UncertainField(
            'Temperature',
            value=300.0,
            distr=Distributions.nor,
            mean=300.0,
            std=15.0,
            min_value=200,
            max_value=400,
            uncertainty=Uncertainties.epi,
            unit_type=Temperature,
            unit='k'
        )

        result = field.to_dict()
        filename = "normal_temperature_k_epistemic.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenLognormal(unittest.TestCase):
    """Golden tests for lognormal distribution."""

    def test_lognormal_pressure_mpa(self):
        """Lognormal distribution for pressure."""
        field = UncertainField(
            'Test Pressure',
            value=50.0,
            distr=Distributions.log,
            mu=3.912,
            sigma=0.2,
            min_value=0,
            max_value=100,
            uncertainty=Uncertainties.ale,
            unit_type=Pressure,
            unit='mpa'
        )

        result = field.to_dict()
        filename = "lognormal_pressure_mpa.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenTruncatedNormal(unittest.TestCase):
    """Golden tests for truncated normal distribution."""

    def test_truncated_normal_distance_m(self):
        """Truncated normal distribution for distance."""
        field = UncertainField(
            'Outer Diameter',
            value=0.5,
            distr=Distributions.tnor,
            mean=0.5,
            std=0.05,
            lower=0.4,
            upper=0.6,
            min_value=0,
            max_value=1,
            uncertainty=Uncertainties.ale,
            unit_type=Distance,
            unit='m'
        )

        result = field.to_dict()
        filename = "truncated_normal_distance_m.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenTruncatedLognormal(unittest.TestCase):
    """Golden tests for truncated lognormal distribution."""

    def test_truncated_lognormal_pressure_mpa(self):
        """Truncated lognormal distribution for pressure."""
        field = UncertainField(
            'Test Pressure',
            value=50.0,
            distr=Distributions.tlog,
            mu=3.912,
            sigma=0.2,
            lower=30.0,
            upper=70.0,
            min_value=0,
            max_value=100,
            uncertainty=Uncertainties.epi,
            unit_type=Pressure,
            unit='mpa'
        )

        result = field.to_dict()
        filename = "truncated_lognormal_pressure_mpa.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenUniform(unittest.TestCase):
    """Golden tests for uniform distribution."""

    def test_uniform_pressure_mpa(self):
        """Uniform distribution for pressure."""
        field = UncertainField(
            'Test Pressure',
            value=50.0,
            distr=Distributions.uni,
            lower=20.0,
            upper=80.0,
            min_value=0,
            max_value=100,
            uncertainty=Uncertainties.ale,
            unit_type=Pressure,
            unit='mpa'
        )

        result = field.to_dict()
        filename = "uniform_pressure_mpa.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenBeta(unittest.TestCase):
    """Golden tests for beta distribution."""

    def test_beta_fraction(self):
        """Beta distribution for a fraction parameter."""
        field = UncertainField(
            'Efficiency Factor',
            value=0.5,
            distr=Distributions.beta,
            alpha=2.0,
            beta=5.0,
            min_value=0,
            max_value=1,
            uncertainty=Uncertainties.ale,
            unit_type=Pressure,  # Using Pressure as placeholder unit type
            unit='mpa'
        )

        result = field.to_dict()
        filename = "beta_fraction.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


class TestGoldenNonStandardUnits(unittest.TestCase):
    """Golden tests for fields with non-standard (non-SI) units."""

    def test_pressure_psi(self):
        """Pressure field in psi (non-SI)."""
        field = UncertainField(
            'Operating Pressure',
            value=1000.0,
            distr=Distributions.nor,
            mean=1000.0,
            std=50.0,
            min_value=0,
            max_value=2000,
            uncertainty=Uncertainties.ale,
            unit=Pressure.psi
        )

        result = field.to_dict()
        filename = "normal_pressure_psi.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)

    def test_distance_inch(self):
        """Distance field in inches (non-SI)."""
        field = UncertainField(
            'Outer Diameter',
            value=24.0,
            distr=Distributions.uni,
            lower=23.5,
            upper=24.5,
            min_value=0,
            max_value=100,
            uncertainty=Uncertainties.ale,
            unit=Distance.inch
        )

        result = field.to_dict()
        filename = "uniform_distance_inch.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)

    def test_temperature_celsius(self):
        """Temperature field in Celsius (non-SI)."""
        field = UncertainField(
            'Operating Temperature',
            value=25.0,
            distr=Distributions.nor,
            mean=25.0,
            std=5.0,
            min_value=-40,
            max_value=100,
            uncertainty=Uncertainties.ale,
            unit=Temperature.c
        )

        result = field.to_dict()
        filename = "normal_temperature_celsius.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, result)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    # Allow running with regeneration from command line
    import sys
    if '--regenerate-golden' in sys.argv:
        set_regenerate_mode(True)
        sys.argv.remove('--regenerate-golden')

    unittest.main()
