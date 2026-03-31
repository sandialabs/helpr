/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material 2.12


ComboBox {
    property bool hasError: false

    id: control
    implicitHeight: inputFieldHeight
    rightPadding: 5
    Layout.alignment: Qt.AlignCenter
    Layout.maximumWidth: 120
    Layout.preferredWidth: 120
    textRole: "display"

    Material.containerStyle: Material.Filled
    Material.accent: hasError ? Material.Red : Material.Blue
    background: Rectangle {
        color: hasError ? "#FFE6E6" : "white"
        border.color: hasError ? Material.color(Material.Red) : Material.color(Material.Blue, Material.Shade400)
        border.width: activeFocus || hasError ? 2 : 1
        radius: 4
    }

    contentItem: Text {
        leftPadding: 10
        text: control.displayText
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        textFormat: Text.RichText
    }

    delegate: ItemDelegate {
        width: control.width
        contentItem: Text {
            text: model[control.textRole]
            font: control.font
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
            textFormat: Text.RichText
        }
        highlighted: control.highlightedIndex === index
    }
}
