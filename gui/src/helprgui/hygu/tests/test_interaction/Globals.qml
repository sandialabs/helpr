/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 *
 * Singleton containing global properties for QML components.
 * These properties mirror those in HELPR's main.qml that UI components depend on.
 *
 * Usage:
 *   import "."  // Import current directory to access singleton
 *   Text { color: Globals.color_primary }
 */
pragma Singleton
import QtQuick
import QtQuick.Controls.Material 2.12

QtObject {
    // ==================== Colors ====================
    readonly property string color_primary: "#020202"
    readonly property color color_danger: Material.color(Material.Red)
    readonly property color color_danger_bg: Material.color(Material.Red, Material.Shade100)
    readonly property color color_info: Material.color(Material.Blue)
    readonly property color color_warning: Material.color(Material.Orange)
    readonly property string color_text_danger: Material.color(Material.Red)
    readonly property string color_text_warning: Material.color(Material.Orange)

    // Status-indexed color arrays (0=error, 1=good, 2=info, 3=warning)
    readonly property var color_text_levels: [
        Material.color(Material.Red),
        color_primary,
        Material.color(Material.Blue),
        Material.color(Material.Orange)
    ]
    readonly property var color_levels: [
        Material.color(Material.Red, Material.Shade100),
        "transparent",
        Material.color(Material.Blue, Material.Shade100),
        Material.color(Material.Orange, Material.Shade100)
    ]

    // ==================== Font Sizes ====================
    readonly property int labelFontSize: 13
    readonly property int inputTopLabelFontSize: 11

    // ==================== Layout Widths ====================
    readonly property int paramLabelWidth: 120
    readonly property int shortInputW: 70
    readonly property int medInputW: 105
    readonly property int longInputW: 200
    readonly property int defaultSelectorW: 130
    readonly property int defaultInputW: medInputW
    readonly property int uncertaintyInputW: medInputW
    readonly property int distributionInputW: defaultSelectorW
}
