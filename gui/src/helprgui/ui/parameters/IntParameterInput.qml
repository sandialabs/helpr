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

import "../components"
import helprgui.classes


Item {
    property IntFormField param;
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
            paramContainer.Layout.preferredHeight = 80;
            paramLabel.color = color_danger;
            alertMsg.text = errorMsg;
            alertDisplay.visible = true;
        }
        else
        {
            paramContainer.Layout.preferredHeight = 36;
            paramLabel.color = color_primary;
            alertMsg.text = "";
            alertDisplay.visible = false;
        }

        valueLabel.visible = true;
        valueInput.visible = true;

        valueLabel.text = "";
        valueInput.text = param.value;

        valueLabel.enabled = param.enabled;
        valueInput.enabled = param.enabled;
    }


    Row
    {
        id: paramInputRow

        Component.onCompleted:
        {
            refresh();
        }

        GridLayout {
            id: paramGrid
            rows: 2
            columns: 7
            flow: GridLayout.TopToBottom

            Connections {
                target: param
                function onModelChanged() { refresh(); }
            }

            Item {
            }
            Text {
                id: paramLabel
                text: param?.label ?? ''
                Layout.preferredWidth: paramLabelWidth
                horizontalAlignment: Text.AlignRight
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

            InputTopLabel {
                id: valueLabel
                text: ""
            }
            DoubleTextField {
                id: valueInput
                text: param.value
                field: "value"
                Layout.maximumWidth: 120
                validator: IntValidator{ bottom: param?.min_value ?? -1000 }
            }
            // spacers
            Item {}
            Item {}
            Item {}
            Item {}
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
