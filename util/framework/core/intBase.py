from util.framework.core.component import Component

class BaseInteraction:
    def __init__(self):
        self._enabled = True

    def priority(self):
        return 0

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

class IOnEncounterStart:
    def on_encounter_start(self, args=None):
        pass

class IOnEncounterEnd:
    def on_encounter_end(self, args=None):
        pass

class IOnEncounterUpdate:
    def on_encounter_update(self, args=None):
        pass