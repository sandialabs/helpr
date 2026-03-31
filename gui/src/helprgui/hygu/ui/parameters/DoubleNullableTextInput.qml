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
    property var paramRef: param ?? null
    property string field: "value";  // reference to associated parameter field, e.g. 'value' or 'a'
    property double max: Infinity
    property double min: -Infinity
    property bool useLimits: true
    property bool hasError: false
    property string errorMsg: ""
    property bool persistError: false  // When true, error state persists after focus is lost

    property alias tooltip: ttip
    property string defaultTooltipText: "Enter a value between " + min + " and " + max + ". Leave blank to indicate infinity.";
    property string tooltipText: (paramRef !== null && paramRef.value_tooltip !== null) ? paramRef.value_tooltip : defaultTooltipText;

    function toggleAlert(status, message)
    {
        if (status === 0)
        {
            errorMsg = message
            hasError = true
            persistError = true
            Material.accent = Material.Red
        }
        else
        {
            errorMsg = ""
            hasError = false
            persistError = false
            Material.accent = Material.Blue
        }
    }

    function refresh()
    {
        // Update tooltip text based on current parameter state
        // let defaultText = "Enter a value between " + min + " and " + max + ". Leave blank to indicate infinity.";
        // tooltipText = (paramRef !== null && paramRef.value_tooltip !== null) ? paramRef.value_tooltip : defaultTooltipText;

        // update text, check explicitly for null fields since qml converts None from python to 0)
        if (field === 'd' && paramRef.d_is_null) {
            text = '';
        }
        else if (field === 'c' && paramRef.c_is_null) {
            text = '';
        }
        else if (!paramRef || Utils.isNullish(paramRef[field])) {
            text = '';
        }
        else if (paramRef && paramRef.is_null) {
            // optional analysis parameter that can be null (i.e. not a distribution parameter)
            text = '';
        }
        else {
            text = Utils.hround(paramRef[field]);
        }
    }


    Layout.alignment: Qt.AlignCenter
    Layout.maximumWidth: 120
    Layout.preferredWidth: 80
    Material.containerStyle: Material.Filled
    bottomPadding: inputFieldPadding
    horizontalAlignment: Text.AlignHCenter
    hoverEnabled: true
    implicitHeight: inputFieldHeight
    topPadding: inputFieldPadding

    Material.accent: hasError ? Material.Red : Material.Blue
    background: Rectangle {
        color: hasError ? "#FFE6E6" : "white"
        border.color: hasError ? Material.color(Material.Red) : Material.color(Material.Blue, Material.Shade400)
        border.width: activeFocus || hasError ? 2 : 1
        radius: 4
    }

    // ToolTip {
    //     visible: hasError && parent.hovered
    //     text: errorMsg
    //     delay: 0
    //     timeout: 5000
    // }

    onEditingFinished: function ()
        {
        // custom validation
        if (Utils.isNullish(text))
        {
            paramRef.set_null(field);
        }
        else if (length > 0 && text >= min && text <= max)
        {
            // Apply the value
            paramRef[field] = text;
        }
        else
        {
            refresh();  // restore value
        }
    }

    onActiveFocusChanged: {
        if (!activeFocus) {
            // Don't clear error state if persistError is true
            // if (!persistError) {
            //     hideAlert();
            // }
        }
    }

    ToolTip {
        id: ttip
        delay: 400
        text: tooltipText
        timeout: 5000
        visible: parent.hovered
    }
}
