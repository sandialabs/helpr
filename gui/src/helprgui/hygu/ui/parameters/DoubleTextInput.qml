/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material 2.12

import "../utils.js" as Utils

import hygu.classes


 TextField {
     property string field;  // reference to associated parameter field, e.g. 'value' or 'a'
     property var paramRef: param ?? null;
     property double max: Infinity
     property double min: -Infinity
     property bool useLimits: true;
     property bool hasError: false
     property string errorMsg: ""
     property bool persistError: false  // When true, error state persists after focus is lost

     property alias tooltip: ttip;
     // To provide a custom tooltip, override these in the parent form.
     property string defaultTooltipText: useLimits ? "Enter a value between " + min + " and " + max : "Enter a value";
     property string tooltipText: (useLimits && paramRef !== null && paramRef.value_tooltip !== null) ? paramRef.value_tooltip : defaultTooltipText;

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

     function refreshLimits()
     {
         // Update validator limits
         if (useLimits)
         {
             vdtr.bottom = paramRef?.min_value ?? min;
             vdtr.top = paramRef?.max_value ?? max;
         }
         else
         {
             vdtr.bottom = min;
             vdtr.top = max;
         }

         // Update tooltip text based on current parameter state
         // let defaultText = "Enter a value between " + vdtr.bottom + " and " + vdtr.top;
         // tooltipText = (paramRef !== null && paramRef.value_tooltip !== null) ? paramRef.value_tooltip : defaultTooltipText;
     }

     function refresh() {
         text = paramRef ? Utils.hround(paramRef[field]) : '';
         refreshLimits();
     }

     Material.containerStyle: Material.Filled
     implicitHeight: inputFieldHeight
     topPadding: inputFieldPadding
     bottomPadding: inputFieldPadding
     Layout.alignment: Qt.AlignCenter
     Layout.maximumWidth: 120
     Layout.preferredWidth: 80
     horizontalAlignment: Text.AlignHCenter

     Material.accent: hasError ? Material.Red : Material.Blue
     background: Rectangle {
         color: hasError ? "#FFE6E6" : "white"
         border.color: hasError ? Material.color(Material.Red) : Material.color(Material.Blue, Material.Shade400)
         border.width: activeFocus || hasError ? 2 : 1
         radius: 4
     }

     text: paramRef ? paramRef[field] : ''

     validator: DoubleValidator {
         id: vdtr
         bottom: useLimits ? (paramRef?.min_value ?? -Infinity) : -Infinity
         top: useLimits ? (paramRef?.max_value ?? Infinity) : Infinity
     }

     // // record change; only fires if input passes validator.
     onEditingFinished: function()
     {
         if (length > 0)
         {
             // Apply the value
             paramRef[field] = text;
         }
     }

     onActiveFocusChanged: {
         if (!activeFocus)
         {
             // disallow blank input
             if (paramRef && (length === 0 || !acceptableInput))
             {
                text = Utils.hround(paramRef[field]);
             }
         }
     }

     hoverEnabled: true
     ToolTip {
         id: ttip
         delay: 400
         timeout: 5000
         visible: parent.hovered
         text: tooltipText
     }
 }
