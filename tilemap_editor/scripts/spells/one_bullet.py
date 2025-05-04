from scripts.spells.spell_global_class import Spells
from scripts.bullets import Bullet
import random

class one_bullet(Spells):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def use(self):
        return [Bullet('bullet', [self.pos[0], self.pos[1]-20], self.angle)]