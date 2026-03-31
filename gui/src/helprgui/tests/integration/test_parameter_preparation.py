"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Integration tests for parameter preparation workflow.

These tests verify that State.get_prepped_param_dict() produces correct
Characterization/Distribution objects that are passed to the backend API.
This is critical for ensuring the refactoring doesn't affect analysis results.

Usage:
    # Run tests comparing against existing golden files
    pytest test_parameter_preparation.py -v

    # Regenerate golden files (do this BEFORE refactoring)
    pytest test_parameter_preparation.py --regenerate-golden
"""
import json
import unittest
from pathlib import Path

import numpy as np

from helprgui import app_settings
from helprgui.models import models
from helprgui.hygu.utils.distributions import Distributions

from probabilistic.capabilities.uncertainty_definitions import (
    DeterministicCharacterization,
    UniformDistribution,
    NormalDistribution,
    LognormalDistribution,
    TruncatedNormalDistribution,
    TruncatedLognormalDistribution,
)


GOLDEN_DIR = Path(__file__).parent / "golden_results"
DELTA = 1e-6


def _serialize_characterization(obj):
    """Serialize a Characterization/Distribution object to a dict for comparison.

    Handles DeterministicCharacterization and all Distribution types from
    probabilistic.capabilities.uncertainty_definitions.

    Note: Distribution objects store parameters in scipy format:
    - nominal: the nominal value
    - parameters: dict with scipy-specific keys (loc, scale, a, b, s, etc.)
    """
    if obj is None:
        return None

    if isinstance(obj, DeterministicCharacterization):
        return {
            'type': 'DeterministicCharacterization',
            'name': obj.name,
            'value': float(obj.value) if obj.value is not None else None,
        }

    elif isinstance(obj, UniformDistribution):
        # Uniform uses loc=lower, scale=range (upper-lower)
        params = obj.parameters
        return {
            'type': 'UniformDistribution',
            'name': obj.name,
            'uncertainty_type': obj.uncertainty_type,
            'nominal': float(obj.nominal) if obj.nominal is not None else None,
            'lower_bound': float(params.get('loc', 0)),
            'upper_bound': float(params.get('loc', 0) + params.get('scale', 0)),
        }

    elif isinstance(obj, NormalDistribution):
        # Normal uses loc=mean, scale=std
        params = obj.parameters
        return {
            'type': 'NormalDistribution',
            'name': obj.name,
            'uncertainty_type': obj.uncertainty_type,
            'nominal': float(obj.nominal) if obj.nominal is not None else None,
            'mean': float(params.get('loc', 0)),
            'std_deviation': float(params.get('scale', 0)),
        }

    elif isinstance(obj, TruncatedNormalDistribution):
        # TruncatedNormal uses loc=mean, scale=std, a/b=normalized bounds
        params = obj.parameters
        mean = params.get('loc', 0)
        std = params.get('scale', 1)
        a = params.get('a', 0)
        b = params.get('b', 0)
        return {
            'type': 'TruncatedNormalDistribution',
            'name': obj.name,
            'uncertainty_type': obj.uncertainty_type,
            'nominal': float(obj.nominal) if obj.nominal is not None else None,
            'mean': float(mean),
            'std_deviation': float(std),
            # Denormalize bounds: bound = mean + a*std
            'lower_bound': float(mean + a * std),
            'upper_bound': float(mean + b * std) if not np.isinf(b) else 'inf',
        }

    elif isinstance(obj, LognormalDistribution):
        # Lognormal uses scale=exp(mu), s=sigma
        params = obj.parameters
        scale = params.get('scale', 1)
        s = params.get('s', 0)
        return {
            'type': 'LognormalDistribution',
            'name': obj.name,
            'uncertainty_type': obj.uncertainty_type,
            'nominal': float(obj.nominal) if obj.nominal is not None else None,
            'mu': float(np.log(scale)) if scale > 0 else 0,
            'sigma': float(s),
        }

    elif isinstance(obj, TruncatedLognormalDistribution):
        # TruncatedLognormal - complex scipy parameterization
        params = obj.parameters
        return {
            'type': 'TruncatedLognormalDistribution',
            'name': obj.name,
            'uncertainty_type': obj.uncertainty_type,
            'nominal': float(obj.nominal) if obj.nominal is not None else None,
            # Store raw scipy params since reverse engineering is complex
            'parameters': {k: float(v) if not np.isinf(v) else ('inf' if v > 0 else '-inf')
                          for k, v in params.items()},
        }

    elif isinstance(obj, Path):
        return str(obj)

    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj

    elif hasattr(obj, '__dict__'):
        # Generic object - try to serialize attributes
        return {'type': type(obj).__name__, 'repr': repr(obj)}

    else:
        return repr(obj)


def _serialize_params(params: dict) -> dict:
    """Serialize the entire params dict for comparison."""
    result = {}
    for key, value in params.items():
        if key in ('session_dir', 'output_dir'):
            # Skip path fields that vary by environment
            continue
        result[key] = _serialize_characterization(value)
    return result


def _compare_params(actual: dict, expected: dict, path: str = "") -> list:
    """Recursively compare parameter dicts, returning list of differences."""
    differences = []

    for key in set(list(actual.keys()) + list(expected.keys())):
        current_path = f"{path}.{key}" if path else key

        if key not in actual:
            differences.append(f"Missing key in actual: {current_path}")
            continue
        if key not in expected:
            differences.append(f"Extra key in actual: {current_path}")
            continue

        actual_val = actual[key]
        expected_val = expected[key]

        if isinstance(expected_val, dict) and isinstance(actual_val, dict):
            differences.extend(_compare_params(actual_val, expected_val, current_path))
        elif isinstance(expected_val, float) and isinstance(actual_val, float):
            if abs(actual_val - expected_val) > DELTA:
                differences.append(
                    f"Value mismatch at {current_path}: {actual_val} != {expected_val} (delta={abs(actual_val - expected_val)})"
                )
        elif actual_val != expected_val:
            differences.append(f"Value mismatch at {current_path}: {actual_val!r} != {expected_val!r}")

    return differences


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


# Global flag for regeneration mode
_REGENERATE_GOLDEN = False


def set_regenerate_mode(value: bool):
    """Set whether to regenerate golden files."""
    global _REGENERATE_GOLDEN
    _REGENERATE_GOLDEN = value


class TestDeterministicParameterPreparation(unittest.TestCase):
    """Tests for deterministic demo parameter preparation."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_det_demo_parameter_preparation(self):
        """Deterministic demo parameters are prepared correctly for API."""
        # Load demo file
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/det_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        # Get prepared parameters
        params = self.state.get_prepped_param_dict()
        serialized = _serialize_params(params)

        filename = "det_demo_params.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, serialized)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        differences = _compare_params(serialized, expected)
        self.assertEqual(differences, [], f"Parameter preparation differences:\n" + "\n".join(differences))

    def test_det_demo_outer_diameter_is_deterministic(self):
        """Outer diameter in det demo should be DeterministicCharacterization."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/det_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()

        outer_diam = params['outer_diameter']
        self.assertIsInstance(outer_diam, DeterministicCharacterization)
        self.assertEqual(outer_diam.name, 'outer_diameter')
        # 36 inches = 0.9144 m
        self.assertAlmostEqual(outer_diam.value, 0.9144, places=4)

    def test_det_demo_max_pressure_is_deterministic(self):
        """Max pressure in det demo should be DeterministicCharacterization."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/det_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()

        max_pressure = params['max_pressure']
        self.assertIsInstance(max_pressure, DeterministicCharacterization)
        self.assertEqual(max_pressure.name, 'max_pressure')
        # 840 psi ≈ 5.79 MPa
        self.assertAlmostEqual(max_pressure.value, 5.79, places=1)


class TestProbabilisticParameterPreparation(unittest.TestCase):
    """Tests for probabilistic demo parameter preparation."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_prb_demo_parameter_preparation(self):
        """Probabilistic demo parameters are prepared correctly for API."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/prb_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()
        serialized = _serialize_params(params)

        filename = "prb_demo_params.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, serialized)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        differences = _compare_params(serialized, expected)

        self.assertEqual(differences, [], f"Parameter preparation differences:\n" + "\n".join(differences))

    def test_prb_demo_has_truncated_normal_distributions(self):
        """Probabilistic demo should contain TruncatedNormalDistribution parameters."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/prb_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()

        # Check that some parameters are probabilistic
        truncated_normal_count = sum(1 for p in params.values() if isinstance(p, TruncatedNormalDistribution))

        self.assertGreater(truncated_normal_count, 0,
                           "Probabilistic demo should have at least one TruncatedNormalDistribution")


class TestSensitivityParameterPreparation(unittest.TestCase):
    """Tests for sensitivity demo parameter preparation."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_sam_demo_parameter_preparation(self):
        """Sensitivity (samples) demo parameters are prepared correctly for API."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/sam_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()
        serialized = _serialize_params(params)

        filename = "sam_demo_params.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, serialized)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        differences = _compare_params(serialized, expected)
        self.assertEqual(differences, [], f"Parameter preparation differences:\n" + "\n".join(differences))

    def test_bnd_demo_parameter_preparation(self):
        """Sensitivity (bounds) demo parameters are prepared correctly for API."""
        demo_file = app_settings.BASE_DIR.joinpath('assets/demo/bnd_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        params = self.state.get_prepped_param_dict()
        serialized = _serialize_params(params)

        filename = "bnd_demo_params.json"

        if _REGENERATE_GOLDEN:
            _save_golden(filename, serialized)
            self.skipTest(f"Regenerated {filename}")

        expected = _load_golden(filename)
        differences = _compare_params(serialized, expected)
        self.assertEqual(differences, [], f"Parameter preparation differences:\n" + "\n".join(differences))


class TestDistributionTypePreparation(unittest.TestCase):
    """Tests for specific distribution type preparation."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_uniform_distribution_preparation(self):
        """Uniform distribution is prepared with correct bounds."""
        # Set up a field with uniform distribution
        self.state.out_diam.distr = Distributions.uni
        self.state.out_diam.lower = 20  # inches
        self.state.out_diam.upper = 24  # inches

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, UniformDistribution)
        self.assertEqual(outer_diam.name, 'outer_diameter')
        self.assertEqual(outer_diam.uncertainty_type, 'aleatory')
        # Bounds in scipy uniform: loc=lower, scale=range
        # So upper = loc + scale
        p = outer_diam.parameters
        lower = p['loc']
        upper = p['loc'] + p['scale']
        self.assertAlmostEqual(lower, 20 * 0.0254, places=4)
        self.assertAlmostEqual(upper, 24 * 0.0254, places=4)

    def test_truncated_normal_distribution_preparation(self):
        """Truncated normal distribution is prepared with correct parameters."""
        # Set up a field with truncated normal distribution
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22  # all in inches
        self.state.out_diam.std = 1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, TruncatedNormalDistribution)
        self.assertEqual(outer_diam.name, 'outer_diameter')
        self.assertEqual(outer_diam.uncertainty_type, 'aleatory')
        # loc=mean, scale=std
        p = outer_diam.parameters
        mean = p['loc']
        std = p['scale']
        # Values should be in meters (SI)
        self.assertAlmostEqual(mean, 22 * 0.0254, places=4)
        self.assertAlmostEqual(std, 1 * 0.0254, places=4)

    def test_truncated_lognormal_distribution_preparation(self):
        """Truncated lognormal distribution is prepared with correct parameters."""
        # Set up a field with truncated lognormal distribution
        self.state.out_diam.distr = Distributions.tlog
        self.state.out_diam.mu = 3.0
        self.state.out_diam.sigma = 0.1
        self.state.out_diam.lower = 20  # inches
        self.state.out_diam.upper = 24  # inches

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, TruncatedLognormalDistribution)
        self.assertEqual(outer_diam.name, 'outer_diameter')
        self.assertEqual(outer_diam.uncertainty_type, 'aleatory')

    def test_epistemic_uncertainty_type(self):
        """Epistemic uncertainty type is correctly set."""
        self.state.out_diam.distr = Distributions.uni
        self.state.out_diam.uncertainty = 'epi'
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertEqual(outer_diam.uncertainty_type, 'epistemic')


class TestUnitConversionInPreparation(unittest.TestCase):
    """Tests that unit conversion is correctly applied during preparation."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_pressure_converted_to_mpa(self):
        """Pressure in psi is converted to MPa in prepared params."""
        self.state.p_max.distr = Distributions.det
        self.state.p_max.unit = 'psi'
        self.state.p_max.value = 1000

        params = self.state.get_prepped_param_dict()
        max_pressure = params['max_pressure']

        # 1000 psi ≈ 6.895 MPa
        self.assertIsInstance(max_pressure, DeterministicCharacterization)
        self.assertAlmostEqual(max_pressure.value, 6.895, places=2)

    def test_distance_converted_to_meters(self):
        """Distance in inches is converted to meters in prepared params."""
        self.state.out_diam.distr = Distributions.det
        self.state.out_diam.unit = 'in'
        self.state.out_diam.value = 24

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        # 24 inches = 0.6096 meters
        self.assertIsInstance(outer_diam, DeterministicCharacterization)
        self.assertAlmostEqual(outer_diam.value, 0.6096, places=4)

    def test_temperature_converted_to_kelvin(self):
        """Temperature in Celsius is converted to Kelvin in prepared params."""
        self.state.temp.distr = Distributions.det
        self.state.temp.unit = 'c'
        self.state.temp.value = 20

        params = self.state.get_prepped_param_dict()
        temperature = params['temperature']

        self.assertIsInstance(temperature, DeterministicCharacterization)
        self.assertAlmostEqual(temperature.value, 293.15, places=1)


class TestChoiceFieldPreparation(unittest.TestCase):
    """Tests for choice field preparation (study_type, crack_assump, etc.)."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_study_type_preserved(self):
        """Study type value is preserved in prepped params."""
        # Note: The mapping to 'sample_type' (deterministic, lhs, etc.)
        # happens in the analysis call, not in get_prepped_param_dict()

        self.state.study_type.set_value_from_key('det')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['study_type'], 'det')

        self.state.study_type.set_value_from_key('prb')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['study_type'], 'prb')

        self.state.study_type.set_value_from_key('sam')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['study_type'], 'sam')

        self.state.study_type.set_value_from_key('bnd')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['study_type'], 'bnd')

    def test_crack_assumption_mapping(self):
        """Crack assumption is mapped correctly to API format."""
        # Proportional
        self.state.crack_assump.set_value_from_key('prop')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['crack_assump'], 'proportional')

        # Fixed
        self.state.crack_assump.set_value_from_key('fix')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['crack_assump'], 'fixed')

        # Independent
        self.state.crack_assump.set_value_from_key('ind')
        params = self.state.get_prepped_param_dict()
        self.assertEqual(params['crack_assump'], 'independent')


class TestDeterministicStudyIgnoresDistribution(unittest.TestCase):
    """Tests that deterministic studies ignore distribution parameters.

    Bug report: "Distribution information does not seem to be ignored when a
    deterministic study is run. Sim never completed when std dev = 0 and
    distribution was shown in the results window."

    The fix ensures that when study_type is 'det', all HelprUncertainField
    values are returned as DeterministicCharacterization, regardless of
    their individual distribution settings.
    """

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_deterministic_study_ignores_truncated_normal_distribution(self):
        """Deterministic study should ignore tnor distribution and use nominal value only."""
        # Set up a field with truncated normal distribution and std=0 (invalid for tnor)
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24
        self.state.out_diam._std = 0  # Bypass setter to set invalid value

        # Set study type to deterministic
        self.state.study_type.set_value_from_key('det')

        # Should NOT raise an error - deterministic study ignores distribution
        params = self.state.get_prepped_param_dict()

        # Should be DeterministicCharacterization, not TruncatedNormalDistribution
        outer_diam = params['outer_diameter']
        self.assertIsInstance(outer_diam, DeterministicCharacterization)
        self.assertEqual(outer_diam.name, 'outer_diameter')

    def test_deterministic_study_ignores_truncated_lognormal_with_zero_sigma(self):
        """Deterministic study should ignore tlog distribution even with sigma=0."""
        # Set up a field with truncated lognormal distribution and sigma=0 (invalid for tlog)
        self.state.out_diam.distr = Distributions.tlog
        self.state.out_diam.mu = 3.0
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24
        self.state.out_diam._sigma = 0  # Bypass setter to set invalid value

        # Set study type to deterministic
        self.state.study_type.set_value_from_key('det')

        # Should NOT raise an error - deterministic study ignores distribution
        params = self.state.get_prepped_param_dict()

        # Should be DeterministicCharacterization, not TruncatedLognormalDistribution
        outer_diam = params['outer_diameter']
        self.assertIsInstance(outer_diam, DeterministicCharacterization)

    def test_deterministic_study_uses_nominal_value(self):
        """Deterministic study should use the nominal value, not mean or other params."""
        # Set up field with different nominal and mean values
        self.state.out_diam.value = 24  # nominal in inches
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22  # different mean
        self.state.out_diam.std = 1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 26

        # Set study type to deterministic
        self.state.study_type.set_value_from_key('det')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, DeterministicCharacterization)
        # Should use nominal value (24 inches = 0.6096 m), not mean
        self.assertAlmostEqual(outer_diam.value, 0.6096, places=4)

    def test_probabilistic_study_uses_distribution(self):
        """Probabilistic study should use the distribution, not just nominal value."""
        # Set up field with truncated normal distribution
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22
        self.state.out_diam.std = 1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        # Set study type to probabilistic
        self.state.study_type.set_value_from_key('prb')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        # Should be TruncatedNormalDistribution for probabilistic study
        self.assertIsInstance(outer_diam, TruncatedNormalDistribution)

    def test_deterministic_study_ignores_uniform_distribution(self):
        """Deterministic study should ignore uniform distribution."""
        self.state.out_diam.distr = Distributions.uni
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        self.state.study_type.set_value_from_key('det')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, DeterministicCharacterization)

    def test_deterministic_study_ignores_truncated_lognormal_distribution(self):
        """Deterministic study should ignore tlog distribution."""
        self.state.out_diam.distr = Distributions.tlog
        self.state.out_diam.mu = 3.0
        self.state.out_diam.sigma = 0.1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        self.state.study_type.set_value_from_key('det')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        self.assertIsInstance(outer_diam, DeterministicCharacterization)

    def test_deterministic_study_converts_all_uncertain_fields(self):
        """Deterministic study should convert ALL HelprUncertainField instances."""
        # Set multiple fields to probabilistic distributions
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22
        self.state.out_diam.std = 1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        self.state.p_max.distr = Distributions.uni
        self.state.p_max.lower = 800
        self.state.p_max.upper = 900

        self.state.study_type.set_value_from_key('det')

        params = self.state.get_prepped_param_dict()

        # Both fields should be DeterministicCharacterization
        self.assertIsInstance(params['outer_diameter'], DeterministicCharacterization)
        self.assertIsInstance(params['max_pressure'], DeterministicCharacterization)

    def test_sensitivity_study_uses_distribution(self):
        """Sensitivity (samples) study should use distributions, not deterministic."""
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22
        self.state.out_diam.std = 1
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        self.state.study_type.set_value_from_key('sam')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        # Should be TruncatedNormalDistribution for sensitivity study
        self.assertIsInstance(outer_diam, TruncatedNormalDistribution)

    def test_bounding_study_uses_distribution(self):
        """Bounding study should use distributions, not deterministic."""
        self.state.out_diam.distr = Distributions.uni
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24

        self.state.study_type.set_value_from_key('bnd')

        params = self.state.get_prepped_param_dict()
        outer_diam = params['outer_diameter']

        # Should be UniformDistribution for bounding study
        self.assertIsInstance(outer_diam, UniformDistribution)


class TestZeroStdSigmaHandling(unittest.TestCase):
    """Tests for handling zero std/sigma in distribution preparation.

    These tests verify that get_prepped_value() raises clear errors when
    std/sigma is zero for probabilistic distributions.
    """

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        self.state = models.State()

    def tearDown(self):
        self.state = None

    def test_truncated_normal_with_zero_std_raises_error(self):
        """TruncatedNormal with std=0 should raise a clear error, not ZeroDivisionError."""
        self.state.out_diam.distr = Distributions.tnor
        self.state.out_diam.mean = 22
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24
        self.state.out_diam._std = 0

        with self.assertRaises(ValueError) as context:
            self.state.out_diam.get_prepped_value()
        self.assertIn('std', str(context.exception).lower())

    def test_truncated_lognormal_with_zero_sigma_raises_error(self):
        """Truncated lognormal with sigma=0 should raise a clear error."""
        self.state.out_diam.distr = Distributions.tlog
        self.state.out_diam.mu = 3.0
        self.state.out_diam.lower = 20
        self.state.out_diam.upper = 24
        self.state.out_diam._sigma = 0

        with self.assertRaises(ValueError) as context:
            self.state.out_diam.get_prepped_value()
        self.assertIn('sigma', str(context.exception).lower())


if __name__ == '__main__':
    # Allow running with regeneration from command line
    import sys
    if '--regenerate-golden' in sys.argv:
        set_regenerate_mode(True)
        sys.argv.remove('--regenerate-golden')

    unittest.main()
