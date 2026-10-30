"""Subtitle-led film with staged derivations and restrained visual transitions.

Physics is in docs/physics.md and independently checked by check_physics.py.
Frames and subtitles use the actual renderer clock, including transitions.
"""
from contextlib import contextmanager
from visuals import *


def math(*parts, size=32, color=FG, width=None):
    m = MathTex(*parts, font_size=size, color=color)
    if width and m.width > width:
        m.scale_to_fit_width(width)
    return m


class StandingWaveFilm(Scene):
    quick = False

    def construct(self):
        self.camera.background_color = BG
        self.timeline, self.beat_index = [], 0
        self.subtitle = self.title = self.tag = None
        self.active_beat = None
        self.progress_value = ValueTracker(0)
        self.brand = txt('驻 波  /  STANDING WAVES',16,MUTED).move_to([-4.87,3.65,0])
        self.rule = Line([-6.1,2.48,0],[6.1,2.48,0],color=GRID,stroke_width=1)
        self.rail = Line([-7.1,-3.96,0],[7.1,-3.96,0],color=GRID,stroke_width=2)
        self.progress = always_redraw(lambda:Line([-7.1,-3.96,0],
            [-7.1+14.2*max(.0001,self.progress_value.get_value()),-3.96,0],color=CYAN,stroke_width=3))
        self.hud = [self.brand,self.rule,self.rail,self.progress,self.progress_value]
        self.add(*self.hud)
        for section in [self.question,self.model,self.phase,self.energy,self.density,
                        self.flux,self.waves,self.compare,self.ending]:
            section()
        (ROOT/'build').mkdir(exist_ok=True)
        dest='layout-timeline.json' if self.quick else 'timeline.json'
        (ROOT/'build'/dest).write_text(json.dumps(self.timeline,ensure_ascii=False,indent=2))

    def move(self, *animations, seconds=.7, rate=smooth):
        """All visual actions have eased motion; physical oscillations pass linear."""
        seconds=max(1/config.frame_rate,round(seconds*config.frame_rate)/config.frame_rate)
        if self.quick:
            seconds=1/config.frame_rate
        extra=[]
        if self.active_beat:
            start,planned=self.active_beat
            fraction=min(1,(self.renderer.time-start+seconds)/planned)
            extra=[self.progress_value.animate(rate_func=linear).set_value(
                (self.beat_index+fraction)/len(SCRIPT['cues']))]
        if animations or extra:
            self.play(*animations,*extra,run_time=seconds,rate_func=rate)
        else:
            self.wait(seconds)

    def reveal(self,*objects,seconds=.65):
        self.move(LaggedStart(*(FadeIn(m,shift=UP*.10) for m in objects),lag_ratio=.14),seconds=seconds)
        # Manim 0.18 may leave introducers inside LaggedStart suspended.
        # Resume live curves explicitly so a fade never freezes the physics.
        for m in objects: m.resume_updating()

    def hide(self,*objects,seconds=.35):
        for m in objects: m.suspend_updating()
        self.move(*(FadeOut(m,shift=DOWN*.06) for m in objects),seconds=seconds)
        self.remove(*objects)

    def morph(self,old,new,seconds=.85):
        self.move(TransformMatchingTex(old,new),seconds=seconds)
        return new

    def layout(self,title,tag):
        if self.title is not None:
            old=[m for m in self.mobjects if m not in self.hud]
            for m in old: m.suspend_updating()
            self.move(FadeOut(Group(*old),shift=DOWN*.10),seconds=.32)
            self.remove(*old)
        self.subtitle=None
        self.title=txt(title,34,width=11.8).move_to([-6.1,2.96,0],aligned_edge=LEFT)
        self.tag=VGroup(RoundedRectangle(width=2.3,height=.38,corner_radius=.12,
                         fill_color='#142838',fill_opacity=1,stroke_width=0),txt(tag,16,CYAN)).move_to([5.1,3.65,0])
        self.reveal(self.title,self.tag,seconds=.38)

    @contextmanager
    def say(self,cid):
        item=CUES[cid]
        start=self.renderer.time
        self.active_beat=(start,duration(item))
        new=txt(item['text'],25,width=12.5).move_to([0,-3.43,0]).set_z_index(10)
        animations=[FadeIn(new,shift=UP*.035)]
        if self.subtitle is not None: animations.append(FadeOut(self.subtitle,shift=UP*.025))
        self.move(*animations,seconds=.20)
        self.subtitle=new
        yield
        remaining=duration(item)-(self.renderer.time-start)
        if self.quick:
            self.wait(1/config.frame_rate)
        elif remaining>0:
            self.move(seconds=remaining)
        self.progress_value.set_value((self.beat_index+1)/len(SCRIPT['cues']))
        self.timeline.append({'id':cid,'scene':item['scene'],'start':round(start,4),
                              'end':round(self.renderer.time,4),'text':item['text']})
        self.active_beat=None
        self.beat_index+=1

    def oscillate(self,t,target):
        remaining=self.active_beat[1]-(self.renderer.time-self.active_beat[0])
        self.move(t.animate.set_value(target),seconds=max(.15,remaining),rate=linear)

    def note(self,s,color=FG,y=-2.55,size=24):
        return txt(s,size,color,width=11.9).move_to([0,y,0])

    def wave(self,t,left=-5.8,width=7.4,base=1.1,amplitude=.62):
        g=axis(left,base,width)
        g.add(live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),t,
                         left=left,width=width,base=base,height=amplitude,stroke=4))
        g.add(*(Dot([left+width*x,base,0],radius=.055,color=FG) for x in [0,.5,1]))
        return g

    def question(self):
        self.layout('波形不走，能量呢？','从观察出发')
        t=ValueTracker(0)
        wave=self.wave(t,left=-5.7,width=11.4,base=.55,amplitude=.9)
        with self.say('01'):
            self.reveal(wave,txt('两端固定的弦',21,MUTED).move_to([0,2.0,0]))
            self.oscillate(t,2*PI)
        with self.say('02'):
            q=VGroup(txt('波形不走',30,FG),Arrow(LEFT*.5,RIGHT*.5,color=MUTED),
                     txt('能量也不动？',34,CYAN)).arrange(RIGHT,buff=.45).move_to([0,-1.75,0])
            self.reveal(*q,seconds=.9)
            self.oscillate(t,4*PI)

    def model(self):
        self.layout('先看：什么保持不动？','建立模型')
        t=ValueTracker(0)
        wave=self.wave(t,left=-5.7,width=11.4,base=.65,amplitude=.8)
        formula=math('y(x,t)','=','A',r'\sin(kx)',r'\cos(\omega t)',size=36).move_to([0,-1.65,0])
        with self.say('03'):
            self.reveal(wave,txt('均匀理想弦 · 小振幅 · 无阻尼   |   n = 2，示意慢放',19,MUTED).move_to([0,2.15,0]))
            self.reveal(formula,seconds=.6)
            self.oscillate(t,2*PI)
        with self.say('04'):
            nodes=VGroup(*(txt('波节',21,CYAN).move_to([-5.7+11.4*x,-.10,0]) for x in [0,.5,1]))
            antinodes=VGroup(*(txt('波腹',21,AMBER).move_to([-5.7+11.4*x,1.75,0]) for x in [.25,.75]))
            bracket=VGroup(DoubleArrow([-5.7,-.7,0],[-2.85,-.7,0],buff=0,color=AMBER,stroke_width=2),
                           eq(r'\lambda/4',25,AMBER).move_to([-4.275,-1.03,0]))
            self.reveal(nodes,antinodes,bracket,seconds=1.0)
            self.oscillate(t,4*PI)
        with self.say('05'):
            self.move(formula[3].animate.set_color(PURPLE),formula[4].animate.set_color(CYAN),seconds=.5)
            b1=Brace(formula[3],DOWN,color=PURPLE,buff=.12)
            b2=Brace(formula[4],DOWN,color=CYAN,buff=.12)
            labels=VGroup(txt('位置因子',19,PURPLE).next_to(b1,DOWN,buff=.1),
                          txt('时间因子',19,CYAN).next_to(b2,DOWN,buff=.1))
            self.reveal(b1,b2,labels,seconds=.6)
            self.move(Indicate(formula[3],color=PURPLE,scale_factor=1.07),seconds=.7)
            self.oscillate(t,6*PI)

    def phase(self):
        self.layout('相位在前进，还是同步起落？','观察相位')
        t=ValueTracker(0); left,width=-4.9,10.6
        upper=VGroup(txt('行波',25,CYAN).move_to([-5.85,1.15,0]),axis(left,1.15,width,False),
                      live_curve(lambda x,p:np.cos(2*PI*x-p),t,left=left,width=width,base=1.15,height=.58))
        peak=always_redraw(lambda:Dot([left+width*((t.get_value()/(2*PI))%1),1.73,0],radius=.075,color=CYAN))
        with self.say('23'):
            self.reveal(upper,peak,txt('跟踪同一个波峰 →',20,CYAN).move_to([3.7,2.0,0]))
            self.oscillate(t,1.7*PI)
        lower=VGroup(txt('驻波',25,GREEN).move_to([-5.85,-1.1,0]),axis(left,-1.1,width,False),
                      live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),t,left=left,width=width,base=-1.1,height=.58,color=GREEN))
        samples=VGroup()
        for x,col in [(.12,GREEN),(.35,GREEN),(.62,PURPLE),(.85,PURPLE)]:
            samples.add(always_redraw(lambda x=x,col=col:Dot([left+width*x,-1.1+.58*np.sin(2*PI*x)*np.cos(t.get_value()),0],color=col,radius=.075)))
        with self.say('24'):
            self.hide(peak,seconds=.2)
            self.reveal(lower,samples,txt('同相',22,GREEN).move_to([-2.25,-2.05,0]),
                        txt('相差 π',22,PURPLE).move_to([3.05,-2.05,0]),
                        DashedLine([.4,-1.9,0],[.4,-.3,0],color=MUTED),seconds=.8)
            self.oscillate(t,3.7*PI)
        with self.say('25'):
            node=Circle(radius=.13,color=FG,stroke_width=2).move_to([.4,-1.1,0])
            self.reveal(node,self.note('波节振幅为零 → 相位不定义',MUTED),seconds=.5)
            self.oscillate(t,5.7*PI)

    def energy(self):
        self.layout('能量多的地方，位移一定大吗？','追踪能量')
        t=ValueTracker(PI/4)
        wave=self.wave(t)
        base=-1.8
        uk=live_curve(lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2,t,width=7.4,base=base,height=1.35,color=CYAN)
        up=live_curve(lambda x,p:np.cos(2*PI*x)**2*np.cos(p)**2,t,width=7.4,base=base,height=1.35,color=AMBER)
        right=panel(3.9,4.8,[4.35,-.05,0])
        title=txt('先看定义',23,FG).move_to([4.35,1.97,0])
        kf=math('u_k','=',r'\tfrac12\mu',r'y_t^2',size=30,color=CYAN).move_to([4.35,1.12,0])
        pf=math('u_p','=',r'\tfrac12\tau',r'y_x^2',size=30,color=AMBER).move_to([4.35,.18,0])
        legend=VGroup(txt('动能',20,CYAN),txt('势能',20,AMBER)).arrange(RIGHT,buff=.35).move_to([.0,-.05,0])
        with self.say('06'):
            self.reveal(wave,txt('弦的位移  y/A',20,MUTED).move_to([-4.9,2.04,0]),
                        eq(r'y=A\sin(kx)\cos(\omega t)',24,MUTED,width=4.4).move_to([-.9,2.04,0]),right)
            self.reveal(title,kf,pf,txt('μ：线密度   τ：张力',17,MUTED).move_to([4.35,-2.08,0]))
        with self.say('06a'):
            newtitle=txt('由位移求导',23,FG).move_to(title)
            self.move(ReplacementTransform(title,newtitle),seconds=.4); title=newtitle
            kt=math('y_t','=',r'-A\omega',r'\sin(kx)',r'\sin(\omega t)',size=28,color=CYAN,width=3.5).move_to(kf)
            pt=math('y_x','=',r'Ak',r'\cos(kx)',r'\cos(\omega t)',size=28,color=AMBER,width=3.5).move_to(pf)
            kf=self.morph(kf,kt)
            pf=self.morph(pf,pt)
            kl=txt('速度',19,CYAN).move_to([4.35,1.58,0])
            pl=txt('斜率',19,AMBER).move_to([4.35,.65,0])
            self.reveal(kl,pl,seconds=.4)
        with self.say('06b'):
            self.move(ReplacementTransform(title,txt('平方后代入',23,FG).move_to(title)),
                      ReplacementTransform(kl,txt('动能密度',19,CYAN).move_to(kl)),
                      ReplacementTransform(pl,txt('势能密度',19,AMBER).move_to(pl)),seconds=.35)
            kfinal=math('u_k','=','U',r'\sin^2(kx)',r'\sin^2(\omega t)',size=27,color=CYAN,width=3.5).move_to(kf)
            pfinal=math('u_p','=','U',r'\cos^2(kx)',r'\cos^2(\omega t)',size=27,color=AMBER,width=3.5).move_to(pf)
            self.reveal(axis(base=base,width=7.4),txt('能量密度 / U',20,MUTED).move_to([-4.8,-.05,0]),legend,seconds=.5)
            kf=self.morph(kf,kfinal,seconds=.7); self.reveal(uk,seconds=.35)
            pf=self.morph(pf,pfinal,seconds=.7); self.reveal(up,seconds=.35)
            self.reveal(eq(r'U=\tfrac12\mu\omega^2A^2',24,MUTED).move_to([4.35,-1.6,0]),seconds=.4)
        state=VGroup(txt('最大形变',25,AMBER),eq(r'\omega t=0',25)).arrange(DOWN,buff=.16).move_to([4.35,-.85,0])
        with self.say('07'):
            self.reveal(state,seconds=.4)
            self.move(t.animate.set_value(0),seconds=1.0)
            self.move(kf.animate.set_opacity(.35),Indicate(pf,color=AMBER,scale_factor=1.05),seconds=.65)
        marks=VGroup()
        for x in [0,.5,1]:
            cx=-5.8+7.4*x
            marks.add(Circle(radius=.15,color=AMBER,stroke_width=2).move_to([cx,1.1,0]),
                      Dot([cx,-.45,0],radius=.065,color=AMBER))
        note=self.note('位移为零的波节，也可以储存弹性势能',AMBER)
        with self.say('08'):
            self.reveal(marks,note,seconds=.65)
            self.move(Indicate(marks,color=AMBER,scale_factor=1.04),seconds=.6)
        nextstate=VGroup(txt('经过平衡位置',24,CYAN),eq(r'\omega t=\pi/2',25)).arrange(DOWN,buff=.16).move_to(state)
        with self.say('09'):
            self.hide(marks,note,seconds=.35)
            self.move(ReplacementTransform(state,nextstate),t.animate.set_value(PI/2),seconds=1.2)
            self.move(kf.animate.set_opacity(1),pf.animate.set_opacity(.35),seconds=.4)
        with self.say('10'):
            pts=VGroup(*(Dot([-5.8+7.4*x,-.45,0],radius=.065,color=CYAN) for x in [.25,.75]))
            self.reveal(pts,self.note('波腹：速度最大 → 动能密度最大',CYAN),seconds=.6)
            self.move(Indicate(kf,color=CYAN,scale_factor=1.05),seconds=.7)

    def density(self):
        self.layout('分布在变，什么时候处处一样？','从瞬时到平均')
        t=ValueTracker(0)
        left,width,base,height=-5.7,11.4,-1.0,1.8
        kin=live_curve(lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2,t,left=left,width=width,base=base,height=height,color=CYAN)
        pot=live_curve(lambda x,p:np.cos(2*PI*x)**2*np.cos(p)**2,t,left=left,width=width,base=base,height=height,color=AMBER)
        total=live_curve(lambda x,p:np.sin(2*PI*x)**2*np.sin(p)**2+np.cos(2*PI*x)**2*np.cos(p)**2,t,left=left,width=width,base=base,height=height,color=GREEN,stroke=4)
        f=math('u','=','u_k','+','u_p',size=35).move_to([0,-2.03,0]); f[2].set_color(CYAN); f[4].set_color(AMBER)
        legends=VGroup(txt('动能',21,CYAN),txt('势能',21,AMBER),txt('总量',21,GREEN)).arrange(RIGHT,buff=.5).move_to([3.8,2.0,0])
        with self.say('11'):
            self.reveal(axis(left,base,width),txt('能量密度 / U',20,MUTED).move_to([-4.8,2.0,0]),legends,
                        eq('1/2',20,MUTED).move_to([-6.15,-.1,0]),eq('1',20,MUTED).move_to([-6.15,.8,0]),kin,pot,seconds=.7)
            self.reveal(f,total,seconds=.55)
            self.oscillate(t,2*PI)
        phase=eq(r'\omega t=\pi/4\quad(t=T_0/8)',25,AMBER).move_to([0,1.45,0])
        with self.say('12'):
            self.reveal(phase,seconds=.35)
            self.move(t.animate.set_value(2*PI+PI/4),seconds=1.0)
            timed=eq(r'\sin^2(\omega t)=\cos^2(\omega t)=\tfrac12',25,AMBER).move_to(phase)
            self.move(ReplacementTransform(phase,timed),seconds=.5); phase=timed
            full=math('u','=',r'\frac U2',r'\left[',r'\sin^2(kx)','+',r'\cos^2(kx)',r'\right]',size=34).move_to(f)
            full[4].set_color(CYAN); full[6].set_color(AMBER)
            f=self.morph(f,full)
        with self.say('12a'):
            b=Brace(VGroup(f[4],f[5],f[6]),DOWN,color=GREEN,buff=.10)
            one=eq('1',24,GREEN).next_to(b,DOWN,buff=.07)
            self.reveal(b,one,seconds=.6)
            self.move(Indicate(VGroup(f[4],f[5],f[6]),color=GREEN,scale_factor=1.06),seconds=.65)
            self.hide(b,one,seconds=.3)
            f=self.morph(f,math('u','=',r'U/2',size=40,color=GREEN).move_to(f))
            self.move(Circumscribe(f,color=GREEN,buff=.15),seconds=.9)
        with self.say('13'):
            self.hide(phase,seconds=.25)
            mean=DashedLine([left,-.1,0],[left+width,-.1,0],color=FG,stroke_width=2)
            self.reveal(mean,txt('白色虚线：对整个周期取平均',20,FG).move_to([0,1.45,0]),seconds=.4)
            f=self.morph(f,math(r'\langle u\rangle_t','=',r'U/2',size=36,color=FG).move_to(f),seconds=.7)
            self.oscillate(t,4*PI+PI/4)

    def flow_arrows(self,t):
        arrows=VGroup()
        for x in np.arange(.0625,1,.125):
            center=-5.7+11.4*x
            def make(x=x,center=center):
                value=np.sin(4*PI*x)*np.sin(2*t.get_value())
                length=max(abs(value)*.9,.002); direction=1 if value>=0 else -1
                a=Arrow([center-direction*length/2,-.12,0],[center+direction*length/2,-.12,0],
                    buff=0,color=GREEN,stroke_width=4,max_tip_length_to_length_ratio=.35)
                return a.set_opacity(min(1,abs(value)*4))
            arrows.add(always_redraw(make))
        return arrows

    def flux(self):
        self.layout('能量怎样从一处到另一处？','局部输运')
        t=ValueTracker(0)
        wave=self.wave(t,left=-5.7,width=11.4,base=1.22,amplitude=.55)
        f=math('P','=',r'(-\tau y_x)',r'y_t',size=39).move_to([0,-1.65,0])
        f[2].set_color(AMBER); f[3].set_color(CYAN)
        description=self.note('横向力 × 横向速度 = 通过截面的功率',MUTED,size=23)
        with self.say('14'):
            self.reveal(wave,txt('正方向沿弦向右',19,MUTED).move_to([-4.8,2.05,0]))
            self.reveal(f,description)
        with self.say('14a'):
            self.hide(description,seconds=.2)
            expanded=math('P','=',r'\tau A^2k\omega',r'\sin(kx)\cos(kx)',r'\sin(\omega t)\cos(\omega t)',size=29,width=11.5).move_to(f)
            expanded[3].set_color(AMBER); expanded[4].set_color(CYAN)
            f=self.morph(f,expanded,seconds=.8)
            b1=Brace(f[3],DOWN,color=AMBER,buff=.1); b2=Brace(f[4],DOWN,color=CYAN,buff=.1)
            labels=VGroup(eq(r'\tfrac12\sin(2kx)',23,AMBER).next_to(b1,DOWN,buff=.1),
                          eq(r'\tfrac12\sin(2\omega t)',23,CYAN).next_to(b2,DOWN,buff=.1))
            self.reveal(b1,b2,labels,seconds=.55)
            self.move(seconds=.6)
            self.hide(b1,b2,labels,seconds=.3)
            f=self.morph(f,math('P','=',r'\frac{\tau A^2k\omega}{4}',r'\sin(2kx)',r'\sin(2\omega t)',size=32).move_to(f),seconds=.9)
            self.move(Indicate(f[2],color=AMBER,scale_factor=1.06),seconds=.55)
        arrows=self.flow_arrows(t)
        with self.say('15'):
            self.reveal(axis(-5.7,-.55,11.4,False),arrows,
                        txt('箭头：能流方向与相对大小',19,MUTED).move_to([-3.9,.35,0]),
                        eq(r'P>0:\ \rightarrow\qquad P<0:\ \leftarrow',23,GREEN).move_to([3.7,.35,0]),seconds=.55)
            self.move(t.animate.set_value(PI/4),seconds=1.0)
        avg=self.note('一个周期后：净输运为零',GREEN)
        with self.say('16'):
            self.reveal(avg,seconds=.4)
            self.oscillate(t,5*PI/4)
        zeros=VGroup()
        for x in [0,.25,.5,.75,1]:
            zeros.add(Dot([-5.7+11.4*x,-.55,0],radius=.055,color=AMBER),eq('P=0',21,AMBER).move_to([-5.7+11.4*x,-.95,0]))
        with self.say('17'):
            self.hide(avg,seconds=.2)
            self.reveal(zeros,seconds=.5)
            shade=RoundedRectangle(width=2.85,height=.88,corner_radius=.08,stroke_color=AMBER,
                stroke_width=1,fill_color=AMBER,fill_opacity=.045).move_to([-4.275,-.25,0]).set_z_index(-1)
            local=self.note('每段 λ/4 区间内，能量往返重分布',size=23)
            self.reveal(shade,local,seconds=.45)
            self.oscillate(t,9*PI/4)
        with self.say('18'):
            self.hide(zeros,shade,local,seconds=.3)
            a,b=.08,.18
            interval=VGroup(Rectangle(width=(b-a)*11.4,height=.72,stroke_color=GREEN,stroke_width=1.5,
                              fill_color=GREEN,fill_opacity=.08).move_to([-5.7+(a+b)*5.7,-.16,0]),
                            eq('a',23,GREEN).move_to([-5.7+a*11.4,-.77,0]),
                            eq('b',23,GREEN).move_to([-5.7+b*11.4,-.77,0]))
            self.reveal(interval,self.note('流入 − 流出 = 区间内能量的增加',GREEN),seconds=.5)
            f=self.morph(f,math(r'\frac{d}{dt}\int_a^b u\,dx','=',r'P(a,t)','-',r'P(b,t)',size=34).move_to(f),seconds=.9)
            f[2].set_color(GREEN); f[4].set_color(AMBER)
        with self.say('18a'):
            self.move(interval[0].animate.stretch(.5,0),interval[1].animate.shift(RIGHT*.285),
                      interval[2].animate.shift(LEFT*.285),seconds=.65)
            f=self.morph(f,math(r'\partial_tu','+',r'\partial_xP','=','0',size=40,color=GREEN).move_to(f),seconds=.9)
            self.move(Circumscribe(f,color=GREEN,buff=.18),seconds=.9)

    def waves(self):
        self.layout('两列行波，怎样解释局部输运？','换一种解释')
        t=ValueTracker(0)
        lanes=[]
        for base,fn,col,name in [(1.5,lambda x,p:.5*np.sin(2*PI*x-p),CYAN,'向右'),
                                 (0,lambda x,p:.5*np.sin(2*PI*x+p),PURPLE,'向左'),
                                 (-1.5,lambda x,p:np.sin(2*PI*x)*np.cos(p),GREEN,'叠加')]:
            lanes.append(VGroup(axis(base=base,labels=False),live_curve(fn,t,base=base,height=.6,color=col),
                                txt(name,18,col).move_to([-6.15,base+.4,0])))
        back=panel(3.65,4.65,[4.35,-.05,0])
        formulas=VGroup(eq(r'y_+=\tfrac A2\sin(kx-\omega t)',27,CYAN,width=3.3),
                        eq(r'y_-=\tfrac A2\sin(kx+\omega t)',27,PURPLE,width=3.3),
                        eq(r'y_++y_-=A\sin(kx)\cos(\omega t)',25,GREEN,width=3.3)).arrange(DOWN,buff=.8).move_to([4.35,.15,0])
        with self.say('19'):
            self.reveal(back,lanes[0],formulas[0],seconds=.45)
            self.reveal(lanes[1],formulas[1],seconds=.45)
            self.reveal(lanes[2],formulas[2],seconds=.45)
            self.oscillate(t,2*PI)
        graph=VGroup(axis(base=-.05,labels=False),
            curve(lambda x:np.cos(PI/4-2*PI*x)**2,base=-.05,height=1.32,color=CYAN),
            curve(lambda x:-np.cos(PI/4+2*PI*x)**2,base=-.05,height=1.32,color=PURPLE),
            txt('固定截面 x = λ/8 处的瞬时能流',20,MUTED).move_to([-2,2.05,0]),
            eq(r'\omega t',21,MUTED).move_to([2.0,-.35,0]),txt('功率以 C 归一化',18,MUTED).move_to([-4.6,-2.5,0]))
        for x,s in [(0,'0'),(.25,r'\pi/2'),(.5,r'\pi'),(.75,r'3\pi/2'),(1,r'2\pi')]:
            graph.add(eq(s,20,MUTED).move_to([-5.8+7.6*x,-1.95,0]))
        right=VGroup(eq(r'P_+=C\cos^2(kx-\omega t)',25,CYAN,width=3.3).move_to([4.35,1.55,0]),
                     eq(r'P_-=-C\cos^2(kx+\omega t)',25,PURPLE,width=3.3).move_to([4.35,.8,0]),
                     eq(r'C=\tau A^2k\omega/4',24,MUTED).move_to([4.35,-1.8,0]))
        with self.say('20'):
            self.hide(*lanes,*formulas,seconds=.4)
            self.reveal(graph,right,seconds=.8)
        sumcurve=curve(lambda x:np.sin(4*PI*x),base=-.05,height=1.32,color=GREEN,stroke=4)
        averages=VGroup(eq(r'\langle P_+\rangle=+C/2',24,CYAN).move_to([4.35,.0,0]),
                        eq(r'\langle P_-\rangle=-C/2',24,PURPLE).move_to([4.35,-.55,0]),
                        eq(r'\langle P\rangle=0',27,GREEN).move_to([4.35,-1.1,0]))
        cursor=ValueTracker(0)
        dots=VGroup()
        for fn,col in [(lambda q:np.cos(PI/4-q)**2,CYAN),(lambda q:-np.cos(PI/4+q)**2,PURPLE),(lambda q:np.sin(2*q),GREEN)]:
            dots.add(always_redraw(lambda fn=fn,col=col:Dot([-5.8+7.6*cursor.get_value()/(2*PI),-.05+1.32*fn(cursor.get_value()),0],color=col,radius=.06)))
        with self.say('21'):
            self.move(Create(sumcurve),seconds=.6)
            self.reveal(averages,dots,eq('P=P_++P_-',29,GREEN).move_to([-.2,-2.5,0]),seconds=.65)
            self.oscillate(cursor,2*PI)
        with self.say('22'):
            # A clean derivation layer replaces the graph; the question remains.
            old=[m for m in self.mobjects if m not in self.hud+[self.title,self.tag,self.subtitle]]
            self.hide(*old,seconds=.4)
            f=math('P','=',r'-\tau',r'(y_{+,x}+y_{-,x})',r'(y_{+,t}+y_{-,t})',size=36,width=11.7).move_to([0,1.25,0])
            self.reveal(f,seconds=.5)
            expanded=math('P','=','P_+','+','P_-','+',r'P_{\rm cross}',size=38).move_to(f)
            expanded[2].set_color(CYAN); expanded[4].set_color(PURPLE); expanded[6].set_color(AMBER)
            f=self.morph(f,expanded,seconds=.85)
            cross=math(r'P_{\rm cross}','=',r'-\tau',r'(y_{+,x}y_{-,t}+y_{-,x}y_{+,t})',size=33,color=AMBER,width=11.3).move_to([0,-.2,0])
            self.reveal(cross,seconds=.65)
        with self.say('22a'):
            relations=VGroup(eq(r'y_{+,t}=-v\,y_{+,x}',30,CYAN).move_to([-3.0,-1.25,0]),
                             eq(r'y_{-,t}=+v\,y_{-,x}',30,PURPLE).move_to([3.0,-1.25,0]))
            self.reveal(*relations,seconds=.65)
            self.move(seconds=.65)
            cancel=math(r'P_{\rm cross}','=',r'-\tau',r'[',r'v y_{+,x}y_{-,x}','-',r'v y_{-,x}y_{+,x}',r']',size=32,color=AMBER,width=11.3).move_to(cross)
            cross=self.morph(cross,cancel,seconds=.85)
            self.move(seconds=.65)
            strikes=VGroup(*(Line(cross[i].get_left()+DOWN*.06,cross[i].get_right()+UP*.06,color=FG,stroke_width=2) for i in [4,6]))
            self.move(Create(strikes),seconds=.5)
            self.hide(strikes,seconds=.2)
            cross=self.morph(cross,math(r'P_{\rm cross}','=','0',size=36,color=AMBER).move_to(cross),seconds=.7)
            final=math('P','=','P_+','+','P_-',size=41,color=GREEN).move_to(f)
            f=self.morph(f,final,seconds=.8)
            self.reveal(self.note('瞬时能流相加；时间平均才相消',GREEN),seconds=.4)

    def compare(self):
        self.layout('同样在振动，能量输运并不相同','对照结论')
        centers=[-4.15,0,4.15]; colors=[AMBER,CYAN,GREEN]
        titles=['简谐振子','单向简谐行波','理想驻波']
        rows=[['动能、势能相互转换','单个振子，无空间输运','一个振动相位'],
              ['动能密度 = 势能密度','平均能流沿传播方向','相位连续推进'],
              ['能量分布交替集中','局部往返，平均能流为零','同一区间同相，相邻反相']]
        backgrounds=VGroup(*(panel(3.9,4.7,[cx,-.05,0]) for cx in centers))
        t=ValueTracker(0)
        focus=RoundedRectangle(width=3.9,height=4.7,corner_radius=.15,color=AMBER,stroke_width=2).move_to([-4.15,-.05,0])
        icons=[VGroup(Line([-5.5,.7,0],[-2.8,.7,0],color=GRID),always_redraw(lambda:Dot([-4.15+.9*np.cos(t.get_value()),.7,0],radius=.11,color=AMBER))),
               live_curve(lambda x,p:np.sin(2*PI*x-p),t,left=-1.4,width=2.8,base=.7,height=.35,color=CYAN),
               live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),t,left=2.75,width=2.8,base=.7,height=.35,color=GREEN)]
        for i,cid in enumerate(['26','27','28']):
            with self.say(cid):
                if i==0: self.reveal(backgrounds,focus,seconds=.5)
                else: self.move(focus.animate.move_to([centers[i],-.05,0]).set_color(colors[i]),seconds=.65)
                texts=VGroup(txt(titles[i],26,colors[i]).move_to([centers[i],1.85,0]),
                    *(txt(s,21,FG,width=3.5).move_to([centers[i],-.55-j*.65,0]) for j,s in enumerate(rows[i])))
                self.reveal(texts,icons[i],seconds=.6)
                self.oscillate(t,t.get_value()+2*PI)

    def ending(self):
        self.layout('波形停在原地，能量仍在局部流动','回到最初的问题')
        t=ValueTracker(PI/4)
        wave=self.wave(t,left=-5.7,width=11.4,base=1.1,amplitude=.55)
        result=math(r'\langle P(x,t)\rangle_t','=','0',size=46,color=GREEN).move_to([0,-.45,0])
        with self.say('29'):
            self.reveal(wave,result,txt('没有时间平均的净输运',29,FG).move_to([0,-1.4,0]),seconds=.75)
            self.move(Circumscribe(result,color=GREEN,buff=.18),seconds=.8)
            self.oscillate(t,2*PI+PI/4)
        with self.say('30'):
            self.reveal(txt('瞬时能流通常不为零',28,CYAN).move_to([0,-2.25,0]),seconds=.6)
            self.oscillate(t,4*PI+PI/4)


class LayoutCheck(StandingWaveFilm):
    """Exercise every transition and save compact per-beat review timings."""
    quick=True
