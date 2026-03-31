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

    function addQoiHistograms(result, bins, nominalVal, color, nomColor, label) {
        // Histogram step lines (added first to determine max Y for nominal line)
        var maxY = 0;
        if (bins) {
            for (let i = 0; i < bins.length; i++) {
                let setLabel = label + (bins.length === 1 ? "" : " " + (i+1));
                for (let j = 0; j < bins[i].length; j++) {
                    if (bins[i][j].y > maxY) maxY = bins[i][j].y;
                }
                result['datasets'].push({
                    label: setLabel,
                    showLine: true,
                    lineTension: 0,
                    data: bins[i],
                    borderColor: color,
                    backgroundColor: color,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    pointStyle: "line",
                    fill: false,
                });
            }
        }

        // Nominal vertical line (scaled to histogram max)
        if (nominalVal && nominalVal !== 0 && maxY > 0) {
            result['datasets'].push({
                label: label + " Nominal",
                fill: false,
                showLine: true,
                lineTension: 0,
                borderDash: [20, 5],
                data: [{x: nominalVal, y: 0}, {x: nominalVal, y: maxY * 1.1}],
                pointRadius: 0,
                pointHoverRadius: 0,
                pointBackgroundColor: nomColor,
                backgroundColor: nomColor,
                borderColor: nomColor,
                pointStyle: "line"
            });
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
                addQoiHistograms(result,
                                 plotData['acrit_bins'], plotData['acrit_nominal'],
                                 'black', 'red', 'Cycles to a(crit)');
                addQoiHistograms(result,
                                 plotData['fad_bins'], plotData['fad_nominal'],
                                 'green', 'darkgreen', 'Cycles to FAD line');
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
                    callbacks: {
                        label: function(item, data) { return getDataLabel(item, data, 3, 0); }
                    }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        fontSize: 14,
                        fontColor: "#000",
                        usePointStyle: true,
                        filter: function(item, chart) {
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
                            fontSize: 18,
                            fontColor: "#000",
                            callback: function(value, index, values) {
                                return '10' + Utils.numToSuperscript(value);
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Cycles to Criteria',
                            fontSize: 18,
                            fontColor: "#000"
                        },
                    }],
                    yAxes: [{
                        ticks: {
                            fontSize: 16,
                            fontColor: "#000",
                            min: 0
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Frequency',
                            fontSize: 18,
                            fontColor: "#000"
                        }
                    }]
                }
            };
        }
    }
}
