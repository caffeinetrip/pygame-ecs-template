from abc import ABC, abstractmethod


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


class IOnEncounterStart(ABC):
    @abstractmethod
    async def on_encounter_start(self, args=None):
        pass


class IOnEncounterEnd(ABC):
    @abstractmethod
    async def on_encounter_end(self, args=None):
        pass


class IOnEncounterUpdate(ABC):
    @abstractmethod
    async def on_encounter_update(self, args=None):
        pass