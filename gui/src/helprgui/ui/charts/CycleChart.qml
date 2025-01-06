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
                    fill: true,
                    pointRadius: 5,
                    radius: 5,
                    pointHoverRadius: 5,
                    data: plotData['nominal_pt'],
                    pointStyle: "circle",
                    pointBackgroundColor: "red",
                    backgroundColor: "red",
                    borderWidth: 1
                };
                result['datasets'].push(data);

                let lineData = plotData['subsets'];
                for (let i = 0; i < lineData.length; i++)
                {
                    let label = (lineData.length === 1) ? "sample set" : "set " + (i+1);
                    let clr = randomColor(1);
                    let ln = lineData[i];
                    let data = {
                        label: label,
                        fill: true,
                        pointRadius: 3,
                        radius: 3,
                        pointHoverRadius: 3,
                        pointStyle: "circle",
                        data: ln,
                        pointBackgroundColor: clr,
                        backgroundColor: clr,
                        borderWidth: 0
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
                        label: function(item, data) { return getDataLabel(item, data, 1, 3); }
                    }
                },
                hover: { mode: 'point' },
                legend: {
                    position: 'right',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
                        usePointStyle: true,
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
