/*
 * Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 * Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
 * You should have received a copy of the BSD License along with HELPR.
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Controls.Material 2.12

import "../components"
import "../utils.js" as Utils

import hygu.classes


Item {
    id: paramContainer

    property UncertainFormField param;
    property alias labelRef: paramLabel
    property string tipText;
    property bool isReadOnly: false
    property bool hasError: false
    property bool showUnits: true
    property string errorMsg: ""

    // must match backend string values from distributions.DistributionParam. Note that the property names can't be uppercased!
    property string param_nominal: "nominal"
    property string param_mean: "mean"
    property string param_std: "std"
    property string param_mu: "mu"
    property string param_sigma: "sigma"
    property string param_lower: "lower"
    property string param_upper: "upper"
    // Beta distribution
    property string param_alpha: "alpha"
    property string param_beta: "beta"

    property string distr_det: "det"
    property string distr_uniform: "uni"
    property string distr_normal: "nor"
    property string distr_lognormal: "log"
    property string distr_beta: "beta"
    property string distr_trunc_normal: "tnor"
    property string distr_trunc_lognormal: "tlog"

    // track sub-parameter error states
    property var subparamErrorStates: ({
        param_nominal: { status: 1, message: "" },
        param_mean: { status: 1, message: "" },
        param_std: { status: 1, message: "" },
        param_mu: { status: 1, message: "" },
        param_sigma: { status: 1, message: "" },
        param_lower: { status: 1, message: "" },
        param_upper: { status: 1, message: "" },
        param_alpha: { status: 1, message: "" },
        param_beta: { status: 1, message: "" }
    })

    Behavior on opacity {NumberAnimation { duration: 100 }}

    Layout.preferredHeight: paramInputRow.height + alertDisplayRow.height;

    Component.onCompleted:
    {
        refresh();

        // Initialize/force validation for all parameters to populate error states
        if (param)
        {
            param.update_all_validation_states();
        }
    }

    // Method to update error for a specific sub-parameter
    function updateSubparamError(paramName, status, message) {
        subparamErrorStates[paramName] = {
            status: status,
            message: message
        };

        // Update overall error state
        updateErrorState();
    }

    // Method to determine overall error state
    function updateErrorState() {
        let hasAnyError = false;
        let errorMessages = [];

        // Check all sub-parameters - status 0 is ERROR
        for (let key in subparamErrorStates)
        {
            let error = subparamErrorStates[key];
            if (error.status === 0 && error.message) {  // status 0 indicates error
                hasAnyError = true;
                errorMessages.push(error.message);
            }
        }

        // Update error properties
        hasError = hasAnyError;
        errorMsg = errorMessages.length > 0 ? errorMessages[0] : "";  // Show first error

        // Refresh UI based on error state
        refresh();
    }

    function refresh()
    {
        // Apply validation states to each input field
        for (let key in subparamErrorStates)
        {
            let error = subparamErrorStates[key];

            if (key === param_nominal && param.use_nominal)
            {
                nominalInput.toggleAlert(error.status, error.message);
                // if (param.input_type === distr_det)
                // {
                //     valueInput.toggleAlert(error.status, error.message);
                // }
                // else
                // {
                // }
            }

            else if (key === param_mean)
            {
                meanInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_std)
            {
                stdInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_mu)
            {
                muInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_sigma)
            {
                sigmaInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_lower)
            {
                lowerBoundInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_upper)
            {
                upperBoundInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_alpha)
            {
                alphaInput.toggleAlert(error.status, error.message);
            }
            else if (key === param_beta)
            {
                betaInput.toggleAlert(error.status, error.message);
            }
        }

        if (hasError)
        {
            // paramContainer.Layout.preferredHeight = 80;
            paramLabel.color = color_danger;
            // alertDisplayRow.visible = true;
        }
        else
        {
            // paramContainer.Layout.preferredHeight = 40;
            paramLabel.color = color_primary;
            // alertDisplayRow.visible = false;
        }

        // valueLabel.visible = false;
        // valueInput.visible = false;

        meanLabel.visible = false;
        meanInput.visible = false;
        stdLabel.visible = false;
        stdInput.visible = false;
        muLabel.visible = false;
        muInput.visible = false;
        sigmaLabel.visible = false;
        sigmaInput.visible = false;
        lowerBoundLabel.visible = false;
        lowerBoundInput.visible = false;
        upperBoundLabel.visible = false;
        upperBoundInput.visible = false;

        alphaLabel.visible = false;
        alphaInput.visible = false;
        betaLabel.visible = false;
        betaInput.visible = false;

        unitSelector.currentIndex = param.get_unit_index();
        unitSelector.visible = showUnits;
        unitLabel.visible = showUnits;

        if (isReadOnly)
        {
            nominalLabel.visible = true;
            nominalLabel.text.font.italic = true;

            nominalInput.visible = true;
            nominalInput.text = Utils.hround(param.value);
            nominalInput.readOnly = true;

            inputTypeSelector.visible = false;
            return;
        }

        let inputType = param.input_type;
        inputTypeSelector.currentIndex = param.get_input_type_index();

        let isProb = inputType !== distr_det;
        // valueLabel.visible = !isProb;
        // valueInput.visible = !isProb;

        uncertaintyLabel.visible = param.show_uncertainty_type;
        uncertaintySelector.visible = param.show_uncertainty_type;

        nominalLabel.visible = param.show_nominal;
        nominalInput.visible = param.show_nominal;

        if (inputType === distr_det)
        {
            // value input only
            nominalInput.text = Utils.hround(param.value);
            nominalInput.tooltipText = param.nominal_tooltip;
            // nominalLabel.visible = false;
        }
        else if (inputType === distr_normal || inputType === distr_trunc_normal)
        {
            // normal distributions use mean and std
            meanLabel.visible = true;
            meanInput.visible = true;
            stdLabel.visible = true;
            stdInput.visible = true;

            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = Utils.hround(param.value);
            nominalInput.tooltipText = param.nominal_tooltip;
            meanInput.text = Utils.hround(param.mean);
            meanInput.tooltipText = param.mean_tooltip;
            stdInput.text = Utils.hround(param.std);
            stdInput.tooltipText = param.std_tooltip;
        }
        else if (inputType === distr_lognormal || inputType === distr_trunc_lognormal)
        {
            // lognormal distributions use mu and sigma
            muLabel.visible = true;
            muInput.visible = true;
            sigmaLabel.visible = true;
            sigmaInput.visible = true;

            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = Utils.hround(param.value);
            nominalInput.tooltipText = param.nominal_tooltip;
            muInput.text = Utils.hround(param.mu);
            muInput.tooltipText = param.mu_tooltip;
            sigmaInput.text = Utils.hround(param.sigma);
            sigmaInput.tooltipText = param.sigma_tooltip;
        }
        else if (inputType === distr_uniform)
        {
            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = Utils.hround(param.value);
            nominalInput.tooltipText = param.nominal_tooltip;
        }
        else if (inputType === distr_beta)
        {
            uncertaintySelector.currentIndex = param.get_uncertainty_index();
            nominalInput.text = Utils.hround(param.value);
            nominalInput.tooltipText = param.nominal_tooltip;

            alphaInput.visible = true;
            alphaLabel.visible = true;
            betaInput.visible = true;
            betaLabel.visible = true;
            alphaInput.text = Utils.hround(param.alpha);
            alphaInput.tooltipText = param.alpha_tooltip;
            betaInput.text = Utils.hround(param.beta);
            betaInput.tooltipText = param.beta_tooltip;
        }

        if (inputType === distr_trunc_lognormal || inputType === distr_trunc_normal || inputType === distr_uniform)
        {
            lowerBoundLabel.visible = true;
            lowerBoundInput.visible = true;
            upperBoundLabel.visible = true;
            upperBoundInput.visible = true;

            lowerBoundInput.text = Utils.hround(param.lower);
            lowerBoundInput.tooltipText = param.lower_tooltip;
            // upperBoundInput.text = param.upper;
            upperBoundInput.refresh();  // nullable
            upperBoundInput.tooltipText = param.upper_tooltip;
        }

        // valueInput.refreshLimits();
        nominalInput.refreshLimits();
        meanInput.refreshLimits();
        stdInput.refreshLimits();
        muInput.refreshLimits();
        sigmaInput.refreshLimits();
        lowerBoundInput.refreshLimits();
        alphaInput.refreshLimits();
        betaInput.refreshLimits();
        // upperBoundInput.refreshLimits();
    }

    Row
    {
        id: paramInputRow
        height: isWindows ? 48 : 48

        Component.onCompleted:
        {
            refresh();
        }

        GridLayout {
            id: paramGrid
            rows: 2
            columns: 10
            flow: GridLayout.TopToBottom
            rowSpacing: isWindows ? 2 : 0

            Connections {
                target: param
                function onInputTypeChanged() { refresh(); }
                function onModelChanged() { refresh(); }
                function onUncertaintyChanged() { refresh(); }
                function onUnitChanged() { refresh(); }

                // Tooltip update connections
                function onNominalTooltipChanged(tooltip) {
                    nominalInput.tooltipText = tooltip;
                    // if (param.input_type === distr_det)
                    // {
                    //     valueInput.tooltipText = tooltip;
                    // }
                }
                function onMeanTooltipChanged(tooltip) {
                    meanInput.tooltipText = tooltip;
                }
                function onStdTooltipChanged(tooltip) { 
                    stdInput.tooltipText = tooltip;
                }
                function onMuTooltipChanged(tooltip) {
                    muInput.tooltipText = tooltip;
                }
                function onSigmaTooltipChanged(tooltip) { 
                    sigmaInput.tooltipText = tooltip;
                }
                function onLowerTooltipChanged(tooltip) {
                    lowerBoundInput.tooltipText = tooltip;
                }
                function onUpperTooltipChanged(tooltip) {
                    upperBoundInput.tooltipText = tooltip;
                }
                function onAlphaTooltipChanged(tooltip) {
                    alphaInput.tooltipText = tooltip;
                }
                function onBetaTooltipChanged(tooltip) {
                    betaInput.tooltipText = tooltip;
                }

                // Validation update connections
                function onSubparamValidationChanged(paramName, status, message)
                {
                    // Update the specific sub-parameter error state
                    updateSubparamError(paramName, status, message);
                }
            }

            Item { }
            Text {
                id: paramLabel
                text: param?.label_rtf ?? ''
                Layout.preferredWidth: paramLabelWidth
                horizontalAlignment: Text.AlignLeft
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
                    if (param !== null) param.unit = displayText;
                }
                Layout.maximumWidth: medInputW
            }

            InputTopLabel {
                id: inputTypeLabel
                text: ""
            }

            DenseComboBox {
                id: inputTypeSelector
                // textRole: "text"
                // valueRole: "value"
                model: param?.distr_choices ?? null
                // model: ListModel {
                //     ListElement { value: "det"; text: "Deterministic" }
                //     ListElement { value: "tnor"; text: "Normal" }
                //     ListElement { value: "tlog"; text: "Lognormal" }
                //     ListElement { value: "uni"; text: "Uniform" }
                // }
                currentIndex: param?.get_input_type_index() ?? 0
                onActivated: {
                    if (param !== null) param.set_input_type_from_index(currentIndex);
                }
                Layout.maximumWidth: distributionInputW
                Layout.preferredWidth: distributionInputW
            }

            // InputTopLabel {
            //     id: valueLabel
            //     text: ""
            // }
            // DoubleTextInput {
            //     id: valueInput
            //     field: 'value'
            //     Layout.maximumWidth: medInputW
            // }

            InputTopLabel {
                id: nominalLabel
                text: "Nominal value"
                visible: false
            }
            DoubleTextInput {
                id: nominalInput
                field: 'value'
                Layout.maximumWidth: medInputW
            }

            InputTopLabel {
                id: uncertaintyLabel
                text: "Uncertainty"
            }
            DenseComboBox {
                id: uncertaintySelector
                visible: false
                Layout.maximumWidth: uncertaintyInputW
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

            // Normal distribution inputs
            InputTopLabel {
                id: meanLabel
                text: "Mean"
            }
            DoubleTextInput {
                id: meanInput
                field: 'mean'
                Layout.maximumWidth: shortInputW
            }

            InputTopLabel {
                id: stdLabel
                text: "Std dev"
            }
            DoubleTextInput {
                id: stdInput
                field: 'std'
                useLimits: false
                Layout.maximumWidth: shortInputW
            }

            // Lognormal distribution inputs
            InputTopLabel {
                id: muLabel
                text: "\u03BC"
            }
            DoubleTextInput {
                id: muInput
                field: 'mu'
                Layout.maximumWidth: shortInputW
            }

            InputTopLabel {
                id: sigmaLabel
                text: "\u03C3"
            }
            DoubleTextInput {
                id: sigmaInput
                field: 'sigma'
                useLimits: false
                Layout.maximumWidth: shortInputW
            }

            InputTopLabel {
                id: lowerBoundLabel
                text: "Lower bound"
            }
            DoubleTextInput {
                id: lowerBoundInput
                field: 'lower'
                Layout.maximumWidth: shortInputW
            }

            InputTopLabel {
                id: upperBoundLabel
                text: "Upper bound"
            }
            DoubleNullableTextInput {
                id: upperBoundInput
                field: 'upper'
                Layout.maximumWidth: shortInputW
                // min: 1
            }

            // Lognormal distribution inputs
            InputTopLabel {
                id: alphaLabel
                text: "\u03B1"
            }
            DoubleTextInput {
                id: alphaInput
                field: 'alpha'
                Layout.maximumWidth: shortInputW
            }

            InputTopLabel {
                id: betaLabel
                text: "\u03B2"
            }
            DoubleTextInput {
                id: betaInput
                field: 'beta'
                Layout.maximumWidth: shortInputW
            }

        }
    }

    Row
    {
        id: alertDisplayRow
        anchors.top: paramInputRow.bottom
        leftPadding: 125
        visible: hasError
        height: hasError ? 30 : 0
        clip: true  // clip contents during animation
        Behavior on height {
            NumberAnimation { duration: 100 }
        }

        AppIcon {
            id: alertIcon
            source: 'circle-exclamation-solid'
            iconColor: Material.color(Material.Red)
            width: 24
            height: 24
        }
        Text {
            id: alertMsg
            text: errorMsg
            anchors.topMargin: 4
            font.italic: true
            anchors.verticalCenter: parent.verticalCenter
            color: color_danger
        }
    }
}
