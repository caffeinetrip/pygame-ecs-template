class Animation:
    def __init__(self, images, config=None, hard_copy=False):
        if not config:
            config = {}

        self.config = config.copy()

        if 'rate' not in self.config:
            self.config['rate'] = 1
        if 'repeat' not in self.config:
            self.config['repeat'] = True
        if 'frozen' not in self.config:
            self.config['frozen'] = False
        if 'durations' not in self.config:
            self.config['durations'] = [0.1 for i in range(len(images))]

        self.images = images
        if hard_copy:
            self.images = [img.copy() for img in self.images]

        self.frame = 0
        self.frame_time = 0
        self.paused = self.config['frozen']
        self.finished = False

    def copy(self):
        new_animation = Animation(self.images, config=self.config.copy())
        new_animation.frame = self.frame
        new_animation.frame_time = self.frame_time
        new_animation.paused = self.paused
        new_animation.finished = self.finished
        return new_animation

    def hard_copy(self):
        return Animation(self.images, config=self.config.copy(), hard_copy=True)

    @property
    def img(self):
        return self.images[max(min(len(self.images) - 1, self.frame), 0)]

    def update(self, dt):
        if not self.paused:
            self.frame_time += dt * self.config['rate']

            current_duration = self.config['durations'][max(min(len(self.images) - 1, self.frame), 0)]

            while self.frame_time >= current_duration:
                if (self.frame >= len(self.images) - 1) and (not self.config['repeat']):
                    self.finished = True
                    return

                self.frame_time -= current_duration
                self.frame = (self.frame + 1) % len(self.images)