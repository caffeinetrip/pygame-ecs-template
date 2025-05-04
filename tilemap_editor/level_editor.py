import os
import sys
import math

import pygame
from pygame.locals import *
from tkinter import filedialog
from tkinter import *

try:
    import scripts.pygpen as pygpen
    from scripts.pygpen.utils.io import read_json, write_json
except ImportError:
    import scripts.pygpen as pygpen
    from scripts.pygpen.utils.io import read_json, write_json

level_editor_config = read_json('editor_assets/level_editor_config.json')
class Draggable(pygpen.Element):
    def __init__(self, pos, radius=10, snap=(8, 8)):
        super().__init__()
        self.pos = list(pos)
        self.dragging = False
        self.radius = radius
        self.hovered = False
        self.last_mpos = [0, 0]
        self.snap = tuple(snap)
    
    @property
    def reduced_snap_pos(self):
        return (math.floor((self.pos[0] + self.snap[0] / 2) / self.snap[0]), math.floor((self.pos[1] + self.snap[1] / 2) / self.snap[1]))
    
    @property
    def snap_pos(self):
        return (math.floor((self.pos[0] + self.snap[0] / 2) / self.snap[0]) * self.snap[0], math.floor((self.pos[1] + self.snap[1] / 2) / self.snap[1]) * self.snap[1])
    
    @property
    def rect(self):
        return pygame.Rect(self.pos[0] - self.radius / 2, self.pos[1] - self.radius / 2, self.radius, self.radius)
    
    def update(self, mpos):
        self.hovered = False
        if self.rect.collidepoint(mpos):
            self.hovered = True
            if self.e['Input'].pressed('place'):
                self.dragging = True
        if self.e['Input'].released('place'):
            self.dragging = False
            self.pos = list(self.snap_pos)
        
        if self.dragging:
            self.pos[0] += mpos[0] - self.last_mpos[0]
            self.pos[1] += mpos[1] - self.last_mpos[1]
        self.last_mpos = list(mpos)
    
    def render(self, offset=(0, 0)):
        color = (255, 255, 255) if (self.hovered or self.dragging) else (100, 100, 100)
        radius = self.radius if (self.hovered or self.dragging) else self.radius / 2
        width = 2 if self.dragging else 1
        self.e['Renderer'].renderf(pygame.draw.circle, color, (self.snap_pos[0] - offset[0], self.snap_pos[1] - offset[1]), radius, width, z=999996)

class Game(pygpen.PygpenGame):
    def load(self):
        self.font_path = 'editor_assets/fonts' if os.path.exists('editor_assets/fonts') else None
        pygpen.init(spritesheet_path=level_editor_config['spritesheet_path'], 
                    input_path='editor_assets/level_editor_keys.json',
                    font_path=self.font_path,
                    flags=pygame.FULLSCREEN)

        self.display = pygame.Surface((640, 360))
        
        self.tilemap = pygpen.Tilemap(tile_size=tuple(level_editor_config['tile_size']))
        self.tile_size = self.tilemap.tile_size
        
        self.camera = pygpen.Camera(self.display.get_size())
        self.camera.move((-self.tilemap.tile_size[0] * 4, -self.tilemap.tile_size[1] * 4))
        
        self.spritesheet_thumbs = {}
        for spritesheet_id, spritesheet in self.e['Assets'].spritesheets.items():
            self.spritesheet_thumbs[spritesheet_id] = self.generate_spritesheet_thumb(spritesheet)
        self.thumb_keys = list(self.spritesheet_thumbs.keys())
        self.menu_scroll = [0, 0, 0]
        self.selected_ss_index = 0
        self.current_tile = None
        self.grid = True
        self.grid_mode = True
        self.on_menu = False
        self.layer = 0
        self.custom_data = ''
        self.mpos = (0, 0)
        self.mouse_idle = [(0, 0), 0]
        self.layer_opacity = False
        self.selection = [None, None]
        self.dimension_selector = Draggable((self.tile_size[0] * self.tilemap.dimensions[0], self.tile_size[1] * self.tilemap.dimensions[1]), snap=tuple(self.tile_size))
        self.metrics = {'tile': self.current_tile, 'pos': (0, 0), 'layer': self.layer, 'map': str(self.tilemap.dimensions[0]) + 'x' + str(self.tilemap.dimensions[1]) + ' (' + str(self.tile_size[0]) + 'x' + str(self.tile_size[1]) + ')',
                        'total': 0, 'visible': 0, 'grid': 0, 'offgrid': 0, 'vlc': tuple(), 'custom': self.custom_data}
        self.metrics_order = ['tile', 'pos', 'layer', 'map', 'total', 'visible', 'grid', 'offgrid', 'vlc', 'custom']
        self.textbox = pygpen.Textbox('small_font', 200, return_event=lambda buffer: self.set_custom_data(buffer.text))
        
        self.history_shalk = []
        self.history = []
        self.max_history_size = 50 
    
    def set_custom_data(self, data):
        self.custom_data = data
        self.metrics['custom'] = self.custom_data
        
    @property
    def selected_ss(self):
        if len(self.thumb_keys):
            ss_id = self.thumb_keys[self.selected_ss_index]
            return self.e['Assets'].spritesheets[ss_id]
        
    @property
    def hovered_loc(self):
        if self.grid:
            return (int((self.mpos[0] + self.camera[0]) // self.tile_size[0]), int((self.mpos[1] + self.camera[1]) // self.tile_size[1]))
        else:
            return (math.floor(self.mpos[0] + self.camera[0]), math.floor(self.mpos[1] + self.camera[1]))
        
    @property
    def offgrid_hovered_loc(self):
        return (math.floor(self.mpos[0] + self.camera[0]), math.floor(self.mpos[1] + self.camera[1]))
    
    @property
    def selection_rect(self):
        if self.selection[1]:
            return pygpen.game_math.rectify(self.selection[0], self.selection[1])
        
    def save_state_shalk(self):
        if len(self.history_shalk) >= self.max_history_size:
            self.history_shalk.pop(0)
        self.history_shalk.append({
            'tiles': self.tilemap.get_tiles(),  
            'dimensions': self.tilemap.dimensions,
            'tile_size': self.tilemap.tile_size,
        })
        
    def save_state(self):
        self.history.append(self.history_shalk[len(self.history_shalk)-1])
        self.history_shalk.pop(len(self.history_shalk)-1)

    def undo(self):

        if self.history:
            state = self.history[len(self.history)-1]
            
            self.tilemap.replace_tiles(state['tiles'])
            self.tilemap.dimensions = state['dimensions']
            self.tilemap.tile_size = state['tile_size']
            
            self.history.pop(len(self.history)-1)
            
    def generate_spritesheet_thumb(self, spritesheet):
        thumb_surf = pygame.Surface((64, 16), pygame.SRCALPHA)
        i = 0
        for loc in spritesheet['assets']:
            if loc[0] == 0:
                thumb_surf.blit(pygame.transform.scale(spritesheet['assets'][loc], (16, 16)), (i * 8, 0))
                i += 1
        return thumb_surf
    
    def update_metrics(self):
        tcount = self.tilemap.count_tiles()
        vcount = self.tilemap.count_rect_tiles(pygame.Rect(*self.camera, *self.display.get_size()))
        self.metrics = {'map': str(self.tilemap.dimensions[0]) + 'x' + str(self.tilemap.dimensions[1]) + ' (' + str(self.tile_size[0]) + 'x' + str(self.tile_size[1]) + ')',
                        'total': sum(tcount.values()), 'visible': vcount, 'grid': tcount['grid'], 'offgrid': tcount['offgrid'],
                        'vlc': tuple(self.tilemap.visible_layer_contains(pygame.Rect(*self.camera, *self.display.get_size()), self.layer)), 'custom': self.custom_data}
        
    def update(self):
        self.display.fill((0, 0, 0))

        camera_movement = [0, 0]
        if not self.e['Input'].holding('lctrl'):
            if self.e['Input'].holding('camera_right'):
                camera_movement[0] += self.tile_size[0] / 4
            if self.e['Input'].holding('camera_left'):
                camera_movement[0] -= self.tile_size[0] / 4
            if self.e['Input'].holding('camera_down'):
                camera_movement[1] += self.tile_size[1] / 4
            if self.e['Input'].holding('camera_up'):
                camera_movement[1] -= self.tile_size[1] / 4
        self.camera.move(camera_movement)
        self.camera.update()
        
        mpos = (self.e['Mouse'].pos[0] * (640 / self.e['Window'].screen.get_width()), self.e['Mouse'].pos[1] * (360 / self.e['Window'].screen.get_height()))
        self.mpos = mpos
        hovering = 'world'
        self.on_menu = False
        if mpos[0] < 70:
            self.on_menu = True
            hovering = 'tile_select'
            if mpos[1] < 80:
                hovering = 'ss_select'
                
        if mpos != self.mouse_idle[0]:
            self.mouse_idle = [mpos, 0]
        else:
            self.mouse_idle[1] += self.e['Window'].dt
        if self.mouse_idle[1] > 1.5:
            self.update_metrics()
            self.mouse_idle[1] = 0
        
        self.dimension_selector.update((mpos[0] + self.camera[0], mpos[1] + self.camera[1]))
        self.dimension_selector.pos[0] = max(self.tile_size[0] * 2, self.dimension_selector.pos[0])
        self.dimension_selector.pos[1] = max(self.tile_size[1] * 2, self.dimension_selector.pos[1])
        self.tilemap.dimensions = self.dimension_selector.reduced_snap_pos
        
        for blit in sorted(self.tilemap.render_prep(pygame.Rect(*self.camera, *self.display.get_size()), offset=self.camera), key=lambda x: x[2]):
            if self.layer_opacity and (blit[2] != self.layer):
                blit[0].set_alpha(100)
            self.display.blit(blit[0], blit[1])
            blit[0].set_alpha(255)
        offset = (self.camera.pos[0] % self.tile_size[0], self.camera.pos[1] % self.tile_size[1])
        grid_surf = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        pygame.draw.line(grid_surf, (255, 255, 255), (-self.camera[0], 0), (-self.camera[0], self.display.get_height()), 3)
        pygame.draw.line(grid_surf, (255, 255, 255), (0, -self.camera[1]), (self.display.get_width(), -self.camera[1]), 3)
        pygame.draw.line(grid_surf, (255, 255, 0), (self.tilemap.dimensions[0] * self.tilemap.tile_size[0] - self.camera[0], max(0, -self.camera[1])), (self.tilemap.dimensions[0] * self.tilemap.tile_size[0] - self.camera[0], min(self.display.get_height(), self.tilemap.dimensions[1] * self.tilemap.tile_size[1] - self.camera[1])), 3)
        pygame.draw.line(grid_surf, (255, 255, 0), (max(0, -self.camera[0]), self.tilemap.dimensions[1] * self.tilemap.tile_size[1] - self.camera[1]), (min(self.display.get_width(), self.tilemap.dimensions[0] * self.tilemap.tile_size[0] - self.camera[0]), self.tilemap.dimensions[1] * self.tilemap.tile_size[1] - self.camera[1]), 3)
        for x in range(self.display.get_width() // self.tile_size[0] + 1):
            pygame.draw.line(grid_surf, (100, 100, 100), (x * self.tile_size[0] - offset[0], 0), (x * self.tile_size[0] - offset[0], self.display.get_height()))
        for y in range(self.display.get_height() // self.tile_size[0] + 1):
            pygame.draw.line(grid_surf, (100, 100, 100), (0, y * self.tile_size[1] - offset[1]), (self.display.get_width(), y * self.tile_size[1] - offset[1]))
        grid_surf.set_alpha(100)
        self.e['Renderer'].blit(grid_surf, (0, 0), z=999996)
        
        self.dimension_selector.render(offset=self.camera)
        
        if self.selection[0]:
            endpoint = self.selection[1] if self.selection[1] else self.offgrid_hovered_loc
            rect = pygpen.game_math.rectify(self.selection[0], endpoint)
            rect.x -= self.camera[0]
            rect.y -= self.camera[1]
            self.e['Renderer'].renderf(pygame.draw.rect, (255, 0, 255), rect, 1, z=999997)
        
        menu_surf = pygame.Surface((70, self.display.get_height()), pygame.SRCALPHA)
        menu_surf.fill((40, 40, 40, 180))
        if len(self.thumb_keys):
            for i in range(4):
                lookup_i = (self.menu_scroll[0] + i) % len(self.thumb_keys)
                thumb = self.spritesheet_thumbs[self.thumb_keys[lookup_i]]
                thumb_r = pygame.Rect(3, 3 + i * 19, 64, 16)
                if thumb_r.collidepoint(mpos):
                    if self.e['Input'].pressed('place'):
                        self.selected_ss_index = lookup_i
                        self.menu_scroll[1] = 0
                        self.menu_scroll[2] = 0
                menu_surf.blit(thumb, (3, 3 + i * 19))
        if self.selected_ss:
            for tile_loc in self.selected_ss['assets']:
                tile = self.selected_ss['assets'][tile_loc]
                if tile_loc[1] - self.menu_scroll[2] >= 0:
                    tile_r = pygame.Rect(3 + (tile_loc[0] - self.menu_scroll[1]) * 18, 83 + (tile_loc[1] - self.menu_scroll[2]) * 18, 16, 16)
                    if tile_r.collidepoint(mpos):
                        if self.e['Input'].pressed('place'):
                            self.current_tile = (self.thumb_keys[self.selected_ss_index], tile_loc)
                    menu_surf.blit(pygame.transform.scale(tile, (16, 16)), (3 + (tile_loc[0] - self.menu_scroll[1]) * 18, 83 + (tile_loc[1] - self.menu_scroll[2]) * 18))
        pygame.draw.line(menu_surf, (120, 120, 120), (menu_surf.get_width() - 1, 0), (menu_surf.get_width() - 1, menu_surf.get_height() - 1))
        pygame.draw.line(menu_surf, (120, 120, 120), (0, 80), (70, 80))
        self.e['Renderer'].blit(menu_surf, (0, 0), z=999998)
        
        if self.current_tile:
            tile_img = self.e['Assets'].spritesheets[self.current_tile[0]]['assets'][self.current_tile[1]].copy()
            tile_img.set_alpha(128)
            if self.grid:
                pos = (self.hovered_loc[0] * self.tile_size[0] - self.camera[0], self.hovered_loc[1] * self.tile_size[1] - self.camera[1])
                self.e['Renderer'].renderf(pygame.draw.rect, (255, 255, 255), pygame.Rect(*pos, *self.tile_size), 1, z=999998)
                self.e['Renderer'].blit(tile_img, pos, z=999998)
            else:
                self.e['Renderer'].blit(tile_img, mpos, z=999998)
        
        if self.font_path:
            self.metrics['tile'] = self.current_tile
            self.metrics['layer'] = self.layer
            self.metrics['pos'] = self.hovered_loc
            for i, metric in enumerate(self.metrics_order):
                text = metric + ': ' + str(self.metrics[metric])
                w = self.e['Text']['small_font'].width(text)
                self.e['Text']['small_font'].renderz(text, (self.display.get_width() - 4 - w, 4 + 10 * i), z=999999)
            
            if self.textbox.bound:
                self.e['Renderer'].blit(self.textbox.surf, (100, 100), z=999999)
        
        self.e['Renderer'].cycle({'default': self.display})
        
        if self.e['Input'].pressed('quit'):
            pygame.quit()
            sys.exit()
            
        if self.e['Input'].pressed('layer_up'):
            if hovering == 'ss_select':
                self.menu_scroll[0] -= 1
            elif hovering == 'tile_select':
                if self.e['Input'].holding('lctrl'):
                    self.menu_scroll[1] += 1
                else:
                    self.menu_scroll[2] += 1
            elif hovering == 'world':
                self.layer += 1
        if self.e['Input'].pressed('layer_down'):
            if hovering == 'ss_select':
                self.menu_scroll[0] += 1
            elif hovering == 'tile_select':
                if self.e['Input'].holding('lctrl'):
                    self.menu_scroll[1] = max(0, self.menu_scroll[2] - 1)
                    
                else:
                    self.menu_scroll[2] = max(0, self.menu_scroll[1] - 1)
            elif hovering == 'world':
                self.layer -= 1
        
        # CUSTOM DATA
        if self.e['Input'].pressed('custom_data'):
            self.textbox.bind()
            
        # CHANGE GRID MODE
        if self.e['Input'].pressed('grid_toggle'):
            self.grid_mode = not self.grid_mode
        
        # CHANGE LAYER MODE
        if self.e['Input'].pressed('layer_toggle'):
            self.layer_opacity = not self.layer_opacity
        
        # SELECT
        if self.e['Input'].pressed('select'):
            if not self.selection[0]:
                self.selection[0] = self.offgrid_hovered_loc
            elif not self.selection[1]:
                self.selection[1] = self.offgrid_hovered_loc
            else:
                self.selection = [None, None]
    
        if self.e['Input'].pressed('delete'):
            print(1)
            if self.selection_rect:
                self.tilemap.rect_delete(self.selection_rect, layer=self.layer)
                
        # LEFT CTRL MODE
        if self.e['Input'].holding('lctrl'):
            if self.e['Input'].pressed('save'):
                self.tilemap.save('save.pmap')
            
            if self.e['Input'].holding('lctrl'):
                if self.e['Input'].pressed('undo'):
                    self.undo()
        
        # LOAD MAP
        if self.e['Input'].pressed('load'):
            root = Tk()
            root.withdraw()
            filename = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Select Map",filetypes = (("pygpen maps", "*.pmap"), ("json files","*.json"), ("all files","*.*")))
            if filename != '':
                self.tilemap.load(filename)
                self.dimension_selector.pos = [self.tile_size[0] * self.tilemap.dimensions[0], self.tile_size[1] * self.tilemap.dimensions[1]]
                self.dimension_selector.snap = tuple(self.tile_size)
        
        # CHEK MENU
        if self.on_menu:
            self.grid = False
        else:
            self.grid = self.grid_mode
        
        if self.current_tile and not self.dimension_selector.dragging:
            if hovering == 'world':
                next_tile = pygpen.Tile(*self.current_tile, self.hovered_loc, layer=self.layer, custom_data=self.custom_data)
                if self.grid:
                    if self.e['Input'].pressed('place'):
                        self.save_state_shalk()
                    
                    if self.e['Input'].holding('place'):
                        self.tilemap.insert(next_tile)
                        
                    if self.e['Input'].pressed('floodfill'):
                        self.save_state_shalk()
                        self.tilemap.floodfill(next_tile)
                        
                else:
                    if self.e['Input'].pressed('place'):
                        self.save_state_shalk()
                        self.tilemap.insert(next_tile, ongrid=False)
                        
                if self.e['Input'].pressed('remove'):
                    self.save_state_shalk()
                        
                if self.e['Input'].holding('remove'):
                    self.tilemap.rect_delete(pygame.Rect(*self.offgrid_hovered_loc, 2, 2), layer=self.layer)
                
                if self.e['Input'].released('place') or self.e['Input'].released('floodfill') or self.e['Input'].released('remove'):
                    self.save_state()
        
        self.e['Window'].screen.blit(pygame.transform.scale(self.display, self.e['Window'].screen.get_size()), (0, 0))
        self.e['Window'].cycle()
        
Game().run() 