/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

import helpr.classes


Rectangle {
    property string name
    property AnalysisController ac
    property int qIndex
    property int a_id: ac.analysis_id
    property double startTime

    id: queueItem
    radius: 5.0
    width: parent?.width ?? 0
    height: 38
    color: "#e0e0e0"

    function updateIcons()
    {
        iconWaiting.visible = false;
        iconProgressing.visible = false;
        iconFinished.visible = false;
        iconError.visible = false;
        let tipText = "";

        if (!ac.started)
        {
            iconWaiting.visible = true;
            tipText = "Analysis queued";
        }
        else if (ac.started && !ac.finished)
        {
            iconProgressing.visible = true;
            tipText = "Analysis in-progress";
        }
        else if (ac.finished && !ac.has_error)
        {
            iconFinished.visible = true;
            tipText = "Analysis complete - click to view results";
        }
        else if (ac.finished && ac.has_error)
        {
            iconError.visible = true;
            tipText = "Error during analysis - click to view more info";
        }

        tooltip.text = tipText;
    }

    Connections {
        target: ac
        function onStartedChanged(val) { updateIcons(); }
        function onFinishedChanged(val) {
            updateIcons();
            timer.stop();
        }
    }

    Component.onCompleted: {
        startTime = new Date().getTime();
    }

    HoverHandler {
        id: mouse
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        onClicked: {
            resultContainer.show(ac, qIndex);
        }
        hoverEnabled: true
        propagateComposedEvents: true

    }

    ToolTip {
        id: tooltip
        delay: 400
        timeout: 5000
        visible: ma.containsMouse
        text: "Analysis in queue"
    }

    Text {
        id: nameLabel
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        leftPadding: 10
        horizontalAlignment: Text.AlignLeft
        font.pointSize: 14
        text: '' + ac.name + ' - ' + ac.study_type_disp.toLowerCase()
    }


    Text {
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: statusIcon.left

        id: timeLabel
        rightPadding: 30
        horizontalAlignment: Text.AlignLeft
        font.pointSize: 12
        text: ''
    }

    Timer {
        id: timer
        interval: 1000; running: true; repeat: true
        onTriggered: {
            var currTime = new Date().getTime();
            var diff = currTime - startTime;  // milliseconds
            var diffStr = new Date(diff).toISOString().slice(11,19);
            timeLabel.text = diffStr;
        }
    }


    Item {
        id: statusIcon
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        width: 32


        AppIcon {
            id: iconWaiting
            visible: !ac.started
            source: 'ellipsis-solid'
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 12
        }

        BusyIndicator {
            id: iconProgressing
            visible: ac.started && !ac.finished
            height: queueItem.height - 10
            running: true
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
        }

        AppIcon {
            id: iconFinished
            visible: ac.finished && !ac.has_error
            source: 'check-solid'
            iconColor: Material.color(Material.Green)
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
        }

        AppIcon {
            id: iconError
            visible: ac.finished && ac.has_error
            source: 'circle-exclamation-solid'
            iconColor: Material.color(Material.Red)
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
        }
    }

    Rectangle {
        id: progressDrawer
        parent: queueItem
        width: parent.width
        height: parent.height
        color: "#e0e0e0"
        visible: !ac.finished && (ma.containsMouse || cancelBtnMa.containsMouse)

        Label {  // same as above
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            leftPadding: 10
            horizontalAlignment: Text.AlignLeft
            font.pointSize: 14
            text: '' + ac.name + ' - ' + ac.study_type_disp.toLowerCase()
        }
        AppButton {
            id: cancelBtn
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            img: 'xmark-solid'
            tooltip: ("Cancel analysis")
            bgColor: Material.color(Material.Red, Material.Shade300)

            MouseArea {
                id: cancelBtnMa
                anchors.fill: parent
                anchors.centerIn: parent
                hoverEnabled: true

                onClicked: function() {
                    // tell backend to cancel analysis, then update frontend immediately.
                    data_controller.cancel_analysis(ac.analysis_id);
                    queueListView.analysisCanceled(qIndex);
                }
            }
        }

    }

    Rectangle {
        id: completionDrawer
        parent: queueItem
        width: parent.width
        height: parent.height
        color: "#e0e0e0"
        visible: ac.finished && (ma.containsMouse || deleteBtnMa.containsMouse)

        Label {
            text: "View results"
            font.italic: true
            anchors.centerIn: parent
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            leftPadding: 10
            horizontalAlignment: Text.AlignLeft
            font.pointSize: 16
        }
        AppButton {
            id: deleteBtn
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            img: 'trash-solid'
            tooltip: ("Delete analysis results")
            bgColor: Material.color(Material.Red, Material.Shade300)

            MouseArea {
                id: deleteBtnMa
                anchors.fill: parent
                anchors.centerIn: parent
                hoverEnabled: true

                onClicked: function() {
                    queueListView.removeItem(qIndex);
                }
            }
        }

    }


}

