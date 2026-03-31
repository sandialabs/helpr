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


 TextField {
     property string field;  // reference to associated parameter field, e.g. 'value' or 'a'
     property bool hasError: false

     Material.containerStyle: Material.Filled
     implicitHeight: inputFieldHeight
     topPadding: inputFieldPadding
     bottomPadding: inputFieldPadding
     Layout.alignment: Qt.AlignCenter
     Layout.maximumWidth: 100
     horizontalAlignment: Text.AlignHCenter

     Material.accent: hasError ? Material.Red : Material.Blue
     background: Rectangle {
         color: hasError ? "#FFE6E6" : "white"
         border.color: hasError ? Material.color(Material.Red) : Material.color(Material.Blue, Material.Shade400)
         border.width: activeFocus || hasError ? 2 : 1
         radius: 4
     }

     text: param ? param[field] : ''

     // record change; only fires if input passes validator.
     onEditingFinished: function()
     {
         if (length > 0)
         {
             param[field] = text;
         }
     }

     onActiveFocusChanged: {
         if (!activeFocus)
         {
             // disallow blank input
//             if (length === 0 || !acceptableInput)
//             {
//                text = param[field];
//             }
         }
     }
 }
