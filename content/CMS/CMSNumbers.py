from util import EntityComponentDefinition, yaml_serializable

@yaml_serializable()
class NumbersComponent(EntityComponentDefinition):
    def __init__(self):
        super().__init__()
        self.max_health = 100
        self.health = self.max_health
        self.max_mana = 10**10
        self.mana = self.max_mana
        self.damage = 1