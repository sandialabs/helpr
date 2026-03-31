/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Tests for DirectorySelector component.
 * Tests directory path display, label, and value changes.
 *
 * Run with: python run_qml_tests.py --test test_directory_selector.qml
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
    title: "DirectorySelector Tests"
    color: "#f0f0f0"

    // ==================== Global Properties (from Globals singleton) ====================
    property string color_primary: Globals.color_primary
    property color color_danger: Globals.color_danger
    property color color_danger_bg: Globals.color_danger_bg
    property color color_info: Globals.color_info
    property color color_warning: Globals.color_warning
    property string color_text_danger: Globals.color_text_danger
    property string color_text_warning: Globals.color_text_warning

    // Status-indexed color arrays (0=error, 1=good, 2=info, 3=warning)
    property var color_text_levels: Globals.color_text_levels
    property var color_levels: Globals.color_levels

    property int labelFontSize: Globals.labelFontSize
    property int inputTopLabelFontSize: Globals.inputTopLabelFontSize

    property int paramLabelWidth: Globals.paramLabelWidth
    property int shortInputW: Globals.shortInputW
    property int medInputW: Globals.medInputW
    property int longInputW: Globals.longInputW
    property int defaultSelectorW: Globals.defaultSelectorW
    property int defaultInputW: Globals.defaultInputW

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
        active: tester !== null && tester.string_field !== null

        sourceComponent: DirectorySelector {
            param: tester ? tester.string_field : null
        }
    }

    // Focus stealer
    TextField {
        id: focusStealer
        anchors.top: fieldLoader.bottom
        anchors.left: parent.left
        anchors.margins: 20
        anchors.topMargin: 60
        placeholderText: "Click to change focus"
        width: 200
    }

    // Run Tests button
    Button {
        id: runButton
        anchors.top: fieldLoader.bottom
        anchors.left: focusStealer.right
        anchors.margins: 20
        anchors.topMargin: 60
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
            test_01_creation_with_path,
            test_02_label_property,
            test_03_value_property,
            test_04_empty_path_creation,
            test_05_set_value,
            test_06_clear_value,
            test_07_multiple_field_creation
        ];

        log("========================================");
        log("DirectorySelector Test Suite");
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

    function test_01_creation_with_path() {
        log("Test: DirectorySelector creation with path");
        tester.create_directory_path_field();
        assertEqual(tester.get_string_value(), "/path/to/output", "Initial directory path");
    }

    function test_02_label_property() {
        log("Test: DirectorySelector label property");
        tester.create_directory_path_field();
        assertEqual(tester.get_string_label(), "Output Directory", "Label is 'Output Directory'");
    }

    function test_03_value_property() {
        log("Test: DirectorySelector value property");
        tester.create_directory_path_field();
        let value = tester.get_string_value();
        assert(value.length > 0, "Value is not empty");
        assert(value.indexOf("/") >= 0, "Value contains path separator");
    }

    function test_04_empty_path_creation() {
        log("Test: DirectorySelector empty path creation");
        tester.create_empty_directory_path_field();
        assertEqual(tester.get_string_value(), "", "Empty directory path");
        assertEqual(tester.get_string_label(), "Output Directory", "Label is 'Output Directory'");
    }

    function test_05_set_value() {
        log("Test: DirectorySelector set value");
        tester.create_directory_path_field();
        tester.set_string_value("/new/output/directory");
        assertEqual(tester.get_string_value(), "/new/output/directory", "Value updated");
    }

    function test_06_clear_value() {
        log("Test: DirectorySelector clear value");
        tester.create_directory_path_field();
        assert(tester.get_string_value().length > 0, "Start with value");
        tester.set_string_value("");
        assertEqual(tester.get_string_value(), "", "Value cleared");
    }

    function test_07_multiple_field_creation() {
        log("Test: Multiple DirectorySelector creation");
        tester.create_directory_path_field();
        assertEqual(tester.get_string_value(), "/path/to/output", "First: with path");

        tester.create_empty_directory_path_field();
        assertEqual(tester.get_string_value(), "", "Second: empty");

        tester.create_directory_path_field();
        assertEqual(tester.get_string_value(), "/path/to/output", "Third: back to path");
    }
}
