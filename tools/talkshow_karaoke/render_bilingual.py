#!/usr/bin/env python3
"""Burn bilingual karaoke subtitle cues and the reusable CTA into a portrait video."""
import argparse, json, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('cues',type=Path);p.add_argument('output',type=Path)
p.add_argument('--badge',type=Path,default=Path(__file__).with_name('talkshow_comment_cta.png'))
a=p.parse_args()
a.output.parent.mkdir(parents=True,exist_ok=True)
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,duration','-of','json',str(a.source)]))['streams'][0]
w,h=meta['width'],meta['height']
if abs(w/h-9/16)>0.025: p.error('Expected a portrait 9:16 video.')
cfg=json.loads(a.cues.read_text(encoding='utf8'));dur=float(meta['duration'])
cues,cta,cta_len=cfg['cues'],float(cfg['cta_start']),float(cfg.get('cta_duration',1.55))
if not cues or not 0<cta<=dur or cta_len<=0 or cta_len>5: p.error('Invalid cue or CTA timing.')
line_scales = cfg.get('line_scale_x', [100] * len(cues))
if (not isinstance(line_scales, list) or len(line_scales) != len(cues)
    or any(type(value) is not int or not 55 <= value <= 100 for value in line_scales)):
 p.error('line_scale_x must contain one integer between 55 and 100 per cue.')
prev=0
for s,e,en,zh in cues:
 if not prev<=s<e<=min(cta,dur) or not en or not zh: p.error('Cues must be nonempty, chronological, and end before CTA.')
 prev=e
outdur=max(dur,cta+cta_len)
hold=outdur-dur
def timestamp(secs):
 cs=round(100*secs);return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'
def label(s):
 if any(c in s for c in '{}\\\n\r'): p.error('Cue text must be plain (no braces, backslashes or line breaks).')
 return s
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: EN,DejaVu Sans,43,&H00FFFFFF,&H00FFFFFF,&H00111518,&H90111518,-1,0,0,0,100,100,0,0,1,3.6,1.0,5,32,32,12,1
Style: ZH,Noto Sans CJK SC,44,&H00E8F4FF,&H00E8F4FF,&H00111518,&H90111518,-1,0,0,0,100,100,0,0,1,3.6,1.0,5,32,32,12,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
with tempfile.TemporaryDirectory(prefix='talkshow_sub_') as tmp:
 ass=Path(tmp)/'bilingual.ass'
 lines=[]
 def event(start,end,style,y,value):
  lines.append(f'Dialogue: 0,{timestamp(start)},{timestamp(end)},{style},,0,0,0,,{{\\an5\\pos(360,{y})}}{value}')
 word_cues=cfg.get('word_onsets')
 if word_cues is not None and len(word_cues)!=len(cues):
  p.error('Provide one onset array per caption cue.')
 for i,(s,e,en,zh) in enumerate(cues):
  words=label(en).split()
  scale=line_scales[i]
  tag=r'{\fscx'+str(scale)+'}' if scale != 100 else ''
  event(s,e,'ZH',1009,label(zh))
  if word_cues is None:
   event(s,e,'EN',950,tag+label(en))
   continue
  times=word_cues[i]
  if len(times)!=len(words) or not s<=times[0]<e or any(a>=b for a,b in zip(times,times[1:])) or times[-1]>=e:
   p.error(f'Word onsets do not match cue {i+1}.')
  if s<times[0]:
   event(s,times[0],'EN',950,tag+en)
  for j,(start,end) in enumerate(zip(times,[*times[1:],e])):
   colored=words.copy()
   colored[j]=r'{\1c&H6DE7FF&}'+colored[j]+r'{\1c&HFFFFFF&}'
   event(start,end,'EN',950,tag+' '.join(colored))
 ass.write_text(header+'\n'.join(lines)+'\n',encoding='utf8')
 width=round(w*.41/2)*2
 filt=(f"[0:v]tpad=stop_mode=clone:stop_duration={hold+.04:.3f},subtitles={ass}[main];"
       f"[1:v]scale={width}:-2,format=rgba[badge];"
       f"[main][badge]overlay=x=(W-w)/2:y=H*0.735:enable='gte(t,{cta:.3f})':format=auto,format=yuv420p[out]")
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(a.source),'-i',str(a.badge),'-filter_complex_threads','2','-filter_complex',filt,'-map','[out]','-map','0:a:0','-af','apad','-t',f'{outdur:.3f}','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-c:a','aac','-b:a','160k','-movflags','+faststart',str(a.output)],check=True)
