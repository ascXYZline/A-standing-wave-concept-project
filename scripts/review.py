"""Validate exported streams and timings; create one review frame per cue."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
video=ROOT/'output/standing_wave.mp4'
timeline=json.loads((ROOT/'output/standing_wave.timeline.json').read_text())
script=json.loads((ROOT/'narration/script.json').read_text())['cues']
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams',
                                          '-show_format','-show_chapters','-of','json',str(video)]))
streams=probe['streams']; visual=[s for s in streams if s['codec_type']=='video']
assert len(visual)==1
v=visual[0]
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert not any(s['codec_type']=='audio' for s in streams)
assert len(timeline)==len(script) and len(probe['chapters'])==9
assert [c['id'] for c in timeline]==[c['id'] for c in script]
assert abs(float(probe['format']['duration'])-timeline[-1]['end'])<.07
for i,c in enumerate(timeline):
    assert c['end']>c['start']
    if i:
        gap=c['start']-timeline[i-1]['end']
        # Short chapter transitions intentionally contain no subtitle.
        allowed=1.0 if c['scene']!=timeline[i-1]['scene'] else .07
        assert -.04<=gap<=allowed,(c['id'],gap)
    assert c['text']==script[i]['text']
    assert '难点' not in c['text']
decoded=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(video),'-f','null','-'],
                       capture_output=True,text=True,check=True)
assert not decoded.stderr,decoded.stderr
frames=ROOT/'build/final_frames'; frames.mkdir(exist_ok=True)
def capture(c):
    stamp=c['start']+(c['end']-c['start'])*.68
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(stamp),'-i',str(video),
                    '-frames:v','1','-vf','scale=640:360','-update','1',str(frames/(c['id']+'.png'))],check=True)
with ThreadPoolExecutor(max_workers=4) as ex: list(ex.map(capture,timeline))
sheet=Image.new('RGB',(1920,360*((len(timeline)+2)//3)))
for i,c in enumerate(timeline): sheet.paste(Image.open(frames/(c['id']+'.png')),((i%3)*640,(i//3)*360))
sheet.save(ROOT/'build/final-sheet.jpg',quality=93)
board=Image.new('RGB',(1920,1080))
for i,cid in enumerate(['02','05','24','06b','12a','18a','22a','28','30']):
    board.paste(Image.open(frames/(cid+'.png')),((i%3)*640,(i//3)*360))
board.save(ROOT/'output/storyboard.jpg',quality=95)
report={'video':str(video.relative_to(ROOT)),'duration_seconds':float(probe['format']['duration']),
        'resolution':[v['width'],v['height']],'fps':v['r_frame_rate'],'codec':v['codec_name'],
        'pixel_format':v['pix_fmt'],'audio_tracks':0,'chapters':9,'subtitle_cues':len(timeline),
        'full_decode':'passed','subtitle_timings':'passed','review_frames':len(timeline),
        'physics':json.loads((ROOT/'build/physics_checks.json').read_text())}
(ROOT/'output/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(f'Export verified: 1080p30 H.264, no audio, {len(timeline)} subtitle cues, 9 chapters, full decode passed.')
