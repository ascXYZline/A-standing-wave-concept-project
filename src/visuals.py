"""Shared typography, colors, charts, and reading-time rules for the film.

All wave panels share x/L and phase theta=omega*t. The visual displacement
is deliberately magnified; energy and power use their own labeled scales.
"""
import json
import os
import re
from pathlib import Path

import manimpango
import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = Path('/mnt/c/Windows/Fonts/msyh.ttc')
if FONT_PATH.exists():
    manimpango.register_font(str(FONT_PATH))
FONT = 'Microsoft YaHei' if 'Microsoft YaHei' in manimpango.list_fonts() else 'Droid Sans Fallback'
BG, FG, MUTED, GRID = '#0B1220', '#EAF0FA', '#91A1B9', '#26354A'
CYAN, AMBER, GREEN, PURPLE = '#59D9ED', '#FFBF69', '#83E3B2', '#B49AFF'
SCRIPT = json.loads((ROOT / 'narration/script.json').read_text())
CUES = {c['id']: c for c in SCRIPT['cues']}
FPS = 30


def duration(cue):
    # Reading time, with a short visual pause. No audio dependency.
    length = len(re.sub(r'[，。？：；、]', '', cue['text']))
    return round(float(cue.get('seconds',max(4.0, length / 6.0 + 1.0))) * FPS) / FPS


def txt(s, size=27, color=FG, width=None):
    m = Text(s, font=FONT, font_size=size, color=color, line_spacing=0.8)
    if width and m.width > width:
        m.scale_to_fit_width(width)
    return m


def eq(s, size=32, color=FG, width=None):
    m = MathTex(s, font_size=size, color=color)
    if width and m.width > width:
        m.scale_to_fit_width(width)
    return m


def panel(w, h, center):
    return RoundedRectangle(width=w, height=h, corner_radius=0.15,
                            stroke_color=GRID, stroke_width=1,
                            fill_color='#111D2E', fill_opacity=0.8).move_to(center)


def curve(fn, left=-5.8, base=0.0, width=7.6, height=1.0, color=CYAN, stroke=3.5):
    x = np.linspace(0, 1, 161)
    y = np.asarray(fn(x)) + np.zeros_like(x)
    points = np.column_stack((left + width*x, base + height*y, np.zeros_like(x)))
    return VMobject(stroke_color=color, stroke_width=stroke).set_points_as_corners(points)


def live_curve(fn, phase, **kwargs):
    m = curve(lambda x: fn(x, phase.get_value()), **kwargs)
    m.add_updater(lambda obj: obj.become(curve(lambda x: fn(x, phase.get_value()), **kwargs)))
    return m


def axis(left=-5.8, base=0, width=7.6, labels=True):
    g = VGroup(Line([left, base, 0], [left+width, base, 0], color=GRID, stroke_width=2))
    for x in [0, .25, .5, .75, 1]:
        g.add(Line([left+x*width,base-.055,0],[left+x*width,base+.055,0],color=MUTED))
        if labels:
            g.add(eq({0:'0',.25:r'\frac14',.5:r'\frac12',.75:r'\frac34',1:'1'}[x],
                     size=19,color=MUTED).move_to([left+x*width,base-.3,0]))
    if labels:
        g.add(eq('x/L',size=20,color=MUTED).move_to([left+width+.48,base,0]))
    return g


