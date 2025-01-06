"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.
"""
import tempfile
import unittest
from pathlib import Path

from helprgui import app_settings
from helprgui.hygu.displays import QueueDisplay
from helprgui.hygu.utils import helpers
from helprgui.models.enums import StressMethod
from . import test_utils

DELTA = 1e-4

class StateAnalysisTestCase(unittest.TestCase):
    """Tests interactions between datastore and backend analysis calls. """

    def setUp(self) -> None:
        app_settings.DEBUG = True
        app_settings.DO_LOGFILE = False
        temp_dir = Path(tempfile.gettempdir()).joinpath("helpr")
        app_settings.SESSION_DIR = helpers.init_session_dir(parent_dir=temp_dir)
        app_settings.DATA_DIR = app_settings.SESSION_DIR / 'data'
        app_settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

        from helprgui.forms.app import HelprAppForm

        self.appform = HelprAppForm()
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

    def test_prb_study_stress_method_anderson_succeeds(self):
        self.appform.load_prb_demo()
        self.state.stress_method.value = StressMethod.anderson
        self.assertTrue(self.state.stress_method.value == StressMethod.anderson)

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self, t_max=25)

        ac = self.appform.result_forms[1]
        self.assertTrue(ac.state.study_type.value == 'prb')
        self.assertTrue(ac.state.stress_method.value == StressMethod.anderson)

    def test_prb_study_stress_method_api_succeeds(self):
        self.appform.load_prb_demo()
        self.state.stress_method.value = StressMethod.api
        self.assertTrue(self.state.stress_method.value == StressMethod.api)

        self.appform.request_analysis()
        test_utils.wait_for_analysis(self, t_max=25)

        ac = self.appform.result_forms[1]
        self.assertTrue(ac.state.is_finished)
        self.assertFalse(ac.state.has_error)
        self.assertTrue(ac.state.study_type.value == 'prb')
        self.assertTrue(ac.state.stress_method.value == StressMethod.api)
