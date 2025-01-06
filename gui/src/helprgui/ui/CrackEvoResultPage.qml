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
import "Chart.js" as Chart
import "../hygu/ui/utils.js" as Utils
import "../hygu/ui/components"
import "../hygu/ui/components/buttons"
import "../hygu/ui/pages"
import "components"
import "charts"
import hygu.classes
import helpr.classes

ResultPage {
    property var cdfData
    property var crackGrowthData
    property var cycleData
    property var designCurveData
    property var detFadData
    property var ensembleData
    property var pdfData
    property int plotAnimDuration: 0
    property int plotH: 400
    property int plotSmW: 500
    property int plotW: 550
    property var probFadData
    property CrackEvolutionResultsForm pyform
    property var sensitivityData

    function dynamicColor(i, total) {
        var r = 100 + i * 155 / total;
        var g = 100 + i * 155 / total;
        var b = i * 255 / total;
        return "rgb(" + r + "," + g + "," + b + ")";
    }

    /// Create label of point data with specified decimals
    function getDataLabel(item, data, xDecimals, yDecimals) {
        var label = data.datasets[item.datasetIndex].label || '';
        if (label) {
            label += ': (' + roundNum(item.xLabel, xDecimals) + ", " + roundNum(item.yLabel, yDecimals) + ")";
        }
        return label;
    }
    function getDataLabelExp(item, data, xDecimals, yDecimals) {
        var label = data.datasets[item.datasetIndex].label || '';
        if (label) {
            label += ': (' + item.xLabel.toExponential(xDecimals) + ", " + item.yLabel.toExponential(yDecimals) + ")";
        }
        return label;
    }
    function parsePlotData(data) {
        if (!data || data === null || data === undefined) {
            return null;
        } else {
            return JSON.parse(data);
        }
    }
    function randomColor(opac) {
        var r = Math.floor(Math.random() * 255);
        var g = Math.floor(Math.random() * 255);
        var b = Math.floor(Math.random() * 255);
        // Avoiding using reds as it's close to specified color for nominal value
        if (r > 200) {
            r -= 50;
        }
        return "rgba(" + r + "," + g + "," + b + "," + opac + ")";
    }

    function roundNum(num, decs) {
        var mul = 10 ** decs;
        var result = Math.round(num * mul) / mul;
        return result;
    }

    function scrollToTop() {
        resultSection.contentY = 0;
    }

    function showDistrParam(elem, param) {
        let val = param.value;
        let fmtVal = val;
        if (val > 1) {
            fmtVal = Math.round(val * 100) / 100;
        } else {
            fmtVal = Math.round(val * 1000) / 1000;
        }
        if (param.input_type === "tnor") {
            // let dstr = param.d_is_null ? "\u221E" : param.d;
            let dstr = param.d_is_null ? "inf" : param.d;
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Normal " + param.a + "+/-" + param.b + ", bounds " + param.c + "-" + dstr + ", " + param.uncertainty_disp + ")";
        } else if (param.input_type === "tlog") {
            let dstr = param.d_is_null ? "inf" : param.d;
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Lognormal " + param.a + "+/-" + param.b + ", bounds " + param.c + "-" + dstr + ", " + param.uncertainty_disp + ")";
        } else if (param.input_type === "nor") {
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Normal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        } else if (param.input_type === "log") {
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Lognormal " + param.a + " +/- " + param.b + ", " + param.uncertainty_disp + ")";
        } else if (param.input_type === "uni") {
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp + " (Uniform " + param.a + " to " + param.b + ", " + param.uncertainty_disp + ")";
        } else {
            elem.textRef.text = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + param.get_unit_disp;
        }
        if (param.uncertainty_plot !== "") {
            elem.btnRef.visible = true;
            elem.filepath = param.uncertainty_plot;
        } else {
            elem.btnRef.visible = false;
            elem.filepath = "";
        }
    }

    function updateContent() {
        let images = [crackGrowthPlot, designCurvePlot, detFadPlot, ensemblePlot, cyclePlot, pdfPlot, cdfPlot, probFadPlot, senPlot];
        images.forEach((img, i) => clearImage(img));

        detSection.visible = false;
        probSection.visible = false;
        senSection.visible = false;
        paramSection.visible = false;
        errorSection.visible = false;
        cancellationSection.visible = false;
        descrip.text = "";
        if (pyform === null) {
            title.text = "Submit an analysis";
            return;
        }
        title.text = "" + pyform.name_str;
        if (!pyform.finished) {
            statusIcon.visible = false;
            status.visible = true;
            status.text = "in-progress";
            status.color = color_progress;
            return;
        }
        status.visible = false;

        // Analysis complete
        Utils.showChoiceParam(study_type, pyform.study_type);
        Utils.showChoiceParam(stress_method, pyform.stress_method);
        Utils.showChoiceParam(surface, pyform.surface);
        Utils.showChoiceParam(crack_assump, pyform.crack_assump);
        Utils.showBasicParam(n_ale, pyform.n_ale);
        Utils.showBasicParam(n_epi, pyform.n_epi);
        Utils.showBasicParam(seed, pyform.seed);
        if (pyform.n_cycles.value === 0) {
            // Val of 0 indicates null
            // n_cycles.text = "<strong>" + pyform.n_cycles.label + "</strong>: a/t";
            n_cycles.visible = false;
        } else {
            n_cycles.visible = true;
            n_cycles.text = "<strong>Max cycles</strong>: " + pyform.n_cycles.value;
        }

        showDistrParam(smys, pyform.smys);
        showDistrParam(r_ratio, pyform.r_ratio);
        showDistrParam(a_m, pyform.a_m);
        showDistrParam(a_c, pyform.a_c);
        showDistrParam(t_r, pyform.t_r);
        showDistrParam(out_diam, pyform.out_diam);
        showDistrParam(thickness, pyform.thickness);
        showDistrParam(yield_str, pyform.yield_str);
        showDistrParam(frac_resist, pyform.frac_resist);
        showDistrParam(vol_h2, pyform.vol_h2);
        showDistrParam(p_max, pyform.p_max);
        showDistrParam(p_min, pyform.p_min);
        showDistrParam(temp, pyform.temp);
        showDistrParam(crack_dep, pyform.crack_dep);
        showDistrParam(crack_len, pyform.crack_len);

        paramSection.visible = true;
        if (pyform.has_error) {
            errorMessage.text = pyform.error_message;
            errorSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }
        if (pyform.was_canceled) {
            cancellationSection.visible = true;
            resultSection.contentHeight = paramSection.height + detSection.height;
            return;
        }

        // Analysis complete and successful
        // status.text = "complete";
        // status.color = color_success;
        statusIcon.visible = true;
        statusIcon.iconColor = color_success;

        let showInteractive = pyform.show_interactive_charts;

        if (pyform.study_type.value === 'det') {
            n_ale.visible = false;
            n_epi.visible = false;

            detInterCharts.visible = showInteractive;
            detStaticCharts.visible = !showInteractive;

            if (showInteractive) {
                crackGrowthData = parsePlotData(pyform.crack_growth_data);
                designCurveData = parsePlotData(pyform.design_curve_data);
                detFadData = parsePlotData(pyform.det_fad_data);
            } else {
                updateImage(crackGrowthPlot, pyform.crack_growth_plot);
                updateImage(designCurvePlot, pyform.design_curve_plot);
                updateImage(detFadPlot, pyform.fad_plot);
            }

            detSection.visible = true;

        } else if (pyform.study_type.value === 'prb') {
            if (pyform.n_epi.value > 0) {
                n_epi.visible = true;
            }
            n_ale.visible = true;

            prbInterCharts.visible = showInteractive;
            prbStaticCharts.visible = !showInteractive;

            if (showInteractive) {
                ensembleData = parsePlotData(pyform.ensemble_data);
                cycleData = parsePlotData(pyform.cycle_data);
                probFadData = parsePlotData(pyform.prob_fad_data);
                pdfData = parsePlotData(pyform.pdf_data);
                cdfData = parsePlotData(pyform.cdf_data);
            } else {
                updateImage(ensemblePlot, pyform.ensemble_plot);
                updateImage(cyclePlot, pyform.cycle_plot);
                updateImage(pdfPlot, pyform.pdf_plot);
                updateImage(cdfPlot, pyform.cdf_plot);
                updateImage(probFadPlot, pyform.fad_plot);
            }
            probSection.visible = true;

        } else {
            if (showInteractive) {
                sensitivityData = parsePlotData(pyform.sensitivity_data);
                senPlot.visible = false;
                senInterChart.visible = true;
            } else {
                updateImage(senPlot, pyform.sen_plot);
                senPlot.visible = true;
                senInterChart.visible = false;
            }
            senSection.visible = true;
        }
        updateHeight();
    }

    // Updates ContentHeight of scroll section.
    // Do this separately from above so it can be tied to heightChanged event of Flickable.
    function updateHeight() {
        if (pyform === null)
            return;
        let study = pyform.study_type.value;
        if (study === 'prb') {
            resultSection.contentHeight = 1800;
        } else if (study === 'det') {
            resultSection.contentHeight = 1400;
        } else {
            resultSection.contentHeight = 820;
        }
    }

    Pane {
        anchors.fill: parent

        Column {
            // main positioner
            anchors.fill: parent
            spacing: 10

            Item {
                height: title.height
                width: parent.width

                Text {
                    id: title

                    elide: Text.ElideRight
                    font.pointSize: 20
                    text: ""
                }
                Text {
                    id: status

                    anchors.left: title.right
                    anchors.leftMargin: 5
                    font.italic: true
                    font.pointSize: 13
                    text: ""
                }
                AppIcon {
                    id: statusIcon

                    anchors.left: title.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter
                    iconColor: Material.color(Material.Green)
                    source: 'check-solid'
                }
                Row {
                    id: buttonBar

                    anchors.right: parent.right
                    anchors.rightMargin: 100
                    anchors.top: parent.top
                    height: 40
                    spacing: 4
                    visible: pyform && pyform.finished && !pyform.has_error

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

                        bgColor: Material.color(Material.Red, Material.Shade300)
                        img: 'trash-solid'
                        tooltip: ("Delete analysis results")

                        onClicked: function () {
                            queueListView.removeItem(qIndex);
                            resultContainer.close();
                        }
                    }
                }
                AppIcon {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    source: 'xmark-solid'

                    MouseArea {
                        anchors.fill: parent

                        onClicked: resultContainer.close()
                    }
                }
            }
            Text {
                id: descrip

                font.italic: true
                font.pointSize: 16
                text: ""
            }
            Text {
                id: inProgressMessage

                font.italic: true
                font.pointSize: 16
                horizontalAlignment: Text.AlignHCenter
                text: "Analysis in-progress - reopen once analysis is complete"
                visible: pyform && !pyform.finished
                width: parent.width
            }
            VSpacer {
                height: 5
            }
            Column {
                id: errorSection

                Text {
                    id: errorHeader

                    color: Material.color(Material.Red)
                    font.italic: true
                    font.pointSize: 16
                    text: "Error during analysis"
                }
                Text {
                    id: errorMessage

                    color: Material.color(Material.Red)
                    font.pointSize: 13
                    text: ""
                }
                VSpacer {
                    height: 10
                }
            }

            // Note: this section rarely visible since queue item removed immediately.
            Column {
                id: cancellationSection

                Row {
                    spacing: 2

                    AppIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        iconColor: color_text_warning
                        source: 'circle-exclamation-solid'
                    }
                    Text {
                        id: cancellationHeader

                        anchors.verticalCenter: parent.verticalCenter
                        color: color_text_warning
                        font.italic: true
                        font.pointSize: 16
                        text: " Analysis canceled"
                    }
                }
                Text {
                    id: cancelMessage

                    color: color_text_warning
                    font.pointSize: 13
                    text: "Analysis successfully canceled"
                }
                VSpacer {
                    height: 10
                }
            }
            Flickable {
                id: resultSection

                Layout.fillHeight: true
                Layout.fillWidth: true
                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.FollowBoundsBehavior
                clip: true
                contentHeight: (paramSection.height + detSection.height + senSection.height + probSection.height)
                contentWidth: parent.width

                // increase scroll speed
                flickDeceleration: 15000
                height: parent.height - y
                visible: pyform && pyform.finished
                width: parent.width

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AlwaysOn
                }

                onHeightChanged: {
                    updateHeight();
                }

                ScrollMouseArea {
                    container: resultSection
                }
                Column {
                    id: paramSection

                    FormSectionHeader {
                        bottomPad: 8
                        iconSrc: "vials-solid"
                        rWidth: barWidth
                        title: "Analysis Specification"
                    }
                    VSpacer {
                        height: 5
                    }
                    FormSectionHeader2 {
                        bottomPad: 5
                        fontSize: 12
                        // iconSrc: "vials-solid"
                        rWidth: barWidth - 20
                        title: "Analysis Description"
                        topPad: 10
                    }
                    Row {
                        id: paramRow1

                        spacing: 35

                        Column {
                            ResultParamText {
                                id: study_type

                            }
                            ResultParamText {
                                id: seed

                            }
                        }
                        Column {
                            ResultParamText {
                                id: n_ale

                            }
                            ResultParamText {
                                id: n_epi

                            }
                            ResultParamText {
                                id: n_cycles

                            }
                        }
                        Column {
                            ResultParamText {
                                id: crack_assump

                            }
                            ResultParamText {
                                id: stress_method
                            }
                            ResultParamText {
                                id: surface
                            }
                        }
                    }
                    VSpacer {
                        height: 15
                    }
                    FormSectionHeader2 {
                        bottomPad: 5
                        fontSize: 12
                        // iconSrc: "vials-solid"
                        rWidth: barWidth - 20
                        title: "User Inputs"
                        topPad: 10
                    }
                    Row {
                        id: paramRow2

                        spacing: 35

                        Column {
                            UncertainResultParam {
                                id: out_diam

                            }
                            UncertainResultParam {
                                id: thickness

                            }
                            UncertainResultParam {
                                id: yield_str

                            }
                            UncertainResultParam {
                                id: frac_resist

                            }
                            UncertainResultParam {
                                id: vol_h2

                            }
                        }
                        Column {
                            UncertainResultParam {
                                id: p_max

                            }
                            UncertainResultParam {
                                id: p_min

                            }
                            UncertainResultParam {
                                id: temp

                            }
                            UncertainResultParam {
                                id: crack_dep

                            }
                            UncertainResultParam {
                                id: crack_len

                            }
                        }
                    }
                    VSpacer {
                        height: 15
                    }
                    FormSectionHeader2 {
                        bottomPad: 5
                        fontSize: 12
                        // iconSrc: "vials-solid"
                        rWidth: barWidth - 20
                        title: "Calculated Parameters"
                        topPad: 10
                    }
                    Row {
                        id: paramRow3

                        spacing: 35

                        Column {
                            UncertainResultParam {
                                id: smys

                            }
                            UncertainResultParam {
                                id: r_ratio

                            }
                        }
                        Column {
                            UncertainResultParam {
                                id: a_m

                            }
                            UncertainResultParam {
                                id: a_c

                            }
                        }
                        Column {
                            UncertainResultParam {
                                id: t_r

                            }
                        }
                    }
                }
                Column {
                    id: detSection

                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        bottomPad: 8
                        iconSrc: "chart-line-solid"
                        rWidth: barWidth
                        title: "Plotted Results (Deterministic)"
                        topPad: 10
                    }
                    Grid {
                        id: detInterCharts
                        columnSpacing: 10
                        columns: 2
                        rowSpacing: 10
                        rows: 2

                        CrackGrowthChart {
                            plotData: crackGrowthData
                        }
                        DesignCurveChart {
                            plotData: designCurveData
                        }
                        DetFadChart {
                            plotData: detFadData
                        }
                    }
                    Grid {
                        id: detStaticCharts
                        columnSpacing: 10
                        columns: 2
                        rowSpacing: 10
                        rows: 2

                        SimImage {
                            id: crackGrowthPlot

                        }
                        SimImage {
                            id: designCurvePlot

                        }
                        SimImage {
                            id: detFadPlot

                        }
                        VSpacer {
                            height: 40
                        }
                    }
                }
                Column {
                    id: senSection

                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        bottomPad: 8
                        iconSrc: "chart-line-solid"
                        rWidth: barWidth
                        title: "Plotted Results (Sensitivity)"
                        topPad: 10
                    }
                    Row {
                        SensitivityChart {
                            id: senInterChart
                            plotData: sensitivityData
                        }
                        SimImage {
                            id: senPlot

                        }
                    }
                    VSpacer {
                        height: 20
                    }
                }
                Column {
                    id: probSection

                    anchors.top: paramSection.bottom
                    anchors.topMargin: 30

                    FormSectionHeader {
                        bottomPad: 8
                        iconSrc: "chart-line-solid"
                        rWidth: barWidth
                        title: "Plotted Results (Probabilistic)"
                        topPad: 10
                    }
                    Grid {
                        id: prbInterCharts
                        columns: 2
                        spacing: 20

                        EnsembleChart {
                            plotData: ensembleData
                        }
                        CycleChart {
                            plotData: cycleData
                        }
                        ProbFadChart {
                            plotData: probFadData
                        }
                        PdfChart {
                            plotData: pdfData
                        }
                        CdfChart {
                            plotData: cdfData
                        }
                    }
                    Grid {
                        id: prbStaticCharts
                        columns: 2
                        spacing: 20

                        SimImage {id: ensemblePlot; height: 420; }
                        SimImage {id: cyclePlot; height: 420; }
                        SimImage {id: probFadPlot; height: 420; }
                        SimImage {id: pdfPlot; height: 420; }
                        SimImage {id: cdfPlot; height: 420; }
                    }
                    VSpacer {
                        height: 20
                    }
                }
            }
        }
    }
}
