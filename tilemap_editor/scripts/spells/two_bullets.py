from scripts.spells.spell_global_class import Spells
from scripts.bullets import Bullet
import random

class two_bullets(Spells):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def use(self):
        return [Bullet('bullet', [self.pos[0], self.pos[1]-20], self.angle-10), 
                Bullet('bullet', [self.pos[0], self.pos[1]-20], self.angle+10)]
