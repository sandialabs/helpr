/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls 2.12
import QtQuick.Dialogs
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "../components"


Popup {
    property string logoSrc
    property string title
    property string urlDescrip
    property string url

    x: parent.width * 0.2
    y: parent.height * 0.05
    width: logoBanner.width * 1.1
    height: parent.height * 0.9
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    AppIcon {
        source: 'xmark-solid'
        anchors.right: parent.right
        anchors.top: parent.top

        MouseArea {
            anchors.fill: parent
            onClicked: close()
        }
    }

    ColumnLayout {
        spacing: 10
        anchors.fill: parent

        Image {
            id: logoBanner
            source: appDir + logoSrc
        }

        Text {
            font.pointSize: 20
            text: title
        }

        Text {
            font.pointSize: contentFontSize
            wrapMode: Text.WordWrap
            Layout.maximumWidth: parent.width * 0.95
            text: app_form?.about_str ?? ''
        }

        Item {
            height: 20
        }

        Text {
            font.pointSize: 16
            text: "Copyright Statement"
        }

        Text {
            font.pointSize: contentFontSize
            wrapMode: Text.WordWrap
            Layout.maximumWidth: parent.width * 0.95
            text: app_form?.copyright_str ?? ''
        }

        Item {
            Layout.fillHeight: true
        }

        RowLayout {
            spacing: 10

            Text {
                text: app_form?.version_str ?? ''
            }

            Text {
                text: urlDescrip
                onLinkActivated: Qt.openUrlExternally(url)
                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton // Don't eat the mouse clicks
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }
    }
}
