"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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

        self.assertIsNotNone(self.state.do_cycle_plot)
        self.assertIsNotNone(self.state.do_fad_plot)
        self.assertIsNotNone(self.state.do_design_curve_plot)
        self.assertIsNotNone(self.state.do_ensemble_plot)
        self.assertIsNotNone(self.state.do_pdf_plot)
        self.assertIsNotNone(self.state.do_cdf_plot)
        self.assertIsNotNone(self.state.do_sen_plot)

    def test_params_set_during_init(self):
        """Verify that parameters have default values. """
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

    def test_values_sent_to_api_match_form_inputs(self):
        self.state.p_min.unit = 'bar'
        self.state.p_min.value = 50  # 5 MPa
        self.state.crack_dep.value = 30

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self)

        delta = 0.01
        ac = self.appform.result_forms[1]
        # compare cloned analysis state instance with original (active form)
        self.assertEqual(self.state.p_min.unit, ac.state.p_min.unit)
        self.assertEqual(self.state.p_min.uncertainty, ac.state.p_min.uncertainty)
        self.assertAlmostEqual(self.state.p_min.value, ac.state.p_min.value, delta=delta)

        self.assertAlmostEqual(ac.state.p_min.value_raw, 5.0, delta=delta)

        self.assertAlmostEqual(self.state.crack_dep.value, ac.state.crack_dep.value, delta=delta)
        self.assertAlmostEqual(self.state.out_diam.value, ac.state.out_diam.value, delta=delta)

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
        self.assertTrue(ac1.analysis_id != ac2.analysis_id)
        self.assertTrue(plot1_filepath != plot2_filepath)


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
