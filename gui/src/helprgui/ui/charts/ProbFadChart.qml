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
            var result = {'datasets': []};
            if (plotData)
            {
                let lineData = plotData['line'];
                if (lineData) {
                    // First line is the FAD boundary equation
                    if (lineData.length > 0) {
                        result['datasets'].push({
                            label: 'FAD Equation',
                            showLine: true,
                            pointRadius: 0,
                            pointHoverRadius: 0,
                            data: lineData[0],
                            pointStyle: "line",
                            borderColor: 'black',
                            fill: false,
                        });
                    }
                    // Remaining lines are sample crack evolution trajectories
                    for (let i = 1; i < lineData.length; i++) {
                        result['datasets'].push({
                            label: 'Crack Evolution ' + i,
                            showLine: true,
                            pointRadius: 0,
                            pointHoverRadius: 0,
                            data: lineData[i],
                            pointStyle: "line",
                            borderColor: 'purple',
                            borderDash: [5, 3],
                            fill: false,
                        });
                    }
                }

                // Nominal trajectory line (red dotted)
                if (plotData['nominal_line'] && plotData['nominal_line'].length > 0) {
                    result['datasets'].push({
                        label: 'Nominal',
                        showLine: true,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        data: plotData['nominal_line'],
                        pointStyle: "line",
                        borderColor: 'red',
                        borderDash: [3, 3],
                        fill: false,
                    });
                } else if (plotData['nominal_pt'] && plotData['nominal_pt'].length > 0) {
                    // Fallback: show nominal as a single point
                    result['datasets'].push({
                        label: 'Nominal',
                        fill: true,
                        pointRadius: 4,
                        radius: 4,
                        pointHoverRadius: 3,
                        data: plotData['nominal_pt'],
                        pointStyle: "circle",
                        pointBackgroundColor: "red",
                        backgroundColor: "red",
                        borderWidth: 1
                    });
                }

                // FAD intersection points (green squares)
                result['datasets'].push({
                    label: "FAD Intersection",
                    fill: true,
                    pointRadius: 3,
                    radius: 3,
                    pointHoverRadius: 3,
                    pointStyle: "rect",
                    data: plotData['pts'],
                    pointBackgroundColor: "green",
                    backgroundColor: "green",
                    borderWidth: 0
                });
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
                    position: 'bottom',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
                        usePointStyle: true,
                        filter: function(item, chart) {
                            return item.text === 'Nominal' ||
                                   item.text === 'FAD Equation' ||
                                   item.text === 'FAD Intersection' ||
                                   item.text === 'Crack Evolution 1';
                        }
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
