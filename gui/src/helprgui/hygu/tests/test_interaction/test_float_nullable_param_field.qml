/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for FloatNullableParamField component.
 * Tests nullable float handling and null state transitions.
 *
 * Run with: python run_qml_tests.py --test test_float_nullable_param_field.qml
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
    title: "FloatNullableParamField Tests"
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
        active: tester !== null && tester.num_field !== null

        sourceComponent: FloatNullableParamField {
            param: tester ? tester.num_field : null
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
            test_01_creation_with_value,
            test_02_is_null_false,
            test_03_set_to_null,
            test_04_set_value_after_null,
            test_05_label_property,
            test_06_min_max_values,
            test_07_unit_type,
            test_08_value_tooltip,
            test_09_multiple_null_transitions,
            test_10_unit_selector_visibility
        ];

        log("========================================");
        log("FloatNullableParamField Test Suite");
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

    function test_01_creation_with_value() {
        log("Test: FloatNullable field creation with value");
        tester.create_nullable_float_field();
        assertClose(parseFloat(tester.get_num_value()), 25.0, 0.1, "Initial value is 25.0");
    }

    function test_02_is_null_false() {
        log("Test: FloatNullable is_null is false when value set");
        tester.create_nullable_float_field();
        assertEqual(tester.get_num_is_null(), false, "is_null is false initially");
    }

    function test_03_set_to_null() {
        log("Test: FloatNullable set to null");
        tester.create_nullable_float_field();
        assertEqual(tester.get_num_is_null(), false, "Start with value");
        tester.set_num_null();
        assertEqual(tester.get_num_is_null(), true, "is_null is true after set_null");
    }

    function test_04_set_value_after_null() {
        log("Test: FloatNullable set value after being null");
        tester.create_nullable_float_field();
        tester.set_num_null();
        assertEqual(tester.get_num_is_null(), true, "Is null");
        tester.set_num_value("50.0");
        assertEqual(tester.get_num_is_null(), false, "is_null is false after setting value");
        assertClose(parseFloat(tester.get_num_value()), 50.0, 0.1, "Value is 50.0");
    }

    function test_05_label_property() {
        log("Test: FloatNullable label property");
        tester.create_nullable_float_field();
        assertEqual(tester.get_num_label(), "Optional Value", "Label is 'Optional Value'");
    }

    function test_06_min_max_values() {
        log("Test: FloatNullable min/max values");
        tester.create_nullable_float_field();
        assertClose(tester.get_num_min_value(), 0, 0.001, "Min value is 0");
        assertClose(tester.get_num_max_value(), 100, 0.001, "Max value is 100");
    }

    function test_07_unit_type() {
        log("Test: FloatNullable unit type");
        tester.create_nullable_float_field();
        assertEqual(tester.get_num_unit_type(), "pres", "Unit type is 'pres'");
    }

    function test_08_value_tooltip() {
        log("Test: FloatNullable value tooltip");
        tester.create_nullable_float_field();
        let tooltip = tester.get_num_value_tooltip();
        assert(tooltip.length > 0, "Tooltip is not empty (got: '" + tooltip.substring(0, 30) + "...')");
    }

    function test_09_multiple_null_transitions() {
        log("Test: FloatNullable multiple null transitions");
        tester.create_nullable_float_field();

        // value -> null -> value -> null
        assertEqual(tester.get_num_is_null(), false, "Start with value");

        tester.set_num_null();
        assertEqual(tester.get_num_is_null(), true, "First null transition");

        tester.set_num_value("75.0");
        assertEqual(tester.get_num_is_null(), false, "Back to value");
        assertClose(parseFloat(tester.get_num_value()), 75.0, 0.1, "Value is 75.0");

        tester.set_num_null();
        assertEqual(tester.get_num_is_null(), true, "Second null transition");
    }

    function test_10_unit_selector_visibility() {
        log("Test: FloatNullable unit selector visibility");
        // Create field with units
        tester.create_nullable_float_field();
        let unitType = tester.get_num_unit_type();
        // Unit selector should be visible for fields with unit types other than 'unitless'
        assert(unitType !== "unitless", "Field has unit type '" + unitType + "' (not unitless)");
    }
}
