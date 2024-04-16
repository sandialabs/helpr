/*
 * Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "../components"
import helprgui.classes


Item {
    property UncertainFormField param;
    property string tipText;
    property bool hasError: false
    property string errorMsg: "test long error msg ERROR HERE"
    property bool isReadOnly: false

    id: paramContainer

    Component.onCompleted:
    {
        refresh();
    }

    function refresh()
    {
        if (hasError)
        {
            paramContainer.Layout.preferredHeight = 80;
            paramLabel.color = color_danger;
            alertMsg.text = errorMsg;
            alertDisplay.visible = true;
        }
        else
        {
            paramContainer.Layout.preferredHeight = 40;
            paramLabel.color = color_primary;
            alertMsg.text = "";
            alertDisplay.visible = false;
        }

        valueLabel.visible = false;
        valueInput.visible = false;

        uncertaintyLabel.visible = false;
        uncertaintySelector.visible = false;
        nominalLabel.visible = false;
        nominalInput.visible = false;
        meanLabel.visible = false;
        meanInput.visible = false;
        devLabel.visible = false;
        devInput.visible = false;
        lowerBoundLabel.visible = false;
        lowerBoundInput.visible = false;
        upperBoundLabel.visible = false;
        upperBoundInput.visible = false;

        unitSelector.currentIndex = param.get_unit_index();


        if (isReadOnly)
        {
            valueLabel.visible = true;
            valueLabel.text.font.italic = true;
            valueInput.visible = true;

            valueInput.text = param.value;
            inputTypeSelector.visible = false;
            valueInput.readOnly = true;
            return;
        }

        let inputType = param.input_type;
        inputTypeSelector.currentIndex = param.get_input_type_index();


        if (inputType === 'det')
        {
            valueLabel.visible = true;
            valueInput.visible = true;
            valueInput.text = param.value;

        } else if (inputType === 'nor' || inputType === 'log') {
            uncertaintyLabel.visible = true;
            uncertaintySelector.visible = true;
            nominalLabel.visible = true;
            nominalInput.visible = true;
            meanLabel.visible = true;
            meanInput.visible = true;
            devLabel.visible = true;
            devInput.visible = true;

            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = param.value;
            meanInput.text = param.a;
            devInput.text = param.b;

        } else if (inputType === 'uni') {
            uncertaintyLabel.visible = true;
            uncertaintySelector.visible = true;
            nominalLabel.visible = true;
            nominalInput.visible = true;
            lowerBoundLabel.visible = true;
            lowerBoundInput.visible = true;
            upperBoundLabel.visible = true;
            upperBoundInput.visible = true;

            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = param.value;
            lowerBoundInput.text = param.a;
            upperBoundInput.text = param.b;
        }

        valueInput.refreshLims();
        nominalInput.refreshLims();
        meanInput.refreshLims();
        devInput.refreshLims();
        lowerBoundInput.refreshLims();
        upperBoundInput.refreshLims();
    }


    Row
    {
        id: paramInputRow

        Component.onCompleted:
        {
            refresh();
        }

        GridLayout {
            id: paramGrid
            rows: 2
            columns: 7
            flow: GridLayout.TopToBottom

            Connections {
                target: param
                function onInputTypeChanged() { refresh(); }
                function onModelChanged() { refresh(); }
                function onUncertaintyChanged() { refresh(); }
                function onUnitChanged() { refresh(); }
            }

            Item { }
            Text {
                id: paramLabel
                text: param?.label_rtf ?? ''
                Layout.preferredWidth: paramLabelWidth
                horizontalAlignment: Text.AlignRight
                font.pointSize: labelFontSize
                textFormat: Text.RichText

                ToolTip {
                    delay: 200
                    timeout: 3000
                    visible: tipText ? ma.containsMouse : false
                    text: tipText
                }

                // for tooltip hover
                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                }

            }

            Item {
                id: unitLabel
            }
            DenseComboBox {
                id: unitSelector
                model: param?.unit_choices ?? null
                currentIndex: param?.get_unit_index() ?? 0
                onActivated: {
                    if (param !== null) param.unit = displayText
                }

            }

            InputTopLabel {
                id: inputTypeLabel
                text: ""
            }

            DenseComboBox {
                id: inputTypeSelector
                textRole: "text"
                valueRole: "value"
                model: ListModel {
                    ListElement { value: "det"; text: "Deterministic" }
                    ListElement { value: "nor"; text: "Normal" }
                    ListElement { value: "log"; text: "Lognormal" }
                    ListElement { value: "uni"; text: "Uniform" }
                }
                currentIndex: param.get_input_type_index()
                onActivated: param.input_type = currentValue
            }

            InputTopLabel {
                id: valueLabel
                text: ""
            }
            DoubleTextField {
                id: valueInput
                field: 'value'
            }

            InputTopLabel {
                id: nominalLabel
                text: "Nominal value"
                visible: false
            }
            DoubleTextField {
                id: nominalInput
                field: 'value'
            }

            InputTopLabel {
                id: uncertaintyLabel
                text: "Uncertainty"
            }
            DenseComboBox {
                id: uncertaintySelector
                visible: false
                Layout.maximumWidth: 100
                textRole: "text"
                valueRole: "value"
                model: ListModel {
                    ListElement { value: "ale"; text: "Aleatory" }
                    ListElement { value: "epi"; text: "Epistemic" }
                }
                currentIndex: param?.get_uncertainty_index() ?? 0
                onActivated: {
                    if (param !== null) param.uncertainty = currentValue;
                }
            }

            InputTopLabel {
                id: meanLabel
                text: "Mean"
            }
            DoubleTextField {
                id: meanInput
                field: 'a'
            }

            InputTopLabel {
                id: lowerBoundLabel
                text: "Lower bound"
            }
            DoubleTextField {
                id: lowerBoundInput
                field: 'a'
            }

            InputTopLabel {
                id: devLabel
                text: "Std deviation"
            }
            DoubleTextField {
                id: devInput
                field: 'b'
                useLimits: false
            }

            InputTopLabel {
                id: upperBoundLabel
                text: "Upper bound"
            }
            DoubleTextField {
                id: upperBoundInput
                field: 'b'
            }
        }
    }

    Row
    {
        id: alertDisplay
        anchors.top: paramInputRow.bottom
        leftPadding: 125

        AppIcon {
            id: alertIcon
            source: 'circle-exclamation-solid'
            iconColor: Material.color(Material.Red)
            width: 24
            height: 24
        }
        Text {
            id: alertMsg
            text: ""
            anchors.topMargin: 4
            font.italic: true
            anchors.verticalCenter: parent.verticalCenter
            color: color_danger
        }
    }
}
