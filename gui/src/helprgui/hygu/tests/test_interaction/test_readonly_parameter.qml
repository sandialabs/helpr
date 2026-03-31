/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for ReadonlyParameter component.
 * Tests display of computed/read-only values including special cases like infinity.
 *
 * Run with: python run_qml_tests.py --test test_readonly_parameter.qml
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
    title: "ReadonlyParameter Tests"
    color: "#f0f0f0"

    // ==================== Global Properties (from Globals singleton) ====================
    property string color_primary: Globals.color_primary
    property color color_danger: Globals.color_danger
    property color color_danger_bg: Globals.color_danger_bg
    property color color_info: Globals.color_info
    property color color_warning: Globals.color_warning
    property string color_text_danger: Globals.color_text_danger
    property string color_text_warning: Globals.color_text_warning

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
        active: tester !== null && tester.field !== null

        sourceComponent: ReadonlyParameter {
            param: tester ? tester.field : null
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
            test_02_label_property,
            test_03_value_property,
            test_04_unit_display,
            test_05_deterministic_distribution,
            test_06_multiple_field_creation
        ];

        log("========================================");
        log("ReadonlyParameter Test Suite");
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
        log("Test: Readonly field creation with value");
        tester.create_readonly_result_field();
        let value = tester.get_field_value();
        assertClose(parseFloat(value), 123.456, 0.01, "Initial value is 123.456");
    }

    function test_02_label_property() {
        log("Test: Readonly label property");
        tester.create_readonly_result_field();
        // Label should contain "Computed Result" (label_rtf may have formatting)
        let field = tester.field;
        assert(field !== null, "Field exists");
        // Access via the property directly
        let label = field.label;
        assertEqual(label, "Computed Result", "Label is 'Computed Result'");
    }

    function test_03_value_property() {
        log("Test: Readonly value property");
        tester.create_readonly_result_field();
        let value = parseFloat(tester.get_field_value());
        assertClose(value, 123.456, 0.01, "Value is approximately 123.456");
    }

    function test_04_unit_display() {
        log("Test: Readonly unit display");
        tester.create_readonly_result_field();
        let unitDisp = tester.get_field_unit_display();
        // Should have a unit display (MPa for pressure)
        assert(unitDisp.length > 0, "Unit display is not empty (got: '" + unitDisp + "')");
    }

    function test_05_deterministic_distribution() {
        log("Test: Readonly uses deterministic distribution");
        tester.create_readonly_result_field();
        let distr = tester.get_current_distribution();
        assertEqual(distr, "det", "Distribution is 'det' (deterministic)");
    }

    function test_06_multiple_field_creation() {
        log("Test: Multiple readonly field creation");
        tester.create_readonly_result_field();
        let label1 = tester.field.label;
        assertEqual(label1, "Computed Result", "First: Computed Result");

        // Create another readonly field
        tester.create_deterministic_field();
        let label2 = tester.field.label;
        assertEqual(label2, "Test Deterministic", "Second: Test Deterministic");

        // Back to readonly
        tester.create_readonly_result_field();
        let label3 = tester.field.label;
        assertEqual(label3, "Computed Result", "Third: Back to Computed Result");
    }
}
