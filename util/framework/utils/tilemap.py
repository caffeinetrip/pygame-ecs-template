import pygame, copy
from .. import Component
from ..utils.io import read_tjson, write_tjson
from util.framework.core.object.ObjectSectors import Sectors
from .. import G

BORDERS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)]

NON_WALKABLE_TILES = [
    'water',
    'lava',
    'wall',
    'pit',
    'spikes',
    'void',
    'barrier',
    'deep_water',
    'acid',
    'fire'
]


def basic_tile_render(tile, offset=(0, 0), group='default'):
    G.render.blit(tile.img, (tile.raw_pos[0] + tile.offset[0] - offset[0],
                             tile.raw_pos[1] + tile.offset[1] - offset[1]), z=tile.layer, group=group)


class Tile(Component):
    def __init__(self, group, tile_id=(0, 0), pos=(0, 0), layer=0, custom_data=''):
        super().__init__()
        self.group = group
        self.render_func = basic_tile_render
        self.change_id(tile_id)
        self.grid_pos = tuple(pos)
        self.raw_pos = tuple(pos)
        self.layer = layer
        self.rect = pygame.Rect(*pos, *self.img.get_size())
        self.map = None
        self.flags = set(self.config['flags'] if 'flags' in self.config else ['solid'])
        self.physics_type = None
        self.custom_data = custom_data
        self.walkable = True if self.group not in NON_WALKABLE_TILES else False

    def render(self, offset=(0, 0), group='default'):
        self.render_func(self, offset=offset, group=group)

    def primitive_render(self, surf, offset=(0, 0)):
        surf.blit(self.img,
                  (self.raw_pos[0] + self.offset[0] - offset[0], self.raw_pos[1] + self.offset[1] - offset[1]))

    def shift_clone(self, pos):
        return Tile(self.group, tile_id=self.tile_id, pos=pos, layer=self.layer)

    def change_id(self, tile_id):
        self.tile_id = tile_id
        self.img = G.assets.spritesheets[self.group]['assets'][tile_id]
        self.config = G.assets.spritesheets[self.group]['config'][tile_id]
        if self.group in G.assets.custom_tile_renderers:
            self.render_func = G.assets.custom_tile_renderers[self.group]
        self.offset = self.config['offset']

    def export(self):
        data = {'group': self.group, 'tile_id': self.tile_id, 'pos': self.grid_pos, 'layer': self.layer}
        if self.custom_data:
            data['c'] = self.custom_data
        return data

    def attach(self, tilemap, ongrid=True):
        if ongrid:
            self.raw_pos = (self.grid_pos[0] * tilemap.tile_size[0], self.grid_pos[1] * tilemap.tile_size[1])
            self.rect = pygame.Rect(*self.raw_pos, *tilemap.tile_size)
        self.map = tilemap
        for flag in self.flags:
            if flag in tilemap.physics_priority:
                self.physics_type = flag
                break

    def neighbors(self, offsets, handle_edge=False):
        neighbors = {}
        for offset in offsets:
            loc = (self.grid_pos[0] + offset[0], self.grid_pos[1] + offset[1])
            if loc in self.map.grid_tiles and self.layer in self.map.grid_tiles[loc]:
                neighbors[tuple(offset[:2])] = self.map.grid_tiles[loc][self.layer]
            elif handle_edge and (not self.map.in_map(loc)) and self.map.demensional_lock:
                neighbors[tuple(offset[:2])] = 'edge'
        return neighbors


class Tilemap(Component):
    def __init__(self, tile_size=(16, 16), dimensions=(16, 16)):
        super().__init__()
        self.tile_size = tuple(tile_size)
        self.physics_priority = {'solid': 1.0, 'dropthrough': 0.9, 'rampr': 0.8, 'rampl': 0.7}
        self.dimensions = tuple(dimensions)
        self.demensional_lock = True
        self.reset()

    @property
    def world_dimensions(self):
        return (self.dimensions[0] * self.tile_size[0], self.dimensions[1] * self.tile_size[1])

    def reset(self):
        self.grid_tiles = {}
        self.physics_map = {}
        self.offgrid_tiles = Sectors((self.tile_size[0] + self.tile_size[1]) * 3)
        self.i = 0

    def save(self, path):
        output = {
            'tile_size': self.tile_size,
            'grid_tiles': {},
            'offgrid_tiles': self.offgrid_tiles.export(lambda x: x.export()),
            'dimensions': self.dimensions
        }

        for loc in self.grid_tiles:
            output['grid_tiles'][loc] = {layer: self.grid_tiles[loc][layer].export()
                                         for layer in self.grid_tiles[loc]}

        write_tjson(path, output)

    def in_map(self, gridpos):
        return 0 <= gridpos[0] < self.dimensions[0] and 0 <= gridpos[1] < self.dimensions[1]

    def get_tiles(self, include_grid=True, include_offgrid=True):
        tiles = []

        if include_grid:
            for loc_dict in self.grid_tiles.values():
                tiles.extend(loc_dict.values())

        if include_offgrid:
            tiles.extend(self.offgrid_tiles.objects.values())

        return tiles

    def replace_tiles(self, new_tiles, ongrid=True):
        self.reset()
        for tile in new_tiles:
            self.insert(tile, ongrid=ongrid)

    def inject(self, tilemap, offset=(0, 0), spawn_hook=lambda tile_data, ongrid: True):
        for loc in tilemap.grid_tiles:
            for tile in tilemap.grid_tiles[loc].values():
                tile = tile.shift_clone((tile.grid_pos[0] + offset[0], tile.grid_pos[1] + offset[1]))
                if spawn_hook(tile.export(), True):
                    self.insert(tile, ongrid=True)

        for tile in tilemap.offgrid_tiles.objects.values():
            tile = tile.shift_clone(
                (tile.grid_pos[0] + offset[0] * self.tile_size[0], tile.grid_pos[1] + offset[1] * self.tile_size[1]))
            if spawn_hook(tile.export(), False):
                self.insert(tile, ongrid=False)

    def load(self, path, spawn_hook=lambda tile_data, ongrid: True):
        data = read_tjson(path)
        self.reset()
        self.tile_size = tuple(data['tile_size'])
        self.dimensions = tuple(data['dimensions'])

        for loc in data['grid_tiles']:
            for layer in data['grid_tiles'][loc]:
                tile_data = data['grid_tiles'][loc][layer]
                if spawn_hook(tile_data, True):
                    custom_data = tile_data.get('c', '')
                    self.insert(
                        Tile(tile_data['group'], tile_id=tuple(tile_data['tile_id']),
                             pos=tuple(tile_data['pos']), layer=tile_data['layer'],
                             custom_data=custom_data))

        for tile_data in data['offgrid_tiles']['objects'].values():
            if spawn_hook(tile_data, False):
                custom_data = tile_data.get('c', '')
                self.insert(
                    Tile(tile_data['group'], tile_id=tuple(tile_data['tile_id']),
                         pos=tuple(tile_data['pos']), layer=tile_data['layer'],
                         custom_data=custom_data), ongrid=False)

    def insert(self, tile, ongrid=True):
        tile.attach(self, ongrid=ongrid)

        if ongrid:
            if self.demensional_lock and not self.in_map(tile.grid_pos):
                return

            if tile.grid_pos not in self.grid_tiles:
                self.grid_tiles[tile.grid_pos] = {}

            self.grid_tiles[tile.grid_pos][tile.layer] = tile

            if tile.group in ('grass', 'bridge', '01') and tile.physics_type:
                if tile.grid_pos not in self.physics_map:
                    self.physics_map[tile.grid_pos] = []

                self.physics_map[tile.grid_pos].append((self.physics_priority[tile.physics_type], self.i, tile))
                self.physics_map[tile.grid_pos].sort(reverse=True)
                self.i += 1
        else:
            pos = (tile.raw_pos[0] / self.tile_size[0], tile.raw_pos[1] / self.tile_size[1])
            if self.demensional_lock and not self.in_map(pos):
                return

            self.offgrid_tiles.add_raw(tile, tile.rect, tag=True)

        return True

    def is_walkable_pos(self, grid_pos, check_layer=None):
        if not self.in_map(grid_pos):
            return False

        if grid_pos not in self.grid_tiles:
            return True

        tiles = self.grid_tiles[grid_pos]

        if check_layer is not None:
            if check_layer in tiles:
                return tiles[check_layer].walkable
            return True
        else:
            for tile in tiles.values():
                if not tile.walkable:
                    return False
            return True

    def is_walkable_world_pos(self, world_pos, check_layer=None):
        grid_pos = (int(world_pos[0] // self.tile_size[0]), int(world_pos[1] // self.tile_size[1]))
        return self.is_walkable_pos(grid_pos, check_layer)

    def get_walkable_positions_in_rect(self, rect, check_layer=None):
        walkable_positions = []
        for loc in self.rect_grid_locs(rect):
            if self.is_walkable_pos(loc, check_layer):
                walkable_positions.append(loc)
        return walkable_positions

    def area_masks(self, rect):
        surfs = {}
        for loc in self.rect_grid_locs(rect):
            if loc in self.grid_tiles:
                layers = self.grid_tiles[loc]
                for layer in layers:
                    if layer not in surfs:
                        surfs[layer] = pygame.Surface(rect.size, pygame.SRCALPHA)
                    tile = layers[layer]
                    tile.primitive_render(surfs[layer], offset=rect.topleft)

        return {layer: pygame.mask.from_surface(surfs[layer]) for layer in surfs}

    def optimize_area(self, rect, layer=0):
        masks = self.area_masks(rect)
        layer_ids = sorted(list(masks))

        if layer in masks:
            involved_layers = layer_ids[layer_ids.index(layer) + 1:]

            if involved_layers:
                combined_mask = masks[involved_layers[0]]

                for top_layer in involved_layers[1:]:
                    combined_mask.draw(masks[top_layer], (0, 0))

                combined_mask.invert()

                for loc in self.rect_grid_locs(rect):
                    if loc in self.grid_tiles and layer in self.grid_tiles[loc]:
                        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                        tile = self.grid_tiles[loc][layer]
                        tile.primitive_render(surf, offset=rect.topleft)
                        tile_mask = pygame.mask.from_surface(surf)

                        if not tile_mask.overlap_area(combined_mask, (0, 0)):
                            self.grid_delete(loc, layer=layer)

    def autotile(self, rect=None, layer=0):
        if rect:
            locs = []
            for loc in self.rect_grid_locs(rect):
                if loc in self.grid_tiles:
                    locs.append(self.grid_tiles[loc])
        else:
            locs = list(self.grid_tiles.values())

        for loc in locs:
            if layer in loc:
                tile = loc[layer]
                if tile.group in G.assets.autotile_config['assignment']:
                    assignment = G.assets.autotile_config['assignment'][tile.group]
                    checks = G.assets.autotile_config['checks'][assignment]
                    neighbors = tile.neighbors(checks, handle_edge=True)

                    for nloc in checks:
                        if nloc in neighbors:
                            if neighbors[nloc] == 'edge':
                                neighbors[nloc] = set(('something', 'self'))
                            else:
                                group = neighbors[nloc].group
                                neighbors[nloc] = set(('something', group))
                                if group == tile.group:
                                    neighbors[nloc].add('self')
                                else:
                                    neighbors[nloc].add('notself')
                        else:
                            neighbors[nloc] = set(('none', 'notself'))

                    new_type = None
                    mappings = G.assets.autotile_config['mappings'][assignment]

                    for tile_type, tile_rules in mappings.items():
                        if tile_rules == 'default':
                            new_type = tile_type
                            continue

                        valid = True
                        for rule in tile_rules:
                            if rule[2] not in neighbors[tuple(rule[:2])]:
                                valid = False
                                break

                        if valid:
                            new_type = tile_type

                    if new_type:
                        tile.change_id(new_type)

    def floodfill(self, tile):
        check_locs = {tile.grid_pos}
        fill_locs = set()
        borders = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        while check_locs and len(fill_locs) <= 2048:
            loc = check_locs.pop()

            valid = True
            if loc in self.grid_tiles and tile.layer in self.grid_tiles[loc]:
                valid = False
            if not self.in_map(loc):
                valid = False

            if valid:
                fill_locs.add(loc)
                for border in borders:
                    check_loc = (loc[0] + border[0], loc[1] + border[1])
                    if check_loc not in fill_locs and check_loc not in check_locs:
                        check_locs.add(check_loc)

        for loc in fill_locs:
            self.insert(tile.shift_clone(loc))

    def grid_delete(self, grid_pos, layer=None):
        if grid_pos in self.grid_tiles:
            if layer is None:
                del self.grid_tiles[grid_pos]
                if grid_pos in self.physics_map:
                    del self.physics_map[grid_pos]
            elif layer in self.grid_tiles[grid_pos]:
                del self.grid_tiles[grid_pos][layer]
                if not self.grid_tiles[grid_pos]:
                    del self.grid_tiles[grid_pos]

    def rect_delete(self, rect, layer=None):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])

        for y in range(topleft[1], bottomright[1] + 1):
            for x in range(topleft[0], bottomright[0] + 1):
                grid_pos = (x, y)
                if grid_pos in self.grid_tiles:
                    tile_r = pygame.Rect(grid_pos[0] * self.tile_size[0], grid_pos[1] * self.tile_size[1],
                                         *self.tile_size)
                    if tile_r.colliderect(rect):
                        if layer is not None:
                            if layer in self.grid_tiles[grid_pos]:
                                if grid_pos in self.physics_map:
                                    for tile in self.physics_map[grid_pos][:]:
                                        if tile[1] == self.grid_tiles[grid_pos][layer]:
                                            self.physics_map[grid_pos].remove(tile)
                                            if not self.physics_map[grid_pos]:
                                                del self.physics_map[grid_pos]
                                del self.grid_tiles[grid_pos][layer]
                                if not self.grid_tiles[grid_pos]:
                                    del self.grid_tiles[grid_pos]
                        else:
                            del self.grid_tiles[grid_pos]
                            if grid_pos in self.physics_map:
                                del self.physics_map[grid_pos]

        tiles = self.offgrid_tiles.query(rect)
        if layer is not None:
            for tile in tiles:
                if tile.layer == layer and tile.rect.colliderect(rect):
                    self.offgrid_tiles.delete(tile)
        else:
            for tile in tiles:
                if tile.rect.colliderect(rect):
                    self.offgrid_tiles.delete(tile)

    def nearby_grid_physics(self, pos):
        grid_pos = (pos[0] // self.tile_size[0], pos[1] // self.tile_size[1])
        tiles = []

        for border in BORDERS:
            check_pos = (grid_pos[0] + border[0], grid_pos[1] + border[1])
            if check_pos in self.physics_map:
                tiles.append(self.physics_map[check_pos][0][2])

        return tiles

    def gridtile(self, pos):
        return self.grid_tiles.get(pos, {})

    def physics_ongridtile(self, pos):
        return self.physics_map[pos][0][2] if pos in self.physics_map else None

    def physics_gridtile(self, pos):
        grid_pos = (pos[0] // self.tile_size[0], pos[1] // self.tile_size[1])
        return self.physics_map[grid_pos][0][2] if grid_pos in self.physics_map else None

    def count_tiles(self):
        count = {'grid': 0, 'offgrid': len(self.offgrid_tiles.objects)}

        for loc in self.grid_tiles:
            count['grid'] += len(self.grid_tiles[loc])

        return count

    def count_rect_tiles(self, rect):
        layers = self.rect_select(rect)
        return sum(len(layers[layer]) for layer in layers)

    def visible_layer_contains(self, rect, layer):
        tile_types = set()
        layers = self.rect_select(rect)

        if layer in layers:
            for tile in layers[layer]:
                tile_types.add(tile.group)

        return tile_types

    def render_prep(self, rect, offset=(0, 0), group='default'):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])
        blits = []

        for y in range(topleft[1], bottomright[1] + 1):
            for x in range(topleft[0], bottomright[0] + 1):
                tiles = self.gridtile((x, y))
                for tile in tiles.values():
                    blits.append((tile.img, (tile.raw_pos[0] + tile.offset[0] - offset[0],
                                             tile.raw_pos[1] + tile.offset[1] - offset[1]), tile.layer, group))

        for tile in self.offgrid_tiles.query(rect):
            blits.append(
                (tile.img, (tile.raw_pos[0] + tile.offset[0] - offset[0],
                            tile.raw_pos[1] + tile.offset[1] - offset[1]),
                 tile.layer, group))

        return blits

    def renderz(self, rect, offset=(0, 0), group='default'):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])

        for y in range(topleft[1], bottomright[1] + 1):
            for x in range(topleft[0], bottomright[0] + 1):
                for tile in self.gridtile((x, y)).values():
                    if tile.group != 'walk_zone':
                        tile.render(offset=offset, group=group)

        for tile in self.offgrid_tiles.query(rect):
            tile.render(offset=offset, group=group)

    def renderz_only(self, rect, offset=(0, 0), group='default', only=set()):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])

        for y in range(topleft[1], bottomright[1] + 1):
            for x in range(topleft[0], bottomright[0] + 1):
                for tile in self.gridtile((x, y)).values():
                    if tile.group in only:
                        tile.render(offset=offset, group=group)

        for tile in self.offgrid_tiles.query(rect):
            if tile.group in only:
                tile.render(offset=offset, group=group)

    def rect_grid_locs(self, rect):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])
        return [(x, y) for y in range(topleft[1], bottomright[1] + 1)
                for x in range(topleft[0], bottomright[0] + 1)]

    def rect_select(self, rect, gridonly=False):
        topleft = (rect.x // self.tile_size[0], rect.y // self.tile_size[1])
        bottomright = (rect.right // self.tile_size[0], rect.bottom // self.tile_size[1])
        layers = {}

        for y in range(topleft[1], bottomright[1] + 1):
            for x in range(topleft[0], bottomright[0] + 1):
                tiles = self.gridtile((x, y))
                for k, v in tiles.items():
                    if k not in layers:
                        layers[k] = []
                    layers[k].append(v)

        if not gridonly:
            for tile in self.offgrid_tiles.query(rect):
                if tile.layer not in layers:
                    layers[tile.layer] = []
                layers[tile.layer].append(tile)

        return layers