/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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
    width: plotW

    function addQoiScatter(result, subsets, nominalPt, color, nomColor, label) {
        // Nominal point
        if (nominalPt && nominalPt.length > 0) {
            result['datasets'].push({
                label: label + " Nominal",
                fill: true,
                pointRadius: 5,
                radius: 5,
                pointHoverRadius: 5,
                data: nominalPt,
                pointStyle: "star",
                pointBackgroundColor: nomColor,
                backgroundColor: nomColor,
                borderWidth: 1
            });
        }

        // Sample subsets
        if (subsets) {
            for (let i = 0; i < subsets.length; i++) {
                let setLabel = label + (subsets.length === 1 ? "" : " set " + (i+1));
                result['datasets'].push({
                    label: setLabel,
                    fill: true,
                    pointRadius: 3,
                    radius: 3,
                    pointHoverRadius: 3,
                    pointStyle: "circle",
                    data: subsets[i],
                    pointBackgroundColor: color,
                    backgroundColor: color,
                    borderWidth: 0
                });
            }
        }
    }

    Chart {
        chartType: 'scatter'
        animationDuration: plotAnimDuration
        height: plotH
        width: plotW

        chartData: {
            var result = {'datasets': []};
            if (plotData)
            {
                addQoiScatter(result,
                              plotData['subsets_acrit'], plotData['nominal_pt_acrit'],
                              'rgba(0, 0, 0, 0.5)', 'red', 'Cycles to a(crit)');
                addQoiScatter(result,
                              plotData['subsets_fad'], plotData['nominal_pt_fad'],
                              'rgba(0, 128, 0, 0.5)', 'darkgreen', 'Cycles to FAD line');
            }
            return result;
        }
        chartOptions: {
            return {
                maintainAspectRatio: true,
                responsive: true,
                intersect: true,
                tooltips: {
                    enabled: true,
                    mode: 'point',
                    callbacks: {
                        label: function(item, data) { return getDataLabel(item, data, 1, 3); }
                    }
                },
                hover: { mode: 'point' },
                legend: {
                    position: 'bottom',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
                        usePointStyle: true,
                        filter: function(item, chart) {
                            return item.text.includes('Nominal') ||
                                   item.text === 'Cycles to a(crit)' ||
                                   item.text === 'Cycles to FAD line';
                        }
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
                            labelString: 'Cycles to a(crit)',
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
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'a(crit)/t',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }
    }
}
