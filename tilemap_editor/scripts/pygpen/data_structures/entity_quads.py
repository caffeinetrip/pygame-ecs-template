from ..utils.elements import ElementSingleton

class EQuads(ElementSingleton):
    def __init__(self, quad_size=64):
        super().__init__()
        
        self.quad_size = quad_size
        self.reset()
        
    def reset(self):
        self.quads = {}
        self.known_locs = {}
        self.active_entities = {}
        
    def count(self):
        return sum([len(self.quads[quad]) for quad in self.quads])
        
    def insert(self, obj, egroup='default'):
        if id(obj) not in self.known_locs:
            quad = (int(obj.pos[0] // self.quad_size), int(obj.pos[1] // self.quad_size))
            if quad not in self.quads:
                self.quads[quad] = []
            self.quads[quad].append(obj)
            self.known_locs[id(obj)] = quad
            
            # flag the group the object is associated with
            obj._egroup = egroup
            if egroup not in self.active_entities:
                self.active_entities[egroup] = []
            
    def delete(self, obj):
        if id(obj) in self.known_locs:
            self.quads[self.known_locs[id(obj)]].remove(obj)
            del self.known_locs[id(obj)]
    
    def update_active(self, rect):
        # wipe active entities
        for group in self.active_entities:
            self.active_entities[group] = []
        
        for y in range(int(rect.top // self.quad_size), int(rect.bottom // self.quad_size + 1)):
            for x in range(int(rect.left // self.quad_size), int(rect.right // self.quad_size + 1)):
                loc = (x, y)
                if loc in self.quads:
                    for obj in self.quads[loc]:
                        new_quad = (int(obj.pos[0] // self.quad_size), int(obj.pos[1] // self.quad_size))
                        
                        # move object's quad if necessary
                        if self.known_locs[id(obj)] != new_quad:
                            old_quad = self.known_locs[id(obj)]
                            self.known_locs[id(obj)] = new_quad
                            self.quads[old_quad].remove(obj)
                            if new_quad not in self.quads:
                                self.quads[new_quad] = []
                            self.quads[new_quad].append(obj)
                        
                        # mark object as active
                        self.active_entities[obj._egroup].append(obj)
    