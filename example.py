
from util.framework.core.intBase import BaseInteraction, IOnEncounterStart

class OnEncounterStartHello(BaseInteraction, IOnEncounterStart):

    def on_encounter_start(self, *args):
        print("Hello world")