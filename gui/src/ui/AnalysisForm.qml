/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls 2.12
import QtQuick.Dialogs
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "../helprgui/ui/components"
import "../helprgui/ui/components/buttons"
import "../helprgui/ui/parameters"
import "../helprgui/ui/pages"
import helpr.classes


FormPage {
    function updateScrollButtons()
    {
        // update button highlighting
        let cy = paramContainer.contentY;
        let btns = [scrollBtn1, scrollBtn2, scrollBtn3, scrollBtn4, scrollBtn5, scrollBtn6, scrollBtn7];

        for (var i=0; i < btns.length; ++i)
        {
            changeButtonTextColor(btns[i]);
        }

        if (cy >= section7.y)
        {
            changeButtonTextColor(scrollBtn7, 0.1);
        }
        else if (cy >= section6.y)
        {
            changeButtonTextColor(scrollBtn6, 0.1);
        }
        else if (cy >= section5.y)
        {
            changeButtonTextColor(scrollBtn5, 0.1);
        }
        else if (cy >= section4.y)
        {
            changeButtonTextColor(scrollBtn4, 0.1);
        }
        else if (cy >= section3.y)
        {
            changeButtonTextColor(scrollBtn3, 0.1);
        }
        else if (cy >= section2.y)
        {
            changeButtonTextColor(scrollBtn2, 0.1);
        }
        else
        {
            changeButtonTextColor(scrollBtn1, 0.1);
        }
    }


    function refreshForm()
    {
        let studyType = study_type_c.value;
        let nEpi = n_epi_c.value;
        let nAle = n_ale_c.value;

        // update readonly parameters
        r_ratio.refresh();
        a_m.refresh();
        a_c.refresh();
        t_r.refresh();

        smys.hideAlert();
        smys.refresh();
        let smysVal = smys.param.value;

        if (smysVal >= 72.0 && smysVal !== Infinity)
        {
            smys.showAlert("Stress is above 72% SMYS", true);
        }

        // check for per-parameter issues. Note: could extract this to backend validation functions when needed.

        // update visibility of output options when study type or # epistemic, aleatory samples changes
        let studyChanged = (oldSampleType === "" || oldNumEpi === -1 || oldNumAle === -1 ||
                            oldSampleType !== studyType || oldNumEpi !== nEpi || oldNumAle !== nAle);

        if (studyChanged)
        {
            crackGrowthPlotSelector.visible = false;
            exRatesPlotSelector.visible = false;
            fadPlotSelector.visible = false;
            ensemblePlotSelector.visible = false;
            cyclePlotSelector.visible = false;
            pdfPlotSelector.visible = false;
            cdfPlotSelector.visible = false;
            senPlotSelector.visible = false;

            if (studyType === 'det')
            {
                crackGrowthPlotSelector.visible = true;
                exRatesPlotSelector.visible = true;
                fadPlotSelector.visible = true;
            }
            else if (studyType === 'prb' && nEpi > 0)
            {
                ensemblePlotSelector.visible = true;
                cyclePlotSelector.visible = true;
                fadPlotSelector.visible = true;
                pdfPlotSelector.visible = true;
                cdfPlotSelector.visible = true;
            }
            else if (studyType === 'prb')
            {
                ensemblePlotSelector.visible = true;
                cyclePlotSelector.visible = true;
                fadPlotSelector.visible = true;
                pdfPlotSelector.visible = true;
                cdfPlotSelector.visible = true;
            }
            else
            {
                senPlotSelector.visible = true;
            }

            oldSampleType = studyType;
            oldNumEpi = nEpi;
            oldNumAle = nAle;
        }
    }

    Component.onCompleted: {
        refreshForm();
    }


    ColumnLayout {
        width: parent.width - 50  // account for scrollbuttons

        // Form header
        Text {
            font.pointSize: header1FontSize
            id: formHeader
            font.weight: 600
            Layout.leftMargin: 14
            text: "Probabilistic Fatigue and Fracture Analysis for Pressurized Cylindrical Shells"
        }

        Rectangle {
            height: 2
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 4
            color: Material.color(Material.Blue, Material.Shade400)
        }

        Item {
            id: inputSpacer2
            Layout.preferredHeight: 4
        }

        Flickable
        {
            id: paramContainer
            Layout.leftMargin: 20
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.minimumWidth: 400
            contentWidth: 840
            contentHeight: paramCols.height + 20 + 120
            height: 580

            flickableDirection: Flickable.HorizontalAndVerticalFlick
            boundsBehavior: Flickable.StopAtBounds
            boundsMovement: Flickable.FollowBoundsBehavior
            // flickDeceleration: 1000
            clip: true

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            ScrollBar.horizontal: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            Component.onCompleted: {
                updateScrollButtons();
            }

            onContentYChanged: {
                updateScrollButtons();
            }

            // ==========================
            // ==== Parameter Inputs ====
            Item {
                id: paramColContainer
                Layout.fillHeight: true
                height: paramCols.height

                ColumnLayout {
                    id: paramCols

                    FormSectionHeader {
                        id: section1
                        title: "Analysis Settings";
                        Layout.topMargin: 10
                        iconSrc: 'gear-solid'
                    }

                    StringParameterInput {
                        param: name_c
                        inputLength: 240
                        tipText: "Enter an alphanumeric name (optional)"
                    }
                    ChoiceParameterInput {
                        param: study_type_c
                        tipText: "Selection of either a deterministic, probabilistic, or sensitivity analysis"
                    }
                    IntParameterInput {
                        param: seed_c
                        tipText: "Integer used to generate the random seed enabling regeneration of results"
                    }

                    FormSectionHeader {
                        id: section2
                        title: "Probabilistic"
                        iconSrc: 'chart-simple-solid'
                    }
                    IntParameterInput {
                        param: n_ale_c
                        tipText: "Number of aleatory samples used in the analysis. Large sample size may substantially prolong analysis."
                    }
                    IntParameterInput {
                        param: n_epi_c
                        tipText: "Number of epistemic samples used in the analysis. Large sample size may substantially prolong analysis."
                    }

                    FormSectionHeader {
                        id: section3
                        title: "Geometry"
                        iconSrc: 'shapes-solid'
                    }
                    ParameterInput {
                        param: out_diam_c
                        tipText: "Outer pipe diameter"
                    }
                    ParameterInput {
                        param: thickness_c
                        tipText: "Pipe wall thickness"
                    }

                    ReadonlyParameter {
                        id: t_r
                        param: t_r_c
                        tipText: "Ratio of wall thickness to pipe inner diameter"
                    }

                    FormSectionHeader {
                        id: section4
                        title: "Material Properties"
                        iconSrc: 'microscope-solid'
                    }
                    ParameterInput {
                        param: yield_str_c
                        tipText: "Material yield strength"
                    }
                    ParameterInput {
                        param: frac_resist_c
                        tipText: "Measured fracture toughness at maximum hydrogen pressure"
                    }

                    FormSectionHeader {
                        id: section5
                        title: "Operating Conditions"
                        iconSrc: 'temperature-half-solid'
                    }
                    ParameterInput {
                        param: p_max_c
                        tipText: "Maximum gas pressure"
                    }
                    ParameterInput {
                        param: p_min_c
                        tipText: "Minimum gas pressure"
                    }
                    ParameterInput {
                        param: temp_c
                        tipText: "Gas temperature"
                    }
                    ParameterInput {
                        param: vol_h2_c
                        tipText: "Volume fraction of hydrogen"
                    }

                    ReadonlyParameter {
                        id: smys
                        param: smys_c
                        tipText: ("Specified Minimum Yield Strength calculated as percentage of Hoop stress to yield strength, " +
                                  "where Hoop stress is calculated as the internal pressure multiplied by the outer diameter divided by " +
                                  "twice the wall thickness")
                    }

                    ReadonlyParameter {
                        id: r_ratio
                        param: r_ratio_c
                        tipText: "Max pressure / min pressure"
                    }

                    FormSectionHeader {
                        id: section6
                        title: "Crack Specification"
                        iconSrc: 'wrench-solid'
                    }
                    ParameterInput {
                        param: crack_dep_c
                        tipText: "Crack depth percent through wall; i.e. % of wall thickness"
                    }
                    ParameterInput {
                        param: crack_len_c
                        tipText: "Length of the initial crack (2c)"
                    }

                    ReadonlyParameter {
                        id: a_m
                        param: a_m_c
                        tipText: "Initial crack depth"
                    }

                    ReadonlyParameter {
                        id: a_c
                        param: a_c_c
                        tipText: "Ratio of flaw depth to flaw length"
                    }

                    FormSectionHeader {
                        id: section7
                        title: "Quantities of Interest"
                        iconSrc: 'magnifying-glass-chart-solid'
                    }

                    BoolParameterInput {
                        id: crackGrowthPlotSelector
                        param: do_crack_growth_plot_c
                    }
                    BoolParameterInput {
                        id: exRatesPlotSelector
                        param: do_ex_rates_plot_c
                    }
                    BoolParameterInput {
                        id: cyclePlotSelector
                        param: do_cycle_plot_c
                    }
                    BoolParameterInput {
                        id: fadPlotSelector
                        param: do_fad_plot_c
                    }
                    BoolParameterInput {
                        id: ensemblePlotSelector
                        param: do_ensemble_plot_c
                    }
                    BoolParameterInput {
                        id: pdfPlotSelector
                        param: do_pdf_plot_c
                    }
                    BoolParameterInput {
                        id: cdfPlotSelector
                        param: do_cdf_plot_c
                    }
                    BoolParameterInput {
                        id: senPlotSelector
                        param: do_sen_plot_c
                    }

                }
            }
        }

        Item {
            Layout.fillHeight: true
        }

        Rectangle {
            height: 1
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 4
            color: Material.color(Material.Blue, Material.Shade400)
        }

        RowLayout {

            // =========================
            // ==== Analysis Button ====
            Button {
                id: submitBtn
                Layout.preferredWidth: 110
                Layout.alignment: Qt.AlignCenter
                Layout.leftMargin: 145
                Layout.bottomMargin: 8
                Material.roundedScale: Material.SmallScale
                Material.accent: Material.Blue
                highlighted: true

                onClicked: {
                    forceActiveFocus();
                    app_form.request_analysis();
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 0

                    AppIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        icon.width: 20
                        source: 'bolt-solid'
                        iconColor: "white"
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Analyze"
                        font.pixelSize: 20
                        font.bold: true
                        color: "white"
                        bottomPadding: lgBtnBottomPadding
                    }
                }
            }

            Rectangle {
                id: alertSection
                visible: false
                Layout.alignment: Qt.AlignLeft
                Layout.leftMargin: 10
                color: color_danger
                radius: 5
                Layout.preferredHeight: 30
                Layout.preferredWidth: alertContents.width

                Row {
                    id: alertContents
                    spacing: 5
                    anchors.verticalCenter: parent.verticalCenter
                    leftPadding: 8

                    AppIcon {
                        id: alertIcon
                        source: 'circle-exclamation-solid'
                        iconColor: color_text_danger
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    TextEdit {
                        id: alertText
                        text: "Test alert NOTIFICATION lorem ipsum"
                        rightPadding: 10
                        color: color_text_danger
                        readOnly: true
                        selectByMouse: true
                        font.pointSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

            }
        }

    }
    // ========================
    // ==== Scroll Buttons ====
    Column {
        id: scrollBtns
        width: 25
        height: 300
        anchors.top: parent.top
        anchors.topMargin: formHeader.height + 2 + inputSpacer2.height + 10
        anchors.right: parent.right
        anchors.rightMargin: 18

        spacing: 0

        SimpleScrollButton {
            id: scrollBtn1
            tipText: "Scroll to Analysis Settings"
            iconSrc: 'gear-solid'
            onClicked: { paramContainer.contentY = section1.y; }
        }

        SimpleScrollButton {
            id: scrollBtn2
            tipText: "Scroll to Probabilities inputs"
            onClicked: { paramContainer.contentY = section2.y; }
            iconSrc: 'chart-simple-solid'
        }

        SimpleScrollButton {
            id: scrollBtn3
            tipText: "Scroll to Geometries inputs"
            onClicked: { paramContainer.contentY = section3.y; }
            iconSrc: 'shapes-solid'
        }

        SimpleScrollButton {
            id: scrollBtn4
            tipText: "Scroll to Materials inputs"
            onClicked: { paramContainer.contentY = section4.y; }
            iconSrc: 'microscope-solid'
            iconWidth: 22
        }

        SimpleScrollButton {
            id: scrollBtn5
            tipText: "Scroll to Operating Conditions"
            iconSrc: 'temperature-half-solid'
            onClicked: { paramContainer.contentY = section5.y; }
            iconWidth: 18
        }

        SimpleScrollButton {
            id: scrollBtn6
            tipText: "Scroll to Crack Specification"
            iconSrc: 'wrench-solid'
            onClicked: { paramContainer.contentY = section6.y; }
        }

        SimpleScrollButton {
            id: scrollBtn7
            tipText: "Scroll to Quantities of Interest"
            iconSrc: 'magnifying-glass-chart-solid'
            onClicked: { paramContainer.contentY = section7.y; }
            iconWidth: 25
        }
    }


}
