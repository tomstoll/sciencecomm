# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 18:28:27 2025

@author: rkmaddox
"""

import numpy as np
import expyfun.stimuli as stim
import expyfun.visual as viz
from expyfun.stimuli import TrackerUD
from expyfun import ExperimentController

fs = 48000
stim_rms = .01
dur_tone = 0.8
dur_pause = 0.3
n_intervals = 3
colors = [[0, 1, 0], [1, 1, 0], [1, 0, 0]]
dur_tot = n_intervals * (dur_tone + dur_pause)
use_joystick = False


def tone(shift):  # shift in semitones
    f0 = 220
    n_harm = 10
    len_tone = int(dur_tone * fs)
    f = f0 * 2 ** (shift / 12) * np.arange(1, n_harm)
    f = f[f < fs / 2]
    a = f[0] * f ** -2
    t = np.arange(len_tone) / fs
    tone = stim.window_edges(np.sum(np.array([np.sin(2 * np.pi * t * f_) * a_
                             for f_, a_ in zip(f, a)]), 0), fs, 0.1)
    tone *= stim_rms / tone.std()
    return tone


def wait_for_joystick():
    pressed = []
    ec.listen_joystick_button_presses()
    while len(pressed) == 0:
        pressed = ec.get_joystick_button_presses()
        ec.check_force_quit()
    return pressed


params = {  # maybe just make this use pyglet instead, but this should work
    'TYPE': 'sound_card',
    'SOUND_CARD_API': 'MME',
    'SOUND_CARD_NAME': 'Microsoft Sound Mapper - Output',
    'SOUND_CARD_TRIGGER_CHANNELS': 0,
    }
pos_text = (0, -2.5)
tracker_trials = 12
with ExperimentController('Pitch', stim_rms=stim_rms,
                          output_dir=None, check_rms=None, participant='PSC',
                          session='', verbose=None, version='dev',
                          audio_controller=params, full_screen=True,
                          trigger_controller='dummy', stim_fs=48000,
                          stim_db=100, joystick=use_joystick) as ec:
    while True:
        tracker = TrackerUD(None, 1, 1, 3, 1, tracker_trials,
                            tracker_trials, 1)
        pb = viz.ProgressBar(ec, [0, -.2, 0.3, 0.03],
                             units='norm', colors=['w', 'w'])
        if use_joystick is False:
            ec.screen_prompt('Press any button to start', wrap=False)
        else:
            ec.screen_text('Press any button to start', wrap=False)
            ec.flip()
            wait_for_joystick()
        while not tracker.stopped:
            test_interval = np.random.randint(n_intervals)
            shift = 2 ** tracker.x_current
            tones = [tone(shift * (i == test_interval))
                     for i in range(n_intervals)]
            silence = np.zeros(int(fs * dur_pause))
            tones = [np.concatenate((t, silence)) for t in tones]
            x = np.concatenate(tones)
            ec.load_buffer(x)
            ec.identify_trial(ec_id="tone", ttl_id=[0])
            c = [viz.Circle(ec, radius=1, pos=(3 * (i - 1), 0),
                            fill_color=colors[i], units='deg')
                 for i in range(n_intervals)]
            ec.screen_text('Pitch difference: %i cents' %
                           (100 * 2 ** tracker.x_current),
                           wrap=False, pos=pos_text, units='deg')
            pb.draw()
            ec.flip()
            ec.wait_secs(1)
            t0 = ec.start_stimulus(flip=False)
            for i in range(0, n_intervals):
                ec.wait_until(t0 + (dur_tone + dur_pause) * i)
                for ii in range(i + 1):
                    c[ii].draw()
                ec.screen_text('Pitch difference: %i cents' %
                               (100 * 2 ** tracker.x_current),
                               wrap=False, pos=pos_text, units='deg')
                pb.draw()
                ec.flip()
            ec.wait_until(t0 + dur_tot)
            ec.stop()
            if use_joystick is False:
                resp = ec.wait_one_press(live_keys=['1', '2', '3'])[0]
                resp = int(resp) - 1
            else:
                pressed = wait_for_joystick()
                resp = int(pressed[0][0])
            correct = resp == test_interval
            tracker.respond(correct)
            c[test_interval].draw()
            if correct:
                ec.screen_text('Correct!', wrap=False, pos=pos_text, units='deg')
            else:
                ec.screen_text('Nope', wrap=False, pos=pos_text, units='deg')
            pb.update_bar(100 * len(tracker.x) / tracker_trials)
            pb.draw()
            ec.flip()
            ec.wait_secs(0.8)
            pb.draw()
            ec.flip()
            ec.wait_secs(0.2)
            ec.trial_ok()
        try:
            str_score = ('Your "just noticeable difference" is %i cents!' %
                         (100 * 2 ** tracker.x[tracker.reversal_inds[3]:].mean()))
        except IndexError:
            str_score = ('Your "just noticeable difference" is %i cents!' %
                         (100 * 2 ** tracker.x.mean()))
        if use_joystick is False:
            ec.screen_prompt(str_score, wrap=False)
        else:
            ec.screen_text(str_score, wrap=False)
            ec.flip()
            wait_for_joystick()
        ec.wait_secs(2)
