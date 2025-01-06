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

    function getLogTicks (chartObj) {
        // Replace ticks with pretty log values, up to max.
        const maxVal = chartObj.ticks.pop();
        const ticks = [1, 10, 100, 1000, 10000, 100000, 1e6, 1e7, 1e8, 1e9, 1e10];
        chartObj.ticks.splice(0, chartObj.ticks.length);
        for(let i=0; i<ticks.length; i++)
        {
            if (ticks[i] > maxVal) break;
            chartObj.ticks.push(ticks[i]);
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
                let data = {
                    label: "Cycles to a(crit)",
                    fill: true,
                    pointRadius: 3,
                    radius: 3,
                    pointHoverRadius: 3,
                    data: plotData['pts'],
                    pointStyle: "circle",
                    pointBackgroundColor: "black",
                    backgroundColor: "black",
                    borderWidth: 3
                };
                result['datasets'].push(data);

                let lineData = plotData['lines'];
                for (let i = 0; i < lineData.length; i++)
                {
                    let data = {
                        label: "curve " + (i+1),
                        fill: false,
                        showLine: true,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        data: lineData[i],
                        pointStyle: "line",
                        borderColor: randomColor(0.5),
                    };
                    result['datasets'].push(data);
                }
            }
            return result;
        }
        chartOptions: {
            return {
                // maintainAspectRatio: true,
                responsive: true,
                // intersect: true,
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
                        usePointStyle: true,
                        filter: function(item, chart) {
                            return !item.text.includes('curve');
                        }
                    }
                },
                scales: {
                    xAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                            min: 1,
                            callback: function(value, index, values) {
                                return Utils.convertValueToSuperscriptString(value);
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Total cycles',
                            fontSize: 18,
                            fontColor: "#000"
                        },
                        type: "logarithmic",
                        afterBuildTicks: getLogTicks,
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
    }
}
