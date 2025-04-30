from util.framework.core.interactors.interactor import Interactor

class Sectors:
    def __init__(self, sector_size):
        self.sector_size = sector_size
        self.reset()

    def reset(self):
        self.objects = {}
        self.map = {}
        self.id_to_loc = {}
        self.next_id = 0

    def export(self, obj_handler=lambda x: None):
        output = {
            'objects': {k: obj_handler(v) for k, v in self.objects.items()},
            'map': self.map,
            'id_to_loc': self.id_to_loc,
            'next_id': self.next_id,
        }
        return output

    def add(self, obj, sector_loc, tag=False, id_jump=1):
        if tag:
            obj.sector_ids.append(self.next_id)
        self.objects[self.next_id] = obj
        if self.next_id not in self.id_to_loc:
            self.id_to_loc[self.next_id] = []
        self.id_to_loc[self.next_id].append(sector_loc)
        if sector_loc not in self.map:
            self.map[sector_loc] = []
        self.map[sector_loc].append(self.next_id)
        self.next_id += id_jump

    def add_raw(self, obj, rect, tag=False):
        if tag:
            obj.sector_ids = []
        sector_locs = [
            (rect.x // self.sector_size, rect.y // self.sector_size),
            (rect.x + rect.width // self.sector_size, rect.y // self.sector_size),
            ((rect.x + rect.width) // self.sector_size, (rect.y + rect.height) // self.sector_size),
            (rect.x // self.sector_size, (rect.y + rect.height) // self.sector_size),
        ]
        sector_locs = set(sector_locs)
        for loc in sector_locs:
            self.add(obj, loc, tag=tag, id_jump=0)
        self.next_id += 1

    def delete(self, obj):
        # assumes object is tagged
        for sector_id in obj.sector_ids:
            if sector_id in self.objects:
                del self.objects[sector_id]
            try:
                for loc in self.id_to_loc[sector_id]:
                    if loc in self.map:
                        if sector_id in self.map[loc]:
                            self.map[loc].remove(sector_id)
            except KeyError:
                continue
            del self.id_to_loc[sector_id]

    def query(self, rect):
        # get bounding coords
        tl = (rect.x // self.sector_size, rect.y // self.sector_size)
        br = ((rect.x + rect.width) // self.sector_size, (rect.y + rect.height) // self.sector_size)

        # lookup entries
        results = []
        for x in range(br[0] - tl[0] + 1):
            for y in range(br[1] - tl[1] + 1):
                loc = (tl[0] + x, tl[1] + y)
                if loc in self.map:
                    results += self.map[loc]

        # remove duplicates
        results = set(results)

        return [self.objects[obj_id] for obj_id in results]

class ObjectSectors(Interactor):
    def __init__(self, sector_size=64):
        super().__init__()
        self.sector_size = sector_size
        self.initialize()

    def initialize(self):
        self.sectors = {}
        self.entity_locations = {}
        self.visible_objects = {}

    def total_objects(self):
        return sum([len(self.sectors[sector]) for sector in self.sectors])

    def register(self, entity, collection_name='main'):
        if id(entity) not in self.entity_locations:
            sector_coords = (int(entity.position[0] // self.sector_size), int(entity.position[1] // self.sector_size))
            if sector_coords not in self.sectors:
                self.sectors[sector_coords] = []
            self.sectors[sector_coords].append(entity)
            self.entity_locations[id(entity)] = sector_coords
            entity._collection = collection_name
            if collection_name not in self.visible_objects:
                self.visible_objects[collection_name] = []

    def unregister(self, entity):
        if id(entity) in self.entity_locations:
            self.sectors[self.entity_locations[id(entity)]].remove(entity)
            del self.entity_locations[id(entity)]

    def remove_collection(self, collection_name):
        if collection_name not in self.visible_objects:
            return

        entities_to_remove = []
        for entity_id, sector_coords in self.entity_locations.items():
            for entity in self.sectors[sector_coords]:
                if hasattr(entity, '_collection') and entity._collection == collection_name:
                    entities_to_remove.append(entity)

        for entity in entities_to_remove:
            self.unregister(entity)

        self.visible_objects[collection_name] = []

    def purge(self):
        self.sectors = {}
        self.entity_locations = {}

        for collection_name in self.visible_objects:
            self.visible_objects[collection_name] = []

    def refresh_visible(self, view_rect):
        for collection_name in self.visible_objects:
            self.visible_objects[collection_name] = []

        # Calculate sector coordinates from view rectangle
        start_y = int(view_rect.top // self.sector_size)
        end_y = int(view_rect.bottom // self.sector_size + 1)
        start_x = int(view_rect.left // self.sector_size)
        end_x = int(view_rect.right // self.sector_size + 1)

        # Process all sectors within view
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                sector_coords = (x, y)
                if sector_coords in self.sectors:
                    for entity in self.sectors[sector_coords]:
                        # Check if entity moved to a new sector
                        new_coords = (int(entity.position[0] // self.sector_size),
                                      int(entity.position[1] // self.sector_size))
                        if self.entity_locations[id(entity)] != new_coords:
                            # Update entity sector location
                            old_coords = self.entity_locations[id(entity)]
                            self.entity_locations[id(entity)] = new_coords

                            # Remove from old sector
                            self.sectors[old_coords].remove(entity)

                            # Add to new sector
                            if new_coords not in self.sectors:
                                self.sectors[new_coords] = []
                            self.sectors[new_coords].append(entity)

                        # Add to visible objects for this collection
                        self.visible_objects[entity._collection].append(entity)