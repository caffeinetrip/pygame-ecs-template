import scripts.pygpen as pp

class Spells(pp.Element):
    def __init__(self, angle, custom_id=None, singleton=False, register=False):
        super().__init__(custom_id, singleton, register)
        
        self.pos = pp.io.read_json('data/hooks/data.json')['player_position']
        self.angle = angle

    def destroy(self):
        del self