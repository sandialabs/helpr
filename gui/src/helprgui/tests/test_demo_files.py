"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests to verify demo .hpr files match the default parameter values in models.py.
When defaults change in State.__init__, run `python scripts/generate_demos.py` to regenerate demo files.
"""
import json
import unittest
from pathlib import Path

from helprgui import app_settings
from helprgui.models.models import State
from helprgui.models.enums import StudyTypes


DELTA = 1e-6

DEMO_DIR = Path(__file__).parent.parent / 'assets' / 'demo'

STUDY_TYPE_FILES = {
    StudyTypes.det: 'det_demo.hpr',
    StudyTypes.prb: 'prb_demo.hpr',
    StudyTypes.sam: 'sam_demo.hpr',
    StudyTypes.bnd: 'bnd_demo.hpr',
}


class TestDemoFileSynchronization(unittest.TestCase):
    """Tests that demo files match the default parameter values defined in models.py.

    These tests will fail when:
    1. Default parameter values in State.__init__ are changed
    2. New fields are added to State
    3. Field serialization format changes

    To fix failing tests, run: python gui/scripts/generate_demos.py
    """

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def _load_demo_file(self, study_type: str) -> dict:
        """Load demo file for the given study type."""
        filename = STUDY_TYPE_FILES[study_type]
        filepath = DEMO_DIR / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _compare_dicts(self, expected: dict, actual: dict, path: str = ""):
        """Recursively compare two dicts, reporting differences."""
        for key in expected:
            full_path = f"{path}.{key}" if path else key
            self.assertIn(key, actual, f"Missing key in demo file: {full_path}")

            exp_val = expected[key]
            act_val = actual[key]

            if isinstance(exp_val, dict):
                self.assertIsInstance(act_val, dict, f"Type mismatch at {full_path}")
                self._compare_dicts(exp_val, act_val, full_path)
            elif isinstance(exp_val, float):
                self.assertAlmostEqual(exp_val, act_val, delta=DELTA,
                                       msg=f"Value mismatch at {full_path}: expected {exp_val}, got {act_val}")
            else:
                self.assertEqual(exp_val, act_val,
                                 f"Value mismatch at {full_path}: expected {exp_val}, got {act_val}")

        # Check for extra keys in actual
        for key in actual:
            full_path = f"{path}.{key}" if path else key
            self.assertIn(key, expected, f"Extra key in demo file: {full_path}")

    def test_det_demo_matches_defaults(self):
        """Deterministic demo file matches State(defaults='det')."""
        state = State(defaults=StudyTypes.det)
        expected = state.to_dict()
        actual = self._load_demo_file(StudyTypes.det)
        self._compare_dicts(expected, actual)

    def test_prb_demo_matches_defaults(self):
        """Probabilistic demo file matches State(defaults='prb')."""
        state = State(defaults=StudyTypes.prb)
        expected = state.to_dict()
        actual = self._load_demo_file(StudyTypes.prb)
        self._compare_dicts(expected, actual)

    def test_sam_demo_matches_defaults(self):
        """Sensitivity (samples) demo file matches State(defaults='sam')."""
        state = State(defaults=StudyTypes.sam)
        expected = state.to_dict()
        actual = self._load_demo_file(StudyTypes.sam)
        self._compare_dicts(expected, actual)

    def test_bnd_demo_matches_defaults(self):
        """Sensitivity (bounds) demo file matches State(defaults='bnd')."""
        state = State(defaults=StudyTypes.bnd)
        expected = state.to_dict()
        actual = self._load_demo_file(StudyTypes.bnd)
        self._compare_dicts(expected, actual)

    def test_all_demo_files_exist(self):
        """All expected demo files exist."""
        for study_type, filename in STUDY_TYPE_FILES.items():
            filepath = DEMO_DIR / filename
            self.assertTrue(filepath.exists(), f"Missing demo file: {filepath}")

    def test_demo_files_are_valid_json(self):
        """All demo files contain valid JSON."""
        for study_type, filename in STUDY_TYPE_FILES.items():
            filepath = DEMO_DIR / filename
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"Invalid JSON in {filename}: {e}")


class TestStateDefaultsParameter(unittest.TestCase):
    """Tests for the State defaults parameter functionality."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def test_default_is_prb(self):
        """State() without defaults parameter uses probabilistic defaults."""
        state = State()
        self.assertEqual(state.study_type.value, StudyTypes.prb)

    def test_det_defaults(self):
        """State(defaults='det') initializes with deterministic defaults."""
        state = State(defaults=StudyTypes.det)
        self.assertEqual(state.study_type.value, StudyTypes.det)
        self.assertEqual(state.n_ale.value, 0)

    def test_prb_defaults(self):
        """State(defaults='prb') initializes with probabilistic defaults."""
        state = State(defaults=StudyTypes.prb)
        self.assertEqual(state.study_type.value, StudyTypes.prb)
        self.assertEqual(state.n_ale.value, 50)

    def test_sam_defaults(self):
        """State(defaults='sam') initializes with sensitivity (samples) defaults."""
        state = State(defaults=StudyTypes.sam)
        self.assertEqual(state.study_type.value, StudyTypes.sam)
        self.assertEqual(state.n_ale.value, 50)

    def test_bnd_defaults(self):
        """State(defaults='bnd') initializes with sensitivity (bounds) defaults."""
        state = State(defaults=StudyTypes.bnd)
        self.assertEqual(state.study_type.value, StudyTypes.bnd)
        self.assertEqual(state.n_ale.value, 0)


if __name__ == '__main__':
    unittest.main()
