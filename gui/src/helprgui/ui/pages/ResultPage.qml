/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material

import "../components"
import helprgui.classes


Item {
    property int qIndex
    property int barWidth: 1162  // align with right side of last button

    property font paramFont: Qt.font({
        bold: false,
        italic: false,
        pixelSize: 14,
    });
    property font paramFontBold: Qt.font({
        bold: true,
        italic: false,
        pixelSize: 14,
    });

    function showChoiceParam(textElem, param)
    {
        textElem.text = "<strong>" + param.label + "</strong>: " + param.value_display;
    }

    function showBasicParam(textElem, param)
    {
        textElem.text = "<strong>" + param.label + "</strong>: " + param.value;
    }

    function showParam(elem, param)
    {
        let val = param.value;
        let fmtVal = val;
        if (val > 1)
        {
            fmtVal = Math.round(val * 100) / 100;
        }
        else {
            fmtVal = Math.round(val * 1000) / 1000;
        }

        if (param.input_type === "nor")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Normal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "log")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Lognormal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "uni")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Uniform " + param.a + " to " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp;
        }
    }

    function clearImage(qimg)
    {
        qimg.source = "";
        qimg.filename = "";
    }

    function updateImage(qimg, fl)
    {
        let val = fl ? fl : "";
        if (val === "" || val === null)
        {
            qimg.visible = false;
            return;
        }
        qimg.visible = true;
        qimg.source = 'file:' + val;
        qimg.filename = val;
    }

    function updateContent()
    {
        // Fill this
    }

    function refresh(resultsForm)
    {
        if (resultsForm !== null)
        {
            pyform = resultsForm;
        }
        updateContent();
    }

    anchors.fill: parent
}
