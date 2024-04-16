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

import "../helprgui/ui/components"
import "../helprgui/ui/components/buttons"
import "../helprgui/ui/pages"
import helprgui.classes
import helpr.classes


ResultPage
{
    property CrackEvolutionResultsForm pyform

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

        if (pyform === null)
        {
            title.text = "Submit an analysis";
            return;
        }

        title.text = "" + pyform.name_str;
        if (!pyform.finished)
        {
            statusIcon.visible = false;
            status.visible = true;
            status.text = "in-progress";
            status.color = color_progress;
            return;
        }

        status.visible = false;

        // Analysis complete
        showChoiceParam(study_type, pyform.study_type);
        showBasicParam(n_ale, pyform.n_ale);
        showBasicParam(n_epi, pyform.n_epi);
        showParam(smys, pyform.smys);
        showBasicParam(seed, pyform.seed);

        showParam(out_diam, pyform.out_diam);
        showParam(thickness, pyform.thickness);
        showParam(yield_str, pyform.yield_str);
        showParam(frac_resist, pyform.frac_resist);
        showParam(vol_h2, pyform.vol_h2);

        showParam(p_max, pyform.p_max);
        showParam(p_min, pyform.p_min);
        showParam(temp, pyform.temp);
        showParam(crack_dep, pyform.crack_dep);
        showParam(crack_len, pyform.crack_len);

        paramSection.visible = true;

        if (pyform.has_error)
        {
            errorMessage.text = pyform.error_message;
            errorSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }

        if (pyform.was_canceled)
        {
            cancellationSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }

        // Analysis complete and successful
        // status.text = "complete";
        // status.color = color_success;
        statusIcon.visible = true;
        statusIcon.iconColor = color_success;

        if (pyform.study_type.value === 'det')
        {
            n_ale.visible = false;
            n_epi.visible = false;
            updateImage(crackGrowthPlot, pyform.crack_growth_plot);
            updateImage(exRatesPlot, pyform.ex_rates_plot);
            updateImage(detFadPlot, pyform.fad_plot);
            detSection.visible = true;
        }

        else if (pyform.study_type.value === 'prb' && pyform.n_epi.value > 0)
        {
            n_ale.visible = true;
            n_epi.visible = true;
            updateImage(ensemblePlot, pyform.ensemble_plot);
            updateImage(cyclePlot, pyform.cycle_plot);
            updateImage(pdfPlot, pyform.pdf_plot);
            updateImage(cdfPlot, pyform.cdf_plot);
            updateImage(prbFadPlot, pyform.fad_plot);
            prbSection.visible = true;
        }

        else if (pyform.study_type.value === 'prb')
        {
            n_ale.visible = true;
            updateImage(ensemblePlot, pyform.ensemble_plot);
            updateImage(cyclePlot, pyform.cycle_plot);
            updateImage(pdfPlot, pyform.pdf_plot);
            updateImage(cdfPlot, pyform.cdf_plot);
            updateImage(prbFadPlot, pyform.fad_plot);
            prbSection.visible = true;
        }

        else
        {
            updateImage(senPlot, pyform.sen_plot);
            senSection.visible = true;
        }

        updateHeight();
    }

    // Updates ContentHeight of scroll section.
    // Do this separately from above so it can be tied to heightChanged event of Flickable.
    function updateHeight()
    {
        if (pyform === null) return;

        let h = 1000;
        if (pyform.study_type.value === 'prb')
        {
            h = 980;
        }
        else if (pyform.study_type.value === 'det')
        {
            h = 1120;
        }
        else
        {
            h = 680;
        }
        resultSection.contentHeight = h;
    }

    Pane {
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
                    elide: Text.ElideRight
                }
                Text {
                    id: status
                    font.pointSize: 13
                    font.italic: true
                    text: ""
                    anchors.left: title.right
                    anchors.leftMargin: 5
                }
                AppIcon {
                    id: statusIcon
                    source: 'check-solid'
                    iconColor: Material.color(Material.Green)
                    anchors.left: title.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter
                }

                Row {
                    id: buttonBar
                    visible: pyform && pyform.finished && !pyform.has_error
                    height: 40
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 100
                    spacing: 4

                    IconButton {
                        id: restoreParamsBtn
                        img: 'tent-arrows-down-solid'
                        tooltip: ("Overwrites form parameter values to match this analysis")
                        onClicked: pyform.overwrite_form_data()
                    }

                    IconButton {
                        id: openOutputBtn
                        img: 'folder-open-solid'
                        tooltip: ("Open directory containing analysis results")
                        onClicked: pyform.open_output_directory()
                    }

                    IconButton {
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
                visible: pyform && !pyform.finished
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
                visible: pyform && pyform.finished

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
                            TextEdit { id: smys; text: ""; font: paramFont; readOnly: true; selectByMouse: true; textFormat: Text.RichText}
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

                    Grid {
                        columns: 2
                        SimImage {
                            id: crackGrowthPlot
                        }

                        SimImage {
                            id: exRatesPlot
                        }
                        //                    }
                        //                    VSpacer { height: 20 }
                        //                    Row {
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

                    Grid {
                        columns: 3

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
                }
            }
        }
    }


}
