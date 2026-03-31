"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.
"""
import unittest
from unittest import mock

from helprgui import app_settings
from helprgui.models import models


class SensitivityPlotStateFieldsTestCase(unittest.TestCase):
    """Tests for sensitivity plot fields on State model."""

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()

    def tearDown(self) -> None:
        self.state = None

    def test_sen_plot_field_exists(self):
        """Verify sen_plot field exists on State."""
        self.assertTrue(hasattr(self.state, 'sen_plot'))

    def test_sen_plot_fad_field_exists(self):
        """Verify sen_plot_fad field exists on State."""
        self.assertTrue(hasattr(self.state, 'sen_plot_fad'))

    def test_sen_plot_defaults_to_empty_string(self):
        """Verify sen_plot defaults to empty string."""
        self.assertEqual(self.state.sen_plot, "")

    def test_sen_plot_fad_defaults_to_empty_string(self):
        """Verify sen_plot_fad defaults to empty string."""
        self.assertEqual(self.state.sen_plot_fad, "")

    def test_do_sen_plot_field_exists(self):
        """Verify do_sen_plot BoolField exists."""
        self.assertTrue(hasattr(self.state, 'do_sen_plot'))
        self.assertIsNotNone(self.state.do_sen_plot)

    def test_sen_plot_can_be_set(self):
        """Verify sen_plot can be assigned a value."""
        self.state.sen_plot = "/path/to/sensitivity.png"
        self.assertEqual(self.state.sen_plot, "/path/to/sensitivity.png")

    def test_sen_plot_fad_can_be_set(self):
        """Verify sen_plot_fad can be assigned a value."""
        self.state.sen_plot_fad = "/path/to/sensitivity_fad.png"
        self.assertEqual(self.state.sen_plot_fad, "/path/to/sensitivity_fad.png")

    def test_sen_data_can_be_set(self):
        """Verify sen_data can be assigned a value."""
        test_data = [{'label': 'test', 'data': [[1, 2], [3, 4]]}]
        self.state.sen_data = test_data
        self.assertEqual(self.state.sen_data, test_data)

    def test_sen_data_fad_can_be_set(self):
        """Verify sen_data_fad can be assigned a value."""
        test_data = [{'label': 'test_fad', 'data': [[5, 6], [7, 8]]}]
        self.state.sen_data_fad = test_data
        self.assertEqual(self.state.sen_data_fad, test_data)


class SensitivityAnalysisResultsTestCase(unittest.TestCase):
    """Tests for sensitivity plot generation in do_crack_evolution_analysis."""

    def test_analysis_results_dict_contains_both_sensitivity_plots_for_sam(self):
        """Verify results dict contains both sen_plot and sen_plot_fad for sampling study."""
        mock_analysis = mock.MagicMock()
        mock_analysis.generate_input_parameter_plots.return_value = {}

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                # Return different data for each call to distinguish them
                mock_plot.side_effect = [
                    (['/path/sen_acrit.png'], [{'label': 'acrit', 'data': [[1, 2]]}]),
                    (['/path/sen_fad.png'], [{'label': 'fad', 'data': [[3, 4]]}])
                ]

                params = self._get_mock_params('sam')
                results = models.do_crack_evolution_analysis(1, params, {})

                self.assertIn('sen_plot', results)
                self.assertIn('sen_data', results)
                self.assertIn('sen_plot_fad', results)
                self.assertIn('sen_data_fad', results)

                self.assertEqual(results['sen_plot'], '/path/sen_acrit.png')
                self.assertEqual(results['sen_plot_fad'], '/path/sen_fad.png')

    def test_analysis_results_dict_contains_both_sensitivity_plots_for_bnd(self):
        """Verify results dict contains both sen_plot and sen_plot_fad for bounding study."""
        mock_analysis = mock.MagicMock()
        mock_analysis.generate_input_parameter_plots.return_value = {}

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                mock_plot.side_effect = [
                    (['/path/sen_acrit.png'], [{'label': 'acrit', 'data': [[1, 2]]}]),
                    (['/path/sen_fad.png'], [{'label': 'fad', 'data': [[3, 4]]}])
                ]

                params = self._get_mock_params('bnd')
                results = models.do_crack_evolution_analysis(1, params, {})

                self.assertIn('sen_plot', results)
                self.assertIn('sen_plot_fad', results)
                self.assertEqual(results['sen_plot'], '/path/sen_acrit.png')
                self.assertEqual(results['sen_plot_fad'], '/path/sen_fad.png')

    def test_plot_sensitivity_called_with_correct_criteria(self):
        """Verify plot_sensitivity_results is called with correct criteria for each plot."""
        mock_analysis = mock.MagicMock()
        mock_analysis.generate_input_parameter_plots.return_value = {}

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                mock_plot.return_value = (['/path/plot.png'], [{'label': 'test', 'data': [[1, 2]]}])

                params = self._get_mock_params('bnd')
                models.do_crack_evolution_analysis(1, params, {})

                # Should be called twice - once for each criteria
                self.assertEqual(mock_plot.call_count, 2)

                # Check first call was for 'Cycles to a(crit)'
                first_call = mock_plot.call_args_list[0]
                self.assertEqual(first_call.kwargs.get('criteria'), 'Cycles to a(crit)')

                # Check second call was for 'Cycles to FAD line'
                second_call = mock_plot.call_args_list[1]
                self.assertEqual(second_call.kwargs.get('criteria'), 'Cycles to FAD line')

    def test_plot_sensitivity_called_with_different_filenames(self):
        """Verify plot_sensitivity_results is called with different filenames to avoid overwriting."""
        mock_analysis = mock.MagicMock()
        mock_analysis.generate_input_parameter_plots.return_value = {}

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                mock_plot.return_value = (['/path/plot.png'], [{'label': 'test', 'data': [[1, 2]]}])

                params = self._get_mock_params('sam')
                models.do_crack_evolution_analysis(1, params, {})

                # Should be called twice with different filenames
                self.assertEqual(mock_plot.call_count, 2)

                first_call = mock_plot.call_args_list[0]
                second_call = mock_plot.call_args_list[1]

                first_filename = first_call.kwargs.get('filename')
                second_filename = second_call.kwargs.get('filename')

                # Filenames should be different to prevent overwriting
                self.assertIsNotNone(first_filename)
                self.assertIsNotNone(second_filename)
                self.assertNotEqual(first_filename, second_filename)

    def test_sensitivity_plots_empty_for_det_study(self):
        """Verify sensitivity plots are empty for deterministic study type."""
        mock_analysis = mock.MagicMock()

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                params = self._get_mock_params('det')
                results = models.do_crack_evolution_analysis(1, params, {})

                # plot_sensitivity_results should not be called for deterministic studies
                mock_plot.assert_not_called()

                # Results should have empty sensitivity data
                self.assertEqual(results['sen_plot'], '')
                self.assertEqual(results['sen_plot_fad'], '')

    def test_sensitivity_plots_not_called_for_prb_study(self):
        """Verify plot_sensitivity_results is not called for probabilistic study type."""
        mock_analysis = mock.MagicMock()

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                params = self._get_mock_params('prb')
                results = models.do_crack_evolution_analysis(1, params, {})

                # plot_sensitivity_results should not be called for probabilistic studies
                mock_plot.assert_not_called()

    def test_sensitivity_plots_not_generated_when_disabled(self):
        """Verify sensitivity plots are not generated when create_sensitivity_plot is False."""
        mock_analysis = mock.MagicMock()
        mock_analysis.generate_input_parameter_plots.return_value = {}

        with mock.patch.object(models, '_do_api_crack_analysis', return_value=mock_analysis):
            with mock.patch.object(models.plots, 'plot_sensitivity_results') as mock_plot:
                params = self._get_mock_params('sam')
                params['create_sensitivity_plot'] = False
                results = models.do_crack_evolution_analysis(1, params, {})

                mock_plot.assert_not_called()
                self.assertEqual(results['sen_plot'], '')
                self.assertEqual(results['sen_plot_fad'], '')

    def _get_mock_params(self, study_type):
        """Create mock params dict for testing."""
        from pathlib import Path
        import tempfile

        return {
            'session_dir': Path(tempfile.gettempdir()),
            'study_type': study_type,
            'analysis_name': 'test_analysis',
            'create_sensitivity_plot': True,
            'create_crack_growth_plot': False,
            'create_fad_plot': False,
            'create_design_curve_plot': False,
            'create_ensemble_plot': False,
            'create_cycle_plot': False,
            'create_pdf_plot': False,
            'create_cdf_plot': False,
            'create_exercised_rates_plot': False,
            'create_failure_assessment_diagram': False,
            'random_loading_profile': None,
        }


class SensitivityResultsFormPropertiesTestCase(unittest.TestCase):
    """Tests for sensitivity plot properties on CrackEvolutionResultsForm."""

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()
        # Create a minimal results form with the state
        from helprgui.forms.results import CrackEvolutionResultsForm
        self.form = CrackEvolutionResultsForm(analysis_id=1, prelim_state=self.state)
        # Update state to be the actual state used by the form
        self.form._state = self.state

    def tearDown(self) -> None:
        self.state = None
        self.form = None

    def test_sen_plot_property_returns_empty_when_no_data(self):
        """Verify sen_plot returns empty string when no data."""
        self.assertEqual(self.form.sen_plot, "")

    def test_sen_plot_fad_property_returns_empty_when_no_data(self):
        """Verify sen_plot_fad returns empty string when no data."""
        self.assertEqual(self.form.sen_plot_fad, "")

    def test_sen_plot_returns_filepath_when_set(self):
        """Verify sen_plot returns filepath when set on state."""
        self.state.sen_plot = "/path/to/sensitivity.png"
        self.assertEqual(self.form.sen_plot, "/path/to/sensitivity.png")

    def test_sen_plot_fad_returns_filepath_when_set(self):
        """Verify sen_plot_fad returns filepath when set on state."""
        self.state.sen_plot_fad = "/path/to/sensitivity_fad.png"
        self.assertEqual(self.form.sen_plot_fad, "/path/to/sensitivity_fad.png")

    def test_sensitivity_data_returns_empty_when_plot_disabled(self):
        """Verify sensitivity_data returns empty when do_sen_plot is False."""
        self.state.do_sen_plot.value = False
        self.state.sen_plot = "/path/to/plot.png"
        self.state.sen_data = [{'label': 'test', 'data': [[1, 2], [3, 4]]}]
        self.assertEqual(self.form.sensitivity_data, '')

    def test_sensitivity_data_fad_returns_empty_when_plot_disabled(self):
        """Verify sensitivity_data_fad returns empty when do_sen_plot is False."""
        self.state.do_sen_plot.value = False
        self.state.sen_plot_fad = "/path/to/plot.png"
        self.state.sen_data_fad = [{'label': 'test', 'data': [[1, 2], [3, 4]]}]
        self.assertEqual(self.form.sensitivity_data_fad, '')

    def test_sensitivity_data_returns_json_when_enabled(self):
        """Verify sensitivity_data returns valid JSON when enabled."""
        import json

        self.state.do_sen_plot.value = True
        self.state.sen_plot = "/path/to/plot.png"
        self.state.sen_data = [
            {'label': 'outer_diameter', 'data': [[100, 0.5], [200, 0.6]]},
            {'label': 'wall_thickness', 'data': [[100, 0.4], [200, 0.7]]}
        ]

        result = self.form.sensitivity_data
        self.assertNotEqual(result, '')

        parsed = json.loads(result)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['label'], 'outer_diameter')
        self.assertEqual(parsed[1]['label'], 'wall_thickness')

    def test_sensitivity_data_fad_returns_json_when_enabled(self):
        """Verify sensitivity_data_fad returns valid JSON when enabled."""
        import json

        self.state.do_sen_plot.value = True
        self.state.sen_plot_fad = "/path/to/plot.png"
        self.state.sen_data_fad = [
            {'label': 'outer_diameter', 'data': [[150, 0.3], [250, 0.8]]},
            {'label': 'wall_thickness', 'data': [[150, 0.2], [250, 0.9]]}
        ]

        result = self.form.sensitivity_data_fad
        self.assertNotEqual(result, '')

        parsed = json.loads(result)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['label'], 'outer_diameter')
        self.assertEqual(parsed[1]['label'], 'wall_thickness')


if __name__ == '__main__':
    unittest.main()
