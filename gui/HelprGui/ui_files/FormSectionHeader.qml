/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls.Material 2.12


Column {
    property string title;
    property int rWidth: 800;
    property int bottomPad: 0;
    property int topPad: 24;

    property string iconSrc: "";

    Layout.topMargin: topPad

    Row {
        spacing: 4

        AppIcon {
            visible: iconSrc !== "";
            source: iconSrc
            iconColor: Material.color(Material.Grey)
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: title
            horizontalAlignment: Text.AlignLeft
            anchors.verticalCenter: parent.verticalCenter
            font.pointSize: 14
            font.bold: true
            color: Material.color(Material.Grey)
        }

    }

    Rectangle {
        width: rWidth
        height: 1
        color: Material.color(Material.Blue)
        opacity: 0.4
    }
    VSpacer {
        height: bottomPad
    }
}

