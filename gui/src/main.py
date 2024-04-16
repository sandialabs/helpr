"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import multiprocessing
import os
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

import logging
import app_settings
from helprgui.forms.fields import StringFormField


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
    app_settings.init()

    log = logging.getLogger(app_settings.APPNAME)
    log.info(f'Initializing {app_settings.APPNAME}...')
    log.info(f"working dir: {app_settings.CWD_DIR}")
    log.info(f"data dir: {app_settings.DATA_DIR}")
    log.info(f"session dir: {app_settings.SESSION_DIR}")
    log.info(f'User set session dir? {app_settings.USER_SET_SESSION_DIR}')

    from helprgui.forms.fields import ChoiceFormField, IntFormField, BoolFormField
    from helprgui.forms.fields_probabilistic import UncertainFormField
    from helprgui.displays import QueueDisplay
    from forms.app import HelprAppForm

    app_form = HelprAppForm()
    queue = QueueDisplay()
    app_form.set_queue(queue)
    app_form.analysisStarted.connect(queue.handle_new_analysis)

    # Create references to fields so they're not GC'd
    session_dir_c = StringFormField(param=app_form.db.session_dir)
    out_diam_c = UncertainFormField(param=app_form.db.out_diam)
    thickness_c = UncertainFormField(param=app_form.db.thickness)
    crack_dep_c = UncertainFormField(param=app_form.db.crack_dep)
    crack_len_c = UncertainFormField(param=app_form.db.crack_len)
    p_max_c = UncertainFormField(param=app_form.db.p_max)
    p_min_c = UncertainFormField(param=app_form.db.p_min)
    temp_c = UncertainFormField(param=app_form.db.temp)
    vol_h2_c = UncertainFormField(param=app_form.db.vol_h2)
    yield_str_c = UncertainFormField(param=app_form.db.yield_str)
    frac_resist_c = UncertainFormField(param=app_form.db.frac_resist)

    name_c = StringFormField(param=app_form.db.analysis_name)
    n_ale_c = IntFormField(param=app_form.db.n_ale)
    n_epi_c = IntFormField(param=app_form.db.n_epi)
    seed_c = IntFormField(param=app_form.db.seed)
    cycle_units_c = ChoiceFormField(param=app_form.db.cycle_units)
    study_type_c = ChoiceFormField(param=app_form.db.study_type)

    do_crack_growth_plot_c = BoolFormField(param=app_form.db.do_crack_growth_plot)
    do_ex_rates_plot_c = BoolFormField(param=app_form.db.do_ex_rates_plot)
    do_fad_plot_c = BoolFormField(param=app_form.db.do_fad_plot)
    do_ensemble_plot_c = BoolFormField(param=app_form.db.do_ensemble_plot)
    do_cycle_plot_c = BoolFormField(param=app_form.db.do_cycle_plot)
    do_pdf_plot_c = BoolFormField(param=app_form.db.do_pdf_plot)
    do_cdf_plot_c = BoolFormField(param=app_form.db.do_cdf_plot)
    do_sen_plot_c = BoolFormField(param=app_form.db.do_sen_plot)

    # intermed params displayed and updated by form when state changes
    r_ratio_c = UncertainFormField(param=app_form.db.r_ratio)
    f_ratio_c = UncertainFormField(param=app_form.db.f_ratio)
    smys_c = UncertainFormField(param=app_form.db.smys)
    a_m_c = UncertainFormField(param=app_form.db.a_m)
    a_c_c = UncertainFormField(param=app_form.db.a_c)
    t_r_c = UncertainFormField(param=app_form.db.t_r)

    if app_settings.IS_WINDOWS:
        icon_file = 'icon.ico'
        # support high DPI scaling on windows
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
    else:
        icon_file = 'icon.icns'

    app = QGuiApplication(sys.argv)
    icon_path = app_settings.BASE_DIR.joinpath('assets/logo/').joinpath(icon_file)
    app.setWindowIcon(QIcon(icon_path.as_posix()))

    engine = QQmlApplicationEngine()
    app_form.set_app(app)
    engine.rootContext().setContextProperty("app_form", app_form)
    engine.rootContext().setContextProperty("queue", queue)

    engine.rootContext().setContextProperty("session_dir_c", session_dir_c)

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

    engine.rootContext().setContextProperty("name_c", name_c)
    engine.rootContext().setContextProperty("n_ale_c", n_ale_c)
    engine.rootContext().setContextProperty("n_epi_c", n_epi_c)
    engine.rootContext().setContextProperty("seed_c", seed_c)
    engine.rootContext().setContextProperty("cycle_units_c", cycle_units_c)
    engine.rootContext().setContextProperty("study_type_c", study_type_c)

    engine.rootContext().setContextProperty("r_ratio_c", r_ratio_c)
    engine.rootContext().setContextProperty("f_ratio_c", f_ratio_c)
    engine.rootContext().setContextProperty("smys_c", smys_c)
    engine.rootContext().setContextProperty("a_m_c", a_m_c)
    engine.rootContext().setContextProperty("a_c_c", a_c_c)
    engine.rootContext().setContextProperty("t_r_c", t_r_c)

    engine.rootContext().setContextProperty("do_crack_growth_plot_c", do_crack_growth_plot_c)
    engine.rootContext().setContextProperty("do_ex_rates_plot_c", do_ex_rates_plot_c)
    engine.rootContext().setContextProperty("do_fad_plot_c", do_fad_plot_c)
    engine.rootContext().setContextProperty("do_ensemble_plot_c", do_ensemble_plot_c)
    engine.rootContext().setContextProperty("do_cycle_plot_c", do_cycle_plot_c)
    engine.rootContext().setContextProperty("do_pdf_plot_c", do_pdf_plot_c)
    engine.rootContext().setContextProperty("do_cdf_plot_c", do_cdf_plot_c)
    engine.rootContext().setContextProperty("do_sen_plot_c", do_sen_plot_c)

    qml_file = Path(__file__).resolve().parent / "ui/main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
