# -*- coding: utf-8 -*-
"""
Created on Sat May 24 20:05:22 2014

@author: rkmaddox
"""

print('Running')  # noqa
import pyglet
import numpy as np
from pyglet.window import key
from time import sleep

pyglet.options['search_local_libs'] = True
control_target = True
vol_base = 0.01
vol_max = vol_base * 10 ** (30 / 20.)
vol_min = vol_base * 10 ** (-30 / 20.)

vol_joy = lambda j: (j.x + 1) / 2 * (vol_max - vol_min) + vol_min  # noqa

joysticks = pyglet.input.get_joysticks()
if joysticks:
    use_joystick = True
else:
    use_joystick = False
assert joysticks, 'No joystick device is connected'
joystick = joysticks[0]
joystick.open()


# =============================================================================
# Make this a classy party
# =============================================================================
class Maskers(object):
    def __init__(self, files=['maskers/NW_F_C.wav',
                              'maskers/NW_F_S.wav',
                              'maskers/NW_M_C.wav',
                              'maskers/NW_M_S.wav'], vol_base=0.01):
        self.files = files
        self.sources = [pyglet.media.load(f, streaming=False)
                        for f in self.files]
        self.duration = np.max([s.duration for s in self.sources])
        self.players = [pyglet.media.Player()
                        for _ in range(len(self.files))]
        self.mask_vol = vol_base
        self.location = 0
        self.gender = 0
        self.set_vols()
        for player in self.players:
            player.loop = True

    def loop(self, dt=None):
        for player, source in zip(self.players, self.sources):
            player.eos_action = 'loop'
            player.queue(source)
        for player in self.players:
            player.play()
        self.set_vols()

    def stop(self):
        for player in self.players:
            # player.next()
            player.pause()

    def set_gender(self, gender):
        self.gender = gender
        self.set_vols()

    def set_location(self, location):
        self.location = location
        self.set_vols()

    def set_mask_vol(self, vol):
        self.mask_vol = vol
        self.set_vols()

    def set_vols(self):
        self.play_ind = 2*self.gender + self.location
        self.vols = [0 for _ in range(len(self.files))]
        self.vols[self.play_ind] = self.mask_vol
        for p, v in zip(self.players, self.vols):
            p.volume = v
        # print([int(v > 0) for v in [p.volume for p in self.players]])
        # print([v for v in [p.volume for p in self.players]])

    def get_volume(self):
        return self.mask_vol

    def get_volume_db(self):
        return 20 * np.log10(self.get_volume())

    def set_volume(self, vol):
        self.mask_vol = vol
        self.set_vols()


class Target(object):
    def __init__(self, screen, file_name='targets/kix1953-ad2-trimmed.mp4',
                 max_vol=1.9952623149688795, show_label=True, vol_base=0.01):
        self._screen = screen
        self.file = file_name
        self.source = pyglet.media.load(self.file, streaming=True)
        self.player = pyglet.media.Player()
        self.duration = self.source.duration
        self.player.volume = vol_base
        self.max_vol = max_vol
        self.show = False
        self.show_label = show_label
        self.first_loop = True
        self.player.loop = True

    def loop(self, dt=None):
        # self.player.eos_action = 'loop'
        self.player.queue(self.source)
        self.player.play()
        if self.first_loop:
            self.player.volume = 0.07
            self.first_loop = False


        if self.player.playing:
            self.tex = self.player.texture
            self.tex.anchor_x = int(self.tex.width / 2)
            self.tex.anchor_y = int(self.tex.height / 2)

        self.label_str = 'Level: %i'
        self.label = None
        self.update_label()


    def stop(self):
        # self.player.next()
        self.player.pause()

    def set_volume(self, vol):
        self.player.volume = np.minimum(vol, self.max_vol)
        print(np.round(20 * np.log10(self.player.volume), 1))
        self.update_label()

    def get_volume(self):
        return self.player.volume

    def get_volume_db(self):
        return 20 * np.log10(self.get_volume())

    def update_label(self):
        if self.label is None:
            x = self._screen.width / 2
            y = self._screen.height / 2 - self.player.texture.height / 2
            self.label = pyglet.text.Label(text='X', x=x, y=y,
                                           anchor_x='center',
                                           anchor_y='top')
        self.label.text = self.label_str % np.round(self.get_volume_db() + 25)

    def draw(self):
        if self.show:
            self.tex.blit(screen.width / 2, screen.height / 2)
        if self.show_label:
            self.label.draw()


# =============================================================================
# Initialize everything
# =============================================================================
# Set up the window and event handlers
display = pyglet.display.get_display()
screen = display.get_default_screen()
win_kwargs = dict(width=screen.width, height=screen.height,
                  caption='Maskers', fullscreen=True,
                  screen=0, style='borderless', visible=True)
window = pyglet.window.Window(**win_kwargs)
keys = key.KeyStateHandler()
window.push_handlers(keys)
window.push_handlers(joystick)
window.set_exclusive_mouse()

# Get the party started
maskers = Maskers(vol_base=vol_base)
target = Target(screen, show_label=False, vol_base=vol_base)

# Set some parameters
vol_inc = 10. ** (1./20)
key_vis = key._1
key_location = key._2
key_gender = key._3


# draw a rectangle where the video will show
# batch = None
batch = pyglet.graphics.Batch()  # breaks things
winsize = window.get_size()
vw = 640
vh = 480
pad = int(winsize[1]//128)
boxcol = (0, 255, 0)
rectangle = pyglet.shapes.Rectangle((winsize[0]-vw-pad)//2,
                                    (winsize[1]-vh-pad)//2,
                                    vw+pad, vh+pad,
                                    color=boxcol, batch=batch)
rectangle_bg = pyglet.shapes.Rectangle((winsize[0]-vw)//2, (winsize[1]-vh)//2,
                                       vw, vh,
                                       color=(0, 0, 0), batch=batch)
# label = pyglet.text.Label('Press for video.',
#                           font_name='Times New Roman',
#                           font_size=52,
#                           x=window.width//2, y=window.height//2,
#                           anchor_x='center', anchor_y='center', batch=batch)

# draw a circle that moves when the sound does
circcol = (255, 255, 0)
# circ_od = 100
circ_od = int(winsize[1]//32)
circ_x = (winsize[0])//2
circ_x_left = circ_x - winsize[0]//4
circ_y = winsize[1]//10
circ_id = int(circ_od - 2 * pad)
circ_outer = pyglet.shapes.Circle(circ_x, circ_y, circ_od,
                                  color=circcol, batch=batch)
circ_bg = pyglet.shapes.Circle(circ_x, circ_y, circ_od-pad,
                               color=(0, 0, 0), batch=batch)
circ_inner = pyglet.shapes.Circle(circ_x, circ_y, circ_id,
                                  color=circcol, batch=batch)


# draw a music note that moves up/down when changing masker gender
notecol = (255, 0, 0)
nl_col = (255, 255, 255)
linex = winsize[0]//2+(1.5*vw//2)
liney = winsize[1]//2
line_width = pad*10
line_spacing = pad*3
line_y_bot = liney-line_spacing
line_y_top = liney+line_spacing
line_top = pyglet.shapes.Line(linex, line_y_top,
                              linex+line_width, line_y_top,
                              thickness=int(pad//2), color=nl_col,
                              batch=batch)
line_bot = pyglet.shapes.Line(linex, line_y_bot,
                              linex+line_width, line_y_bot,
                              thickness=int(pad//2), color=nl_col,
                              batch=batch)
# d_maj = pad*2
# d_min = pad
# elx = linex+line_width//2
# ely = line_y_top
# stem_thickness = 2
# stem_x = elx+d_maj
# stem_y = ely
# stem_h = line_spacing*2
# note_base = pyglet.shapes.Ellipse(linex+line_width//2, ely,
#                                   d_maj, d_min, color=notecol, batch=batch)
# note_stem = pyglet.shapes.Line(stem_x, stem_y, stem_x, stem_y+stem_h,
#                                thickness=stem_thickness, color=notecol,
#                                batch=batch)

note_x = linex+line_width//2
note_y = line_y_top
note_im = pyglet.image.load('note.png')
note_im.anchor_x = note_im.width//2
note = pyglet.sprite.Sprite(note_im, note_x, note_y, batch=batch)
scale = line_spacing / note.height
note.scale = scale*2
note_x = linex+line_width//2+note.width//6
note.x = note_x
note_y_top = line_y_top - line_spacing//4
note_y_bot = line_y_bot - line_spacing//4
note.y = note_y_top

# add talkers that get louder/quieter depending on volume
crowd_im = pyglet.image.load('people.png')
crowd_im.anchor_x = crowd_im.width//2
crowd_im.anchor_y = crowd_im.height//2
crowd_x = winsize[0]//2-vw
crowd_y = winsize[0]//2
crowd = pyglet.sprite.Sprite(crowd_im, crowd_x, crowd_y, batch=batch)
crowd.x = winsize[0]//2-1.5*vw//2-crowd.width//2
crowd.y = winsize[1]//2

# =============================================================================
# Begin callback functions
# =============================================================================
@window.event
def on_key_press(symbol, modifiers):
    if not use_joystick:
        if symbol == key_location:
            maskers.set_location(1)
            circ_inner.x = circ_x_left
        elif symbol == key_gender:
            maskers.set_gender(1)
        elif symbol == key_vis:
            target.show = True
    if symbol == key.UP:
        if control_target:
            target.set_volume(target.get_volume() * vol_inc)
        else:
            maskers.set_volume(maskers.get_volume() * vol_inc)
    elif symbol == key.DOWN:
        if control_target:
            target.set_volume(target.get_volume() / vol_inc)
        else:
            maskers.set_volume(maskers.get_volume() / vol_inc)
    if symbol == key.ESCAPE:
        target.stop()
        maskers.stop()
        window.has_exit = True


@window.event
def on_key_release(symbol, modifiers):
    if symbol == key_location:
        maskers.set_location(0)
        circ_inner.x = circ_x
    if symbol == key_gender:
        maskers.set_gender(0)
    elif symbol == key_vis:
        target.show = False


def on_joybutton_press():
    target.show = 1 - joystick.buttons[0]
    maskers.set_location(1 - joystick.buttons[1])
    if joystick.buttons[1]:
        circ_inner.x = circ_x_left
    else:
        circ_inner.x = circ_x
    maskers.set_gender(1 - joystick.buttons[2])


@window.event
def on_draw():
    # set masker volume and opacity of the crowd
    maskers.set_volume(vol_joy(joystick))
    crowd.opacity = int(max(0, min(255, vol_joy(joystick)/.32*255)))
    target.show = joystick.buttons[0]
    # update location (audio and visuals)
    maskers.set_location(joystick.buttons[1])
    if joystick.buttons[1]:
        circ_inner.x = circ_x_left
    else:
        circ_inner.x = circ_x
    # update gender (audio and visuals)
    maskers.set_gender(joystick.buttons[2])
    if joystick.buttons[2]:
        note.y = note_y_bot
    else:
        note.y = note_y_top

    window.clear()
    batch.draw()
    if target.show:
        target.draw()
    # if target.show:
    #     window.clear()
    #     batch.draw()
    #     target.draw()
    # else:
    #     window.clear()
    #     batch.draw()


# =============================================================================
# Finish up and get it going
# =============================================================================
# Keep the party going
pyglet.clock.schedule_once(maskers.loop, 0)
pyglet.clock.schedule_once(target.loop, 0)

pyglet.app.run()
