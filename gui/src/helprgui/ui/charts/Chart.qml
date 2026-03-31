/*!
 * Elypson's Chart.qml adaptor to Chart.js
 * (c) 2020 ChartJs2QML contributors (starting with Elypson, Michael A. Voelkel, https://github.com/Elypson)
 * Released under the MIT License
 */

import QtQuick 2.13
import "Chart.js" as Chart

Canvas {
    id: root

    property var jsChart: undefined
    property string chartType
    property var chartData
    property var chartOptions
    property double chartAnimationProgress: 0.1
    property var animationEasingType: Easing.InOutExpo
    property double animationDuration: 500
    property var memorizedContext
    property var memorizedData
    property var memorizedOptions
    property alias animationRunning: chartAnimator.running

    signal animationFinished()

    // Check if context is valid before operations
    function hasValidContext() {
        var ctx = root.getContext('2d');
        return ctx !== null && root.visible && root.width > 0 && root.height > 0;
    }

    function animateToNewData()
    {
        if (!hasValidContext() || !jsChart) {
            return;
        }
        chartAnimationProgress = 0.1;
        jsChart.update();
        chartAnimator.restart();
    }

    MouseArea {
        id: event
        anchors.fill: root
        hoverEnabled: true
        enabled: true
        property var handler: undefined

        property QtObject mouseEvent: QtObject {
            property int left: 0
            property int top: 0
            property int x: 0
            property int y: 0
            property int clientX: 0
            property int clientY: 0
            property string type: ""
            property var target
        }

        function submitEvent(mouse, type) {
            mouseEvent.type = type
            mouseEvent.clientX = mouse ? mouse.x : 0;
            mouseEvent.clientY = mouse ? mouse.y : 0;
            mouseEvent.x = mouse ? mouse.x : 0;
            mouseEvent.y = mouse ? mouse.y : 0;
            mouseEvent.left = 0;
            mouseEvent.top = 0;
            mouseEvent.target = root;

            if(handler) {
                handler(mouseEvent);
            }

            if (root.hasValidContext()) {
                root.requestPaint();
            }
        }

        onClicked: function(mouse) {
            submitEvent(mouse, "click");
        }
        onPositionChanged: function(mouse) {
            submitEvent(mouse, "mousemove");
        }
        onExited: {
            submitEvent(undefined, "mouseout");
        }
        onEntered: {
            submitEvent(undefined, "mouseenter");
        }
        onPressed: function(mouse) {
            submitEvent(mouse, "mousedown");
        }
        onReleased: function(mouse) {
            submitEvent(mouse, "mouseup");
        }
    }

    PropertyAnimation {
        id: chartAnimator
        target: root
        property: "chartAnimationProgress"
        alwaysRunToEnd: false  // Changed to false so we can stop it when hidden
        to: 1
        duration: root.animationDuration
        easing.type: root.animationEasingType
        onFinished: {
            root.animationFinished();
        }
    }

    onChartAnimationProgressChanged: {
        if (hasValidContext()) {
            root.requestPaint();
        }
    }

    onVisibleChanged: {
        // Stop animations when becoming invisible to prevent errors
        if (!visible) {
            chartAnimator.stop();
        }
    }

    onPaint: {
        var ctx = root.getContext('2d');

        // Guard against invalid context (can happen when component is hidden/destroyed)
        if (ctx === null || !visible) {
            return;
        }

        if(memorizedContext != ctx || memorizedData != root.chartData || memorizedOptions != root.chartOptions) {
            jsChart = new Chart.build(ctx, {
                type: root.chartType,
                data: root.chartData,
                options: root.chartOptions
                });

            memorizedData = root.chartData;
            memorizedContext = ctx;
            memorizedOptions = root.chartOptions;

            root.jsChart.bindEvents(function(newHandler) {event.handler = newHandler;});

            chartAnimator.start();
        }

        if (jsChart) {
            jsChart.draw(chartAnimationProgress);
        }
    }

    onWidthChanged: {
        if(jsChart && hasValidContext()) {
            jsChart.resize();
        }
    }

    onHeightChanged: {
        if(jsChart && hasValidContext()) {
            jsChart.resize();
        }
    }
}