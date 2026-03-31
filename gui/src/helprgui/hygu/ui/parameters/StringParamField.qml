/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material

import "../components"
import hygu.classes


Item {
    property StringFormField param;
    property int inputLength: 120;
    property bool hasError: false;
    property string errorMsg: "test long error msg ERROR HERE";
    property string tipText;

    id: paramContainer

    Component.onCompleted:
    {
        refresh();
    }

    function refresh()
    {
        if (hasError)
        {
            paramContainer.Layout.preferredHeight = paramRowErrorHeight;
            paramLabel.color = color_danger;
            alertMsg.text = errorMsg;
            alertDisplay.visible = true;
        }
        else
        {
            paramContainer.Layout.preferredHeight = paramRowHeight;
            paramLabel.color = color_primary;
            alertMsg.text = "";
            alertDisplay.visible = false;
        }

        valueInput.visible = true;
        valueInput.text = param.value;
        valueInput.enabled = param.enabled;
    }


    RowLayout
    {
        id: paramInputRow

        Component.onCompleted:
        {
            refresh();
        }

        Connections {
            target: param
            function onModelChanged() { refresh(); }
        }

        Text {
            id: paramLabel
            text: param?.label ?? ''
            Layout.preferredWidth: paramLabelWidth
            horizontalAlignment: Text.AlignLeft
            font.pointSize: labelFontSize

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

        StringTextField {
            id: valueInput
            text: param.value
            field: "value"
            Layout.maximumWidth: inputLength
            Layout.preferredWidth: inputLength
            horizontalAlignment: Text.AlignLeft
        }
    }

    Row
    {
        id: alertDisplay
        anchors.top: paramInputRow.bottom
        leftPadding: 125

        AppIcon {
            id: alertIcon
            source: 'circle-exclamation-solid'
            iconColor: Material.color(Material.Red)
            width: 24
            height: 24
        }
        Text {
            id: alertMsg
            text: ""
            anchors.topMargin: 4
            font.italic: true
            anchors.verticalCenter: parent.verticalCenter
            color: color_danger
        }
    }
}
