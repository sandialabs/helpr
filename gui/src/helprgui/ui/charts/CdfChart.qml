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

    function addQoiDatasets(result, plotData, key, nominalKey, color, label) {
        // Nominal dashed line
        if (plotData[nominalKey] && plotData[nominalKey].length > 0) {
            result['datasets'].push({
                label: label + " Nominal",
                fill: false,
                showLine: true,
                lineTension: 0,
                borderDash: [20, 5],
                data: plotData[nominalKey][0],
                pointRadius: 0,
                pointHoverRadius: 0,
                pointBackgroundColor: color,
                backgroundColor: color,
                borderColor: color,
                pointStyle: "line"
            });
        }

        // CDF sample lines
        let lineData = plotData[key];
        if (lineData) {
            // Legend entry for this QoI group
            if (lineData.length > 0) {
                result['datasets'].push({
                    label: label,
                    showLine: true,
                    data: lineData[0],
                    borderColor: color,
                    backgroundColor: color,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    pointStyle: "line",
                    fill: false,
                });
            }
            for (let i = 1; i < lineData.length; i++) {
                result['datasets'].push({
                    label: label + " " + (i + 1),
                    showLine: true,
                    data: lineData[i],
                    borderColor: color,
                    backgroundColor: color,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    pointStyle: "line",
                    fill: false,
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
                addQoiDatasets(result, plotData,
                               'acrit_lines', 'acrit_nominal',
                               'black', 'Cycles to a(crit)');
                addQoiDatasets(result, plotData,
                               'fad_lines', 'fad_nominal',
                               'green', 'Cycles to FAD line');
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
                        label: function(item, data) { return getDataLabel(item, data, 0, 3); }
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
                            // Show only the first line and nominal for each QoI
                            let lbl = item.text;
                            return lbl === 'Cycles to a(crit)' ||
                                   lbl === 'Cycles to FAD line' ||
                                   lbl.includes('Nominal');
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
                            labelString: 'Cycles to Criteria [#]',
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
                            min: 0,
                            max: 1.0
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Cumulative Probability',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }
    }
}
