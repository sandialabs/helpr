"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.
"""
import unittest
from unittest import mock

from probabilistic.capabilities.uncertainty_definitions import DeterministicCharacterization

from helprgui import app_settings
from helprgui.models import models
from helprgui.models.fields import HelprUncertainField


class DeterministicIntermediatesFieldTestCase(unittest.TestCase):
    """Tests for the use_deterministic_intermediates field."""

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()

    def tearDown(self) -> None:
        self.state = None

    def test_field_exists(self):
        """Verify use_deterministic_intermediates field exists on State."""
        self.assertTrue(hasattr(self.state, 'use_deterministic_intermediates'))

    def test_field_defaults_to_true(self):
        """Verify use_deterministic_intermediates defaults to True."""
        self.assertTrue(self.state.use_deterministic_intermediates.value)

    def test_field_can_be_set_to_false(self):
        """Verify use_deterministic_intermediates can be toggled off."""
        self.state.use_deterministic_intermediates.value = False
        self.assertFalse(self.state.use_deterministic_intermediates.value)


class GetPreppedParamDictForceDeterministicTestCase(unittest.TestCase):
    """Tests for the force_deterministic parameter in get_prepped_param_dict."""

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()
        # Ensure we're in probabilistic mode with uncertain distributions
        self.state.study_type.set_value_from_key('prb')

    def tearDown(self) -> None:
        self.state = None

    def test_without_force_deterministic_uses_distributions(self):
        """In probabilistic mode without force, uncertain fields use their distributions."""
        # Disable the intermediate override to test normal behavior
        self.state.use_deterministic_intermediates.value = False

        params = self.state.get_prepped_param_dict(force_deterministic=False)

        # out_diam (slug: outer_diameter) has a uniform distribution in prb mode default
        out_diam_param = params['outer_diameter']
        # Should NOT be a DeterministicCharacterization
        self.assertNotIsInstance(out_diam_param, DeterministicCharacterization)

    def test_with_force_deterministic_uses_deterministic_characterization(self):
        """With force_deterministic=True, all uncertain fields become DeterministicCharacterization."""
        params = self.state.get_prepped_param_dict(force_deterministic=True)

        # Check that all HelprUncertainField parameters are DeterministicCharacterization
        for field in self.state.fields:
            if isinstance(field, HelprUncertainField):
                param = params.get(field.slug)
                if param is not None:
                    self.assertIsInstance(
                        param,
                        DeterministicCharacterization,
                        f"Field {field.slug} should be DeterministicCharacterization when force_deterministic=True"
                    )

    def test_force_deterministic_uses_nominal_values(self):
        """With force_deterministic=True, DeterministicCharacterization uses the nominal value."""
        # Set a specific value
        self.state.out_diam.value = 30.0

        params = self.state.get_prepped_param_dict(force_deterministic=True)

        # out_diam field has slug 'outer_diameter'
        out_diam_param = params['outer_diameter']
        self.assertIsInstance(out_diam_param, DeterministicCharacterization)
        # The value in the characterization should match the field's internal value
        self.assertAlmostEqual(out_diam_param.value, self.state.out_diam._value, places=6)

    def test_force_deterministic_in_det_mode_still_works(self):
        """force_deterministic=True works even when already in deterministic mode."""
        self.state.study_type.set_value_from_key('det')

        params = self.state.get_prepped_param_dict(force_deterministic=True)

        for field in self.state.fields:
            if isinstance(field, HelprUncertainField):
                param = params.get(field.slug)
                if param is not None:
                    self.assertIsInstance(param, DeterministicCharacterization)

    def test_force_deterministic_overrides_study_type_in_params(self):
        """force_deterministic=True sets study_type to 'det' in params dict."""
        # Start in probabilistic mode
        self.state.study_type.set_value_from_key('prb')
        self.assertEqual(self.state.study_type.value, 'prb')

        params = self.state.get_prepped_param_dict(force_deterministic=True)

        # study_type in params should be 'det' regardless of actual study type
        self.assertEqual(params['study_type'], 'det')

    def test_force_deterministic_zeros_aleatory_samples(self):
        """force_deterministic=True sets aleatory_samples to 0 in params dict."""
        self.state.study_type.set_value_from_key('prb')
        self.state.n_ale.value = 50

        params = self.state.get_prepped_param_dict(force_deterministic=True)

        self.assertEqual(params['aleatory_samples'], 0)

    def test_force_deterministic_zeros_epistemic_samples(self):
        """force_deterministic=True sets epistemic_samples to 0 in params dict."""
        self.state.study_type.set_value_from_key('prb')
        self.state.n_epi.value = 5

        params = self.state.get_prepped_param_dict(force_deterministic=True)

        self.assertEqual(params['epistemic_samples'], 0)

    def test_without_force_deterministic_preserves_study_type(self):
        """Without force_deterministic, study_type is preserved."""
        self.state.study_type.set_value_from_key('prb')

        params = self.state.get_prepped_param_dict(force_deterministic=False)

        self.assertEqual(params['study_type'], 'prb')

    def test_without_force_deterministic_preserves_sample_counts(self):
        """Without force_deterministic, sample counts are preserved."""
        self.state.study_type.set_value_from_key('prb')
        self.state.n_ale.value = 50
        self.state.n_epi.value = 5

        params = self.state.get_prepped_param_dict(force_deterministic=False)

        self.assertEqual(params['aleatory_samples'], 50)
        self.assertEqual(params['epistemic_samples'], 5)


class IntermediateRefreshOverrideTestCase(unittest.TestCase):
    """Tests for _do_intermediate_refresh using the deterministic override."""

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()
        # Start in probabilistic mode
        self.state.study_type.set_value_from_key('prb')

    def tearDown(self) -> None:
        self.state = None

    def test_intermediate_refresh_uses_deterministic_when_override_enabled(self):
        """When use_deterministic_intermediates is True, refresh uses deterministic mode."""
        self.state.use_deterministic_intermediates.value = True

        with mock.patch.object(models, '_calc_intermediate_params') as mock_calc:
            mock_calc.return_value = {
                'r_ratio': 0.75,
                'f_ratio': 1.0,
                'smys': 50.0,
                'a_c': 0.1,
                't_r': 0.05,
                'a_m': 0.001,
            }

            self.state._do_intermediate_refresh()

            # Verify _calc_intermediate_params was called with 'deterministic'
            mock_calc.assert_called_once()
            _, sample_type = mock_calc.call_args[0]
            self.assertEqual(sample_type, 'deterministic')

    def test_intermediate_refresh_uses_actual_study_type_when_override_disabled(self):
        """When use_deterministic_intermediates is False, refresh uses actual study type."""
        self.state.use_deterministic_intermediates.value = False
        self.state.study_type.set_value_from_key('prb')

        with mock.patch.object(models, '_calc_intermediate_params') as mock_calc:
            mock_calc.return_value = {
                'r_ratio': 0.75,
                'f_ratio': 1.0,
                'smys': 50.0,
                'a_c': 0.1,
                't_r': 0.05,
                'a_m': 0.001,
            }

            self.state._do_intermediate_refresh()

            # Verify _calc_intermediate_params was called with 'lhs' (probabilistic)
            mock_calc.assert_called_once()
            _, sample_type = mock_calc.call_args[0]
            self.assertEqual(sample_type, 'lhs')

    def test_intermediate_refresh_passes_force_deterministic_to_get_prepped_param_dict(self):
        """Verify that get_prepped_param_dict is called with correct force_deterministic value."""
        self.state.use_deterministic_intermediates.value = True

        with mock.patch.object(self.state, 'get_prepped_param_dict', wraps=self.state.get_prepped_param_dict) as mock_prep:
            with mock.patch.object(models, '_calc_intermediate_params') as mock_calc:
                mock_calc.return_value = {
                    'r_ratio': 0.75,
                    'f_ratio': 1.0,
                    'smys': 50.0,
                    'a_c': 0.1,
                    't_r': 0.05,
                    'a_m': 0.001,
                }

                self.state._do_intermediate_refresh()

                mock_prep.assert_called_once_with(force_deterministic=True)

    def test_intermediate_refresh_force_deterministic_false_when_override_disabled(self):
        """Verify get_prepped_param_dict called with force_deterministic=False when override disabled."""
        self.state.use_deterministic_intermediates.value = False

        with mock.patch.object(self.state, 'get_prepped_param_dict', wraps=self.state.get_prepped_param_dict) as mock_prep:
            with mock.patch.object(models, '_calc_intermediate_params') as mock_calc:
                mock_calc.return_value = {
                    'r_ratio': 0.75,
                    'f_ratio': 1.0,
                    'smys': 50.0,
                    'a_c': 0.1,
                    't_r': 0.05,
                    'a_m': 0.001,
                }

                self.state._do_intermediate_refresh()

                mock_prep.assert_called_once_with(force_deterministic=False)


if __name__ == '__main__':
    unittest.main()
