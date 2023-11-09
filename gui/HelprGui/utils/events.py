

class Event:
    """Generic event class with basic listener and emitter functionality. """
    def __init__(self):
        self.listeners = []

    def __iadd__(self, listener):
        self.listeners.append(listener)
        return self

    def __isub__(self, other):
        if other in self.listeners:
            self.listeners.remove(other)
        return self

    def notify(self, *args, **kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)


