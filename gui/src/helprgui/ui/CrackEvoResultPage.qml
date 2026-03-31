/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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
import "../hygu/ui/parameters"
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
    property int plotW: 450
    property int plotH: 420
    property int plotSmallW: 390
    property int plotSmallH: 360
    property int plotLgW: plotW * 1.5
    property int plotLgH: plotH * 1.5
    property int sectionMargin: 30
    property var probFadData
    property CrackEvolutionResultsForm pyform
    property var sensitivityData
    property var sensitivityDataFad

    Connections {
        target: pyform

        function onImaFinished(status)
        {
            displayInspectionMitigationResults(status);
        }
    }

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
        let unit = param.get_unit_disp;
        let lbl = "<strong>" + param.label_rtf + "</strong>: " + fmtVal + " " + unit;

        // Deterministic studies use only the nominal value regardless of distribution
        let isDet = pyform.study_type.value === 'det';
        if (isDet || param.input_type === "det")
        {
            elem.textRef.text = lbl;
        }
        else if (param.input_type === "tnor")
        {
            let dstr = param.upper_is_null ? "\u221E" : Utils.hround(param.upper);
            elem.textRef.text = lbl + " (Normal " + Utils.hround(param.mean) + "\u00B1" + Utils.hround(param.std) + ", bounds " + Utils.hround(param.lower) + "\u2013" + dstr + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "tlog")
        {
            let dstr = param.upper_is_null ? "\u221E" : Utils.hround(param.upper);
            elem.textRef.text = lbl + " (Lognormal \u03BC=" + Utils.hround(param.mu) + " \u03C3=" + Utils.hround(param.sigma) + ", bounds " + Utils.hround(param.lower) + "\u2013" + dstr + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "nor")
        {
            elem.textRef.text = lbl + " (Normal " + Utils.hround(param.mean) + "\u00B1" + Utils.hround(param.std) + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "log")
        {
            elem.textRef.text = lbl + " (Lognormal \u03BC=" + Utils.hround(param.mu) + " \u03C3=" + Utils.hround(param.sigma) + ", " + param.uncertainty_disp + ")";
        }
        else if (param.input_type === "uni")
        {
            elem.textRef.text = lbl + " (Uniform " + Utils.hround(param.lower) + "\u2013" + Utils.hround(param.upper) + ", " + param.uncertainty_disp + ")";
        }
        else
        {
            elem.textRef.text = lbl;
        }
        if (!isDet && param.uncertainty_plot !== "") {
            elem.btnRef.visible = true;
            elem.filepath = param.uncertainty_plot;
        } else {
            elem.btnRef.visible = false;
            elem.filepath = "";
        }
    }

    function updateContent() {
        let images = [crackGrowthPlot, designCurvePlot, detFadPlot, ensemblePlot, cyclePlot,
            pdfPlot, cdfPlot, probFadPlot, senPlot, randomLoadingProfilePlot];
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

        let isBounds = pyform.study_type.value === 'bnd';
        n_ale.visible = !isBounds;
        n_epi.visible = !isBounds;
        if (!isBounds) {
            Utils.showBasicParam(n_ale, pyform.n_ale);
            Utils.showBasicParam(n_epi, pyform.n_epi);
        }
        Utils.showBasicParam(seed, pyform.seed);

        Utils.showChoiceParam(evolution_method, pyform.evolution_method);
        if (pyform.evolution_method.value === "cycles") {
            Utils.showBasicParam(cycle_step_size, pyform.cycle_step_size);
        }
        else {
            cycle_step_size.text = "<strong>" + pyform.cycle_step_size.label + "</strong>: --";
        }

        if (pyform.n_cycles.value === 0) {
            // Val of 0 indicates null
            // n_cycles.text = "<strong>" + pyform.n_cycles.label + "</strong>: a/t";
            n_cycles.visible = false;
        } else {
            n_cycles.visible = true;
            n_cycles.text = "<strong>Max cycles</strong>: " + pyform.n_cycles.value;
        }
        
        // Show random loading profile if used OR show pressures
        if (pyform.random_loading_profile && pyform.random_loading_profile.value && pyform.random_loading_profile.value !== "") {
            p_min.visible = false;
            p_max.visible = false;
            randomLoadingProfile.visible = true;
            randomLoadingProfile.text = "<strong>Random loading profile (" + pyform.profile_units.value + ")</strong>: " + pyform.random_loading_profile.value;
            randomLoadingProfilePlot.visible = true;
            updateImage(randomLoadingProfilePlot, pyform.loading_profile_plot);
        } else {
            randomLoadingProfile.visible = false;
            randomLoadingProfilePlot.visible = false;
            p_min.visible = true;
            p_max.visible = true;
            showDistrParam(p_max, pyform.p_max);
            showDistrParam(p_min, pyform.p_min);
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
        showDistrParam(residual_stress_intensity, pyform.stress_intensity);
        showDistrParam(vol_h2, pyform.vol_h2);
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
        statusIcon.visible = true;
        statusIcon.iconColor = color_success;

        let showInteractive = pyform.show_interactive_charts;

        imaSection.visible = true;

        if (pyform.study_type.value === 'det') {
            n_ale.visible = false;
            n_epi.visible = false;
            imaSection.visible = false;

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
                sensitivityDataFad = parsePlotData(pyform.sensitivity_data_fad);
                senPlot.visible = false;
                senPlotFad.visible = false;
                senInterChart.visible = true;
                senInterChartFad.visible = true;
            } else {
                updateImage(senPlot, pyform.sen_plot);
                updateImage(senPlotFad, pyform.sen_plot_fad);
                senPlot.visible = true;
                senPlotFad.visible = true;
                senInterChart.visible = false;
                senInterChartFad.visible = false;
            }
            senSection.visible = true;
            imaSection.visible = false;
        }

        // load any existing results from backend
        displayInspectionMitigationResults();
    }

    /**
     * Careful! This call uses the "frozen" state model of this analysis (pyform), but the inputs are bound to the main form (app_form).
     * So must retrieve them manually and then pass to pyform function.
     *
     */
    function inspectionMitigationAnalysis()
    {
        alert.level = 1;
        alert.msg = "";
        imaButton.enabled = false;
        clearImage(imaHistogramPlot);
        clearImage(imaCdfPlot);
        imaSpinner.visible = true;
        imaInputSummary.text = "";
        imaCloseWarning.text = "Don't close this form while the analysis is in-progress";
        imaCloseWarning.visible = true;

        app_form.request_inspection_mitigation_analysis(pyform.analysis_id);
        // now wait for event to trigger on form
    }

    function displayInspectionMitigationResults(status)
    {
        imaButton.enabled = true;
        imaSpinner.visible = false;
        clearImage(imaHistogramPlot);
        clearImage(imaCdfPlot);
        // imaPercentMitigated.text = "";

        imaInputSummary.text = "";
        imaCloseWarning.visible = false;

        const resultJson = pyform.ima_results;
        if (resultJson === "" || resultJson === null)
        {
            return;
        }

        const results = JSON.parse(resultJson);

        if (results === "")
        {
            return;
        }

        if (results.status !== 1)
        {
            alert.level = 2;
            alert.msg = results.message;
            return;
        }

        updateImage(imaHistogramPlot, results.histogram_plot);
        updateImage(imaCdfPlot, results.cdf_plot);

        // Display input values
        imaInputSummary.text = "<b>Analysis Parameters:</b><br/>" +
                               "Probability of detection: " + (results.probability_of_detection * 100).toFixed(0) + "%<br/>" +
                               "Detection resolution: " + (results.detection_resolution * 100).toFixed(0) + "%<br/>" +
                               "Inspection interval: " + results.inspection_interval + " days";
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
                    visible: pyform && pyform.finished

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
                contentHeight: {
                    // Use actual y positions (computed by anchor system) for reliable sizing
                    if (imaSection.visible) return imaSection.y + imaSection.height + sectionMargin;
                    if (detSection.visible) return detSection.y + detSection.height + sectionMargin;
                    if (probSection.visible) return probSection.y + probSection.height + sectionMargin;
                    if (senSection.visible) return senSection.y + senSection.height + sectionMargin;
                    return paramSection.height + sectionMargin;
                }
                contentWidth: parent.width

                // increase scroll speed
                flickDeceleration: 15000
                height: parent.height - y
                visible: pyform && pyform.finished
                width: parent.width

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AlwaysOn
                }

                ScrollMouseArea {
                    container: resultSection
                }

                CollapsibleSection {
                    id: paramSection
                    asHeader: true
                    startOpen: true
                    title: "Analysis Specification"
                    iconSrc: "vials-solid"
                    titleFontSize: 15
                    w: parent.width - 50

                    ColumnLayout {
                        parent: paramSection.containerRef

                        VSpacer {
                            height: 5
                        }
                        FormSectionHeader2 {
                            bottomPad: 2
                            fontSize: 12
                            // iconSrc: "vials-solid"
                            rWidth: barWidth - 20
                            title: "Analysis Description"
                            topPad: 0
                        }
                        Row {
                            id: paramRow1

                            spacing: 35

                            Column {
                                ResultParamText {id: study_type}
                                ResultParamText {id: seed}
                            }
                            Column {
                                ResultParamText {id: n_ale}
                                ResultParamText {id: n_epi}
                            }
                            Column {
                                ResultParamText {id: crack_assump}
                                ResultParamText {id: stress_method}
                                ResultParamText {id: surface}
                            }
                            Column {
                                ResultParamText {id: n_cycles}
                                ResultParamText {id: evolution_method}
                                ResultParamText {id: cycle_step_size}
                            }
                        }
                        
                        // Display random loading profile on its own line if present
                        Text {
                            id: randomLoadingProfile
                            visible: false
                            text: ""
                            font.pixelSize: 12
                            textFormat: Text.RichText
                            wrapMode: Text.WordWrap
                            width: barWidth - 40
                            Layout.topMargin: 10
                        }
                        SimImage {
                            id: randomLoadingProfilePlot
                            width: plotW
                            height: plotH
                            Layout.preferredWidth: plotW
                            Layout.preferredHeight: plotH
                        }
                        
                        VSpacer {
                            height: 15
                        }
                        FormSectionHeader2 {
                            bottomPad: 2
                            fontSize: 12
                            // iconSrc: "vials-solid"
                            rWidth: barWidth - 20
                            title: "User Inputs"
                            topPad: 0
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
                                    id: residual_stress_intensity
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
                            bottomPad: 2
                            fontSize: 12
                            // iconSrc: "vials-solid"
                            rWidth: barWidth - 20
                            title: "Calculated Parameters"
                            topPad: 0
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
                }

                CollapsibleSection {
                    id: detSection
                    asHeader: true
                    startOpen: true
                    iconSrc: "chart-line-solid"
                    title: "Plotted Results (Deterministic)"
                    titleFontSize: 15
                    w: parent.width - 50
                    anchors.top: paramSection.bottom
                    anchors.topMargin: sectionMargin

                    Column {
                        // id: detSection
                        parent: detSection.containerRef

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

                            SimImage {id: crackGrowthPlot; width: plotW; height: plotH; }
                            SimImage {id: designCurvePlot; width: plotW; height: plotH; }
                            SimImage {id: detFadPlot; width: plotW; height: plotH; }
                            VSpacer {
                                height: 40
                            }
                        }
                    }
                }


                CollapsibleSection {
                    id: senSection
                    asHeader: true
                    startOpen: true
                    iconSrc: "chart-line-solid"
                    title: "Plotted Results (Sensitivity)"
                    titleFontSize: 15
                    w: parent.width - 50
                    anchors.top: paramSection.bottom
                    anchors.topMargin: sectionMargin

                    Column {
                        parent: senSection.containerRef

                        Grid {
                            columns: 2
                            spacing: 20

                            // Cycles to a(crit) sensitivity plot
                            SensitivityChart {
                                id: senInterChart
                                plotData: sensitivityData
                                chartTitle: "Cycles to a(crit)"
                            }
                            SimImage {id: senPlot; width: plotW; height: plotH; }

                            // Cycles to FAD line sensitivity plot
                            SensitivityChart {
                                id: senInterChartFad
                                plotData: sensitivityDataFad
                                chartTitle: "Cycles to FAD line"
                            }
                            SimImage {id: senPlotFad; width: plotW; height: plotH; }
                        }
                        VSpacer {
                            height: 20
                        }
                    }
                }

                CollapsibleSection {
                    id: probSection
                    asHeader: true
                    startOpen: true
                    iconSrc: "chart-line-solid"
                    title: "Plotted Results (Probabilistic)"
                    titleFontSize: 15
                    w: parent.width - 50
                    anchors.top: paramSection.bottom
                    anchors.topMargin: sectionMargin

                    Column {
                        parent: probSection.containerRef
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

                            SimImage {id: ensemblePlot; width: plotW; height: plotH; }
                            SimImage {id: cyclePlot; width: plotW; height: plotH; }
                            SimImage {id: probFadPlot; width: plotW; height: plotH; }
                            SimImage {id: pdfPlot; width: plotW; height: plotH; }
                            SimImage {id: cdfPlot; width: plotW; height: plotH; }
                        }
                        VSpacer {
                            height: 20
                        }
                    }
                }


                CollapsibleSection {
                    id: imaSection
                    asHeader: true
                    startOpen: true
                    // iconSrc: "chart-line-solid"
                    title: "Inspection Mitigation Specification"
                    titleFontSize: 15
                    w: parent.width - 50
                    anchors.top: detSection.visible ? detSection.bottom : (senSection.visible ? senSection.bottom : probSection.bottom)
                    anchors.topMargin: sectionMargin
                    anchors.bottomMargin: sectionMargin

                    ColumnLayout {
                        parent: imaSection.containerRef
                        width: parent.width

                        FloatParamField {
                            id: probDetectionInput
                            param: probability_of_detection_c
                            tipText: "Probability of a crack being detected at each inspection"
                        }

                        FloatParamField {
                            id: detectionResolutionInput
                            param: detection_resolution_c
                            tipText: "Crack depth that is detectable by inspection. For example, a value of 0.3 indicates any crack larger than 30% of wall thickness is detectable."
                        }

                        IntParamField {
                            id: inspectionIntervalInput
                            param: inspection_interval_c
                            tipText: "Days between each inspection"
                        }

                        RowLayout {
                            Layout.leftMargin: 122
                            Layout.bottomMargin: 8
                            Layout.fillWidth: true

                            Button {
                                id: imaButton
                                Layout.preferredWidth: defaultInputW
                                Material.roundedScale: Material.SmallScale
                                Material.accent: Material.BlueGrey
                                highlighted: true

                                onClicked: {
                                    forceActiveFocus();
                                    inspectionMitigationAnalysis();
                                }

                                Row {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 0

                                    AppIcon {
                                        anchors.verticalCenter: parent.verticalCenter
                                        icon.width: 16
                                        source: 'bolt-solid'
                                        iconColor: "white"
                                    }

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: "Calculate"
                                        font.pixelSize: 16
                                        font.bold: true
                                        color: "white"
                                    }
                                }
                            }

                            BusyIndicator {
                                id: imaSpinner
                                visible: false
                                height: 40
                                Layout.preferredHeight: 40
                                running: true
                            }


                        }

                        SectionAlert {id: alert; }

                        Text {
                            id: imaCloseWarning
                            font.pixelSize: 14
                            font.bold: false
                            font.italic: true
                            text: ""

                        }

                        Text {
                            id: imaInputSummary
                            font.pixelSize: 14
                            text: ""
                            textFormat: Text.RichText
                            Layout.topMargin: 2
                            Layout.bottomMargin: 10
                        }

                        Column {
                            spacing: 5
                            Layout.topMargin: 0
                            Layout.bottomMargin: 0

                            Rectangle {
                                width: plotLgW
                                height: width / (imaHistogramPlot.sourceSize.width / imaHistogramPlot.sourceSize.height || 1)
                                color: "transparent";
                                SimImage {
                                    anchors.fill: parent
                                    id: imaHistogramPlot
                                }
                            }
                            Rectangle {
                                width: plotLgW
                                height: width / (imaCdfPlot.sourceSize.width / imaCdfPlot.sourceSize.height || 1)
                                color: "transparent";
                                SimImage {
                                    anchors.fill: parent
                                    id: imaCdfPlot
                                }
                            }

                        }

                        VSpacer {
                            height: 25
                        }

                    }
                }


            }
        }
    }
}
