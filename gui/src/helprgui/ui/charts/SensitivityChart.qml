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
    width: 650

    Chart {
        chartType: 'scatter'
        animationDuration: plotAnimDuration
        height: plotH
        width: plotW

        chartData: {
            var result = {'datasets': []};
            if (plotData)
            {
                for (let i = 0; i < plotData.length; i++)
                {
                    let color = randomColor(0.9);
                    let data = {
                        label: plotData[i].label,
                        showLine: true,
                        data: plotData[i].data,
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
                responsive: true,
                intersect: true,
                tooltips: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(item, data) { return getDataLabel(item, data, 0, 1); }
                    }
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                },
                legend: {
                    position: 'right',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
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
                            labelString: '% of Nominal Value',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }
    }
}
