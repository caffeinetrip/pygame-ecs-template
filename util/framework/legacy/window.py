from util.framework.components.window import WindowComponent

class Window:
    def __init__(self, dimensions=(640, 480), caption='window', flags=0, fps_cap=60, dt_cap=1, opengl=False,
                 frag_path=None):
        from util.framework import world
        self.e = world
        self._name = "Window"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.window_component = self.entity.add_component(WindowComponent,
                                                          dimensions,
                                                          caption,
                                                          flags,
                                                          fps_cap,
                                                          dt_cap,
                                                          opengl,
                                                          frag_path)

    @property
    def opengl(self):
        return self.window_component.opengl

    @opengl.setter
    def opengl(self, value):
        self.window_component.opengl = value

    @property
    def frag_path(self):
        return self.window_component.frag_path

    @frag_path.setter
    def frag_path(self, value):
        self.window_component.frag_path = value

    @property
    def dimensions(self):
        return self.window_component.dimensions

    @dimensions.setter
    def dimensions(self, value):
        self.window_component.dimensions = value

    @property
    def flags(self):
        return self.window_component.flags

    @flags.setter
    def flags(self, value):
        self.window_component.flags = value

    @property
    def fps_cap(self):
        return self.window_component.fps_cap

    @fps_cap.setter
    def fps_cap(self, value):
        self.window_component.fps_cap = value

    @property
    def dt_cap(self):
        return self.window_component.dt_cap

    @dt_cap.setter
    def dt_cap(self, value):
        self.window_component.dt_cap = value

    @property
    def background_color(self):
        return self.window_component.background_color

    @background_color.setter
    def background_color(self, value):
        self.window_component.background_color = value

    @property
    def time(self):
        return self.window_component.time

    @time.setter
    def time(self, value):
        self.window_component.time = value

    @property
    def start_time(self):
        return self.window_component.start_time

    @start_time.setter
    def start_time(self, value):
        self.window_component.start_time = value

    @property
    def runtime_(self):
        return self.window_component.runtime_

    @runtime_.setter
    def runtime_(self, value):
        self.window_component.runtime_ = value

    @property
    def frames(self):
        return self.window_component.frames

    @frames.setter
    def frames(self, value):
        self.window_component.frames = value

    @property
    def frame_log(self):
        return self.window_component.frame_log

    @frame_log.setter
    def frame_log(self, value):
        self.window_component.frame_log = value

    @property
    def screen(self):
        return self.window_component.screen

    @screen.setter
    def screen(self, value):
        self.window_component.screen = value

    @property
    def clock(self):
        return self.window_component.clock

    @clock.setter
    def clock(self, value):
        self.window_component.clock = value

    @property
    def last_frame(self):
        return self.window_component.last_frame

    @last_frame.setter
    def last_frame(self, value):
        self.window_component.last_frame = value

    @property
    def dt(self):
        return self.window_component.dt

    @dt.setter
    def dt(self, value):
        self.window_component.dt = value

    @property
    def tremor(self):
        return self.window_component.tremor

    @tremor.setter
    def tremor(self, value):
        self.window_component.tremor = value

    @property
    def fight(self):
        return self.window_component.fight

    @fight.setter
    def fight(self, value):
        self.window_component.fight = value

    @property
    def transition(self):
        return self.window_component.transition

    @transition.setter
    def transition(self, value):
        self.window_component.transition = value

    @property
    def transition_speed(self):
        return self.window_component.transition_speed

    @transition_speed.setter
    def transition_speed(self, value):
        self.window_component.transition_speed = value

    @property
    def transitioning(self):
        return self.window_component.transitioning

    @transitioning.setter
    def transitioning(self, value):
        self.window_component.transitioning = value

    @property
    def e_transition(self):
        return self.window_component.e_transition

    @e_transition.setter
    def e_transition(self, value):
        self.window_component.e_transition = value

    @property
    def e_transition_speed(self):
        return self.window_component.e_transition_speed

    @e_transition_speed.setter
    def e_transition_speed(self, value):
        self.window_component.e_transition_speed = value

    @property
    def e_transitioning(self):
        return self.window_component.e_transitioning

    @e_transitioning.setter
    def e_transitioning(self, value):
        self.window_component.e_transitioning = value

    @property
    def open(self):
        return self.window_component.open

    @open.setter
    def open(self, value):
        self.window_component.open = value

    @property
    def noise_gain(self):
        return self.window_component.noise_gain

    @noise_gain.setter
    def noise_gain(self, value):
        self.window_component.noise_gain = value

    @property
    def render_object(self):
        return self.window_component.render_object

    @render_object.setter
    def render_object(self, value):
        self.window_component.render_object = value

    @property
    def fps(self):
        return self.window_component.fps

    def start_transition(self, alternative=False):
        self.window_component.start_transition(alternative)

    def update_transition(self, alternative=False):
        self.window_component.update_transition(alternative)

    def cycle(self, uniforms):
        self.window_component.cycle(uniforms)

    def delete(self):
        self.entity.delete()