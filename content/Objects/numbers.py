import asyncio

from content.CMS.CMSNumbers import NumbersComponent
from util import CMS, CMSEntity
from util.framework.core.interactors.interactor import Interactor
from util.framework.globals import G


class NumbersEntity(Interactor, CMSEntity):
    def __init__(self):
        Interactor.__init__(self)
        CMSEntity.__init__(self, "NumbersComponent")

        self._is_processing = False
        self._cooldown_coroutine = None

        self.numbers = self.define(NumbersComponent)

        CMS.init()

    def awake(self):
        Interactor.awake(self)
        G.register_interactor('Numbers', self)

    async def _add_damage_func(self):
        if self._is_processing or (self._cooldown_coroutine is not None and not self._cooldown_coroutine.done()):
            return False

        self._is_processing = True
        try:
            if self.numbers and self._on_spell_use(self.numbers):
                self.numbers.damage += 1
                self.numbers.to_yaml()
                print(f"Damage increased to: {self.numbers.damage}")

                self._cooldown_coroutine = self.start_coroutine(self._action_with_cooldown())
            return False
        finally:
            self._is_processing = False
            return None

    async def add_damage(self):
        if self.enabled:
            return await self._add_damage_func()
        return False

    def _on_spell_use(self, numbers):
        if numbers.mana >= 5:
            G.window.start_transition()
            numbers.mana -= 5
            return True
        else:
            return False

    @staticmethod
    async def _action_with_cooldown():
        await asyncio.sleep(1.0)
        print("Cooldown end")