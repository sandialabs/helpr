/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for NumListParamField component.
 * Tests list value handling, unit types, and validation.
 *
 * Run with: python run_qml_tests.py --test test_num_list_param_field.qml
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
    height: 600
    visible: true
    title: "NumListParamField Tests"
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

    // The field under test - use Loader to avoid null param errors
    Loader {
        id: fieldLoader
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        active: tester !== null && tester.num_list_field !== null

        sourceComponent: NumListParamField {
            param: tester ? tester.num_list_field : null
        }
    }

    // Focus stealer
    TextField {
        id: focusStealer
        anchors.top: fieldLoader.bottom
        anchors.left: parent.left
        anchors.margins: 20
        placeholderText: "Click to change focus"
        width: 200
    }

    // Run Tests button
    Button {
        id: runButton
        anchors.top: fieldLoader.bottom
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

    function assertClose(actual, expected, tolerance, message) {
        let pass = Math.abs(actual - expected) < tolerance;
        if (!pass) {
            return assert(false, message + " (expected: " + expected + " +/- " + tolerance + ", got: " + actual + ")");
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
            test_01_creation_with_values,
            test_02_label_property,
            test_03_value_count,
            test_04_value_as_string,
            test_05_set_value_from_string,
            test_06_min_max_values,
            test_07_empty_list_creation,
            test_08_temperature_list_creation,
            test_09_value_tooltip,
            test_10_multiple_field_creation
        ];

        log("========================================");
        log("NumListParamField Test Suite");
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

    // ==================== Test Cases ====================

    function test_01_creation_with_values() {
        log("Test: NumListField creation with initial values");
        tester.create_cycle_times_field();
        assertEqual(tester.get_num_list_count(), 5, "Initial list has 5 values");
    }

    function test_02_label_property() {
        log("Test: NumListField label property");
        tester.create_cycle_times_field();
        assertEqual(tester.get_num_list_label(), "Cycle Times", "Label is 'Cycle Times'");
    }

    function test_03_value_count() {
        log("Test: NumListField value count");
        tester.create_cycle_times_field();
        assertEqual(tester.get_num_list_count(), 5, "Has 5 values");

        tester.create_temperature_list_field();
        assertEqual(tester.get_num_list_count(), 3, "Temperature list has 3 values");
    }

    function test_04_value_as_string() {
        log("Test: NumListField value as string");
        tester.create_cycle_times_field();
        let valueStr = tester.get_num_list_value();
        // Values should be space-separated
        assert(valueStr.length > 0, "Value string is not empty (got: '" + valueStr + "')");
        assert(valueStr.indexOf("1") >= 0, "Value string contains '1' (got: '" + valueStr + "')");
    }

    function test_05_set_value_from_string() {
        log("Test: NumListField set value from string");
        tester.create_cycle_times_field();
        tester.set_num_list_value("10 20 30");
        assertEqual(tester.get_num_list_count(), 3, "List now has 3 values after setting '10 20 30'");
    }

    function test_06_min_max_values() {
        log("Test: NumListField min/max values");
        tester.create_cycle_times_field();
        assertClose(tester.get_num_list_min_value(), 0, 0.001, "Min value is 0");
        assertClose(tester.get_num_list_max_value(), 100, 0.001, "Max value is 100");
    }

    function test_07_empty_list_creation() {
        log("Test: NumListField empty list creation");
        tester.create_empty_list_field();
        assertEqual(tester.get_num_list_count(), 0, "Empty list has 0 values");
        assertEqual(tester.get_num_list_label(), "Empty List", "Label is 'Empty List'");
    }

    function test_08_temperature_list_creation() {
        log("Test: NumListField temperature list creation");
        tester.create_temperature_list_field();
        assertEqual(tester.get_num_list_label(), "Temperature Profile", "Label is 'Temperature Profile'");
        assertEqual(tester.get_num_list_count(), 3, "Has 3 temperature values");
        assertClose(tester.get_num_list_min_value(), 200, 0.1, "Min temp is 200");
        assertClose(tester.get_num_list_max_value(), 600, 0.1, "Max temp is 600");
    }

    function test_09_value_tooltip() {
        log("Test: NumListField value tooltip");
        tester.create_cycle_times_field();
        let tooltip = tester.get_num_list_value_tooltip();
        assert(tooltip.length > 0, "Tooltip is not empty (got: '" + tooltip.substring(0, 30) + "...')");
    }

    function test_10_multiple_field_creation() {
        log("Test: Multiple NumListField creation");
        tester.create_cycle_times_field();
        assertEqual(tester.get_num_list_label(), "Cycle Times", "First: Cycle Times");

        tester.create_temperature_list_field();
        assertEqual(tester.get_num_list_label(), "Temperature Profile", "Second: Temperature Profile");

        tester.create_empty_list_field();
        assertEqual(tester.get_num_list_label(), "Empty List", "Third: Empty List");

        // Verify no crashes from old field cleanup
        tester.create_cycle_times_field();
        assertEqual(tester.get_num_list_label(), "Cycle Times", "Fourth: Back to Cycle Times");
    }
}
