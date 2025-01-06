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

            epiInput.enabled = studyType !== studyKeyDet;
            epiInput.opacity = studyType !== studyKeyDet ? 1 : fadeVal;
            aleInput.enabled = studyType !== studyKeyDet;
            aleInput.opacity = studyType !== studyKeyDet ? 1 : fadeVal;

            nCyclesInput.enabled = studyType === studyKeyDet || studyType === studyKeyProb;
            nCyclesInput.opacity = studyType === studyKeyDet || studyType === studyKeyProb ? 1 : fadeVal;

            nCyclesWarning.visible = studyType === studyKeyProb;
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
                        titleFontSize: labelFontSize;
                        isItalic: true
                        asHeader: false
                        startOpen: false
                        btnRef.anchors.leftMargin: 330

                        ColumnLayout {
                            parent: advSettingsSection.containerRef
                            Layout.leftMargin: 5

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
                                    h: stressCol.height + 30
                                    w: stressCol.width + 10
                                    tipText: "View illustration of stress intensity methods"

                                    ColumnLayout {
                                        id: stressCol
                                        parent: stressPopup.contentRef

                                        Text {
                                            text: "<b>Stress Intensity Factor Models</b>"
                                            font.pointSize: 14
                                            textFormat: Text.RichText
                                        }
                                        Row {
                                            spacing: 10

                                            Column {
                                                spacing: 5
                                                SimImage {
                                                    filename: appDir + "ui/resources/pipe_geom_infinite.png";
                                                    source: appDir + "ui/resources/pipe_geom_infinite.png";
                                                    height: 400
                                                    sourceSize.height: height
                                                }
                                                Text {
                                                    text: "Infinite crack length (left) and finite crack length (right"
                                                    font.italic: true
                                                    font.pointSize: 12
                                                }
                                            }
                                            Column {
                                                spacing: 5
                                                SimImage {
                                                    filename: appDir + "ui/resources/pipe_geom_elliptical.png";
                                                    source: appDir + "ui/resources/pipe_geom_elliptical.png"
                                                    height: 400
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
                                    text: "Cracks may evolve past cycle count due to current numerical implementation being limited by slowest evolving cracks"
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
                    }
                    IntParamField {
                        id: aleInput
                        param: n_ale_c
                        minValue: 0
                        enabled: study_type_c.value !== studyKeyDet
                        opacity: study_type_c.value !== studyKeyDet ? 1 : fadeVal
                        tipText: "Number of aleatory samples used in the analysis. Large sample size may substantially prolong analysis."
                    }
                    IntParamField {
                        id: epiInput
                        param: n_epi_c
                        minValue: 0
                        enabled: study_type_c.value !== studyKeyDet
                        opacity: study_type_c.value !== studyKeyDet ? 1 : fadeVal
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

                    FormSectionHeader {
                        id: section5
                        title: "Operating Conditions"
                        iconSrc: 'temperature-half-solid'
                    }
                    UncertainParamField {
                        param: p_max_c
                        tipText: "Maximum gas pressure"
                    }
                    UncertainParamField {
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
    }

}
