/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for FloatParamField component.
 * Tests value changes, unit switching, and validation.
 *
 * Run with: python run_qml_tests.py --test test_float_param_field.qml
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
    title: "FloatParamField Tests"
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

    // The field under test - use Loader to avoid null param errors at startup/shutdown
    Loader {
        id: fieldLoader
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        active: tester !== null && tester.num_field !== null

        sourceComponent: FloatParamField {
            id: testFieldInner
            param: tester ? tester.num_field : null
        }
    }

    property var testField: fieldLoader.item

    // Focus stealer - click here to trigger onEditingFinished
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
        testLog = testLog;  // Trigger binding update
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
        interval: 150  // Time between tests
        repeat: true
        onTriggered: runNextTest()
    }

    function startTests() {
        // Reset state
        testsRun = 0;
        testsPassed = 0;
        testsFailed = 0;
        testLog = [];
        currentTestIndex = 0;

        // Build list of test functions
        testFunctions = [
            test_01_pressure_field_creation,
            test_02_temperature_field_creation,
            test_03_distance_field_creation,
            test_04_fractional_field_creation,
            test_05_set_value,
            test_06_field_label,
            test_07_min_max_values,
            test_08_unit_index,
            test_09_value_tooltip_exists,
            test_10_multiple_field_creation,
            test_11_unit_change
        ];

        log("========================================");
        log("FloatParamField Test Suite");
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

    // Auto-start tests after window is shown
    Component.onCompleted: {
        startTestsTimer.start();
    }

    Timer {
        id: startTestsTimer
        interval: 500  // Wait for window to fully render
        repeat: false
        onTriggered: startTests()
    }

    // ==================== Test Cases ====================

    function test_01_pressure_field_creation() {
        log("Test: Pressure field creation");
        tester.create_pressure_field();
        assertEqual(tester.get_num_unit_type(), "pres", "Unit type is pres");
        assertClose(parseFloat(tester.get_num_value()), 50.0, 0.1, "Initial value is 50.0");
    }

    function test_02_temperature_field_creation() {
        log("Test: Temperature field creation");
        tester.create_temperature_field();
        assertEqual(tester.get_num_unit_type(), "temp", "Unit type is temp");
        assertClose(parseFloat(tester.get_num_value()), 300.0, 0.1, "Initial value is 300.0");
    }

    function test_03_distance_field_creation() {
        log("Test: Distance field creation");
        tester.create_distance_field();
        assertEqual(tester.get_num_unit_type(), "dist_sm", "Unit type is dist_sm");
        assertClose(parseFloat(tester.get_num_value()), 0.005, 0.0001, "Initial value is 0.005");
    }

    function test_04_fractional_field_creation() {
        log("Test: Fractional field creation");
        tester.create_fractional_field();
        assertEqual(tester.get_num_unit_type(), "frac", "Unit type is frac");
        assertClose(parseFloat(tester.get_num_value()), 0.5, 0.01, "Initial value is 0.5");
    }

    function test_05_set_value() {
        log("Test: Set value");
        tester.create_pressure_field();
        tester.set_num_value("75.5");
        assertClose(parseFloat(tester.get_num_value()), 75.5, 0.1, "Value updated to 75.5");
    }

    function test_06_field_label() {
        log("Test: Field label property");
        tester.create_pressure_field();
        assertEqual(tester.get_num_label(), "Test Pressure", "Pressure field label");

        tester.create_temperature_field();
        assertEqual(tester.get_num_label(), "Test Temperature", "Temperature field label");
    }

    function test_07_min_max_values() {
        log("Test: Min/max values");
        tester.create_pressure_field();
        assertClose(tester.get_num_min_value(), 0, 0.001, "Min value is 0");
        assertClose(tester.get_num_max_value(), 100, 0.001, "Max value is 100");

        tester.create_temperature_field();
        assertClose(tester.get_num_min_value(), 200, 0.001, "Temp min value is 200");
        assertClose(tester.get_num_max_value(), 500, 0.001, "Temp max value is 500");
    }

    function test_08_unit_index() {
        log("Test: Unit index");
        tester.create_pressure_field();
        let unitIdx = tester.get_num_unit_index();
        assert(unitIdx >= 0, "Unit index is non-negative (got: " + unitIdx + ")");
    }

    function test_09_value_tooltip_exists() {
        log("Test: Value tooltip exists");
        tester.create_pressure_field();
        let tooltip = tester.get_num_value_tooltip();
        assert(tooltip.length > 0, "Tooltip is not empty (got: '" + tooltip.substring(0, 30) + "...')");
    }

    function test_10_multiple_field_creation() {
        log("Test: Multiple field creation preserves old fields");
        tester.create_pressure_field();
        assertEqual(tester.get_num_unit_type(), "pres", "First: Pressure");

        tester.create_temperature_field();
        assertEqual(tester.get_num_unit_type(), "temp", "Second: Temperature");

        tester.create_distance_field();
        assertEqual(tester.get_num_unit_type(), "dist_sm", "Third: Small Distance");

        tester.create_fractional_field();
        assertEqual(tester.get_num_unit_type(), "frac", "Fourth: Fractional");

        // Verify no crashes from old field cleanup
        tester.create_pressure_field();
        assertEqual(tester.get_num_unit_type(), "pres", "Fifth: Back to Pressure");
    }

    function test_11_unit_change() {
        log("Test: Unit change");
        tester.create_pressure_field();
        let initialUnit = tester.get_num_unit();
        assertEqual(initialUnit, "mpa", "Initial unit is MPa");

        // Change unit
        tester.set_num_unit("psi");
        assertEqual(tester.get_num_unit(), "psi", "Unit changed to psi");
    }
}
