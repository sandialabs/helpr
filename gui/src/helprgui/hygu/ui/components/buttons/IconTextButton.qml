/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material


import "../"


Button {
    id: buttonId
    property alias tooltipRef: ttip;
    property color bgColor: btnColorDefault;
    property color btnIconColor: color_primary;
    property string img;
    property string btnText: "Button";
    property string tooltip;
    property int itemSpacing: 2

    // font.pixelSize: 14
    Material.background: bgColor;
    Material.roundedScale: Material.SmallScale
    Material.elevation: enabled ? 1 : 0
    height: parent.height - 2  // if inside Layout, set this directly

    RowLayout {
        id: rowLayout
        spacing: itemSpacing
        anchors.centerIn: parent

        AppIcon {
            id: btnIcon
            source: img
            Layout.alignment: Qt.AlignVCenter
            iconColor: enabled ? btnIconColor : color_disabled
            icon.width: 14
        }

        Text {
            Layout.alignment: Qt.AlignVCenter
            text: btnText
            color: buttonId.hovered ? Material.accent : Material.foreground
            font.pointSize: contentFontSize - 1
        }
    }

    hoverEnabled: true
    ToolTip {
        id: ttip
        delay: 400
        timeout: 5000
        visible: parent.hovered && tooltip !== ""
        text: tooltip
    }
}
