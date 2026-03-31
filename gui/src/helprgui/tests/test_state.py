"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.
"""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from helprgui import app_settings

from helprgui.models import models
from helprgui.forms import app
from helprgui.hygu.displays import QueueDisplay
from . import test_utils

DELTA = 1e-4


class StateInitTestCase(unittest.TestCase):
    """Tests GUI initialization of datastore. """

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()

    def tearDown(self) -> None:
        self.state = None
        self.out_diam_c = None
        self.thickness_c = None

    def test_params_exist(self):
        """Verify that all parameters exist in datastore. """
        self.assertIsNotNone(self.state.seed)
        self.assertIsNotNone(self.state.n_epi)
        self.assertIsNotNone(self.state.n_ale)
        self.assertIsNotNone(self.state.study_type)

        self.assertIsNotNone(self.state.out_diam)
        self.assertIsNotNone(self.state.thickness)
        self.assertIsNotNone(self.state.p_max)
        self.assertIsNotNone(self.state.p_min)
        self.assertIsNotNone(self.state.temp)
        self.assertIsNotNone(self.state.vol_h2)
        self.assertIsNotNone(self.state.yield_str)
        self.assertIsNotNone(self.state.frac_resist)
        self.assertIsNotNone(self.state.crack_dep)
        self.assertIsNotNone(self.state.crack_len)
        self.assertIsNotNone(self.state.surface)
        self.assertIsNotNone(self.state.stress_intensity)

        self.assertIsNotNone(self.state.do_cycle_plot)
        self.assertIsNotNone(self.state.do_fad_plot)
        self.assertIsNotNone(self.state.do_design_curve_plot)
        self.assertIsNotNone(self.state.do_ensemble_plot)
        self.assertIsNotNone(self.state.do_pdf_plot)
        self.assertIsNotNone(self.state.do_cdf_plot)
        self.assertIsNotNone(self.state.do_sen_plot)

    def test_params_set_during_init(self):
        """Verify that parameters have default values. """
        self.assertTrue(self.state.study_type.value == 'prb')
        self.assertAlmostEqual(self.state.out_diam.value, 22)
        self.assertAlmostEqual(self.state.out_diam.value_raw, 0.5588, places=4)
        self.assertAlmostEqual(self.state.thickness.value, 0.281)
        self.assertAlmostEqual(self.state.thickness.value_raw, 0.0071374, places=4)


class StateAnalysisTestCase(unittest.TestCase):
    """Tests interactions between datastore and backend analysis calls. """

    def setUp(self) -> None:
        app_settings.init()
        self.appform = app.HelprAppForm()
        self.queue = QueueDisplay()
        self.appform.set_queue(self.queue)

        self.state = self.appform.db

        self.sleep_t = 1
        self.delay_t = 1
        self.guard_t = 0

    def tearDown(self) -> None:
        self.appform.shutdown()
        self.appform = None
        self.queue = None
        self.state = None
        self.guard_t = 0

    # @unittest.skip
    def test_default_analysis_request_succeeds(self):
        """Multiprocessed analysis with default inputs completes successfully. """
        real_func = self.appform.analysis_finished_callback

        self.appform.analysis_finished_callback = mock.Mock(name='analysis_finished_callback')
        self.appform.request_analysis()

        # Wait for analysis to finish. TODO: more graceful way to do this.
        test_utils.wait_for_analysis(self)

        self.appform.analysis_finished_callback.assert_called_once()

        state_obj, result_dict = self.appform.analysis_finished_callback.call_args[0]
        self.assertIsInstance(state_obj, models.State)

        self.assertIsInstance(result_dict, dict)
        self.assertTrue('status' in result_dict)
        self.assertTrue(result_dict['status'] == 1)

        self.appform.analysis_finished_callback = real_func

    # @unittest.skip
    def test_analysis_with_multiprocess_critical_error_is_gracefully_handled(self):
        """Critical error during multiprocessed analysis is handled by callback, yielding state update. """
        real_func = models.do_crack_evolution_analysis
        models.do_crack_evolution_analysis = mock.Mock(name='do_crack_evolution_analysis')  # throws error because mock not pickleable

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self)

        self.assertTrue(len(self.appform.result_forms) == 1)
        ac = self.appform.result_forms[1]
        self.assertTrue(ac.state.analysis_id == 1)
        self.assertTrue(ac._finished)
        self.assertTrue(ac.state.is_finished)
        self.assertTrue(ac.state.has_error)

        models.do_crack_evolution_analysis = real_func

    # @unittest.skip
    def test_values_sent_to_api_match_form_inputs(self):
        self.state.p_min.unit = 'bar'
        self.state.p_min.value = 40  # 4 MPa
        self.state.p_min.a = 40
        self.state.p_min.c = 40
        self.state.p_min.d = 50

        self.state.crack_dep.value = 30

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self, t_max=25)

        delta = 0.01
        ac = self.appform.result_forms[1]
        # compare cloned analysis state instance with original (active form)
        self.assertEqual(self.state.p_min.unit, ac.state.p_min.unit)
        self.assertEqual(self.state.p_min.uncertainty, ac.state.p_min.uncertainty)
        self.assertAlmostEqual(self.state.p_min.value, ac.state.p_min.value, delta=delta)

        self.assertAlmostEqual(ac.state.p_min.value_raw, 4.0, delta=delta)

        self.assertAlmostEqual(self.state.crack_dep.value, ac.state.crack_dep.value, delta=delta)
        self.assertAlmostEqual(self.state.out_diam.value, ac.state.out_diam.value, delta=delta)

    # @unittest.skip
    def test_det_study_creates_plots(self):
        self.state.study_type.set_value_from_key('det')
        self.appform.request_analysis()

        test_utils.wait_for_analysis(self)

        ac = self.appform.result_forms[1]
        self.assertTrue(ac.state.study_type.value == 'det')
        self.assertTrue(ac.state.do_crack_growth_plot)
        self.assertTrue(ac.state.do_design_curve_plot)
        self.assertTrue(ac.state.do_fad_plot)

        self.assertTrue(Path(ac.state.crack_growth_plot).exists())
        self.assertTrue(Path(ac.state.design_curve_plot).exists())
        self.assertTrue(Path(ac.state.fad_plot).exists())

    # @unittest.skip
    def test_prb_study_creates_plots(self):
        self.appform.load_prb_demo()

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self, t_max=25)

        ac = self.appform.result_forms[1]
        self.assertTrue(ac.state.study_type.value == 'prb')
        self.assertTrue(ac.state.do_fad_plot)
        self.assertTrue(ac.state.do_ensemble_plot)
        self.assertTrue(ac.state.do_cycle_plot)
        self.assertTrue(ac.state.do_pdf_plot)
        self.assertTrue(ac.state.do_cdf_plot)

        self.assertTrue(Path(ac.state.fad_plot).exists())
        self.assertTrue(Path(ac.state.ensemble_plot).exists())
        self.assertTrue(Path(ac.state.cycle_plot).exists())
        self.assertTrue(Path(ac.state.pdf_plot).exists())
        self.assertTrue(Path(ac.state.cdf_plot).exists())

    # @unittest.skip
    def test_second_det_study_creates_new_plots(self):
        self.state.study_type.set_value_from_key('det')

        self.appform.request_analysis()
        time.sleep(1)
        self.appform.request_analysis()

        test_utils.wait_for_analysis(self, n_complete=2, t_max=20)

        ac1 = self.appform.result_forms[1]
        plot1_filepath = ac1.state.crack_growth_plot
        self.assertTrue(Path(plot1_filepath).exists())

        ac2 = self.appform.result_forms[2]
        plot2_filepath = ac2.state.crack_growth_plot
        self.assertTrue(Path(plot2_filepath).exists())

        self.assertIsNotNone(plot1_filepath)
        self.assertIsNotNone(plot2_filepath)
        print(plot1_filepath)
        print(plot2_filepath)
        self.assertTrue(ac1.analysis_id != ac2.analysis_id)
        self.assertTrue(plot1_filepath != plot2_filepath)


class ImaStateTestCase(unittest.TestCase):
    """Tests that IMA uses the completed analysis state, not the current form state."""

    def setUp(self) -> None:
        app_settings.init()
        self.appform = app.HelprAppForm()
        self.queue = QueueDisplay()
        self.appform.set_queue(self.queue)
        self.state = self.appform.db

        self.sleep_t = 1
        self.delay_t = 1
        self.guard_t = 0

    def tearDown(self) -> None:
        self.appform.shutdown()
        self.appform = None
        self.queue = None
        self.state = None
        self.guard_t = 0

    def test_ima_uses_completed_analysis_state_not_current_form(self):
        """IMA params must come from the completed analysis, not the live form."""
        # Run a det analysis with default outer diameter (~22 in)
        self.state.study_type.set_value_from_key('det')
        original_od_raw = self.state.out_diam.value_raw

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self)

        # Verify analysis completed
        result_form = self.appform.result_forms[1]
        self.assertTrue(result_form._finished)
        completed_od_raw = result_form.state.out_diam.value_raw
        self.assertAlmostEqual(completed_od_raw, original_od_raw, places=6)

        # Now change the live form state to a very different value
        self.state.out_diam.value = 50.0  # 50 inches, very different from default ~22
        changed_od_raw = self.state.out_diam.value_raw
        self.assertNotAlmostEqual(changed_od_raw, completed_od_raw, places=2)

        # Verify directly that request_inspection_mitigation_analysis builds
        # params from the completed state, not self.db
        # We intercept at the thread level to capture the params dict before it's sent
        captured_params = {}
        real_request = self.appform.thread.request_new_analysis

        def capturing_request(state_data, analysis_func, started_cb, finished_cb):
            if isinstance(state_data, dict):
                captured_params.update(state_data)
            return real_request(state_data, analysis_func, started_cb, finished_cb)

        self.appform.thread.request_new_analysis = capturing_request

        try:
            self.appform.request_inspection_mitigation_analysis(1)

            # The outer_diameter in params must match the completed analysis, not the form
            self.assertIn('outer_diameter', captured_params)
            ima_od = captured_params['outer_diameter']
            # Extract the value - it's a Characterization object with a .value attribute
            ima_od_val = ima_od.value if hasattr(ima_od, 'value') else ima_od
            self.assertAlmostEqual(float(ima_od_val), completed_od_raw, places=4,
                                   msg="IMA must use the completed analysis state, not the current form")
            # Ensure it does NOT match the changed form value
            self.assertNotAlmostEqual(float(ima_od_val), changed_od_raw, places=2,
                                      msg="IMA must NOT use the current form state")
        finally:
            self.appform.thread.request_new_analysis = real_request


class StateHistoryTestCase(unittest.TestCase):
    """Tests functionality of data history tracking, undo, and redo. """

    def setUp(self) -> None:
        app_settings.init()
        from helprgui.hygu.forms.fields_probabilistic import UncertainFormField
        from helprgui.forms.app import HelprAppForm

        self.appform = HelprAppForm()

        self.state = self.appform.db
        self.out_diam_c = UncertainFormField(param=self.appform.db.out_diam)
        self.thickness_c = UncertainFormField(param=self.appform.db.thickness)

    def tearDown(self) -> None:
        self.appform.shutdown()
        self.appform = None
        self.state = None
        self.out_diam_c = None
        self.thickness_c = None

    def test_initial_history_has_one_entry(self):
        self.assertEqual(len(self.state._history), 1)
        self.assertEqual(len(self.state._redo_history), 0)

    def test_new_history_entry_after_val_change(self):
        self.assertEqual(len(self.state._history), 1)
        self.assertEqual(len(self.state._redo_history), 0)
        self.out_diam_c.value = 4
        self.assertAlmostEqual(self.state.out_diam.value, 4)
        self.assertEqual(len(self.state._history), 2)

    def test_new_history_entry_after_unit_change(self):
        self.assertEqual(len(self.state._history), 1)
        self.assertEqual(len(self.state._redo_history), 0)
        self.out_diam_c.unit = 'm'
        self.assertEqual(len(self.state._history), 2)

    def test_one_new_history_entry_after_file_load(self):
        # Avoid importing data that matches current
        fpath = app_settings.BASE_DIR.joinpath('assets/demo/det_demo.hpr')
        self.state.load_data_from_file(fpath.as_posix())

        prev = len(self.state._history)
        fpath = app_settings.BASE_DIR.joinpath('assets/demo/prb_demo.hpr')
        self.state.load_data_from_file(fpath.as_posix())
        self.assertEqual(len(self.state._history), prev + 1)

    def test_undo(self):
        self.assertEqual(len(self.state._history), 1)
        self.assertEqual(len(self.state._redo_history), 0)
        self.out_diam_c.value = 4
        self.assertAlmostEqual(self.state.out_diam.value, 4)
        self.assertEqual(len(self.state._history), 2)

        self.appform.undo()
        self.assertAlmostEqual(self.state.out_diam.value, 22)
        self.assertEqual(len(self.state._history), 1)
        self.assertEqual(len(self.state._redo_history), 1)


class ResidualStressIntensityTestCase(unittest.TestCase):
    """Tests for residual stress intensity factor field configuration.

    Verifies fix for issue: lower bound was defaulting to -inf when using
    uniform distribution, but should default to 0 since negative values
    are not physically meaningful.
    """

    def setUp(self) -> None:
        app_settings.init()
        self.state = models.State()

    def tearDown(self) -> None:
        self.state = None

    def test_stress_intensity_lower_bound_defaults_to_zero(self):
        """Lower bound should default to 0, not -inf."""
        field = self.state.stress_intensity
        self.assertEqual(field._lower, 0)
        self.assertEqual(field.lower, 0)

    def test_stress_intensity_min_value_is_zero(self):
        """Min value should be 0 to enforce non-negative lower bound."""
        field = self.state.stress_intensity
        self.assertEqual(field._min_value, 0)

    def test_stress_intensity_uniform_distribution_lower_bound_is_zero(self):
        """When switching to uniform distribution, lower bound should be 0."""
        from helprgui.hygu.utils.distributions import Distributions

        field = self.state.stress_intensity

        # Switch to uniform distribution
        field.distr = Distributions.uni

        # Lower bound should be 0, not -inf
        self.assertEqual(field.lower, 0)
        self.assertNotEqual(field.lower, float('-inf'))

    def test_stress_intensity_upper_bound_validation_requires_greater_than_lower(self):
        """Upper bound must be greater than lower bound."""
        from helprgui.hygu.utils.distributions import Distributions
        from helprgui.hygu.utils.distributions import DistributionParam as DP
        from helprgui.hygu.utils.helpers import InputStatus

        field = self.state.stress_intensity
        field.distr = Distributions.uni

        # Set valid bounds
        field.lower = 0
        field.upper = 10

        # Validation should pass
        response = field.validate_subparam_incoming_value(DP.UPPER, field._upper)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Set upper below lower - validation should fail
        field.upper = 0
        field.lower = 5
        response = field.validate_subparam_incoming_value(DP.UPPER, field._upper)
        self.assertEqual(response.status, InputStatus.ERROR)

    def test_stress_intensity_lower_bound_validation_requires_non_negative(self):
        """Lower bound must be >= 0 (min_value)."""
        from helprgui.hygu.utils.distributions import Distributions
        from helprgui.hygu.utils.distributions import DistributionParam as DP
        from helprgui.hygu.utils.helpers import InputStatus

        field = self.state.stress_intensity
        field.distr = Distributions.uni

        # Trying to set negative lower bound should fail validation
        response = field.validate_subparam_incoming_value(DP.LOWER, -1)
        self.assertEqual(response.status, InputStatus.ERROR)

        # Setting lower bound to 0 should pass
        response = field.validate_subparam_incoming_value(DP.LOWER, 0)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Setting positive lower bound should pass
        response = field.validate_subparam_incoming_value(DP.LOWER, 5)
        self.assertEqual(response.status, InputStatus.GOOD)
