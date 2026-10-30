"""Silent, subtitle-led Manim film. Run through scripts/render.py.

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
    return round(max(4.0, length / 6.0 + 1.0) * FPS) / FPS


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


class StandingWaveFilm(Scene):
    def construct(self):
        self.camera.background_color = BG
        self.timeline = []
        self.subtitle = None
        self.chapter = None
        self.badge = None
        self.progress = None
        self.elapsed = 0.0
        self.total = sum(duration(c) for c in SCRIPT['cues'])
        self.sections = [self.question, self.model, self.phase, self.energy, self.density,
                         self.flux, self.waves, self.compare, self.ending]
        for section in self.sections:
            section()
        (ROOT/'build').mkdir(exist_ok=True)
        (ROOT/'build/timeline.json').write_text(json.dumps(self.timeline,ensure_ascii=False,indent=2))

    def layout(self, title, tag):
        self.clear()
        self.subtitle = None
        self.progress = None
        self.add(txt('驻 波  /  STANDING WAVES',16,MUTED).move_to([-4.86,3.67,0]))
        self.add(txt(title,35,width=11.8).move_to([-6.1,2.92,0],aligned_edge=LEFT))
        self.add(txt(tag,17,CYAN).move_to([5.5,3.67,0]))
        self.add(Line([-6.1,2.48,0],[6.1,2.48,0],color=GRID,stroke_width=1))
        self.add(Rectangle(width=14.3,height=.95,stroke_width=0,fill_color=BG,fill_opacity=1).move_to([0,-3.44,0]))
        self.add(Line([-7.1,-3.96,0],[7.1,-3.96,0],color=GRID,stroke_width=3))

    def cue(self, cid, *animations):
        item = CUES[cid]
        d = duration(item)
        if self.subtitle is not None:
            self.remove(self.subtitle)
        self.subtitle = txt(item['text'],25,width=12.5).move_to([0,-3.43,0]).set_z_index(10)
        self.add(self.subtitle)
        if self.progress is not None:
            self.remove(self.progress)
        self.progress = Line([-7.1,-3.96,0],[-7.1+14.2*max(.001,self.elapsed/self.total),-3.96,0],color=CYAN,stroke_width=3)
        self.add(self.progress)
        self.timeline.append({'id':cid,'scene':item['scene'],'start':round(self.renderer.time,4),
                              'end':round(self.renderer.time+d,4),'text':item['text']})
        if animations:
            if cid in {'07','09','12','14','15'}:
                transition=round(min(2.0,d*.45)*config.frame_rate)/config.frame_rate
                self.play(*animations,run_time=transition,rate_func=linear)
                self.wait(d-transition)
            else:
                self.play(*animations,run_time=d,rate_func=linear)
        else:
            self.wait(d)
        self.elapsed += d

    def note(self, s, color=FG, y=-2.55, size=25):
        return txt(s,size,color,width=11.9).move_to([0,y,0])

    def wave_panel(self, t, left=-5.8, width=7.6, base=1.15, amplitude=.65):
        g = axis(left,base,width)
        g.add(live_curve(lambda x,p: np.sin(2*PI*x)*np.cos(p),t,
                         left=left,width=width,base=base,height=amplitude))
        for x in [0,.5,1]:
            g.add(Dot([left+width*x,base,0],radius=.055,color=FG))
        return g

    def question(self):
        self.layout('波形不走，能量呢？','从观察出发')
        t = ValueTracker(0)
        wave = self.wave_panel(t,left=-5.7,width=11.4,base=.65,amplitude=1.0)
        self.add(wave)
        self.add(txt('两端固定的弦',22,MUTED).move_to([0,2.05,0]))
        self.add(eq(r'y(x,t)=A\sin(kx)\cos(\omega t)',size=34).move_to([0,-1.35,0]))
        self.cue('01',t.animate.set_value(4*PI))
        question = txt('不移动的波形  ≠  完全静止的能量',32,CYAN).move_to([0,-2.35,0])
        self.add(question)
        self.cue('02',t.animate.set_value(6*PI))

    def model(self):
        self.layout('什么保持不动？','建立模型')
        t=ValueTracker(0)
        self.add(self.wave_panel(t,left=-5.7,width=11.4,base=.6,amplitude=.85))
        self.add(eq(r'k_n=\frac{n\pi}{L},\qquad f_n=\frac{nv}{2L},\qquad v=\sqrt{\tau/\mu}',size=31).move_to([0,-1.5,0]))
        self.add(txt('均匀理想弦 · 小振幅 · 无阻尼     |     n = 2，示意慢放',20,MUTED).move_to([0,2.17,0]))
        self.cue('03',t.animate.set_value(4*PI))
        marks=VGroup()
        for x in [0,.5,1]:
            marks.add(txt('波节',22,CYAN).move_to([-5.7+11.4*x,-.15,0]))
        for x in [.25,.75]:
            marks.add(txt('波腹',22,AMBER).move_to([-5.7+11.4*x,1.77,0]))
        marks.add(DoubleArrow([-5.7,-.8,0],[-2.85,-.8,0],buff=0,color=AMBER,stroke_width=2))
        marks.add(eq(r'\lambda/4',26,AMBER).move_to([-4.275,-1.1,0]))
        self.add(marks)
        self.cue('04',t.animate.set_value(6*PI))
        self.add(eq(r'\underbrace{\sin(kx)}_{\text{space}}\;\underbrace{\cos(\omega t)}_{\text{time}}',size=31,color=CYAN).move_to([0,-2.4,0]))
        self.cue('05',t.animate.set_value(8*PI))

    def energy(self):
        self.layout('能量多的地方，位移一定大吗？','追踪能量')
        t=ValueTracker(PI/4)
        self.add(panel(3.65,4.65,[4.35,-.05,0]))
        self.add(self.wave_panel(t))
        self.add(txt('弦的位移  y/A',20,MUTED).move_to([-4.9,2.03,0]))
        self.add(axis(base=-1.8))
        self.add(txt('能量密度 / U',20,MUTED).move_to([-4.8,-.02,0]))
        kin=live_curve(lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2,t,base=-1.8,height=1.4,color=CYAN)
        pot=live_curve(lambda x,p:np.cos(2*PI*x)**2*np.cos(p)**2,t,base=-1.8,height=1.4,color=AMBER)
        self.add(kin,pot)
        self.add(eq(r'u_k=\tfrac12\mu y_t^2',29,CYAN).move_to([4.35,1.65,0]))
        self.add(eq(r'u_p=\tfrac12\tau y_x^2',29,AMBER).move_to([4.35,.9,0]))
        self.add(eq(r'U=\tfrac12\mu\omega^2 A^2',26,MUTED).move_to([4.35,-1.8,0]))
        self.add(txt('μ：线密度   τ：张力',17,MUTED,width=3.3).move_to([4.35,-1.3,0]))
        legend=VGroup(txt('动能',21,CYAN),txt('势能',21,AMBER)).arrange(RIGHT,buff=.5).move_to([-.1,-.05,0])
        self.add(legend)
        self.cue('06')
        state=txt('最大形变',27,AMBER).move_to([4.35,-.15,0])
        self.add(state,eq(r'\omega t=0',27).move_to([4.35,-.8,0]))
        self.cue('07',t.animate.set_value(0))
        slopes=VGroup()
        for x in [0,.5,1]:
            slopes.add(Circle(radius=.19,color=AMBER,stroke_width=2).move_to([-5.8+7.6*x,1.15,0]))
        note=self.note('势能由局部伸长决定，不由位移大小决定',AMBER)
        self.add(slopes,note)
        self.cue('08')
        self.remove(slopes,note,state)
        # Replace only the state label; keep energy scales identical.
        for obj in list(self.mobjects):
            if isinstance(obj,MathTex) and obj.get_tex_string()==r'\omega t=0': self.remove(obj)
        self.add(txt('经过平衡位置',25,CYAN).move_to([4.35,-.15,0]))
        self.add(eq(r'\omega t=\pi/2',27).move_to([4.35,-.8,0]))
        self.cue('09',t.animate.set_value(PI/2))
        self.add(self.note('波腹：速度最大 → 动能密度最大',CYAN))
        self.cue('10')

    def density(self):
        self.layout('能量分布会怎样变化？','从瞬时到平均')
        t=ValueTracker(0)
        left,width,base,height=-5.7,11.4,-1.15,2.0
        self.add(axis(left,base,width))
        self.add(txt('能量密度 / U',20,MUTED).move_to([-4.8,2.05,0]))
        self.add(DashedLine([left,base+height/2,0],[left+width,base+height/2,0],color=GRID))
        self.add(eq('1/2',size=21,color=MUTED).move_to([left-.45,base+height/2,0]))
        self.add(eq('1',size=21,color=MUTED).move_to([left-.45,base+height,0]))
        for fn,col in [(lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2,CYAN),
                       (lambda x,p:np.cos(2*PI*x)**2*np.cos(p)**2,AMBER),
                       (lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2+np.cos(2*PI*x)**2*np.cos(p)**2,GREEN)]:
            self.add(live_curve(fn,t,left=left,width=width,base=base,height=height,color=col))
        self.add(VGroup(txt('动能',22,CYAN),txt('势能',22,AMBER),txt('总量',22,GREEN)).arrange(RIGHT,buff=.6).move_to([3.8,2.05,0]))
        formula=eq(r'u=U[\sin^2(kx)\sin^2(\omega t)+\cos^2(kx)\cos^2(\omega t)]',28,width=11.9).move_to([0,-2.15,0])
        self.add(formula)
        self.cue('11',t.animate.set_value(2*PI))
        self.remove(formula)
        instant=eq(r'\omega t=\pi/4:\qquad u(x,t)=U/2',33,GREEN).move_to([0,-2.15,0])
        self.add(instant)
        self.cue('12',t.animate.set_value(2*PI+PI/4))
        self.remove(instant)
        self.add(DashedLine([left,base+height/2,0],[left+width,base+height/2,0],color=FG,stroke_width=2))
        self.add(eq(r'\langle u\rangle_t=U/2\qquad\text{(all }x\text{)}',30,FG).move_to([0,-2.15,0]))
        self.add(txt('白色虚线：时间平均',20,FG).move_to([0,1.6,0]))
        self.cue('13',t.animate.set_value(4*PI+PI/4))

    def flux(self):
        self.layout('能量怎样从一处到另一处？','局部输运')
        t=ValueTracker(0)
        self.add(self.wave_panel(t,left=-5.7,width=11.4,base=1.25,amplitude=.6))
        formula=eq(r'P=-\tau y_x y_t=\frac{\tau A^2k\omega}{4}\sin(2kx)\sin(2\omega t)',30,width=11.9).move_to([0,-1.55,0])
        self.add(formula)
        self.add(txt('箭头表示能流方向与相对大小',19,MUTED).move_to([-3.95,2.07,0]))
        self.add(eq(r'P>0:\ \rightarrow\qquad P<0:\ \leftarrow',24,GREEN).move_to([3.9,2.07,0]))
        self.add(axis(-5.7,-.55,11.4,labels=False))
        flow=VGroup()
        for x in np.arange(.0625,1,.125):
            center=-5.7+11.4*x
            def make_arrow(x=x,center=center):
                value=np.sin(4*PI*x)*np.sin(2*t.get_value())
                length=max(abs(value)*.9,.002)
                direction=1 if value>=0 else -1
                a=Arrow([center-direction*length/2,-.15,0],[center+direction*length/2,-.15,0],buff=0,
                        color=GREEN,stroke_width=4,max_tip_length_to_length_ratio=.35)
                a.set_opacity(min(1,abs(value)*4))
                return a
            flow.add(always_redraw(make_arrow))
        self.add(flow)
        self.cue('14',t.animate.set_value(PI/12))
        self.cue('15',t.animate.set_value(PI/2-PI/12))
        self.cue('16',t.animate.set_value(2*PI-PI/12))
        zeros=VGroup()
        for x in [0,.25,.5,.75,1]:
            zeros.add(Dot([-5.7+11.4*x,-.55,0],radius=.06,color=AMBER))
            zeros.add(eq('P=0',22,AMBER).move_to([-5.7+11.4*x,-1.0,0]))
        self.add(zeros,self.note('相邻波节与波腹之间：λ/4 的局部重分布',size=24))
        self.cue('17',t.animate.set_value(3*PI+PI/4))
        self.remove(formula)
        law=eq(r'\frac{d}{dt}\int_a^b u\,dx=P(a,t)-P(b,t)\quad\Longleftrightarrow\quad\partial_tu+\partial_xP=0',30,width=12).move_to([0,-1.75,0])
        self.add(law)
        self.cue('18',t.animate.set_value(4*PI+PI/4))

    def waves(self):
        self.layout('两列行波，为什么没有平均净输运？','换一种解释')
        t=ValueTracker(0)
        waveplots=VGroup()
        for base,fn,col,name in [(1.5,lambda x,p:.5*np.sin(2*PI*x-p),CYAN,'向右'),
                                 (.0,lambda x,p:.5*np.sin(2*PI*x+p),PURPLE,'向左'),
                                 (-1.5,lambda x,p:np.sin(2*PI*x)*np.cos(p),GREEN,'叠加')]:
            waveplots.add(axis(base=base,labels=False),live_curve(fn,t,base=base,height=.65,color=col))
            waveplots.add(txt(name,19,col).move_to([-6.2,base+.4,0]))
        self.add(waveplots,panel(3.65,4.65,[4.35,-.05,0]))
        right=VGroup(eq(r'y_+=\frac A2\sin(kx-\omega t)',27,CYAN,width=3.3),
                     eq(r'y_-=\frac A2\sin(kx+\omega t)',27,PURPLE,width=3.3),
                     eq(r'y_++y_-=A\sin(kx)\cos(\omega t)',25,GREEN,width=3.3)).arrange(DOWN,buff=.8).move_to([4.35,.15,0])
        self.add(right)
        self.cue('19',t.animate.set_value(4*PI))
        self.remove(waveplots,right)
        self.add(txt('固定截面 x = λ/8 处的瞬时能流',20,MUTED).move_to([-2,2.05,0]))
        self.add(axis(base=-.05,labels=False))
        self.add(eq(r'\omega t',21,MUTED).move_to([2.05,-.35,0]))
        for x,s in [(0,'0'),(.25,r'\pi/2'),(.5,r'\pi'),(.75,r'3\pi/2'),(1,r'2\pi')]:
            self.add(eq(s,20,MUTED).move_to([-5.8+7.6*x,-1.95,0]))
        self.add(curve(lambda x:np.cos(PI/4-2*PI*x)**2,base=-.05,height=1.35,color=CYAN))
        self.add(curve(lambda x:-np.cos(PI/4+2*PI*x)**2,base=-.05,height=1.35,color=PURPLE))
        self.add(eq(r'P_+=C\cos^2(kx-\omega t)',25,CYAN,width=3.3).move_to([4.35,1.55,0]))
        self.add(eq(r'P_-=-C\cos^2(kx+\omega t)',25,PURPLE,width=3.3).move_to([4.35,.8,0]))
        self.add(eq(r'C=\tau A^2k\omega/4',24,MUTED).move_to([4.35,-1.8,0]))
        self.add(txt('功率以 C 归一化',18,MUTED).move_to([-4.65,-2.5,0]))
        self.cue('20')
        self.add(curve(lambda x:np.sin(4*PI*x),base=-.05,height=1.35,color=GREEN,stroke=4))
        self.add(eq(r'\langle P_+\rangle=+C/2',24,CYAN).move_to([4.35,.05,0]))
        self.add(eq(r'\langle P_-\rangle=-C/2',24,PURPLE).move_to([4.35,-.5,0]))
        self.add(eq(r'\langle P\rangle=0',27,GREEN).move_to([4.35,-1.1,0]))
        cursor=ValueTracker(0)
        dots=VGroup()
        for fn,col in [(lambda q:np.cos(PI/4-q)**2,CYAN),(lambda q:-np.cos(PI/4+q)**2,PURPLE),(lambda q:np.sin(2*q),GREEN)]:
            dots.add(always_redraw(lambda fn=fn,col=col:Dot([-5.8+7.6*cursor.get_value()/(2*PI),-.05+1.35*fn(cursor.get_value()),0],color=col,radius=.065)))
        self.add(dots)
        self.cue('21',cursor.animate.set_value(2*PI))
        self.remove(dots)
        self.add(eq(r'P_{\rm cross}=-\tau(y_{+,x}y_{-,t}+y_{-,x}y_{+,t})=0',26,width=8.0).move_to([-1.9,1.6,0]))
        self.add(eq(r'P=P_++P_-',32,GREEN).move_to([-.2,-2.5,0]))
        self.cue('22')

    def phase(self):
        self.layout('波形驻留，相位怎样变化？','观察相位')
        t=ValueTracker(0)
        left,width=-4.9,10.6
        self.add(txt('行波',25,CYAN).move_to([-5.85,1.2,0]))
        self.add(txt('驻波',25,GREEN).move_to([-5.85,-1.15,0]))
        self.add(axis(left,1.15,width,False),axis(left,-1.15,width,False))
        self.add(live_curve(lambda x,p:np.cos(2*PI*x-p),t,left=left,width=width,base=1.15,height=.6))
        self.add(live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),t,left=left,width=width,base=-1.15,height=.6,color=GREEN))
        peak=always_redraw(lambda:Dot([left+width*((t.get_value()/(2*PI))%1),1.75,0],radius=.075,color=CYAN))
        self.add(peak,txt('跟踪波峰 →',20,CYAN).move_to([3.9,2.05,0]))
        self.cue('23',t.animate.set_value(1.8*PI))
        self.remove(peak)
        samples=VGroup()
        for x,col in [(.12,GREEN),(.35,GREEN),(.62,PURPLE),(.85,PURPLE)]:
            samples.add(always_redraw(lambda x=x,col=col:Dot([left+width*x,-1.15+.6*np.sin(2*PI*x)*np.cos(t.get_value()),0],color=col,radius=.08)))
        self.add(samples)
        self.add(txt('同相',22,GREEN).move_to([-2.25,-2.15,0]))
        self.add(txt('相差 π',22,PURPLE).move_to([3.05,-2.15,0]))
        self.add(DashedLine([left+width/2,-1.95,0],[left+width/2,-.35,0],color=MUTED))
        self.cue('24',t.animate.set_value(5.8*PI))
        self.add(self.note('空间相位分段为 0 / π；波节处相位不定义',MUTED,size=24))
        self.cue('25',t.animate.set_value(7.8*PI))

    def compare(self):
        self.layout('同样在振动，能量输运并不相同','对照结论')
        centers=[-4.15,0,4.15]
        colors=[AMBER,CYAN,GREEN]
        titles=['简谐振子','单向简谐行波','理想驻波']
        rows=[['动能、势能相互转换','单个振子，无空间输运','一个振动相位'],
              ['动能密度 = 势能密度','平均能流沿传播方向','相位连续推进'],
              ['能量分布交替集中','局部往返，平均能流为零','同一区间同相，相邻反相']]
        cards=[]
        t=ValueTracker(0)
        for i,cx in enumerate(centers):
            g=VGroup(panel(3.9,4.7,[cx,-.05,0]),txt(titles[i],26,colors[i]).move_to([cx,1.85,0]))
            for j,s in enumerate(rows[i]):
                g.add(txt(s,21,FG,width=3.5).move_to([cx,-.55-j*.65,0]))
            cards.append(g)
            self.add(g)
        # A small moving icon in each card connects the table to the animations.
        self.add(Line([-5.5,.7,0],[-2.8,.7,0],color=GRID))
        bob=always_redraw(lambda:Dot([-4.15+.9*np.cos(t.get_value()),.7,0],radius=.12,color=AMBER))
        self.add(bob)
        self.add(live_curve(lambda x,p:np.sin(2*PI*x-p),t,left=-1.4,width=2.8,base=.7,height=.35,color=CYAN))
        self.add(live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),t,left=2.75,width=2.8,base=.7,height=.35,color=GREEN))
        highlights=[RoundedRectangle(width=3.9,height=4.7,corner_radius=.15,color=c,stroke_width=2).move_to([cx,-.05,0]) for cx,c in zip(centers,colors)]
        for cid,i in [('26',0),('27',1),('28',2)]:
            if i: self.remove(highlights[i-1])
            self.add(highlights[i])
            self.cue(cid,t.animate.increment_value(2*PI))

    def ending(self):
        self.layout('波形停在原地，能量仍在局部流动','回到最初的问题')
        t=ValueTracker(PI/4)
        self.add(self.wave_panel(t,left=-5.7,width=11.4,base=1.15,amplitude=.6))
        self.add(eq(r'\boxed{\langle P(x,t)\rangle_t=0}',size=48,color=GREEN).move_to([0,-.45,0]))
        self.add(txt('没有平均净输运',30,FG).move_to([0,-1.5,0]))
        self.cue('29',t.animate.set_value(2*PI+PI/4))
        self.add(txt('瞬时能流通常不为零',27,CYAN).move_to([0,-2.3,0]))
        self.cue('30',t.animate.set_value(4*PI+PI/4))


class LayoutCheck(StandingWaveFilm):
    """Same compositions, two frames per cue for a rapid layout inspection."""
    def cue(self,cid,*animations):
        item=CUES[cid]
        if self.subtitle is not None: self.remove(self.subtitle)
        self.subtitle=txt(item['text'],25,width=12.5).move_to([0,-3.43,0]).set_z_index(10)
        self.add(self.subtitle)
        if animations:
            self.play(*animations,run_time=2/config.frame_rate,rate_func=linear)
        else: self.wait(2/config.frame_rate)
        self.timeline.append({'id':cid,'scene':item['scene'],'start':self.renderer.time-2/config.frame_rate,'end':self.renderer.time,'text':item['text']})
