"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import unittest
from ..utils.events import Event


class EventTestCase(unittest.TestCase):
    """Tests for the Event pub-sub system."""

    def test_subscribe_and_notify(self):
        """Listener receives notification with correct args."""
        event = Event()
        received = []
        event += lambda *args: received.append(args)
        event.notify("a", 1)
        self.assertEqual(received, [("a", 1)])

    def test_multiple_listeners(self):
        """All subscribed listeners are called."""
        event = Event()
        calls = []
        event += lambda x: calls.append("first")
        event += lambda x: calls.append("second")
        event.notify(None)
        self.assertEqual(calls, ["first", "second"])

    def test_unsubscribe(self):
        """Removed listener is no longer called."""
        event = Event()
        calls = []

        def listener(x):
            calls.append(x)

        event += listener
        event.notify(1)
        event -= listener
        event.notify(2)
        self.assertEqual(calls, [1])

    def test_unsubscribe_missing_listener_is_noop(self):
        """Removing a listener that was never added does not raise."""
        event = Event()

        def listener(x):
            pass

        event -= listener  # should not raise

    def test_clear(self):
        """Clear removes all listeners."""
        event = Event()
        event += lambda x: None
        event += lambda x: None
        self.assertEqual(len(event.listeners), 2)
        event.clear()
        self.assertEqual(len(event.listeners), 0)

    def test_notify_empty_is_noop(self):
        """Notifying with no listeners does not raise."""
        event = Event()
        event.notify("data")

    def test_notify_iterates_over_copy(self):
        """Listener removing itself during notify does not skip other listeners."""
        self._test_event = Event()
        calls = []

        def self_removing_listener(x):
            calls.append("removing")
            self._test_event.listeners.remove(self_removing_listener)

        def second_listener(x):
            calls.append("second")

        self._test_event += self_removing_listener
        self._test_event += second_listener
        self._test_event.notify(None)
        self.assertIn("second", calls)
        self.assertEqual(len(self._test_event.listeners), 1)

    def test_duplicate_subscribe(self):
        """Same listener added twice fires twice and remove only removes first."""
        event = Event()
        calls = []

        def listener(x):
            calls.append(x)

        event += listener
        event += listener
        event.notify(1)
        self.assertEqual(calls, [1, 1])

        event -= listener  # removes first occurrence
        calls.clear()
        event.notify(2)
        self.assertEqual(calls, [2])

    def test_kwargs_passed(self):
        """Keyword arguments are forwarded to listeners."""
        event = Event()
        received = {}

        def listener(**kwargs):
            received.update(kwargs)

        event += listener
        event.notify(key="value")
        self.assertEqual(received, {"key": "value"})
