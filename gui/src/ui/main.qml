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
    property bool isDebug: app_form.is_debug_mode;

    property string appDir: Qt.resolvedUrl("../");

    Material.theme: Material.Light
    Material.accent: Material.Blue
    property string color_primary: "#020202"
    property string color_success: Material.color(Material.Green)
    property string color_progress: Material.color(Material.Orange)
    property string color_info: Material.color(Material.Blue)
    property string color_text_info: "black"

    property string color_danger: Material.color(Material.Red)
    property string color_danger_bg: Material.color(Material.Red, Material.Shade100)
    property string color_text_danger: "white"

    property string color_warning: "lightyellow"
    property string color_text_warning: "darkgoldenrod"

    property string color_disabled: Material.color(Material.Grey, Material.Shade700)

    property string oldSampleType: ""
    property int oldNumEpi: -1
    property int oldNumAle: -1

    property color btnColorDefault: Material.color(Material.Grey, Material.Shade200);

    property var color_levels: [color_danger, color_primary, color_info, color_warning]
    property var color_text_levels: [color_text_danger, color_text_info, color_text_info, color_text_warning]

    property int scrollBtnHeight: 40

    // Platform-specific properties adjusted via onComplete below
    // default windows font point size is 9; mac is 13
    property int labelFontSize: 13;
    property int inputTopLabelFontSize: 11;
    property int contentFontSize: 13;
    property int header1FontSize: 16;
    property int lgBtnBottomPadding: 4;
    property int headerTopPadding: 12;
    property int paramLabelWidth: 120;

    Connections {
        target: app_form
        function onAlertChanged(msg, level)
        {
            // handleAlertChange(msg, level);
        }

        function onNewMessageEvent(msg)
        {
            handleNewMessageEvent(msg);
        }
    }

    onClosing: function(close) {
        close.accepted = false;
        doShutdown();
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

    /// Shutdown application by first opening dialog, then calling shutdown.
    function doShutdown()
    {
        shutdownPopup.open();
    }

    function refreshForm()
    {
        analysisForm.refreshForm();

        undoBtn.enabled = app_form.can_undo;
        redoBtn.enabled = app_form.can_redo;
    }

    /// Top-level function that restores deleted analysis queue item onto listview queue
    function restoreAnalysis(analysis_id)
    {
        queue.restore_item(ac_id);
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


    MessagePopupSmall {
        id: shutdownPopup
        allowClose: false
        isCentered: true
        header: "Closing HELPR"
        content: "Please wait while HELPR shuts down..."
        onOpened: app_form.shutdown()
    }



    // ======================
    // ==== File Dialogs ====
    FileDialog {
        id: saveFileDialog
        onAccepted: {
            app_form.save_file_as(selectedFile);
        }
        fileMode: FileDialog.SaveFile
        nameFilters: ["HELPR files (*.hpr)", "JSON files (*.JSON *.json)"]
        defaultSuffix: "hpr"
//        currentFolder: StandardPaths.standardLocations(StandardPaths.DocumentsLocation)[0]
    }

    FileDialog {
        id: loadFileDialog
        onAccepted: {
            app_form.load_save_file(selectedFile);
        }
        fileMode: FileDialog.OpenFile
        nameFilters: ["HELPR files (*.hpr)", "JSON files (*.JSON *.json)"]
        defaultSuffix: "hpr"
    }

    // ==== App settings ====
    SettingsPage {
        id: settingsPage
    }


    // =======================
    // ==== RESULTS Popup ====
    Popup {
        id: resultContainer
        x: parent.width * 0.02
        y: parent.height * 0.02
        width: parent.width * 0.92
        height: parent.height * 0.96
        modal: true
        focus: true

        CrackEvoResultPage {
            id: resultDisplay
            pyform: null
            qIndex: -1  // used to delete result in queue
        }

        function show(resultForm, qIndex) {
            resultDisplay.qIndex = qIndex;
            resultDisplay.refresh(resultForm);
            open();
        }
    }

    AboutPage {
        id: aboutPopup
        logoSrc: "assets/logo/icon_banner.jpg"
        title: "About HELPR"
        urlDescrip: '<html><style type="text/css"></style><a href="https://helpr.sandia.gov">HELPR Website</a></html>'
        url: "https://helpr.sandia.gov"
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
                    // Layout.preferredWidth: parent.width + 4

                    background: Rectangle {
                        anchors.fill: parent
                        color: "white"
                    }

                    Connections {
                        target: app_form
                        function onHistoryChanged() { refreshForm(); }
                    }

                    Menu {
                        title: "File"
                        Action {
                            text: "New..."
                            onTriggered: app_form.load_new_form()
                        }
                        Action {
                            text: "Open..."
                            onTriggered: loadFileDialog.open()
                        }
                        Action {
                            text: "Save"
                            onTriggered: {
                                if (app_form.save_file_exists)
                                {
                                    app_form.save_file();
                                }
                                else
                                {
                                    saveFileDialog.open();  // no existing save-file
                                }
                            }
                        }

                        Action {
                            text: "Save As..."
                            onTriggered: saveFileDialog.open()
                        }
                        MenuSeparator { }

                        Action {
                            text: "Open Settings"
                            icon.source: '../helprgui/resources/icons/gear-solid.svg'
                            onTriggered:  settingsPage.open();
                        }
                        Action {
                            text: "Open Data Directory"
                            icon.source: '../helprgui/resources/icons/folder-open-solid.svg'
                            onTriggered: app_form.open_data_directory()
                        }

                        MenuSeparator { }
                        Action {
                            text: "Quit"
                            onTriggered: doShutdown()
                        }
                    }
                    Menu {
                        title: "Demo"
                        Action {
                            text: "Load Deterministic Demo"
                            onTriggered: app_form.load_det_demo()
                        }
                        Action {
                            text: "Load Probabilistic Demo"
                            onTriggered: app_form.load_prb_demo()
                        }
                        Action {
                            text: "Load Sensitivity (Samples) Demo"
                            onTriggered: app_form.load_sam_demo()
                        }
                        Action {
                            text: "Load Sensitivity (Bounds) Demo"
                            onTriggered: app_form.load_bnd_demo()
                        }
                    }
                    Menu {
                        title: "Help"
                        Action {
                            text: "&About"
                            onTriggered: aboutPopup.open()
                        }
                    }
                    Menu {
                        id: devMenu
                        title: "Dev"
                        Action {
                            text: "Print state"
                            onTriggered: app_form.print_state()
                        }
                        Action {
                            text: "Print history"
                            onTriggered: app_form.print_history()
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

                        IconButton {
                            id: openSettingsBtn
                            img: 'gear-solid'
                            tooltip: "View HELPR settings"
                            onClicked: {
                                settingsPage.open();
                            }
                        }

                        IconButton {
                            id: topSaveBtn
                            img: 'save-solid'
                            tooltip: "Save changes"
                            onClicked: {
                                if (app_form.save_file_exists)
                                {
                                    app_form.save_file();
                                }
                                else
                                {
                                    saveFileDialog.open();  // no existing save-file
                                }
                            }

                        }

                        IconButton {
                            id: undoBtn
                            img: 'rotate-left-solid'
                            tooltip: "Undo last change"
                            onClicked: app_form.undo()

                        }

                        IconButton {
                            id: redoBtn
                            img: 'rotate-right-solid'
                            tooltip: "Revert last undo"
                            onClicked: app_form.redo()
                        }
                    }
                }

                Item {
                    id: inputSpacer1
                    Layout.preferredHeight: headerTopPadding
                }

                AnalysisForm {
                    id: analysisForm
                    appForm: app_form
                    //width: parent.width
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                }

//                Rectangle {   height: 10 Layout.fillWidth: true color: "blue" }  // layout guide
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
                width: 400
                fillMode: Image.PreserveAspectFit
            }

            ListView {
                id: queueListView
                anchors.horizontalCenter: parent.horizontalCenter
                width: 400
                anchors.top: parent.top
//                anchors.topMargin: 96
                anchors.topMargin: queueHeaderImage.height
                height: parent.height - queueHeaderImage.height

                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.FollowBoundsBehavior
                flickDeceleration: 10000
                clip: true

                spacing: 4
                model: queue  // py QueueDisplay
                delegate:  QueueItem {
                    fm: model.item
                    qIndex: index
                }

                // called from list elem (delete btn clicked)
                function removeItem(idx)
                {
                    // save refs to ac before deleting elem
                    var elem = queueListView.itemAtIndex(idx);
                    var fm = elem.fm;

                    queue.remove_item(idx);

                    // post temp message to allow undo
                    let ctx = {
                        "msg": "Analysis deleted. to undo, click here.",
                        "callback": function() { restoreItem(fm.analysis_id) }
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
                onClicked: function(mouse) {
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
