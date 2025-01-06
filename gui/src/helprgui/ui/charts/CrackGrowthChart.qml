/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import "Chart.js" as Chart

Rectangle {
    property var plotData;
    enabled: plotData !== null && plotData !== undefined
    visible: plotData !== null && plotData !== undefined
    color: "white"
    height: plotH
    width: plotSmW

    Chart {
        chartType: 'scatter'
        animationDuration: plotAnimDuration
        height: plotH
        width: plotSmW

        chartData: {
            return {
                datasets: [{
                    label: 'a/t',
                    showLine: true,
                    radius: 1,
                    pointRadius: 1,
                    pointHoverRadius: 1,
                    data: plotData ? plotData['a_t'] : [],
                    pointStyle: "line",
                    borderColor: 'rgb(92,153,213)',
                    fill: false,
                    backgroundColor: 'rgba(0, 0, 0, 1)',  // for legend
                }, {
                    label: 'Cycles to a(crit)',
                    data: plotData ? plotData['acrit_pt'] : [],
                    pointStyle: "rectRot",
                    pointBackgroundColor: 'rgb(7,23,0)',
                    pointHoverBackgroundColor: 'rgb(7,23,0)',
                    fill: true,
                    backgroundColor: 'rgba(0, 0, 0, 1)',
                    pointRadius: 8,
                    radius: 8,
                    pointHoverRadius: 8
                }, {
                    label: 'Cycles at 25% a(crit)',
                    data: plotData ? plotData['25acrit_pt'] : [],
                    pointStyle: "circle",
                    pointBackgroundColor: 'rgb(145,0,0)',
                    pointHoverBackgroundColor: 'rgb(145,0,0)',
                    pointRadius: 8,
                    radius: 8,
                    pointHoverRadius: 8,
                    fill: false,
                    backgroundColor: 'rgba(0, 0, 0, 1)',
                }, {
                    label: 'Half of a(crit) cycles',
                    data: plotData ? plotData['half_pt'] : [],
                    pointStyle: "rect",
                    pointBackgroundColor: 'rgb(0,49,217)',
                    pointHoverBackgroundColor: 'rgb(0,49,217)',
                    backgroundColor: 'rgb(0,49,217)',
                    pointRadius: 8,
                    radius: 8,
                    pointHoverRadius: 8,
                    fill: false,
                    backgroundColor: 'rgba(0, 0, 0, 1)',
                },]
            };
        }
        chartOptions: {
            return {
                maintainAspectRatio: true,
                responsive: true,
                tooltips: {
                    // i.e. vertical cursor showing nearest pt
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false,  // if true, only applies if mouse intersects position
                    callbacks: {
                        label: function(item, data) { return getDataLabel(item, data, 0, 3); }
                    }
                },
                legend: {
                    position: 'chartArea',
                    labels: {
                        fontSize: 16,
                        fontColor: "#000",
                        usePointStyle: true
                    }
                },
                scales: {
                    xAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                            callback: function(value, index, ticks) {
                                if (value > 1e4) {
                                    return value.toExponential(1);
                                }
                                else {
                                    return parseInt(value);
                                }
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Total Cycles',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                            min: 0,
                            max: 0.8
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'a/t',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }

        MouseArea {
            anchors.fill: parent
            onClicked: { }
        }
    }
}
