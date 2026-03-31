/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Comprehensive tests for UncertainParamField component.
 * Tests distribution switching, field visibility, validation, and error states.
 *
 * Run with: python run_qml_tests.py
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
    title: "UncertainParamField Tests"
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
        active: tester !== null && tester.field !== null

        sourceComponent: UncertainParamField {
            id: testFieldInner
            param: tester ? tester.field : null
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
            log("  ✓ " + message);
            return true;
        } else {
            testsFailed++;
            log("  ✗ FAIL: " + message);
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
            test_01_deterministic_field_creation,
            test_02_uniform_field_visibility,
            test_03_normal_field_visibility,
            test_04_truncated_normal_field_visibility,
            test_05_lognormal_field_visibility,
            test_06_truncated_lognormal_field_visibility,
            test_07_beta_field_visibility,
            test_10_validation_events_recorded,
            test_11_invalid_lower_bound_shows_error,
            test_12_fix_validation_clears_error,
            test_20_create_all_distribution_types,
            test_30_set_nominal_value,
            test_31_set_distribution_parameters,
            test_40_rapid_field_creation,
            test_41_boundary_values
        ];

        log("========================================");
        log("UncertainParamField Test Suite");
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
            log("  ✗ EXCEPTION: " + e);
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

    function test_01_deterministic_field_creation() {
        log("Test: Deterministic field creation");
        tester.create_deterministic_field();
        assertEqual(tester.get_input_type(), "det", "Distribution is deterministic");
    }

    function test_02_uniform_field_visibility() {
        log("Test: Uniform distribution field visibility");
        tester.create_uniform_field();
        assertEqual(tester.get_input_type(), "uni", "Distribution is uniform");
        assert(tester.is_field_visible("lower"), "Lower bound visible for uniform");
        assert(tester.is_field_visible("upper"), "Upper bound visible for uniform");
        assert(!tester.is_field_visible("mean"), "Mean not visible for uniform");
    }

    function test_03_normal_field_visibility() {
        log("Test: Normal distribution field visibility");
        tester.create_normal_field();
        assertEqual(tester.get_input_type(), "nor", "Distribution is normal");
        assert(tester.is_field_visible("mean"), "Mean visible for normal");
        assert(tester.is_field_visible("std"), "Std visible for normal");
        assert(!tester.is_field_visible("lower"), "Lower not visible for normal");
    }

    function test_04_truncated_normal_field_visibility() {
        log("Test: Truncated normal distribution field visibility");
        tester.create_truncated_normal_field();
        assertEqual(tester.get_input_type(), "tnor", "Distribution is truncated normal");
        assert(tester.is_field_visible("mean"), "Mean visible for tnor");
        assert(tester.is_field_visible("std"), "Std visible for tnor");
        assert(tester.is_field_visible("lower"), "Lower visible for tnor");
        assert(tester.is_field_visible("upper"), "Upper visible for tnor");
    }

    function test_05_lognormal_field_visibility() {
        log("Test: Lognormal distribution field visibility");
        tester.create_lognormal_field();
        assertEqual(tester.get_input_type(), "log", "Distribution is lognormal");
        assert(tester.is_field_visible("mu"), "Mu visible for lognormal");
        assert(tester.is_field_visible("sigma"), "Sigma visible for lognormal");
        assert(!tester.is_field_visible("mean"), "Mean not visible for lognormal");
    }

    function test_06_truncated_lognormal_field_visibility() {
        log("Test: Truncated lognormal distribution field visibility");
        tester.create_truncated_lognormal_field();
        assertEqual(tester.get_input_type(), "tlog", "Distribution is truncated lognormal");
        assert(tester.is_field_visible("mu"), "Mu visible for tlog");
        assert(tester.is_field_visible("sigma"), "Sigma visible for tlog");
        assert(tester.is_field_visible("lower"), "Lower visible for tlog");
        assert(tester.is_field_visible("upper"), "Upper visible for tlog");
    }

    function test_07_beta_field_visibility() {
        log("Test: Beta distribution field visibility");
        tester.create_beta_field();
        assertEqual(tester.get_input_type(), "beta", "Distribution is beta");
        assert(tester.is_field_visible("alpha"), "Alpha visible for beta");
        assert(tester.is_field_visible("beta"), "Beta param visible for beta dist");
        assert(!tester.is_field_visible("mean"), "Mean not visible for beta");
    }

    function test_10_validation_events_recorded() {
        log("Test: Validation events are recorded");
        tester.create_uniform_field();
        tester.clear_validation_events();
        tester.set_subparam("lower", "80");  // Invalid: > upper (60)
        let eventCount = tester.get_validation_event_count();
        assert(eventCount > 0, "Validation event recorded (count: " + eventCount + ")");
    }

    function test_11_invalid_lower_bound_shows_error() {
        log("Test: Invalid lower bound triggers error");
        tester.create_uniform_field();  // lower=40, upper=60
        tester.clear_validation_events();
        tester.set_subparam("lower", "70");  // > upper
        assert(tester.has_error(), "Error state detected for invalid bounds");
    }

    function test_12_fix_validation_clears_error() {
        log("Test: Fixing validation clears error");
        tester.create_uniform_field();
        tester.set_subparam("lower", "70");  // Create error
        tester.clear_validation_events();
        tester.set_subparam("lower", "30");  // Fix error

        let hasOk = false;
        for (let i = 0; i < tester.get_validation_event_count(); i++) {
            if (tester.get_validation_event_status(i) === 1) {
                hasOk = true;
                break;
            }
        }
        assert(hasOk, "OK validation event received after fix");
    }

    function test_20_create_all_distribution_types() {
        log("Test: Create fields for all distribution types");

        tester.create_deterministic_field();
        assertEqual(tester.get_input_type(), "det", "Deterministic created");

        tester.create_uniform_field();
        assertEqual(tester.get_input_type(), "uni", "Uniform created");

        tester.create_normal_field();
        assertEqual(tester.get_input_type(), "nor", "Normal created");

        tester.create_truncated_normal_field();
        assertEqual(tester.get_input_type(), "tnor", "Truncated normal created");

        tester.create_lognormal_field();
        assertEqual(tester.get_input_type(), "log", "Lognormal created");

        tester.create_truncated_lognormal_field();
        assertEqual(tester.get_input_type(), "tlog", "Truncated lognormal created");

        tester.create_beta_field();
        assertEqual(tester.get_input_type(), "beta", "Beta created");
    }

    function test_30_set_nominal_value() {
        log("Test: Set nominal value");
        tester.create_deterministic_field();
        tester.set_subparam("value", "75.5");

        let val = parseFloat(tester.get_field_value());
        assert(Math.abs(val - 75.5) < 0.1, "Nominal value updated to 75.5 (got: " + val + ")");
    }

    function test_31_set_distribution_parameters() {
        log("Test: Set distribution parameters");
        tester.create_truncated_normal_field();
        tester.clear_validation_events();

        tester.set_subparam("mean", "55");
        tester.set_subparam("std", "8");
        tester.set_subparam("lower", "35");
        tester.set_subparam("upper", "75");

        assert(tester.get_validation_event_count() > 0, "Parameters updated (events recorded)");
    }

    function test_40_rapid_field_creation() {
        log("Test: Rapid field creation");

        tester.create_deterministic_field();
        tester.create_uniform_field();
        tester.create_normal_field();
        tester.create_truncated_lognormal_field();
        tester.create_beta_field();
        tester.create_deterministic_field();

        assertEqual(tester.get_input_type(), "det", "Final distribution is deterministic");
    }

    function test_41_boundary_values() {
        log("Test: Boundary values");
        tester.create_deterministic_field();  // min=0, max=100
        tester.clear_validation_events();

        tester.set_subparam("value", "0");
        tester.set_subparam("value", "100");

        let errorCount = 0;
        for (let i = 0; i < tester.get_validation_event_count(); i++) {
            if (tester.get_validation_event_status(i) === 0) {
                errorCount++;
            }
        }
        assert(errorCount === 0, "Boundary values are valid (no errors)");
    }
}
