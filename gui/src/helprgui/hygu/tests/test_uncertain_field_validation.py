"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
You should have received a copy of the BSD License along with HELPR.
"""

import pytest

from ..models.fields_probabilistic import UncertainField
from ..utils.distributions import Distributions, DistributionParam
from ..utils.helpers import InputStatus


class TestUncertainFieldValidation:
    """Tests for UncertainField validation state tracking"""

    def test_validation_state_tracking(self):
        """Test that validation states are tracked properly for each parameter"""
        field = UncertainField('Test Field', 10, distr=Distributions.uni, lower=5, upper=15)
        
        # By default all states should be valid
        assert field.get_validation_state(DistributionParam.NOMINAL).status == InputStatus.GOOD
        assert field.get_validation_state(DistributionParam.LOWER).status == InputStatus.GOOD
        assert field.get_validation_state(DistributionParam.UPPER).status == InputStatus.GOOD
        
        # Validate an invalid value (lower above upper)
        result = field.validate_subparam_incoming_value(DistributionParam.LOWER, 20)
        assert result.status == InputStatus.ERROR
        
        # Check internal state updated when param changed
        field.lower = 20
        state = field.get_validation_state(DistributionParam.LOWER)
        assert state.status == InputStatus.ERROR
        assert "above upper bound" in state.message
        
        # Other sub-params won't be valid
        assert field.get_validation_state(DistributionParam.NOMINAL).status == InputStatus.ERROR
        assert field.get_validation_state(DistributionParam.UPPER).status == InputStatus.ERROR

    def test_validation_state_persists_after_field_changes(self):
        """Test that validation states persist after field input changes"""
        field = UncertainField('Test Field', 10, distr=Distributions.tnor, mean=10, std=2)

        # Set an invalid standard deviation directly (bypassing setter validation)
        field._std = -1
        field.update_all_validation_states()
        print(field.std)

        state = field.get_validation_state(DistributionParam.STD)
        assert state.status == InputStatus.ERROR
        assert "positive" in state.message

        # Change the nominal value
        field.value = 12

        # The STD validation error should persist
        state = field.get_validation_state(DistributionParam.STD)
        assert state.status == InputStatus.ERROR
        assert "positive" in state.message

    def test_related_parameter_validation(self):
        """Test that changing one parameter validates related parameters"""
        field = UncertainField('Test Field', 10, distr=Distributions.uni, lower=5, upper=15)
        
        # Set lower bound higher than nominal value
        field.lower = 12
        
        # Nominal will not be in error state
        assert field.get_validation_state(DistributionParam.NOMINAL).status == InputStatus.ERROR
        assert field.get_validation_state(DistributionParam.LOWER).status == InputStatus.GOOD
        
        # Fix by updating nominal value
        field.value = 13
        
        # Both should now be valid
        assert field.get_validation_state(DistributionParam.NOMINAL).status == InputStatus.GOOD
        assert field.get_validation_state(DistributionParam.LOWER).status == InputStatus.GOOD

    def test_validation_event_emitted(self):
        """Test that validation events are emitted when validation state changes"""
        field = UncertainField('Test Field', 10, distr=Distributions.uni, lower=5, upper=15)
        
        # Set up event listener
        events = []
        def validation_listener(sender, param_name, status, message):
            print(f'HEARD EVENT: {param_name} {status} {message}')
            events.append((param_name, status, message))
            
        field.subparam_validation_changed += validation_listener

        field.lower = 20

        # every subparam has event but most are valid so check the two failures we expect
        assert len(events) >= 1
        for event in events:
            if event[0] == "lower":
                assert event[1] == InputStatus.ERROR
                assert "above upper bound" in event[2]
            elif event[0] == "upper":
                assert event[1] == InputStatus.ERROR
                assert "below lower bound" in event[2]

        field.subparam_validation_changed -= validation_listener

    def test_distribution_change_resets_validation(self):
        """Test that changing distribution type resets validation states"""
        field = UncertainField('Test Field', 10, distr=Distributions.uni, lower=5, upper=15)

        # Set invalid lower bound
        field._lower = 20
        assert field.get_validation_state(DistributionParam.LOWER).status == InputStatus.ERROR

        # Change distribution type
        field.distr = Distributions.nor

        # All validation states should be reset
        assert field.get_validation_state(DistributionParam.NOMINAL).status == InputStatus.GOOD
        assert field.get_validation_state(DistributionParam.MEAN).status == InputStatus.GOOD
        assert field.get_validation_state(DistributionParam.STD).status == InputStatus.GOOD

    def test_std_zero_is_invalid_for_normal_distribution(self):
        """Test that standard deviation of 0 is accepted by setter but fails validation.

        A standard deviation must be strictly positive (> 0).
        """
        field = UncertainField('Test Field', 50, distr=Distributions.nor, mean=50, std=1, min_value=10, max_value=100)

        field.std = 0
        assert field.std == 0, "std=0 should be accepted by setter"

        result = field.check_valid()
        assert result.status == InputStatus.ERROR, f"std=0 validation should fail, got: {result.message}"

    def test_std_zero_is_invalid_for_truncated_normal_distribution(self):
        """Test that standard deviation of 0 is accepted by setter but fails validation.

        A standard deviation must be strictly positive (> 0). This test also verifies
        that std is not incorrectly compared to the field's min_value (which bounds
        the parameter value, not the standard deviation).
        """
        field = UncertainField(
            'Test Field', 50,
            distr=Distributions.tnor,
            mean=50, std=1,
            lower=10, upper=100,
            min_value=10, max_value=100
        )

        field.std = 0
        assert field.std == 0, "std=0 should be accepted by setter"

        result = field.check_valid()
        assert result.status == InputStatus.ERROR, f"std=0 validation should fail for tnor, got: {result.message}"

        # Negative std should also be invalid
        field.std = -1
        result_negative = field.check_valid()
        assert result_negative.status == InputStatus.ERROR

    def test_std_not_compared_to_min_max_bounds(self):
        """Test that std is not validated against min_value/max_value.

        The min_value and max_value are bounds for the parameter value (e.g.,
        pipe thickness must be >= 0), not for the standard deviation.
        """
        # Field where min_value=50, max_value=200
        field = UncertainField(
            'Test Field', 100,
            distr=Distributions.tnor,
            mean=100, std=10,
            lower=50, upper=200,
            min_value=50, max_value=200
        )

        # std=10 is less than min_value=50, but should still be valid
        result = field.validate_subparam_incoming_value(DistributionParam.STD, 10)
        assert result.status == InputStatus.GOOD, f"std=10 should be valid even when < min_value=50, got: {result.message}"

        # std=300 exceeds max_value=200, but should still be valid
        result = field.validate_subparam_incoming_value(DistributionParam.STD, 300)
        assert result.status == InputStatus.GOOD, f"std=300 should be valid even when > max_value=200, got: {result.message}"

    def test_mu_not_compared_to_bounds_for_lognormal(self):
        """Test that mu is not validated against min_value/max_value for lognormal distribution. """
        field = UncertainField(
            'Test Field', 100,
            distr=Distributions.log,
            mu=1, sigma=0.5,  # mu=1 is well below min_value
            min_value=50, max_value=500
        )

        state = field.get_validation_state(DistributionParam.MU)
        assert state.status == InputStatus.GOOD, f"mu=1 should be valid for log distribution, got: {state.message}"

        result = field.validate_subparam_incoming_value(DistributionParam.MU, 1)
        assert result.status == InputStatus.GOOD, f"mu=1 validation should pass, got: {result.message}"

        # Even negative mu should be valid (results in small positive values for X)
        result_negative = field.validate_subparam_incoming_value(DistributionParam.MU, -5)
        assert result_negative.status == InputStatus.GOOD, f"mu=-5 should be valid, got: {result_negative.message}"

        result_large = field.validate_subparam_incoming_value(DistributionParam.MU, 1000)
        assert result_large.status == InputStatus.GOOD, f"mu=1000 should be valid, got: {result_large.message}"

    def test_mu_not_compared_to_bounds_for_truncated_lognormal(self):
        """Test that mu is not validated against bounds for truncated lognormal distribution.

        This test covers the bug where mu was incorrectly flagged as
        'below lower bound' because mu was being compared to the distribution's
        lower/upper bounds (and min_value/max_value), which apply to X, not ln(X).
        """
        field = UncertainField(
            'Test Field', 100,
            distr=Distributions.tlog,
            mu=2, sigma=0.3,  # mu=2 << lower=50
            lower=50, upper=200,
            min_value=10, max_value=500
        )

        state = field.get_validation_state(DistributionParam.MU)
        assert state.status == InputStatus.GOOD, f"mu=2 should be valid for tlog distribution, got: {state.message}"

        result = field.validate_subparam_incoming_value(DistributionParam.MU, 2)
        assert result.status == InputStatus.GOOD, f"mu=2 validation should pass for tlog, got: {result.message}"

        result_below_min = field.validate_subparam_incoming_value(DistributionParam.MU, 5)
        assert result_below_min.status == InputStatus.GOOD, f"mu=5 should be valid even when < min_value=10, got: {result_below_min.message}"

        result_negative = field.validate_subparam_incoming_value(DistributionParam.MU, -10)
        assert result_negative.status == InputStatus.GOOD, f"mu=-10 should be valid, got: {result_negative.message}"

        result_above = field.validate_subparam_incoming_value(DistributionParam.MU, 300)
        assert result_above.status == InputStatus.GOOD, f"mu=300 should be valid even when > upper=200, got: {result_above.message}"