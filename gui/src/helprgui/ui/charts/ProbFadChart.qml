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
                    pointRadius: 4,
                    radius: 4,
                    pointHoverRadius: 3,
                    data: plotData['nominal_pt'],
                    pointStyle: "circle",
                    pointBackgroundColor: "red",
                    backgroundColor: "red",
                    borderWidth: 1
                };
                result['datasets'].push(data);

                let ptData = plotData['pts'];
                for (let i = 0; i < ptData.length; i++)
                {
                    let ln = ptData[i];
                    let data = {
                        label: "set " + (i+1),
                        fill: true,
                        pointRadius: 3,
                        radius: 3,
                        pointHoverRadius: 3,
                        pointStyle: "circle",
                        data: ln,
                        pointBackgroundColor: "lightblue",
                        backgroundColor: "lightblue",
                        borderWidth: 0
                    };
                    result['datasets'].push(data);
                }
                let lnData = {
                    label: 'line',
                    showLine: true,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    data: plotData['line'][0],
                    pointStyle: "line",
                    borderColor: 'black',
                    fill: false,
                    // backgroundColor: 'rgba(0, 0, 0, 1)',  // for legend
                }
                result['datasets'].push(lnData);
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
                        label: function(item, data) { return getDataLabel(item, data, 3, 3); }
                    }
                },
                hover: { mode: 'point' },
                legend: {
                    position: 'right',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
                        usePointStyle: true,
                        filter: function(item, chart) { return item.text.includes('nominal'); }
                    }
                },
                scales: {
                    xAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Lᵣ (load ratio)',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Kᵣ (toughness ratio)',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }
    }
}
