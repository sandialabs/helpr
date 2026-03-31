"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Lightweight integration tests for analysis execution.

These tests verify that the full analysis pipeline executes successfully
and returns the expected result structure. They use minimal sample sizes
and disable plot generation to keep execution fast.

Unlike the parameter preparation tests, these tests actually run the
HELPR analysis engine to catch regressions in the execution path.

Usage:
    pytest test_analysis_execution.py -v
"""
import tempfile
import shutil
import unittest
from pathlib import Path

from helprgui import app_settings
from helprgui.models import models
from helprgui.models.models import do_crack_evolution_analysis
from helpr import api


class AnalysisExecutionTestBase(unittest.TestCase):
    """Base class for analysis execution tests with common setup/teardown."""

    @classmethod
    def setUpClass(cls):
        app_settings.init()

    def setUp(self):
        """Create State and temp directory for each test."""
        self.state = models.State()
        self.temp_dir = Path(tempfile.mkdtemp(prefix='helpr_test_'))
        # Use temp dir as session directory
        app_settings.SESSION_DIR = self.temp_dir

    def tearDown(self):
        """Clean up temp directory after each test."""
        self.state = None
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _prepare_minimal_params(self, study_type: str = 'det') -> dict:
        """Prepare parameters with minimal samples and plots disabled.

        Args:
            study_type: One of 'det', 'prb', 'sam', 'bnd'

        Returns:
            Parameter dict ready for analysis execution.
        """
        # Load the corresponding demo file
        demo_file = app_settings.BASE_DIR.joinpath(f'assets/demo/{study_type}_demo.hpr')
        self.state.load_data_from_file(demo_file.as_posix())

        # Minimize sample sizes for fast execution
        # Note: prb postprocessing uses single_pipe_index=2, so need at least 3 samples
        if study_type in ('prb', 'sam'):
            self.state.n_ale.set_from_model(3)
            self.state.n_epi.set_from_model(0)

        # Disable all plot generation for speed
        self.state.do_crack_growth_plot.set_from_model(False)
        self.state.do_design_curve_plot.set_from_model(False)
        self.state.do_fad_plot.set_from_model(False)
        self.state.do_ensemble_plot.set_from_model(False)
        self.state.do_cycle_plot.set_from_model(False)
        self.state.do_pdf_plot.set_from_model(False)
        self.state.do_cdf_plot.set_from_model(False)
        self.state.do_sen_plot.set_from_model(False)

        # Get prepared parameters
        params = self.state.get_prepped_param_dict()

        # Add session directory for output
        params['session_dir'] = self.temp_dir

        return params

    def _assert_common_result_structure(self, results: dict, analysis_id: int):
        """Assert common result structure present in all study types."""
        self.assertIn('status', results)
        self.assertEqual(results['status'], 1, f"Analysis failed: {results.get('message', 'No message')}")

        self.assertIn('analysis_id', results)
        self.assertEqual(results['analysis_id'], analysis_id)

        self.assertIn('crack_analysis', results)
        self.assertIsNotNone(results['crack_analysis'])
        self.assertIsInstance(results['crack_analysis'], api.CrackEvolutionAnalysis)

        self.assertIn('output_dir', results)
        self.assertTrue(results['output_dir'].exists())


class TestDeterministicAnalysisExecution(AnalysisExecutionTestBase):
    """Tests for deterministic analysis execution."""

    def test_det_analysis_executes_successfully(self):
        """Deterministic analysis should execute and return valid results."""
        params = self._prepare_minimal_params('det')
        analysis_id = 1
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)

        self._assert_common_result_structure(results, analysis_id)

    def test_det_analysis_result_structure(self):
        """Deterministic analysis should return det-specific result keys."""
        params = self._prepare_minimal_params('det')
        analysis_id = 2
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)

        # Deterministic-specific keys (even if empty when plots disabled)
        self.assertIn('crack_growth_plot', results)
        self.assertIn('crack_growth_data', results)
        self.assertIn('design_curve_plot', results)
        self.assertIn('design_curve_data', results)
        self.assertIn('fad_plot', results)
        self.assertIn('fad_data', results)

    def test_det_analysis_crack_analysis_has_results(self):
        """Deterministic analysis crack_analysis object should have results."""
        params = self._prepare_minimal_params('det')
        analysis_id = 3
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)

        crack_analysis = results['crack_analysis']
        # The analysis object should have been populated after perform_study()
        self.assertIsNotNone(crack_analysis)


class TestProbabilisticAnalysisExecution(AnalysisExecutionTestBase):
    """Tests for probabilistic (LHS) analysis execution."""

    def test_prb_analysis_executes_successfully(self):
        """Probabilistic analysis should execute and return valid results."""
        params = self._prepare_minimal_params('prb')
        analysis_id = 10
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self._assert_common_result_structure(results, analysis_id)

    def test_prb_analysis_result_structure(self):
        """Probabilistic analysis should return prb-specific result keys."""
        params = self._prepare_minimal_params('prb')
        analysis_id = 11
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)

        self.assertIn('ensemble_plot', results)
        self.assertIn('ensemble_data', results)
        self.assertIn('cycle_plot', results)
        self.assertIn('cycle_data', results)
        self.assertIn('pdf_plot', results)
        self.assertIn('pdf_data', results)
        self.assertIn('cdf_plot', results)
        self.assertIn('cdf_data', results)
        self.assertIn('input_param_plots', results)


class TestSensitivityAnalysisExecution(AnalysisExecutionTestBase):
    """Tests for sensitivity analysis execution (both bnd and sam)."""

    def test_bnd_analysis_executes_successfully(self):
        """Bounding sensitivity analysis should execute and return valid results."""
        params = self._prepare_minimal_params('bnd')
        analysis_id = 20
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self._assert_common_result_structure(results, analysis_id)

    def test_bnd_analysis_result_structure(self):
        """Bounding analysis should return sensitivity-specific result keys."""
        params = self._prepare_minimal_params('bnd')
        analysis_id = 21
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self.assertIn('sen_plot', results)
        self.assertIn('sen_data', results)
        self.assertIn('input_param_plots', results)

    def test_sam_analysis_executes_successfully(self):
        """Sample sensitivity analysis should execute and return valid results."""
        params = self._prepare_minimal_params('sam')
        analysis_id = 30
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self._assert_common_result_structure(results, analysis_id)

    def test_sam_analysis_result_structure(self):
        """Sample sensitivity analysis should return sensitivity-specific result keys."""
        params = self._prepare_minimal_params('sam')
        analysis_id = 31
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self.assertIn('sen_plot', results)
        self.assertIn('sen_data', results)
        self.assertIn('input_param_plots', results)


class TestAnalysisErrorHandling(AnalysisExecutionTestBase):
    """Tests for analysis error handling paths."""

    def test_analysis_returns_error_status_on_invalid_input(self):
        """Analysis with invalid inputs should return error status, not raise exception."""
        params = self._prepare_minimal_params('det')

        # Create an invalid configuration to force physics error: set min_pressure > max_pressure
        from probabilistic.capabilities.uncertainty_definitions import DeterministicCharacterization
        params['min_pressure'] = DeterministicCharacterization(name='min_pressure', value=100)
        params['max_pressure'] = DeterministicCharacterization(name='max_pressure', value=1)

        analysis_id = 99
        global_status_dict = {}

        # Should not raise - should return error status
        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)
        self.assertIn('status', results)
        self.assertEqual(results['status'], -1, "Expected error status -1 for invalid inputs")
        self.assertIn('analysis_id', results)


class TestOutputDirectoryCreation(AnalysisExecutionTestBase):
    """Tests for output directory handling."""

    def test_output_directory_created_on_success(self):
        """Successful analysis should create output directory."""
        params = self._prepare_minimal_params('det')
        analysis_id = 50
        global_status_dict = {}

        results = do_crack_evolution_analysis(analysis_id, params, global_status_dict)

        self.assertEqual(results['status'], 1)
        self.assertIn('output_dir', results)
        self.assertTrue(results['output_dir'].exists())
        self.assertTrue(results['output_dir'].is_dir())


if __name__ == '__main__':
    unittest.main()
