"""
 Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

 You should have received a copy of the BSD License along with HELPR.

 """
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, Qt, QPointF, QUrl

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from helprgui import app_settings
from helprgui.hygu.forms.fields import StringFormField, NumListFormField, NumFormField, ChoiceFormField, IntFormField, BoolFormField
from helprgui.hygu.forms.fields_probabilistic import UncertainFormField
from helprgui.hygu.models.fields import ChoiceField, NumField, StringField, NumListField, IntField, BoolField
from helprgui.hygu.models.fields_probabilistic import UncertainField

import pytest

"""
Use pytest-qt to conduct interaction tests with rendered GUI.

References
----------
https://github.com/pytest-dev/pytest-qt/issues/251
"""



@pytest.fixture(scope="session")
def qapp():
    QCoreApplication.setOrganizationName("test")
    QCoreApplication.setOrganizationDomain("test")
    QCoreApplication.setAttribute(Qt.AA_DontUseNativeDialogs)
    yield QGuiApplication([])

@pytest.fixture()
def window(qtbot, qapp):
    """Create a Qt application and window.
    TODO: this currently mirrors the main.py function. Refactor to import here.
    TODO: how to render headless?
    """
    app_settings.init()

    from helprgui.hygu.displays import QueueDisplay
    from helprgui.forms.app import HelprAppForm

    app_form = HelprAppForm()
    queue = QueueDisplay()
    app_form.set_queue(queue)
    app_form.analysisStarted.connect(queue.handle_new_analysis)

    # app = QGuiApplication(sys.argv)
    app = qapp
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    app_form.set_app(app)

    # session_dir_c = StringFormField(param=app_form.db.session_dir)
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

    qml_file = Path(__file__).resolve().parent.parent / "ui/main.qml"
    engine.load(qml_file)
    main_window = engine.rootObjects()[0]  # if this errs, there's a bug in the QML
    yield main_window

@pytest.skip
def test_window_title(window):
    assert "Hydrogen Extremely Low Probability of Rupture" in window.title()
