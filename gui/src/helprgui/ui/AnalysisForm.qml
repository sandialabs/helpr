/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls 2.12
import QtQuick.Dialogs
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "../hygu/ui/utils.js" as Utils
import "../hygu/ui/components"
import "../hygu/ui/components/buttons"
import "../hygu/ui/parameters"
import "../hygu/ui/pages"
import helpr.classes


FormPage {
    property string studyKeyDet: "det";
    property string studyKeyProb: "prb";
    property string studyKeySam: "sam";
    property string studyKeyBound: "bnd";

    function updateScrollButtons()
    {
        // update button highlighting
        let cy = paramContainer.contentY;
        let btns = [scrollBtn1, scrollBtn2, scrollBtn3, scrollBtn4, scrollBtn5, scrollBtn6];

        for (var i=0; i < btns.length; ++i)
        {
            changeButtonTextColor(btns[i]);
        }

        if (cy >= section6.y)
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
            oldSampleType = studyType;
            oldNumEpi = nEpi;
            oldNumAle = nAle;

            let showSamples = studyType !== studyKeyDet && studyType !== studyKeyBound;
            section2.visible = showSamples;
            epiInput.visible = showSamples;
            epiInput.enabled = showSamples;
            epiInput.opacity = showSamples ? 1 : fadeVal;
            aleInput.visible = showSamples;
            aleInput.enabled = showSamples;
            aleInput.opacity = showSamples ? 1 : fadeVal;

            nCyclesInput.enabled = studyType === studyKeyDet || studyType === studyKeyProb;
            nCyclesInput.opacity = studyType === studyKeyDet || studyType === studyKeyProb ? 1 : fadeVal;

            nCyclesWarning.visible = studyType === studyKeyProb;
        }

        cycleStepSizeInput.enabled = evolution_method_c.value === "cycles";
        cycleStepSizeWarning.visible = evolution_method_c.value === "cycles" && cycle_step_size_c.value > 1;

        // random loading profile overrides min and max pressures
        if (Utils.isNullish(random_loading_profile_c.value))
        {
            profileUnitsInput.enabled = false;
            profileUnitsInput.opacity = fadeVal;
            minPressureInput.enabled = true;
            minPressureInput.opacity = 1;
            maxPressureInput.enabled = true;
            maxPressureInput.opacity = 1;
        }
        else
        {
            profileUnitsInput.enabled = true;
            profileUnitsInput.opacity = 1;
            minPressureInput.enabled = false;
            minPressureInput.opacity = fadeVal;
            maxPressureInput.enabled = false;
            maxPressureInput.opacity = fadeVal;
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
            clip: true

            // increase scroll speed
            flickDeceleration: 15000
            ScrollMouseArea {container: paramContainer}

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

                    StringParamField {
                        param: analysis_name_c
                        inputLength: longInputW
                        tipText: "Enter an alphanumeric name (optional)"
                    }
                    ChoiceParamField {
                        param: study_type_c
                        selector.Layout.preferredWidth: longInputW
                        selector.Layout.maximumWidth: longInputW
                        tipText: "Selection of either a deterministic, probabilistic, or sensitivity analysis"
                    }

                    CollapsibleSection {
                        id: advSettingsSection
                        w: sectionW
                        title: "Advanced..."
                        titleFontSize: labelFontSize + 1;
                        isItalic: false
                        asHeader: false
                        startOpen: false
                        btnRef.anchors.leftMargin: 330

                        ColumnLayout {
                            parent: advSettingsSection.containerRef
                            Layout.leftMargin: 5

                            SubSectionHeader {
                                title: "Model Assumptions"
                                topMargin: 5
                                fontSize: labelFontSize
                                textColor: headerColor
                            }

                            RowLayout {
                                ChoiceParamField {
                                    param: stress_method_c
                                    selector.Layout.preferredWidth: longInputW
                                    selector.Layout.maximumWidth: longInputW
                                    tipText: (
                                        "For axial flaws in cylinders under internal pressure loading. Selection based on stress method and surface:\n" +
                                        "Anderson Internal Elliptical: From TL Anderson. Fracture Mechanics: Fundamentals and Applications (Second Edition). Boca Raton FL: CRC Press (1995).\n" +
                                        "API 579-1 Internal Elliptical: From API 579-1 Section 9B5.10 (finite crack) and 9B.5.4 (infinite crack)\n" +
                                        "API 579-1 External Elliptical: From API 579-1 Section 9B5.10 (finite crack) and 9B.5.4 (infinite crack)"
                                    )
                                }

                                ButtonPopup {
                                    id: stressPopup
                                    h: 620
                                    w: 920
                                    tipText: "View illustration of stress intensity methods"

                                    ColumnLayout {
                                        id: stressCol
                                        parent: stressPopup.contentRef
                                        anchors.fill: parent

                                        Text {
                                            text: "<b>Stress Intensity Factor Models</b>"
                                            font.pointSize: 14
                                            textFormat: Text.RichText
                                        }
                                        Row {
                                            spacing: 10

                                            Column {
                                                spacing: 5
                                                Image {
                                                    source: "resources/pipe_geom_infinite.png"
                                                    height: 300
                                                    fillMode: Image.PreserveAspectFit
                                                    sourceSize.height: height
                                                }
                                                Text {
                                                    text: "Infinite crack length (left) and finite crack length (right)"
                                                    font.italic: true
                                                    font.pointSize: 12
                                                }
                                            }
                                            Column {
                                                spacing: 5
                                                Image {
                                                    source: "resources/pipe_geom_elliptical.png"
                                                    height: 300
                                                    fillMode: Image.PreserveAspectFit
                                                    sourceSize.height: height
                                                }
                                                Text {
                                                    text: ""
                                                    font.italic: true
                                                    font.pointSize: 13
                                                }
                                            }
                                        }

                                        Item { Layout.preferredHeight: 10 }

                                        Text {
                                            text: "<b>Anderson</b>"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                        }
                                        Text {
                                            text: "a/t &lt;= 0.8 (0.75 for infinite length)"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                            horizontalAlignment: Text.AlignLeft
                                            leftPadding: 10
                                        }
                                        Text {
                                            text: "0.05 &lt;= t/R<sub>i</sub> &lt;= 0.2"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                            horizontalAlignment: Text.AlignLeft
                                            leftPadding: 10
                                        }

                                        Item { Layout.preferredHeight: 10 }

                                        Text {
                                            text: "\n<b>API 579-1</b>"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                        }
                                        Text {
                                            text: "a/t &lt;= 0.8"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                            horizontalAlignment: Text.AlignLeft
                                            leftPadding: 10
                                        }
                                        Text {
                                            text: "0 &lt;= t/R<sub>i</sub> &lt;= 1"
                                            font.pointSize: 13
                                            textFormat: Text.RichText
                                            horizontalAlignment: Text.AlignLeft
                                            leftPadding: 10
                                        }

                                        Item { Layout.fillHeight: true }
                                    }
                                }
                            }
                            ChoiceParamField {
                                param: surface_c
                                label.text: "Surface of defect location"
                                selector.Layout.preferredWidth: longInputW
                                selector.Layout.maximumWidth: longInputW
                                tipText: "Surface on which the defect is located"
                            }

                            ChoiceParamField {
                                param: crack_assump_c
                                selector.Layout.preferredWidth: longInputW
                                selector.Layout.maximumWidth: longInputW
                                tipText: "Assumption about correlation between crack depth and length growth"
                            }

                            SubSectionHeader {
                                title: "Analysis Specifications"
                                topMargin: 15
                                fontSize: labelFontSize
                                textColor: headerColor
                            }

                            IntParamField {
                                id: nCyclesInput
                                param: n_cycles_c
                                allowNull: true
                                tipText: "Maximum number of cycles cracks will evolve"
                            }

                            Rectangle {
                                id: nCyclesWarning
                                Layout.preferredWidth: 500
                                Layout.leftMargin: paramLabelWidth
                                radius: 5
                                color: color_warning
                                Layout.preferredHeight: 40
                                Behavior on Layout.preferredHeight {NumberAnimation { duration: 100 }}

                                Text {
                                    text: "Cracks may evolve past cycle count due to adaptive time stepping implementation unless using fixed cycle step size option"
                                    color: color_text_warning
                                    anchors.margins: 10
                                    anchors.fill: parent
                                    anchors.verticalCenter: parent.verticalCenter
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                    font.pointSize: labelFontSize
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                }
                            }

                            ChoiceParamField {
                                id: evolutionMethodInput
                                param: evolution_method_c
                                selector.Layout.preferredWidth: medInputW
                                selector.Layout.maximumWidth: medInputW
                                tipText: "Determines whether crack growth is evolved in terms of crack depth normalized " +
                                    "by wall thickness (a/t) or a specified number of cycles. \nWhen a/t is used the numerical " +
                                    "step size selection is adaptive leading to faster computations, which may result in some " +
                                    "numerical error. \nEvolving using a cycle step size of one is currently required when " +
                                    "using random loading profiles."
                            }
                            IntParamField {
                                id: cycleStepSizeInput
                                param: cycle_step_size_c
                                allowNull: true
                                tipText: "Step size by which to evolve cracks during analysis. Ignored if using a/t for evolving cracks."
                            }

                            Rectangle {
                                id: cycleStepSizeWarning
                                // visible: cycle_step_size_c.value > 1
                                Layout.preferredWidth: 500
                                Layout.leftMargin: paramLabelWidth
                                radius: 5
                                color: color_warning
                                Layout.preferredHeight: 30

                                Text {
                                    text: "Step sizes > 1 may result in numerical error"
                                    color: color_text_warning
                                    anchors.margins: 10
                                    anchors.fill: parent
                                    anchors.verticalCenter: parent.verticalCenter
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                    font.pointSize: labelFontSize
                                    font.bold: true
                                }
                            }

                            IntParamField {
                                param: seed_c
                                allowNull: false
                                tipText: "Integer used to generate the random seed enabling regeneration of results"
                            }

                            BoolParamField {
                                id: doInteractiveCharts
                                param: do_interactive_charts_c
                            }

                        }
                    }

                    FormSectionHeader {
                        id: section2
                        title: "Probabilistic"
                        iconSrc: 'chart-simple-solid'
                        visible: study_type_c.value !== studyKeyDet && study_type_c.value !== studyKeyBound
                    }
                    IntParamField {
                        id: aleInput
                        param: n_ale_c
                        minValue: 0
                        visible: study_type_c.value !== studyKeyDet && study_type_c.value !== studyKeyBound
                        enabled: study_type_c.value !== studyKeyDet && study_type_c.value !== studyKeyBound
                        opacity: visible ? 1 : fadeVal
                        tipText: "Number of aleatory samples used in the analysis. Large sample size may substantially prolong analysis."
                    }
                    IntParamField {
                        id: epiInput
                        param: n_epi_c
                        minValue: 0
                        visible: study_type_c.value !== studyKeyDet && study_type_c.value !== studyKeyBound
                        enabled: study_type_c.value !== studyKeyDet && study_type_c.value !== studyKeyBound
                        opacity: visible ? 1 : fadeVal
                        tipText: "Number of epistemic samples used in the analysis. Large sample size may substantially prolong analysis."
                    }


                    FormSectionHeader {
                        id: section3
                        title: "Geometry"
                        iconSrc: 'shapes-solid'
                    }
                    UncertainParamField {
                        param: out_diam_c
                        tipText: "Outer pipe diameter"
                    }
                    UncertainParamField {
                        param: thickness_c
                        tipText: "Pipe wall thickness"
                    }

                    ReadonlyParameter {
                        id: t_r
                        param: t_r_c
                        tipText: "Ratio of wall thickness to pipe inner radius"
                    }

                    FormSectionHeader {
                        id: section4
                        title: "Material Properties"
                        iconSrc: 'microscope-solid'
                    }
                    UncertainParamField {
                        param: yield_str_c
                        tipText: "Material yield strength"
                    }
                    UncertainParamField {
                        param: frac_resist_c
                        tipText: "Measured fracture toughness at maximum hydrogen pressure"
                    }
                    UncertainParamField {
                        param: stress_intensity_c
                        labelRef.wrapMode: Text.WordWrap
                        tipText: "Describe residual stress via static, explicit intensity factor"
                    }


                    FormSectionHeader {
                        id: section5
                        title: "Operating Conditions"
                        iconSrc: 'temperature-half-solid'
                    }
                    FileSelector {
                        id: randomLoadingProfileInput
                        param: random_loading_profile_c
                        inputLength: 400
                        Layout.preferredHeight: 45
                        tipText: "Select a CSV file containing random loading profile data. Overrides minimum and maximum pressure parameters if used. To re-enable pressure inputs, clear file selector."
                        fileDialog.onAccepted: {
                            app_form.set_random_loading_profile(fileDialog.selectedFile);
                        }
                        extraButton.onClicked: {
                            app_form.clear_random_loading_profile();
                        }

                        IconTextButton {
                            id: templateDownloadButton
                            parent: randomLoadingProfileInput.contentRow
                            height: 36
                            Layout.preferredHeight: 36
                            Layout.preferredWidth: 80
                            img: 'file-arrow-down-solid'
                            btnText: "Template"

                            onClicked: {
                                let url = appDir + "assets/demo/random_loading_demo.csv";
                                Qt.openUrlExternally(url);
                            }
                        }

                    }

                    ChoiceParamField {
                        id: profileUnitsInput
                        selector.Layout.preferredWidth: medInputW
                        selector.Layout.maximumWidth: medInputW
                        param: profile_units_c
                        tipText: "Units of the random loading profile data"
                    }

                    UncertainParamField {
                        id: maxPressureInput
                        param: p_max_c
                        tipText: "Maximum gas pressure"
                    }
                    UncertainParamField {
                        id: minPressureInput
                        param: p_min_c
                        tipText: "Minimum gas pressure"
                    }
                    UncertainParamField {
                        param: temp_c
                        tipText: "Gas temperature"
                    }
                    UncertainParamField {
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
                    UncertainParamField {
                        param: crack_dep_c
                        tipText: "Crack depth percent through wall; i.e. % of wall thickness"
                    }
                    UncertainParamField {
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
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                Layout.bottomMargin: 7
                color: color_danger
                radius: 5
                Layout.preferredHeight: 40
                Layout.preferredWidth: alertContents.width
                // Layout.fillWidth: true
                // Layout.maximumWidth: parent.width - submitBtn.width - 100

                Row {
                    id: alertContents
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter
                    leftPadding: 4

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
                        wrapMode: Text.WordWrap
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
    }

}
