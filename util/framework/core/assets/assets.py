from util.framework.globals import G
from util.framework.core.component import Component
from util.framework.utils.assets import load_img_directory
from util.framework.utils.io import read_tjson
from util.framework.utils.spritesheets import load_spritesheets


class Assets(Component):
    def __init__(self, spritesheet_path=None, colorkey=(0, 0, 0)):
        super().__init__()
        self.spritesheet_path = spritesheet_path
        self.spritesheets = load_spritesheets(spritesheet_path, colorkey=colorkey) if spritesheet_path else {}
        self.autotile_config = self.parse_autotile_config(
            read_tjson(spritesheet_path + '/autotile.json')) if spritesheet_path else {}
        self.custom_tile_renderers = {}
        self.images = {}

    def load_folder(self, path, alpha=False, colorkey=None):
        self.images[path.split('/')[-1]] = load_img_directory(path, alpha=alpha, colorkey=colorkey)

    def enable(self, *args, **kwargs):
        pass

    def parse_autotile_config(self, config):
        checks = {}
        for mapping in config['mappings']:
            checks[mapping] = []
            for offset in config['mappings'][mapping]:
                if type(config['mappings'][mapping][offset]) != str:
                    for check in config['mappings'][mapping][offset]:
                        checks[mapping].append(tuple(check[:2]))
            checks[mapping] = list(set(checks[mapping]))
        config['checks'] = checks
        return config