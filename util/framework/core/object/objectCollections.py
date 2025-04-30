import pygame
from util.framework.core.interactors.interactor import Interactor
from .ObjectSectors import ObjectSectors


class ObjectCollections(Interactor):
    def __init__(self, sector_size=64, spatial_collections=[]):
        super().__init__()
        self.collections = {}
        self.processing = False
        self.pending_items = []

        self.spatial_collections = set(spatial_collections)
        self.object_sectors = ObjectSectors(sector_size=sector_size)

    def configure_spatial_collections(self, spatial_collections=[]):
        self.spatial_collections = set(spatial_collections)

    def register(self, game_object, collection):
        if self.processing:
            self.pending_items.append((game_object, collection))
        else:
            if collection in self.spatial_collections:
                self.object_sectors.register(game_object, collection_name=collection)
            else:
                if collection not in self.collections:
                    self.collections[collection] = []
                self.collections[collection].append(game_object)

    def process(self, collection=None, release_lock=True, view_area=pygame.Rect(0, 0, 100, 100)):
        time_delta = self.get_component_in_parent('Window').dt

        if len(self.spatial_collections) and not collection:
            self.object_sectors.refresh_visible(view_area)
            self.collections.update(self.object_sectors.visible_objects)

        self.processing = True
        if collection:
            if collection in self.collections:
                for game_object in self.collections[collection].copy():
                    should_remove = game_object.tick(time_delta)
                    if should_remove:
                        self.collections[collection].remove(game_object)
                        if collection in self.spatial_collections:
                            self.object_sectors.unregister(game_object)
        else:
            for collection in self.collections:
                self.process(collection, release_lock=False)

        if release_lock:
            self.processing = False
            if len(self.pending_items):
                for item in self.pending_items:
                    self.register(*item)
                self.pending_items = []

    def draw(self, surface, collection=None, camera_offset=(0, 0)):
        if collection:
            if collection in self.collections:
                for game_object in self.collections[collection]:
                    game_object.draw(surface, camera_offset=camera_offset)
        else:
            for collection in self.collections:
                self.draw(surface, collection=collection, camera_offset=camera_offset)

    def draw_layered(self, collection=None, layer_group='main', camera_offset=(0, 0)):
        if collection:
            if collection in self.collections:
                for game_object in self.collections[collection]:
                    game_object.draw_layered(group=layer_group, camera_offset=camera_offset)
        else:
            for collection in self.collections:
                self.draw_layered(collection=collection, layer_group=layer_group, camera_offset=camera_offset)