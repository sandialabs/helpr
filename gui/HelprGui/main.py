"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import multiprocessing
import os
import sys
from datetime import datetime
from pathlib import Path

import logging
import gui_settings as settings
from utils import helpers

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

# import rc_resources

"""
This file initializes the Qt HELPR GUI and backing data model.

Notes
-----
If using the QML resources system, import rc_resources above. (Not used currently.)
If resources are changed, must delete the rc_resources.py file so it is regenerated. Or manually: pyrcc5 resources.qrc -o rc_resources.py

HELPR-related modules are imported below after logging is setup so the logging config can be centralized.

"""


def main():
    # set up output directory and logging before key imports, otherwise they'll be misconfigured
    settings.SESSION_DIR = helpers.init_session_dir(settings.TEMP_DIR)
    settings.setup_logging(settings.SESSION_DIR)

    log = logging.getLogger("HELPR")
    log.info('Initializing HELPR...')
    log.info(f"working dir: {settings.CWD_DIR}")
    log.info(f"session dir: {settings.SESSION_DIR}")

    from state.controllers import DataController
    from analyses.controllers import QueueController
    from parameters.controllers import (ParameterController, ChoiceParameterController, BasicParameterController, BoolParameterController)

    dc = DataController()
    queue = QueueController()
    dc.set_controller(queue)
    dc.analysisStarted.connect(queue.handle_new_analysis)

    # Create references to ParameterControllers so they're not GC'd
    out_diam_c = ParameterController(param=dc.db.out_diam)
    thickness_c = ParameterController(param=dc.db.thickness)
    crack_dep_c = ParameterController(param=dc.db.crack_dep)
    crack_len_c = ParameterController(param=dc.db.crack_len)
    p_max_c = ParameterController(param=dc.db.p_max)
    p_min_c = ParameterController(param=dc.db.p_min)
    temp_c = ParameterController(param=dc.db.temp)
    vol_h2_c = ParameterController(param=dc.db.vol_h2)
    yield_str_c = ParameterController(param=dc.db.yield_str)
    frac_resist_c = ParameterController(param=dc.db.frac_resist)

    n_ale_c = BasicParameterController(param=dc.db.n_ale)
    n_epi_c = BasicParameterController(param=dc.db.n_epi)
    seed_c = BasicParameterController(param=dc.db.seed)
    cycle_units_c = ChoiceParameterController(param=dc.db.cycle_units)
    study_type_c = ChoiceParameterController(param=dc.db.study_type)

    do_crack_growth_plot_c = BoolParameterController(param=dc.db.do_crack_growth_plot)
    do_ex_rates_plot_c = BoolParameterController(param=dc.db.do_ex_rates_plot)
    do_fad_plot_c = BoolParameterController(param=dc.db.do_fad_plot)
    do_ensemble_plot_c = BoolParameterController(param=dc.db.do_ensemble_plot)
    do_cycle_plot_c = BoolParameterController(param=dc.db.do_cycle_plot)
    do_pdf_plot_c = BoolParameterController(param=dc.db.do_pdf_plot)
    do_cdf_plot_c = BoolParameterController(param=dc.db.do_cdf_plot)
    do_sen_plot_c = BoolParameterController(param=dc.db.do_sen_plot)

    if settings.IS_WINDOWS:
        icon_file = 'icon.ico'
        # support high DPI scaling on windows
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
    else:
        icon_file = 'icon.icns'

    app = QGuiApplication(sys.argv)
    icon_path = settings.BASE_DIR.joinpath('assets/logo/').joinpath(icon_file)
    app.setWindowIcon(QIcon(icon_path.as_posix()))

    engine = QQmlApplicationEngine()
    dc.set_app(app)
    engine.rootContext().setContextProperty("data_controller", dc)
    engine.rootContext().setContextProperty("queue", queue)

    engine.rootContext().setContextProperty("out_diam_c", out_diam_c)
    engine.rootContext().setContextProperty("thickness_c", thickness_c)
    engine.rootContext().setContextProperty("crack_dep_c", crack_dep_c)
    engine.rootContext().setContextProperty("crack_len_c", crack_len_c)
    engine.rootContext().setContextProperty("p_max_c", p_max_c)
    engine.rootContext().setContextProperty("p_min_c", p_min_c)
    engine.rootContext().setContextProperty("temp_c", temp_c)
    engine.rootContext().setContextProperty("vol_h2_c", vol_h2_c)
    engine.rootContext().setContextProperty("yield_str_c", yield_str_c)
    engine.rootContext().setContextProperty("frac_resist_c", frac_resist_c)

    engine.rootContext().setContextProperty("n_ale_c", n_ale_c)
    engine.rootContext().setContextProperty("n_epi_c", n_epi_c)
    engine.rootContext().setContextProperty("seed_c", seed_c)
    engine.rootContext().setContextProperty("cycle_units_c", cycle_units_c)
    engine.rootContext().setContextProperty("study_type_c", study_type_c)

    engine.rootContext().setContextProperty("do_crack_growth_plot_c", do_crack_growth_plot_c)
    engine.rootContext().setContextProperty("do_ex_rates_plot_c", do_ex_rates_plot_c)
    engine.rootContext().setContextProperty("do_fad_plot_c", do_fad_plot_c)
    engine.rootContext().setContextProperty("do_ensemble_plot_c", do_ensemble_plot_c)
    engine.rootContext().setContextProperty("do_cycle_plot_c", do_cycle_plot_c)
    engine.rootContext().setContextProperty("do_pdf_plot_c", do_pdf_plot_c)
    engine.rootContext().setContextProperty("do_cdf_plot_c", do_cdf_plot_c)
    engine.rootContext().setContextProperty("do_sen_plot_c", do_sen_plot_c)

    qml_file = Path(__file__).resolve().parent / "ui_files/main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
