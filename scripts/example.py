
from util.framework.core.interactors.intBase import BaseInteraction, IOnEncounterStart
import asyncio


class OnEncounterStartHello(BaseInteraction, IOnEncounterStart):

    async def on_encounter_start(self, *args):
        print("Hello world")
        await asyncio.sleep(1)
        print("Bye-bye world")