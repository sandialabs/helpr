/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for hygu parameter field components.
 * Tests IntParamField, BoolParamField, ChoiceParamField, and StringParamField.
 *
 * Run with: python run_qml_tests.py --test test_param_fields.qml
 */
import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material 2.12
import QtQuick.Layouts
import QtQuick.Window

import "../../ui/parameters"
import "."  // For Globals singleton

ApplicationWindow {
    id: root
    width: 900
    height: 700
    visible: true
    title: "Parameter Fields Test Suite"
    color: "#f0f0f0"

    // ==================== Global Properties (from Globals singleton) ====================
    property string color_primary: Globals.color_primary
    property color color_danger: Globals.color_danger
    property color color_danger_bg: Globals.color_danger_bg
    property color color_info: Globals.color_info
    property color color_warning: Globals.color_warning

    property int labelFontSize: Globals.labelFontSize
    property int inputTopLabelFontSize: Globals.inputTopLabelFontSize

    property int paramLabelWidth: Globals.paramLabelWidth
    property int shortInputW: Globals.shortInputW
    property int medInputW: Globals.medInputW
    property int longInputW: Globals.longInputW
    property int defaultSelectorW: Globals.defaultSelectorW
    property int defaultInputW: Globals.defaultInputW
    property int uncertaintyInputW: Globals.uncertaintyInputW
    property int distributionInputW: Globals.distributionInputW

    // ==================== Test State ====================
    property int testsRun: 0
    property int testsPassed: 0
    property int testsFailed: 0
    property bool testsComplete: false
    property var testLog: []
    property int currentTestIndex: 0
    property var testFunctions: []

    // Field loaders - use Loaders to avoid null param errors
    ColumnLayout {
        id: fieldsContainer
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 10

        Text {
            text: "Test Fields"
            font.bold: true
            font.pixelSize: 14
        }

        Loader {
            id: intFieldLoader
            active: tester !== null && tester.int_field !== null
            sourceComponent: IntParamField {
                param: tester ? tester.int_field : null
            }
        }

        Loader {
            id: boolFieldLoader
            active: tester !== null && tester.bool_field !== null
            sourceComponent: BoolParamField {
                param: tester ? tester.bool_field : null
            }
        }

        Loader {
            id: choiceFieldLoader
            active: tester !== null && tester.choice_field !== null
            sourceComponent: ChoiceParamField {
                param: tester ? tester.choice_field : null
            }
        }

        Loader {
            id: stringFieldLoader
            active: tester !== null && tester.string_field !== null
            sourceComponent: StringParamField {
                param: tester ? tester.string_field : null
            }
        }
    }

    // Focus stealer
    TextField {
        id: focusStealer
        anchors.top: fieldsContainer.bottom
        anchors.left: parent.left
        anchors.margins: 20
        placeholderText: "Click to change focus"
        width: 200
    }

    // Run Tests button
    Button {
        id: runButton
        anchors.top: fieldsContainer.bottom
        anchors.left: focusStealer.right
        anchors.margins: 20
        text: "Run Tests"
        onClicked: startTests()
    }

    // Test output display
    Rectangle {
        id: outputPanel
        anchors.top: focusStealer.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        color: "white"
        border.color: "#ccc"
        radius: 4

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            Text {
                text: "Test Results: " + testsPassed + "/" + testsRun + " passed" +
                      (testsFailed > 0 ? " (" + testsFailed + " failed)" : "")
                font.bold: true
                font.pixelSize: 16
                color: testsFailed > 0 ? "#c00" : (testsRun > 0 ? "#080" : "#000")
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    id: logOutput
                    readOnly: true
                    font.family: "Courier"
                    font.pixelSize: 12
                    text: testLog.join("\n")
                    wrapMode: TextEdit.Wrap
                }
            }
        }
    }

    // ==================== Test Utilities ====================

    function log(msg) {
        testLog.push(msg);
        testLog = testLog;
        console.log(msg);
    }

    function assert(condition, message) {
        testsRun++;
        if (condition) {
            testsPassed++;
            log("  PASS: " + message);
            return true;
        } else {
            testsFailed++;
            log("  FAIL: " + message);
            return false;
        }
    }

    function assertEqual(actual, expected, message) {
        let pass = actual === expected;
        if (!pass) {
            return assert(false, message + " (expected: " + expected + ", got: " + actual + ")");
        }
        return assert(true, message);
    }

    // ==================== Test Runner ====================

    Timer {
        id: testRunner
        interval: 150
        repeat: true
        onTriggered: runNextTest()
    }

    function startTests() {
        testsRun = 0;
        testsPassed = 0;
        testsFailed = 0;
        testLog = [];
        currentTestIndex = 0;

        testFunctions = [
            // IntField tests
            test_int_01_creation,
            test_int_02_set_value,
            test_int_03_min_max,
            test_int_04_label,
            test_int_05_null_handling,
            // BoolField tests
            test_bool_01_creation,
            test_bool_02_toggle,
            test_bool_03_initial_false,
            test_bool_04_label,
            // ChoiceField tests
            test_choice_01_creation,
            test_choice_02_change_selection,
            test_choice_03_get_index,
            test_choice_04_label,
            test_choice_05_value_display,
            test_choice_06_choice_count,
            // StringField tests
            test_string_01_creation,
            test_string_02_set_value,
            test_string_03_empty_value,
            test_string_04_label
        ];

        log("========================================");
        log("Parameter Fields Test Suite");
        log("========================================");
        log("Running " + testFunctions.length + " tests...");
        log("");

        runButton.enabled = false;
        testRunner.start();
    }

    function runNextTest() {
        if (currentTestIndex >= testFunctions.length) {
            testRunner.stop();
            finishTests();
            return;
        }

        try {
            testFunctions[currentTestIndex]();
        } catch (e) {
            log("  EXCEPTION: " + e);
            testsFailed++;
            testsRun++;
        }

        currentTestIndex++;
    }

    function finishTests() {
        log("");
        log("========================================");
        log("Final Results: " + testsPassed + "/" + testsRun + " tests passed");
        if (testsFailed > 0) {
            log("FAILURES: " + testsFailed);
        }
        log("========================================");
        runButton.enabled = true;
        testsComplete = true;
    }

    Component.onCompleted: {
        startTestsTimer.start();
    }

    Timer {
        id: startTestsTimer
        interval: 500
        repeat: false
        onTriggered: startTests()
    }

    // ==================== IntField Test Cases ====================

    function test_int_01_creation() {
        log("Test: IntField creation");
        tester.create_sample_count_field();
        assertEqual(tester.get_int_value(), "50", "Initial value is 50");
    }

    function test_int_02_set_value() {
        log("Test: IntField set value");
        tester.create_sample_count_field();
        tester.set_int_value("75");
        assertEqual(tester.get_int_value(), "75", "Value updated to 75");
    }

    function test_int_03_min_max() {
        log("Test: IntField min/max values");
        tester.create_sample_count_field();
        assertEqual(tester.get_int_min_value(), 1, "Min value is 1");
        assertEqual(tester.get_int_max_value(), 10000, "Max value is 10000");
    }

    // ==================== BoolField Test Cases ====================

    function test_bool_01_creation() {
        log("Test: BoolField creation with true");
        tester.create_enabled_field();
        assertEqual(tester.get_bool_value(), true, "Initial value is true");
    }

    function test_bool_02_toggle() {
        log("Test: BoolField toggle");
        tester.create_enabled_field();
        assertEqual(tester.get_bool_value(), true, "Start as true");
        tester.set_bool_value(false);
        assertEqual(tester.get_bool_value(), false, "Toggled to false");
        tester.set_bool_value(true);
        assertEqual(tester.get_bool_value(), true, "Toggled back to true");
    }

    function test_bool_03_initial_false() {
        log("Test: BoolField creation with false");
        tester.create_debug_field();
        assertEqual(tester.get_bool_value(), false, "Initial value is false");
    }

    // ==================== ChoiceField Test Cases ====================

    function test_choice_01_creation() {
        log("Test: ChoiceField creation");
        tester.create_study_type_field();
        assertEqual(tester.get_choice_value(), "det", "Initial value is 'det'");
    }

    function test_choice_02_change_selection() {
        log("Test: ChoiceField change selection");
        tester.create_study_type_field();
        tester.set_choice_by_index(1);
        assertEqual(tester.get_choice_value(), "prb", "Changed to 'prb'");
        tester.set_choice_by_index(2);
        assertEqual(tester.get_choice_value(), "sam", "Changed to 'sam'");
    }

    function test_choice_03_get_index() {
        log("Test: ChoiceField get index");
        tester.create_study_type_field();
        assertEqual(tester.get_choice_index(), 0, "Initial index is 0");
        tester.set_choice_by_index(2);
        assertEqual(tester.get_choice_index(), 2, "Index updated to 2");
    }

    // ==================== StringField Test Cases ====================

    function test_string_01_creation() {
        log("Test: StringField creation");
        tester.create_name_field();
        assertEqual(tester.get_string_value(), "Test Analysis", "Initial value is 'Test Analysis'");
    }

    function test_string_02_set_value() {
        log("Test: StringField set value");
        tester.create_name_field();
        tester.set_string_value("New Analysis Name");
        assertEqual(tester.get_string_value(), "New Analysis Name", "Value updated");
    }

    function test_string_03_empty_value() {
        log("Test: StringField empty value");
        tester.create_description_field();
        assertEqual(tester.get_string_value(), "", "Initial value is empty");
        tester.set_string_value("Some description");
        assertEqual(tester.get_string_value(), "Some description", "Value set from empty");
    }

    // ==================== Additional IntField Tests ====================

    function test_int_04_label() {
        log("Test: IntField label property");
        tester.create_sample_count_field();
        assertEqual(tester.get_int_label(), "Sample Count", "Label is 'Sample Count'");
    }

    function test_int_05_null_handling() {
        log("Test: IntField null handling");
        tester.create_sample_count_field();
        assertEqual(tester.get_int_is_null(), false, "Initially not null");
        tester.set_int_null();
        assertEqual(tester.get_int_is_null(), true, "Is null after set_null");
    }

    // ==================== Additional BoolField Tests ====================

    function test_bool_04_label() {
        log("Test: BoolField label property");
        tester.create_enabled_field();
        assertEqual(tester.get_bool_label(), "Enabled", "Label is 'Enabled'");
    }

    // ==================== Additional ChoiceField Tests ====================

    function test_choice_04_label() {
        log("Test: ChoiceField label property");
        tester.create_study_type_field();
        assertEqual(tester.get_choice_label(), "Study Type", "Label is 'Study Type'");
    }

    function test_choice_05_value_display() {
        log("Test: ChoiceField value display");
        tester.create_study_type_field();
        assertEqual(tester.get_choice_value_display(), "Deterministic", "Display is 'Deterministic'");
        tester.set_choice_by_index(1);
        assertEqual(tester.get_choice_value_display(), "Probabilistic", "Display is 'Probabilistic'");
    }

    function test_choice_06_choice_count() {
        log("Test: ChoiceField choice count");
        tester.create_study_type_field();
        assertEqual(tester.get_choice_count(), 4, "Has 4 choices");

        tester.create_method_field();
        assertEqual(tester.get_choice_count(), 3, "Has 3 choices");
    }

    // ==================== Additional StringField Tests ====================

    function test_string_04_label() {
        log("Test: StringField label property");
        tester.create_name_field();
        assertEqual(tester.get_string_label(), "Analysis Name", "Label is 'Analysis Name'");
    }
}
