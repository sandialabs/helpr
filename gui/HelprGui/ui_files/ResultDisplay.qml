/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material

import helpr.classes


Item {
    property AnalysisController ac
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
        if (param.input_type === "nor")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + param.value + " " + param.get_unit_disp + " (Normal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "log")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + param.value + " " + param.get_unit_disp + " (Lognormal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "uni")
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + param.value + " " + param.get_unit_disp + " (Uniform " + param.a + " to " + param.b + ", " + param.uncertainty_disp + ")";
        }
        else
        {
            elem.text = "<strong>" + param.label_rtf + "</strong>: " + param.value + " " + param.get_unit_disp;
        }
    }

    function clearImage(qimg)
    {
        qimg.source = "";
        qimg.filename = "";
    }

    function showImage(qimg, fl)
    {
        let val = fl ? fl : "";
        if (val === "" || val === null) return;
        qimg.source = 'file:' + val;
        qimg.filename = val;
    }

    function updateContent()
    {
        // reset all sections
        let images = [crackGrowthPlot, exRatesPlot, detFadPlot, ensemblePlot, cyclePlot, pdfPlot, cdfPlot, prbFadPlot, senPlot];
        images.forEach((img, i) => clearImage(img));

        detSection.visible = false;
        prbSection.visible = false;
        senSection.visible = false;
        paramSection.visible = false;
        errorSection.visible = false;
        cancellationSection.visible = false;

        descrip.text = "";

        if (ac === null)
        {
            title.text = "Submit an analysis";
            return;
        }

        title.text = "" + ac.name;
        if (!ac.finished)
        {
            status.text = "in-progress";
            status.color = color_progress;
            return;
        }

        // Analysis complete
        showChoiceParam(study_type, ac.study_type);
        showBasicParam(n_ale, ac.n_ale);
        showBasicParam(n_epi, ac.n_epi);
        showBasicParam(seed, ac.seed);

        showParam(out_diam, ac.out_diam);
        showParam(thickness, ac.thickness);
        showParam(yield_str, ac.yield_str);
        showParam(frac_resist, ac.frac_resist);
        showParam(vol_h2, ac.vol_h2);

        showParam(p_max, ac.p_max);
        showParam(p_min, ac.p_min);
        showParam(temp, ac.temp);
        showParam(crack_dep, ac.crack_dep);
        showParam(crack_len, ac.crack_len);

        paramSection.visible = true;

        if (ac.has_error)
        {
            status.text = "error";
            status.color = color_danger;
            errorMessage.text = ac.error_message;
            errorSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }

        if (ac.was_canceled)
        {
            cancellationSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }

        // Analysis complete and successful
        status.text = "complete";
        status.color = color_success;

        if (ac.study_type.value === 'det')
        {
            n_ale.visible = false;
            n_epi.visible = false;
            showImage(crackGrowthPlot, ac.crack_growth_plot);
            showImage(exRatesPlot, ac.ex_rates_plot);
            showImage(detFadPlot, ac.fad_plot);
            detSection.visible = true;
        }

        else if (ac.study_type.value === 'prb' && ac.n_epi.value > 0)
        {
            n_ale.visible = true;
            n_epi.visible = true;
            showImage(ensemblePlot, ac.ensemble_plot);
            showImage(cyclePlot, ac.cycle_plot);
            showImage(pdfPlot, ac.pdf_plot);
            showImage(cdfPlot, ac.cdf_plot);
            showImage(prbFadPlot, ac.fad_plot);
            prbSection.visible = true;
        }

        else if (ac.study_type.value === 'prb')
        {
            n_ale.visible = true;
            showImage(ensemblePlot, ac.ensemble_plot);
            showImage(cyclePlot, ac.cycle_plot);
            showImage(pdfPlot, ac.pdf_plot);
            showImage(cdfPlot, ac.cdf_plot);
            showImage(prbFadPlot, ac.fad_plot);
            prbSection.visible = true;
        }

        else
        {
            showImage(senPlot, ac.sen_plot);
            senSection.visible = true;
        }

        updateHeight();
    }

    // Updates ContentHeight of scroll section.
    // Do this separately from above so it can be tied to heightChanged event of Flickable.
    function updateHeight()
    {
        if (ac === null) return;

        let h = 1000;
        if (ac.study_type.value === 'prb')
        {
            h = 980;
        }
        else if (ac.study_type.value === 'det')
        {
            h = 1120;
        }
        else
        {
            h = 680;
        }
        resultSection.contentHeight = h;
    }

    function refresh(analysisController)
    {
        if (analysisController !== null)
        {
            ac = analysisController;
        }
        updateContent();
    }

    anchors.fill: parent

    Pane {
        id: resultPane1
        anchors.fill: parent

        Column {  // main positioner
            anchors.fill: parent
            spacing: 10

            Item {
                width: parent.width
                height: title.height

                Text {
                    id: title
                    font.pointSize: 20
                    text: ""
                }
                Text {
                    id: status
                    font.pointSize: 13
                    font.italic: true
                    text: ""
                    anchors.left: title.right
                }

                Row {
                    id: buttonBar
                    visible: ac && ac.finished && !ac.has_error
                    height: 50
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 100
                    spacing: 4

                    AppButton {
                        id: restoreParamsBtn
                        img: 'tent-arrows-down-solid'
                        tooltip: ("Overwrites form parameter values to match this analysis")
                        onClicked: ac.overwrite_form_data()
                    }

                    AppButton {
                        id: openOutputBtn
                        img: 'folder-open-solid'
                        tooltip: ("Open directory containing analysis results")
                        onClicked: ac.open_output_directory()
                    }

                    AppButton {
                        id: deleteBtn
                        img: 'trash-solid'
                        tooltip: ("Delete analysis results")
                        bgColor: Material.color(Material.Red, Material.Shade300)
                        onClicked: function() {
                            queueListView.removeItem(qIndex);
                            resultContainer.close();
                        }
                    }
                }


                AppIcon {
                    source: 'xmark-solid'
                    anchors.right: parent.right
                    anchors.top: parent.top

                    MouseArea {
                        anchors.fill: parent
                        onClicked: resultContainer.close()
                    }
                }
            }

            Text {
                id: descrip
                font.pointSize: 16
                font.italic: true
                text: ""
            }
            Text {
                id: inProgressMessage
                visible: ac && !ac.finished
                font.pointSize: 16
                font.italic: true
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: "Analysis in-progress - reopen once analysis is complete"
            }

            VSpacer { height: 5 }

            Column {
                id: errorSection

                Text {
                    id: errorHeader
                    font.pointSize: 16
                    font.italic: true
                    color: Material.color(Material.Red)
                    text: "Error during analysis"
                }
                Text {
                    id: errorMessage
                    font.pointSize: 13
                    color: Material.color(Material.Red)
                    text: ""
                }
                VSpacer { height: 10 }
            }

            // Note: this section rarely visible since queue item removed immediately.
            Column {
                id: cancellationSection

                Row {
                    spacing: 2

                    AppIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        source: 'circle-exclamation-solid'
                        iconColor: color_text_warning
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        id: cancellationHeader
                        font.pointSize: 16
                        font.italic: true
                        color: color_text_warning
                        text: " Analysis canceled"
                    }
                }

                Text {
                    id: cancelMessage
                    font.pointSize: 13
                    color: color_text_warning
                    text: "Analysis successfully canceled"
                }
                VSpacer { height: 10 }
            }

            Flickable
            {
                id: resultSection
                clip: true
                contentHeight: (paramSection.height + detSection.height +
                                senSection.height +
                                prbSection.height
                                )
                contentWidth: parent.width
                height: parent.height - y
                width: parent.width
                visible: ac && ac.finished

                onHeightChanged: { updateHeight(); }

                Layout.fillHeight: true
                Layout.fillWidth: true

                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.FollowBoundsBehavior
                flickDeceleration: 10000

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AlwaysOn
                }

                Column {
                    id: paramSection

                    FormSectionHeader {
                        iconSrc: "vials-solid"
                        title: "Analysis Parameters"
                        rWidth: barWidth
                        bottomPad: 8
                    }

                    Row {
                        id: paramRow
                        spacing: 35
                        Column {
                            TextEdit { id: study_type; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: seed; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: n_ale; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: n_epi; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                        }
                        Column {
                            TextEdit { id: out_diam; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: thickness; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: yield_str; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: frac_resist; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: vol_h2; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                        }

                        Column {
                            TextEdit { id: p_max; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: p_min; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: temp; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: crack_dep; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                            TextEdit { id: crack_len; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
                        }
                    }

//                    VSpacer { height: 20 }
                }

                Column {
                    id: detSection
                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        title: "Plotted Results (Deterministic)"
                        iconSrc: "chart-line-solid"
                        rWidth: barWidth
                        topPad: 10
                        bottomPad: 8
                    }

                    Row {
                        SimImage {
                            id: crackGrowthPlot
                        }

                        SimImage {
                            id: exRatesPlot
                        }
                    }
                    VSpacer { height: 20 }
                    Row {
                        SimImage {
                            id: detFadPlot
                        }
                    }
                    VSpacer { height: 20 }
                }

                Column {
                    id: senSection
                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        title: "Plotted Results (Sensitivity)"
                        iconSrc: "chart-line-solid"
                        rWidth: barWidth
                        topPad: 10
                        bottomPad: 8
                    }

                    Row {
                        SimImage {
                            id: senPlot
                        }
                    }
                    VSpacer { height: 20 }
                }

                Column {
                    id: prbSection
                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        iconSrc: "chart-line-solid"
                        title: "Plotted Results (Probabilistic)"
                        rWidth: barWidth
                        topPad: 10
                        bottomPad: 8
                    }

                    Row {
                        SimImage {
                            id: ensemblePlot
                            height: 350
                        }
                        SimImage {
                            id: cyclePlot
                            height: 350
                        }
                        SimImage {
                            id: prbFadPlot
                            height: 350
                        }
                    }
                    VSpacer { height: 20 }

                    Row {
//                        id: probPlotRow2
                        SimImage {
                            id: pdfPlot
                            height: 350
                        }
                        SimImage {
                            id: cdfPlot
                            height: 350
                        }
                    }

                    VSpacer { height: 20 }
//                    Row {
////                        id: probPlotRow3
//                    }
//                    VSpacer { height: 20 }

//                    ListView {
//                        id: cycleCbvView
//                        orientation: Qt.Horizontal
//                        height: 350
//                        width: parent.width
//                        delegate:
//                            SimImage {
//                            width: 350
//                            sourceSize.width: width
//                            source: 'file:' + modelData
//                            filename: modelData
//                        }
//                    }

                }
            }
        }
    }

}
