/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls.Material 2.12

RowLayout {
    id: root
    spacing: 10

    property string title: "Subsection"
    property alias textRef: headerText
    property alias lineRef: headerLine
    property int fontSize: 13
    property real textOpacity: 0.85
    property int lineWidth: 250
    property int topMargin: 5
    property int leftMargin: 0
    property color textColor: Material.color(Material.Grey, Material.Shade700)

    Layout.fillWidth: true
    Layout.preferredHeight: 26
    Layout.topMargin: topMargin

    Text {
        id: headerText
        text: title
        font.pointSize: fontSize
        font.italic: true
        color: textColor
        opacity: textOpacity
        Layout.leftMargin: leftMargin
    }

    Rectangle {
        id: headerLine
        height: 1
        Layout.preferredWidth: lineWidth
        color: textColor
        opacity: 0.2
        Layout.fillWidth: true
    }
}