/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material 2.12
import hygu.classes
import "../utils.js" as Utils

TextField {
    property bool allowNullVal: true
    property int max: 2e9
    property int min: 0
    property var paramRef: param ?? null
    property bool hasError: false
    property alias tooltip: ttip
    property int w: 100

    function refresh() {
        // update text, check explicitly for null fields since qml converts None from python to 0)
        if (allowNullVal && paramRef.is_null) {
            text = '';
        } else {
            text = parseInt(paramRef.value);
        }
    }

    Layout.alignment: Qt.AlignCenter
    Layout.maximumWidth: w
    Layout.preferredWidth: w
    Material.containerStyle: Material.Filled
    bottomPadding: inputFieldPadding
    horizontalAlignment: Text.AlignHCenter

    Material.accent: hasError ? Material.Red : Material.Blue
    background: Rectangle {
        color: hasError ? "#FFE6E6" : "white"
        border.color: hasError ? Material.color(Material.Red) : Material.color(Material.Blue, Material.Shade400)
        border.width: activeFocus || hasError ? 2 : 1
        radius: 4
    }

    // disallow blank input
    // onActiveFocusChanged: { if (!activeFocus && (length === 0 || !acceptableInput)) text = val.toString(); }

    hoverEnabled: true
    implicitHeight: inputFieldHeight
    topPadding: inputFieldPadding

    // record change; only fires if input passes validator.
    onEditingFinished: {
        let val = parseInt(text.replace(/,/g, ''));  // remove commas
        if (allowNullVal && Utils.isNullish(text))
        {
            paramRef.set_null();
        } else if (length > 0 && !Utils.isNullish(val))
        {
            if (val >= min && val <= max)
            {
                paramRef.value = val;
                text = val;
            } else
            {
                refresh();  // restore value
            }
        } else
        {
            refresh();
        }
    }

    ToolTip {
        id: ttip

        delay: 400
        timeout: 5000
        visible: parent.hovered
    }
}
