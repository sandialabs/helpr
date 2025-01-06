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
    width: plotW

    Chart {
        chartType: 'scatter'
        animationDuration: plotAnimDuration
        height: plotH
        width: plotW

        chartData: {
            var result = {'datasets': []};
            if (plotData)
            {
                let data = {
                    label: "nominal",
                    fill: false,
                    showLine: true,
                    lineTension: 0,
                    borderDash: [20, 5],
                    data: plotData["nominal"][0],
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    pointBackgroundColor: "red",
                    backgroundColor: "red",
                    borderColor: 'red',
                    pointStyle: "line"
                };
                result['datasets'].push(data);

                let lineData = plotData['lines'];
                for (let i = 0; i < lineData.length; i++)
                {
                    let label = (lineData.length === 1) ? "sample line" : "line " + (i+1);
                    let color = randomColor(0.9);
                    let data = {
                        label: label,
                        showLine: true,
                        data: lineData[i],
                        borderColor: color,
                        backgroundColor: color,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        pointStyle: "line",
                        fill: false,
                    };
                    result['datasets'].push(data);
                }

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
                    position: 'right',
                    labels: {
                        fontSize: 14,
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
