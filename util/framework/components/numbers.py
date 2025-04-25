import asyncio
from util.framework.core.component import Component
from util.framework.utils.yaml import yaml_serializable

@yaml_serializable(auto_save=True)
class NumberComponent(Component):
    def __init__(self, **kwargs):
        super(NumberComponent, self).__init__(**kwargs)

        self.max_health = 100
        self.health = self.max_health

        self.max_mana = 100
        self.mana = self.max_mana

        self.damage = 1
        self._is_processing = False
        self._lock = asyncio.Lock()

    async def add_damage(self):
        async with self._lock:
            if self._is_processing:
                return

            self._is_processing = True
            try:
                self._on_spell_use()
                self.damage += 1
                print(self.damage)
            finally:
                self._is_processing = False

    def _on_spell_use(self):
        if self.mana > 0:
            self.mana -= 5
        else:
            return