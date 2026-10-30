"""Regression: introducing a dynamic curve must not freeze its phase updater."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from standing_wave import StandingWaveFilm, ValueTracker, live_curve, PI, np, config

config.dry_run=True
config.frame_rate=15
config.progress_bar='none'
class DynamicCurveCheck(StandingWaveFilm):
    def construct(self):
        self.active_beat=None
        phase=ValueTracker(0)
        c=live_curve(lambda x,p:np.sin(2*PI*x)*np.cos(p),phase,base=0,height=1)
        self.reveal(c,seconds=.2)
        assert not c.updating_suspended,'Fade-in froze the curve'
        assert c.get_top()[1]>.99
        self.move(phase.animate.set_value(PI/2),seconds=.3)
        self.move(seconds=.15)
        assert abs(c.get_top()[1])<1e-8,'Wave did not reach equilibrium after phase change'
        self.move(phase.animate.set_value(PI),seconds=.3)
        self.move(seconds=.15)
        assert c.get_top()[1]>.99,'Wave failed to resume motion'
        self.hide(c,seconds=.2)
        assert c not in self.mobjects,'Hidden curve remains on screen'
DynamicCurveCheck().render()
print('Dynamic curve regression passed: fade-in, phase change, resume, fade-out.')
