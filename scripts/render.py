"""Render the complete silent film, export timed subtitles and a cover image."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--quality',choices=['preview','final'],default='final')
args=parser.parse_args()
(ROOT/'output').mkdir(exist_ok=True)
(ROOT/'build').mkdir(exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'scripts/check_physics.py')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/check_animation.py')],cwd=ROOT,check=True)
size,rate=('1280,720','30') if args.quality=='preview' else ('1920,1080','30')
cmd=[sys.executable,'-m','manim','-r',size,'--fps',rate,'src/standing_wave.py','StandingWaveFilm']
with (ROOT/'build/render.log').open('w') as log:
    subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
height=size.split(',')[1]
source=ROOT/f'media/videos/standing_wave/{height}p{rate}/StandingWaveFilm.mp4'
name='standing_wave' if args.quality=='final' else 'standing_wave_preview'
target=ROOT/f'output/{name}.mp4'
timeline=json.loads((ROOT/'build/timeline.json').read_text())
def timestamp(t):
    ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
srt='\n\n'.join(f"{i+1}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}" for i,c in enumerate(timeline))+'\n'
(ROOT/f'output/{name}.srt').write_text(srt)
(ROOT/f'output/{name}.timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
titles={'question':'波形不走，能量呢？','model':'什么保持不动？','energy':'能量在哪里？',
        'density':'瞬时分布与时间平均','flux':'局部能量输运','waves':'两列行波的解释',
        'phase':'相位','compare':'三方对比','ending':'回到问题'}
metadata=[';FFMETADATA1','title=驻波：波形不走，能量呢？','comment=Manim · 无声字幕版 · 理想均匀弦的小振幅模型']
starts=[c for i,c in enumerate(timeline) if i==0 or c['scene']!=timeline[i-1]['scene']]
for i,c in enumerate(starts):
    end=starts[i+1]['start'] if i+1<len(starts) else timeline[-1]['end']
    start=round(c['start']*1000) if i else 0
    metadata.extend(['[CHAPTER]','TIMEBASE=1/1000',f"START={start}",f'END={round(end*1000)}',f"title={titles[c['scene']]}"])
meta=ROOT/'build/chapters.txt'; meta.write_text('\n'.join(metadata)+'\n')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-i',str(meta),
                '-map','0:v:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-an',
                '-movflags','+faststart',str(target)],check=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','7','-i',str(target),
                '-frames:v','1','-update','1',str(ROOT/'output/cover.png')],check=True)
print(f'Exported {target}; {timeline[-1]["end"]:.2f} seconds, no audio')
