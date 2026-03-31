/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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
            return {
                datasets: [{
                    label: 'FAD Equation',
                    fill: false,
                    showLine: true,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    data: plotData ? plotData['ln1'] : [],
                    pointStyle: "line",
                    borderColor: 'black'
                }, {
                    label: 'Crack Evolution',
                    fill: false,
                    showLine: true,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    data: plotData ? plotData['evolution'] : [],
                    pointStyle: "line",
                    borderColor: 'purple',
                    borderDash: [5, 3]
                }, {
                    label: 'Beyond Plot',
                    data: plotData ? plotData['beyond_pt'] : [],
                    pointStyle: "triangle",
                    pointBackgroundColor: 'rgba(0,0,0,0)',
                    backgroundColor: 'rgba(0,0,0,0)',
                    pointBorderColor: 'black',
                    borderColor: 'black',
                    borderWidth: 2,
                    pointRadius: 7,
                    radius: 7,
                    pointHoverRadius: 7
                }, {
                    label: 'FAD Intersection',
                    data: plotData ? plotData['pt1'] : [],
                    pointStyle: "rect",
                    pointBackgroundColor: 'green',
                    backgroundColor: 'green',
                    pointRadius: 6,
                    radius: 6,
                    pointHoverRadius: 6
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
                    position: 'chartArea',
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
                            min: 0,
                            max: 1.5
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
                            min: 0,
                            max: 1.01
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
