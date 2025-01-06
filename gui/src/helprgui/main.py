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
from helprgui import app_settings
from helprgui.hygu.forms.fields import StringFormField, NumListFormField, NumFormField
from helprgui.hygu.models.fields import ChoiceField, NumField, StringField, NumListField, IntField, BoolField
from helprgui.hygu.models.fields_probabilistic import UncertainField

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

    from helprgui.hygu.forms.fields import ChoiceFormField, IntFormField, BoolFormField
    from helprgui.hygu.forms.fields_probabilistic import UncertainFormField
    from helprgui.hygu.displays import QueueDisplay
    from forms.app import HelprAppForm

    app_form = HelprAppForm()
    queue = QueueDisplay()
    app_form.set_queue(queue)
    app_form.analysisStarted.connect(queue.handle_new_analysis)

    if app_settings.IS_WINDOWS:
        icon_file = 'icon.ico'
        # support high DPI scaling on windows
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"

    else:
        icon_file = 'icon.icns'

    app = QGuiApplication(sys.argv)
    icon_path = app_settings.CWD_DIR.joinpath('assets/logo/').joinpath(icon_file)
    app.setWindowIcon(QIcon(icon_path.as_posix()))

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    app_form.set_app(app)

    # Create references to fields so they're not GC'd
    session_dir_c = StringFormField(param=app_form.db.session_dir)

    param_refs = {}
    class_pairs = {ChoiceField: ChoiceFormField,
                   UncertainField: UncertainFormField,
                   StringField: StringFormField,
                   NumListField: NumListFormField,
                   IntField: IntFormField,
                   BoolField: BoolFormField}
    for attr, value in app_form.db.__dict__.items():
        fc = class_pairs.get(type(value), None)
        if fc is not None:
            form_param = fc(param=value)
            param_refs[attr] = form_param
            qml_name = attr + "_c"
            ctx.setContextProperty(qml_name, form_param)

    ctx.setContextProperty("app_form", app_form)
    ctx.setContextProperty("queue", queue)
    ctx.setContextProperty("session_dir_c", session_dir_c)

    qml_file = Path(__file__).resolve().parent / "ui/main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
