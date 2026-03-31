/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Dialogs
import QtQuick.Controls.Material

import "../components"
import "../components/buttons"
import "../utils.js" as Utils
import hygu.classes


Item {
    property StringFormField param;
    property int inputLength: 240;
    property bool hasError: false;
    property string errorMsg: "";
    property string tipText;
    property string fileButtonTooltip: "Select a CSV file"
    property string nameFilter1: "CSV files (*.csv)"
    property alias fileDialog: dialog;
    property alias selectButton: fileBtn;
    property alias extraButton: extraBtn;
    property alias contentRow: contentRowId


    id: paramContainer
    Layout.preferredHeight: 70

    Component.onCompleted:
    {
        refresh();
    }

    function refresh()
    {
        let color = color_primary;
        if (param.status === 1)
        {
            alertText.text = "";
            alertDisplay.visible = false;
        }
        else
        {
            alertText.text = param.alert;
            alertDisplay.visible = true;
        }

        paramLabel.color = color_text_levels[param.status];
        alertText.color = color_text_levels[param.status];
        alertIcon.iconColor = color_text_levels[param.status];
        alertDisplay.color = color_levels[param.status];

        valueInput.visible = true;
        valueInput.text = param.value;
        valueInput.enabled = param.enabled;
    }

    FileDialog {
        id: dialog
        nameFilters: [nameFilter1, "All files (*)"]
        fileMode: FileDialog.OpenFile
        // currentFile: param?.value === true && !Utils.isNullish(param.value) ? "file:///" + param.value : ""  // not sure === true is needed
    }


    Row
    {
        id: paramInputRow

        Component.onCompleted:
        {
            refresh();
        }

        RowLayout {
            id: contentRowId
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
                wrapMode: Text.WordWrap

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
                readOnly: true
                Layout.maximumWidth: inputLength
                Layout.preferredWidth: inputLength
                horizontalAlignment: Text.AlignLeft
            }

            IconButton {
                id: fileBtn
                img: "file-import-solid"
                tooltip: fileButtonTooltip
                Layout.maximumHeight: 40
                Layout.maximumWidth: Layout.maximumHeight
                onClicked:
                {
                    dialog.open();
                }
            }

            IconButton {
                id: extraBtn
                img: "xmark-solid"
                tooltip: "Clear selected file"
                Layout.maximumHeight: 40
                Layout.maximumWidth: Layout.maximumHeight
            }
        }
    }

    Rectangle {
        id: alertDisplay
        visible: true
        color: color_danger
        radius: 5
        anchors.left: parent.left
        anchors.leftMargin: 125
        anchors.top: paramInputRow.bottom
        height: 28
        width: alertContents.width

        Row {
            id: alertContents
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter
            leftPadding: 6

            AppIcon {
                id: alertIcon
                source: 'circle-exclamation-solid'
                iconColor: color_text_danger
                height: 26
                anchors.verticalCenter: parent.verticalCenter
            }
            TextEdit {
                id: alertText
                text: ""
                rightPadding: 10
                color: color_text_danger
                readOnly: true
                selectByMouse: true
                font.pointSize: 10
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
        }

    }
}