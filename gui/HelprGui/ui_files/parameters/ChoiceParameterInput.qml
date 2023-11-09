/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material

import "../"

import helpr.classes


Row {
    property ChoiceParameterController param;
    property string tipText;

    function refresh()
    {
        valueSelector.currentIndex = param.get_index()
    }

    height: 30
    Layout.preferredHeight: 30

    GridLayout {
        rows: 2
        columns: 2
        flow: GridLayout.TopToBottom

        Connections {
            target: param
            function onModelChanged() { refresh(); }
        }

        Item {
        }
        Text {
            text: param?.label ?? ''
            font.pointSize: labelFontSize
            Layout.preferredWidth: 120
            horizontalAlignment: Text.AlignRight

            MouseArea {
                id: ma
                anchors.fill: parent
                hoverEnabled: true
            }

            ToolTip {
                delay: 200
                timeout: 3000
                visible: tipText ? ma.containsMouse : false
                text: tipText
            }
        }

        Item {
            id: valueLabel
        }
        DenseComboBox {
            id: valueSelector
            Layout.preferredWidth: 170
            Layout.maximumWidth: 170
            model: param?.choices ?? null
            currentIndex: param?.get_index() ?? 0
            textRole: "display"
            onActivated: param.value = currentIndex
        }
    }
}
