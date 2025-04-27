import asyncio
from util.framework.core import Interactor
from util.framework.utils.yaml import yaml_serializable


@yaml_serializable(auto_save=True)
class NumberManager(Interactor):
    def __init__(self):
        super().__init__()

        self.max_health = 100
        self.health = self.max_health

        self.max_mana = 100
        self.mana = self.max_mana

        self.damage = 1
        self._is_processing = False
        self._cooldown_coroutine = None

    async def add_damage(self):
        if self._is_processing or (self._cooldown_coroutine is not None and not self._cooldown_coroutine.done()):
            return False

        self._is_processing = True
        try:
            if self._on_spell_use():
                self.damage += 1
                print(f"Damage increased to: {self.damage}")

                self._cooldown_coroutine = asyncio.create_task(self._action_with_cooldown())
                return True
            return False
        finally:
            self._is_processing = False

    def _on_spell_use(self):
        if self.mana >= 5:
            self.mana -= 5
            return True
        else:
            return False

    async def _action_with_cooldown(self):
        await asyncio.sleep(1.0)
        print("Cooldown end")