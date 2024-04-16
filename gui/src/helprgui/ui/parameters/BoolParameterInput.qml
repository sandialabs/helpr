/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material

import helprgui.classes


Row {
    property BoolFormField param;
//    property string tipText;  mouseArea capture breaks checkbox

    function refresh()
    {
        valueCheckbox.checked = param.value
    }

    function checked()
    {
        return param.value === true;
    }

    Component.onCompleted: {
    }

    height: 30
    Layout.preferredHeight: 30

    GridLayout {
        // columns: 8
        rows: 2
        columns: 2
        flow: GridLayout.TopToBottom

        Connections {
            target: param
            function onModelChanged() { refresh(); }
        }

        Item {
        }
        Item {
            Layout.preferredWidth: paramLabelWidth
        }

        Item {
            id: valueLabel
        }
        CheckBox {
            id: valueCheckbox
            implicitHeight: 36
            checked: param?.value ?? true
            text: param?.label ?? ''
            font.pointSize: labelFontSize
            onToggled:  param.value = checked
            leftPadding: 0
        }

        Item {
        }
    }
}
