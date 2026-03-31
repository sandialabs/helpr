"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import copy
import unittest

from ..models.models import ModelBase
from ..models.fields import NumField, StringField
from ..utils.units_of_measurement import Unitless


class ModelWithFields(ModelBase):
    """Test-only model with fields for exercising history."""

    def __init__(self):
        super().__init__()
        self.param_a = NumField(label='Param A',
                                value=1.0,
                                unit_type=Unitless,
                                min_value=0,
                                max_value=100)
        self.param_b = NumField(label='Param B',
                                value=2.0,
                                unit_type=Unitless,
                                min_value=0,
                                max_value=100)
        self.fields = [self.param_a, self.param_b, self.analysis_name]
        self.post_init()


class RedoTestCase(unittest.TestCase):
    """Tests for redo_state_change."""

    def setUp(self):
        self.model = ModelWithFields()

    def test_redo_restores_undone_change(self):
        """Redo restores the value that was undone."""
        self.model.param_a.value = 10.0
        self.model.param_a.value = 20.0
        self.assertEqual(self.model.param_a.value, 20.0)

        self.model.undo_state_change()
        self.assertEqual(self.model.param_a.value, 10.0)

        self.model.redo_state_change()
        self.assertEqual(self.model.param_a.value, 20.0)

    def test_redo_when_nothing_to_redo(self):
        """Redo with empty redo history is a no-op."""
        initial_val = self.model.param_a.value
        self.model.redo_state_change()
        self.assertEqual(self.model.param_a.value, initial_val)

    def test_undo_redo_undo_cycle(self):
        """Multiple undo/redo cycles produce correct state."""
        self.model.param_a.value = 10.0
        self.model.param_a.value = 20.0
        self.model.param_a.value = 30.0

        self.model.undo_state_change()  # back to 20
        self.model.undo_state_change()  # back to 10
        self.assertEqual(self.model.param_a.value, 10.0)

        self.model.redo_state_change()  # forward to 20
        self.assertEqual(self.model.param_a.value, 20.0)

        self.model.undo_state_change()  # back to 10
        self.assertEqual(self.model.param_a.value, 10.0)

    def test_new_change_clears_redo_history(self):
        """Making a new change after undo clears redo history."""
        self.model.param_a.value = 10.0
        self.model.param_a.value = 20.0

        self.model.undo_state_change()  # back to 10
        self.assertTrue(self.model.can_redo())

        self.model.param_a.value = 50.0  # new change
        self.assertFalse(self.model.can_redo())

    def test_redo_does_not_record_history(self):
        """Redo should not add extra entries to history."""
        self.model.param_a.value = 10.0
        history_len_after_change = len(self.model._history)

        self.model.undo_state_change()
        self.model.redo_state_change()
        self.assertEqual(len(self.model._history), history_len_after_change)

    def test_history_changed_emitted_on_redo(self):
        """history_changed event fires during redo."""
        self.model.param_a.value = 10.0
        self.model.undo_state_change()

        notified = []
        self.model.history_changed += lambda x: notified.append(True)
        self.model.redo_state_change()
        self.assertTrue(notified)


class DeepCopyTestCase(unittest.TestCase):
    """Tests for ModelBase.__deepcopy__."""

    def setUp(self):
        self.model = ModelWithFields()

    def test_clone_is_independent(self):
        """Mutating the clone does not affect the original."""
        clone = copy.deepcopy(self.model)
        clone.param_a._value = 999.0
        self.assertNotEqual(self.model.param_a._value, 999.0)

    def test_clone_preserves_field_values(self):
        """Clone has same field values as original."""
        self.model.param_a.value = 42.0
        clone = copy.deepcopy(self.model)
        self.assertEqual(clone.param_a._value, self.model.param_a._value)

    def test_clone_has_empty_event_listeners(self):
        """Deep copy should have fresh (empty) event listeners."""
        clone = copy.deepcopy(self.model)
        # Events on the clone should not fire back to original
        self.assertEqual(len(clone.param_a.changed.listeners), 0)

    def test_clone_fields_list_preserved(self):
        """Clone preserves the fields list."""
        clone = copy.deepcopy(self.model)
        self.assertEqual(len(clone.fields), len(self.model.fields))
