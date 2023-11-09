/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Controls 2.12
import Qt5Compat.GraphicalEffects

Item
{
    id: appIcon

    property string source
    property string iconColor
    property alias icon: btn.icon
    property int h: 28

    implicitWidth: btn.icon.width
    implicitHeight: btn.icon.height / Screen.devicePixelRatio


    Button
    {
        id: btn
        anchors.centerIn: parent
        height: h - 1

        icon.source: '../assets/icons/' + parent.source + '.svg'
        icon.color: iconColor ? iconColor : color_primary

        // disable button functionality
        enabled: false
        flat: true
        MouseArea {
            enabled: false
            hoverEnabled: false
            scrollGestureEnabled: false
        }
    }
}
