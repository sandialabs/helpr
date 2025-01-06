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
                    label: 'load ratio',
                    fill: false,
                    showLine: true,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    data: plotData ? plotData['ln1'] : [],
                    pointStyle: "line",
                    borderColor: 'rgb(92,153,213)'
                }, {
                    label: 'point',
                    data: plotData ? plotData['pt1'] : [],
                    pointStyle: "circle",
                    pointBackgroundColor: 'rgb(7,23,0)',
                    backgroundColor: 'rgb(7,23,0)',
                    pointRadius: 8,
                    radius: 8,
                    pointHoverRadius: 8
                }]
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
                        label: function(item, data) { return getDataLabel(item, data, 3, 3); }
                    }
                },
                legend: {
                    display: false
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
                            fontColor: "#000"
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
