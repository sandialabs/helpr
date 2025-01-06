/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls 2.12
import QtQuick.Controls.Material
import "../../hygu/ui/components"
import "../../hygu/ui/components/buttons"

Row {
    property alias btnRef: btn
    property alias textRef: textElem
    property string filepath

    spacing: 4

    ResultParamText {
        id: textElem

    }
    IconButtonFlat {
        id: btn
        btnIconColor: Material.color(Material.Grey)
        img: "chart-simple-solid"
        tooltipRef.visible: false

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                popup.open();
            }
            onExited: {
                popup.close();
            }
        }
    }

    ImagePopup {
        id: popup
        fpath: filepath
    }
}
