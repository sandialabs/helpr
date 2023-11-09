/*
 * Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick 2.12
import QtQuick.Layouts
import QtQuick.Controls 2.12
import QtQuick.Dialogs
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "parameters"


ApplicationWindow {
    id: main
    width: 1366
    height: 768

    minimumWidth: 1024
    minimumHeight: 700

    visible: true
    title: "Hydrogen Extremely Low Probability of Rupture (HELPR)"

    // ===========================
    // ==== Global Properties ====
    property bool isWindows: Qt.platform.os === "windows";
    property bool isDebug: data_controller.is_debug_mode;

    Material.theme: Material.Light
    Material.accent: Material.Blue
    property string color_primary: "#020202"
    property string color_success: Material.color(Material.Green)
    property string color_info: Material.color(Material.Blue)
    property string color_progress: Material.color(Material.Orange)
    property string color_danger: Material.color(Material.Red)
    property string color_warning: "lightyellow"
    property string color_disabled: Material.color(Material.Grey, Material.Shade700)
    property string oldSampleType: ""
    property int oldNumEpi: -1
    property int oldNumAle: -1

    property string color_text_info: "black"
    property string color_text_warning: "darkgoldenrod"
    property string color_text_danger: "white"

    property var color_levels: [color_primary, color_info, color_warning, color_danger]
    property var color_text_levels: [color_text_info, color_text_info, color_text_warning, color_text_danger]

    property int scrollBtnHeight: 40

    // Platform-specific properties adjusted via onComplete below
    // default windows font point size is 9; mac is 13
    property int labelFontSize: 13;
    property int inputTopLabelFontSize: 11;
    property int contentFontSize: 13;
    property int header1FontSize: 16;
    property int lgBtnBottomPadding: 4;
    property int headerTopPadding: 12;

    Connections {
        target: data_controller
        function onAlertChanged(msg, level)
        {
            handleAlertChange(msg, level);
        }

        function onNewMessageEvent(msg)
        {
            handleNewMessageEvent(msg);
        }
    }

    onClosing: {
        main.close.accepted = false;
        data_controller.shutdown();
    }

    Component.onCompleted: {
        refreshForm();

        // make platform-specific adjustments
        if (isWindows)
        {
            labelFontSize = 10;
            inputTopLabelFontSize = 9;
            contentFontSize = 10;
        }
        else
        {
            labelFontSize = 13;
            inputTopLabelFontSize = 11;
            contentFontSize = 12;
            lgBtnBottomPadding = 2;
            header1FontSize = 20;
            headerTopPadding = 16;
        }

        if (isDebug)
        {
            ;
        }
        else
        {
            mainMenu.removeMenu(devMenu);
        }
    }

    function refreshForm()
    {
        undoBtn.enabled = data_controller.can_undo;
        redoBtn.enabled = data_controller.can_redo;

        let studyType = study_type_c.value;
        let nEpi = n_epi_c.value;
        let nAle = n_ale_c.value;

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

    // Top-level function that restores deleted analysis queue item onto listview queue
    function restoreAnalysis(analysis_id)
    {
        queue.restore_item(ac_id);
    }

    function handleAlertChange(msg, level)
    {
        if (level === 0)
        {
            alertSection.visible = false;
            alertText.text = "";
        }
        else
        {
            alertSection.visible = true;
            alertText.text = msg;
            alertText.color = color_text_levels[level];
            alertSection.color = color_levels[level];
            alertIcon.iconColor = color_text_levels[level];
        }
    }

    /// Displays generic message events
    function handleNewMessageEvent(msg)
    {
        // post temp message to allow undo
        let ctx = {
            "msg": msg,
            "callback": function() { ; }
        };
        messagesView.model.append(ctx);
        resultContainer.close();

    }

    function normalScroll(flickableObj, up)
    {
        flickableObj.flick(0, up ? 300 : -300);
    }

    // ======================
    // ==== File Dialogs ====
    FileDialog {
        id: saveFileDialog
        onAccepted: {
            data_controller.save_file_as(selectedFile);
        }
        fileMode: FileDialog.SaveFile
        nameFilters: ["HELPR files (*.hpr)", "JSON files (*.JSON *.json)"]
        defaultSuffix: "hpr"
//        currentFolder: StandardPaths.standardLocations(StandardPaths.DocumentsLocation)[0]
    }

    FileDialog {
        id: loadFileDialog
        onAccepted: {
            data_controller.load_save_file(selectedFile);
        }
        fileMode: FileDialog.OpenFile
        nameFilters: ["HELPR files (*.hpr)", "JSON files (*.JSON *.json)"]
        defaultSuffix: "hpr"
    }

    // =======================
    // ==== RESULTS Popup ====
    Popup {
        id: resultContainer
        x: parent.width * 0.02
        y: parent.height * 0.02
        width: parent.width * 0.96
        height: parent.height * 0.96
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        ResultDisplay {
            id: resultDisplay
            ac: null
            qIndex: -1  // used to delete result in queue
        }

        function show(ac, qIndex) {
            resultDisplay.qIndex = qIndex;
            resultDisplay.refresh(ac);
            open();
        }
    }

    // =====================
    // ==== ABOUT Popup ====
    Popup {
        id: aboutView
        x: parent.width * 0.2
        y: parent.height * 0.05
        width: logoBanner.width * 1.1
        height: parent.height * 0.9
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        AppIcon {
            source: 'xmark-solid'
            anchors.right: parent.right
            anchors.top: parent.top

            MouseArea {
                anchors.fill: parent
                onClicked: aboutView.close()
            }
        }

        ColumnLayout {
            spacing: 10
            anchors.fill: parent

            Image {
                id: logoBanner
                source: "../assets/logo/icon_banner.jpg"
            }

            Text {
                font.pointSize: 20
                text: "About HELPR"
            }

            Text {
                font.pointSize: contentFontSize
                wrapMode: Text.WordWrap
                Layout.maximumWidth: parent.width * 0.95
                text: data_controller?.about_str ?? ''
            }

            Item {
                height: 20
            }

            Text {
                font.pointSize: 16
                text: "Copyright Statement"
            }

            Text {
                font.pointSize: contentFontSize
                wrapMode: Text.WordWrap
                Layout.maximumWidth: parent.width * 0.95
                text: data_controller?.copyright_str ?? ''
            }

            Item {
                Layout.fillHeight: true
            }

            RowLayout {
                spacing: 10

                Text {
                    id: helprVersion
                    text: data_controller?.version_str ?? ''
                }

                Text {
                    text: '<html><style type="text/css"></style><a href="https://helpr.sandia.gov">HELPR Website</a></html>'
                    onLinkActivated: Qt.openUrlExternally("https://helpr.sandia.gov")
                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton // Don't eat the mouse clicks
                        cursorShape: Qt.PointingHandCursor
                    }
                }
            }
        }
    }


    // =====================================
    // ==== Main Contents: form & queue ====
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ==============================================
        // ==== Left Section (Menu & Parameter Form) ====
        Pane {
            id: inputSection
            Layout.fillHeight: true
            Layout.fillWidth: true
            topPadding: 0
            leftPadding: 0
            bottomPadding: 0
            rightPadding: 0

            ColumnLayout {
                anchors.fill: parent
                spacing: 4

                // Main menu
                MenuBar {
                    id: mainMenu
                    Layout.fillWidth: true
                    Layout.preferredWidth: parent.width + 4

                    background: Rectangle {
                        anchors.fill: parent
                        color: "white"
                    }

                    Connections {
                        target: data_controller
                        function onHistoryChanged() { refreshForm(); }
                    }

                    Menu {
                        title: "&File"
                        Action {
                            text: "&New..."
                            onTriggered: data_controller.load_new_form()
                        }
                        Action {
                            text: "&Open..."
                            onTriggered: loadFileDialog.open()
                        }
                        Action {
                            text: "&Save"
                            onTriggered: {
                                if (data_controller.save_file_exists)
                                {
                                    data_controller.save_file();
                                }
                                else
                                {
                                    saveFileDialog.open();  // no existing save-file
                                }
                            }
                        }

                        Action {
                            text: "Save &As..."
                            onTriggered: saveFileDialog.open()
                        }
                        MenuSeparator { }

                        Action {
                            text: "Open &Data Directory"
                            icon.source: '../assets/icons/folder-open-solid.svg'
                            onTriggered: data_controller.open_data_directory()
                        }

                        MenuSeparator { }
                        Action {
                            text: "&Quit"
                            onTriggered: data_controller.shutdown()
                        }
                    }
                    Menu {
                        title: "&Demo"
                        Action {
                            text: "Load Deterministic Demo"
                            onTriggered: data_controller.load_det_demo()
                        }
                        Action {
                            text: "Load Probabilistic Demo"
                            onTriggered: data_controller.load_prb_demo()
                        }
                        Action {
                            text: "Load Sensitivity (Samples) Demo"
                            onTriggered: data_controller.load_sam_demo()
                        }
                        Action {
                            text: "Load Sensitivity (Bounds) Demo"
                            onTriggered: data_controller.load_bnd_demo()
                        }
                    }
                    Menu {
                        title: "&Help"
                        Action {
                            text: "&About"
                            onTriggered: aboutView.open()
                        }
                    }
                    Menu {
                        id: devMenu
                        title: "Dev"
                        Action {
                            text: "Print state"
                            onTriggered: data_controller.print_state()
                        }
                        Action {
                            text: "Print history"
                            onTriggered: data_controller.print_history()
                        }
                    }


                    Row {
                        id: buttonBar
                        parent: mainMenu
                        height: 40
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.leftMargin: 156
                        spacing: 4

                        Item {
                            height: 32
                            implicitWidth: 24
                        }

                        Rectangle {
                            width: 1
                            height: parent.height - 6
                            anchors.verticalCenter: parent.verticalCenter
                            color: Material.color(Material.Grey, Material.Shade500)
                        }

                        Item {
                            height: 32
                            implicitWidth: 18
                        }

                        AppButton {
                            id: topSaveBtn
                            img: 'save-solid'
                            tooltip: "Save changes"
                            onClicked: {
                                if (data_controller.save_file_exists)
                                {
                                    data_controller.save_file();
                                }
                                else
                                {
                                    saveFileDialog.open();  // no existing save-file
                                }
                            }

                        }

                        AppButton {
                            id: undoBtn
                            img: 'rotate-left-solid'
                            tooltip: "Undo last change"
                            onClicked: data_controller.undo()

                        }

                        AppButton {
                            id: redoBtn
                            img: 'rotate-right-solid'
                            tooltip: "Revert last undo"
                            onClicked: data_controller.redo()
                        }
                    }
                }

                Item {
                    id: inputSpacer1
                    Layout.preferredHeight: headerTopPadding
                }

                // Form header
                Text {
                    // textFormat: Text.StyledText
                    font.pointSize: header1FontSize
                    id: formHeader1
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

                // Form description
//                Text {
//                    font.pointSize: 14
//                    font.italic: true
//                    text: ""
//                }

                Item {
                    id: inputSpacer2
                    Layout.preferredHeight: 4
                }

                Flickable {
                    id: paramContainer
                    Layout.leftMargin: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    // shift left to make room for scrollbuttons
//                    Layout.rightMargin: 48
                    Layout.rightMargin: scrollBtns.width + scrollBtns.anchors.rightMargin + 4
                    Layout.minimumWidth: 400
                    contentWidth: 840
                    contentHeight: paramCols.height + 20 + 120
                    height: 530

                    flickableDirection: Flickable.HorizontalAndVerticalFlick
                    boundsBehavior: Flickable.StopAtBounds
                    boundsMovement: Flickable.FollowBoundsBehavior
                    flickDeceleration: 10000
                    clip: true

                    ScrollBar.vertical: ScrollBar {
                        // parent: paramContainer.parent
                        policy: ScrollBar.AsNeeded
                    }

                    ScrollBar.horizontal: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    function changeButtonTextColor(btn, opac = 0)
                    {
                        btn.background.opacity = opac;
                    }

                    function updateScrollButtons()
                    {
                        // update button highlighting
                        let cy = paramContainer.contentY;
                        let btns = [scrollBtnA, scrollBtnP, scrollBtnG, scrollBtnM, scrollBtnC, scrollBtnCrack, scrollBtnQ];
                        let dColor = Material.color(Material.Grey);
                        let highlight = Material.color(Material.Blue);

                        for (var i=0; i < btns.length; ++i)
                        {
                            changeButtonTextColor(btns[i]);
                        }

                        if (cy >= paramSectionQoi.y)
                        {
                            changeButtonTextColor(scrollBtnQ, 0.1);
                        }
                        else if (cy >= paramSectionCrack.y)
                        {
                            changeButtonTextColor(scrollBtnCrack, 0.1);
                        }
                        else if (cy >= paramSectionConditions.y)
                        {
                            changeButtonTextColor(scrollBtnC, 0.1);
                        }
                        else if (cy >= paramSectionMaterial.y)
                        {
                            changeButtonTextColor(scrollBtnM, 0.1);
                        }
                        else if (cy >= paramSectionGeom.y)
                        {
                            changeButtonTextColor(scrollBtnG, 0.1);
                        }
                        else if (cy >= paramSectionProb.y)
                        {
                            changeButtonTextColor(scrollBtnP, 0.1);
                        }
                        else
                        {
                            changeButtonTextColor(scrollBtnA, 0.1);
                        }
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
                                id: paramSectionSettings
                                title: "Analysis Settings";
                                Layout.topMargin: 10
                                iconSrc: 'gear-solid'
                            }

                            ChoiceParameterInput {
                                param: study_type_c
                                tipText: "Selection of either a deterministic, probabilistic, or sensitivity analysis"
                            }
                            BasicParameterInput {
                                param: seed_c
                                tipText: "Integer used to generate the random seed enabling regeneration of results"
                            }

                            FormSectionHeader {
                                id: paramSectionProb
                                title: "Probabilistic"
                                iconSrc: 'chart-simple-solid'
                            }
                            BasicParameterInput {
                                param: n_ale_c
                                tipText: "Number of aleatory samples used in the analysis. Large sample size may substantially prolong analysis."
                            }
                            BasicParameterInput {
                                param: n_epi_c
                                tipText: "Number of epistemic samples used in the analysis. Large sample size may substantially prolong analysis."
                            }

                            FormSectionHeader {
                                id: paramSectionGeom
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

                            FormSectionHeader {
                                id: paramSectionMaterial
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
                                id: paramSectionConditions
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

                            FormSectionHeader {
                                id: paramSectionCrack
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

                            FormSectionHeader {
                                id: paramSectionQoi
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
                        Layout.preferredWidth: 120
                        Layout.alignment: Qt.AlignCenter
                        //                            Layout.leftMargin: 144  // align with unit input
                        Layout.leftMargin: 48
                        Layout.bottomMargin: 8
                        Material.roundedScale: Material.SmallScale
                        Material.accent: Material.Blue
                        highlighted: true

                        onClicked: {
                            forceActiveFocus();
                            data_controller.request_analysis();
                        }

                        Row {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 0

                            AppIcon {
                                anchors.verticalCenter: parent.verticalCenter
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
                                text: "Test alert NOTIFICATION 123"
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

                    Item {
                        Layout.fillWidth: true
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
                anchors.topMargin: mainMenu.height + formHeader1.height + inputSpacer1.height + inputSpacer2.height + 16
                anchors.right: parent.right
                anchors.rightMargin: 18

                spacing: 0

                TextButton {
                    id: scrollBtnA
                    tipText: "Scroll to Analysis Settings"
                    onClicked: { paramContainer.contentY = paramSectionSettings.y; }

                    AppIcon {
                        source: 'gear-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                TextButton {
                    id: scrollBtnP
                    tipText: "Scroll to Probabilities inputs"
                    onClicked: { paramContainer.contentY = paramSectionProb.y; }

                    AppIcon {
                        source: 'chart-simple-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
                TextButton {
                    id: scrollBtnG
                    tipText: "Scroll to Geometries inputs"
                    onClicked: { paramContainer.contentY = paramSectionGeom.y; }

                    AppIcon {
                        source: 'shapes-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                TextButton {
                    id: scrollBtnM
                    tipText: "Scroll to Materials inputs"
                    onClicked: { paramContainer.contentY = paramSectionMaterial.y; }

                    AppIcon {
                        width: 22
                        source: 'microscope-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                TextButton {
                    id: scrollBtnC
                    tipText: "Scroll to Operating Conditions"
                    onClicked: { paramContainer.contentY = paramSectionConditions.y; }

                    AppIcon {
                        width: 18
                        source: 'temperature-half-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                TextButton {
                    id: scrollBtnCrack
                    tipText: "Scroll to Crack Specification"
                    onClicked: { paramContainer.contentY = paramSectionCrack.y; }

                    AppIcon {
                        source: 'wrench-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                TextButton {
                    id: scrollBtnQ
                    tipText: "Scroll to Quantities of Interest"
                    onClicked: { paramContainer.contentY = paramSectionQoi.y; }

                    AppIcon {
                        width: 25
                        source: 'magnifying-glass-chart-solid'
                        iconColor: Material.color(Material.Grey)
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
            }
        }


        Rectangle {
            Layout.preferredWidth: 4
            Layout.fillHeight: true
        }

        // ========================================
        // ==== RIGHT SECTION (ANALYSIS QUEUE) ====
        Pane {
            id: resultQueuePane
            Layout.preferredWidth: 400
            Layout.fillHeight: true
            spacing: 2
            topPadding: 4
            leftPadding: 0
            bottomPadding: 0
            rightPadding: 4

            Image {
                id: queueHeaderImage
                source: "../assets/logo/icon_banner.jpg"
                width: parent.width
                fillMode: Image.PreserveAspectFit
            }

            ListView {
                id: queueListView
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                anchors.top: parent.top
//                anchors.topMargin: 96
                anchors.topMargin: queueHeaderImage.height
                height: parent.height - queueHeaderImage.height

                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.FollowBoundsBehavior
                flickDeceleration: 10000
                clip: true

                spacing: 4
                model: queue  // py QueueController
                delegate:  QueueItem {
                    ac: model.item
                    qIndex: index
                }

                // called from list elem (delete btn clicked)
                function removeItem(idx)
                {
                    // save refs to ac before deleting elem
                    var elem = queueListView.itemAtIndex(idx);
                    var ac = elem.ac;

                    queue.remove_item(idx);

                    // post temp message to allow undo
                    let ctx = {
                        "msg": "Analysis deleted. to undo, click here.",
                        "callback": function() { restoreItem(ac.analysis_id) }
                    };
                    messagesView.model.append(ctx);
                }

                // called from queue item (cancel btn clicked)
                function analysisCanceled(idx)
                {
                    queue.remove_item(idx);

                    let ctx = {
                        "msg": "Analysis canceled",
                        "callback": function() { ; }
                    };
                    messagesView.model.append(ctx);

                }

                // restores deleted AC list element
                function restoreItem(ac_id)
                {
                    queue.restore_item(ac_id);
                }

                remove: Transition {
                    ParallelAnimation {
                        NumberAnimation { property: "opacity"; to: 0; duration: 100 }
                        NumberAnimation { properties: "height"; to: 0; duration: 200 }
                    }
                }
                removeDisplaced: Transition {
                    NumberAnimation { properties: "y"; duration: 200 }
                }

            }
        }

    }

    // ===========================
    // ==== Notification Area ====
    // Temporary top msg display. Messages can include a callback function which is executed when the message is clicked.
    // Messages disappear after 5s.

    ListView {
        id: messagesView
        model: ListModel { dynamicRoles: true }
        orientation: Qt.Vertical
        verticalLayoutDirection: ListView.BottomToTop
        width: 240
        height: 150
        spacing: 4
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 5
        anchors.right: parent.right
        interactive: false

        remove: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; to: 0; duration: 100 }
                NumberAnimation { properties: "height"; to: 0; duration: 200 }
            }
        }
        removeDisplaced: Transition {
            NumberAnimation { properties: "y"; duration: 200 }
        }

        // TODO: add transitions don't work because analysis item is added via backend(?)
        add: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; to: 1; duration: 100 }
                NumberAnimation { properties: "height"; to: 30; duration: 200 }
            }
        }
        addDisplaced: Transition {
            NumberAnimation { properties: "y"; duration: 200 }
        }

        delegate:  Rectangle {
            color: Material.color(Material.Blue, Material.Shade100)
            // width: messagesView.width
            width: msgLabel.width
            anchors.right: parent?.right
            anchors.rightMargin: 4
            radius: 5
            height: 30

            Component.onCompleted: {
                tmr.start();
            }

            Label {
                id: msgLabel
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                leftPadding: 5
                rightPadding: 5
                horizontalAlignment: Text.AlignRight
                font.pointSize: contentFontSize
                font.weight: 500
                font.italic: true
                text: msg
                color: "#333333"
            }

            MouseArea {
                id: msgArea
                anchors.fill: parent
                anchors.centerIn: parent
                onClicked: {
                    if (typeof callback === "function")
                    {
                        callback();
                        // immediately remove msg
                        messagesView.model.remove(index);
                        mouse.accepted = true;  // don't propagate
                    }
                }
            }

            Timer {
                id: tmr
                interval: 4000
                running: true
                repeat: false
                onTriggered: messagesView.model.remove(index)
            }

        }
    }

 }
