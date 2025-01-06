/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import "Chart.js" as Chart
import "../../hygu/ui/utils.js" as Utils


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
                    label: 'Design curve',
                    fill: false,
                    showLine: true,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    data: plotData ? plotData['ln1'] : [],
                    pointStyle: "line",
                    borderColor: 'rgb(231,64,88)'
                }, {
                    label: 'Exercised rates',
                    fill: false,
                    showLine: true,
                    pointRadius: 4,
                    radius: 4,
                    pointHoverRadius: 4,
                    data: plotData ? plotData['ln2'] : [],
                    pointStyle: "line",
                    borderColor: 'rgb(0,0,0)',
                    borderWidth: 7
                },]
            };
        }
        chartOptions: {
            return {
                maintainAspectRatio: true,
                responsive: true,
                tooltips: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false,
                    callbacks: {
                        label: function(item, data) { return getDataLabelExp(item, data, 2, 2); }
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
                            callback: function(value, index, values) {
                                return Utils.convertValueToSuperscriptString(value);
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'ΔK (MPa m¹⸍²)',
                            fontSize: 18,
                            fontColor: "#000"
                        },
                        type: "logarithmic",
                        afterBuildTicks: Utils.getLogTicks,
                    }],
                    yAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                            callback: function(value, index, values) {
                                return Utils.convertValueToSuperscriptString(value);
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'da/dN (m/cycles)',
                            fontSize: 18,
                            fontColor: "#000"
                        },
                        type: "logarithmic",
                        afterBuildTicks: Utils.getLogYAxisTicks,
                    }]
                }
            };
        }
    }
}
