#!/usr/bin/env python3
"""Generate the vector and transparent raster version of the Talk Show CTA."""
from pathlib import Path
from xml.sax.saxutils import escape
import sys, subprocess
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

root=Path(__file__).resolve().parent
f=TTFont(sys.argv[1] if len(sys.argv)>1 else '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',fontNumber=int(sys.argv[2]) if len(sys.argv)>2 else 2)
gs=f.getGlyphSet(); cmap=f.getBestCmap()
label='评论区看解析'
scale=31/f['head'].unitsPerEm
x=71
shapes=[]
for ch in label:
 name=cmap[ord(ch)]
 p=SVGPathPen(gs);gs[name].draw(p)
 shapes.append(f'<path d="{escape(p.getCommands())}" transform="translate({x:.3f},49) scale({scale:.6f},{-scale:.6f})"/>')
 x+=gs[name].width*scale+1.1
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="328" height="80" viewBox="0 0 328 80" role="img" aria-label="{label}">
<title>{label}</title>
<rect x="4" y="8" width="320" height="68" rx="34" fill="#05090E" fill-opacity=".47"/>
<rect x="4" y="4" width="320" height="68" rx="34" fill="#141923" stroke="#E9C277" stroke-width="2"/>
<circle cx="40" cy="38" r="22" fill="#F5D58C"/>
<path d="M31 29h18a2.5 2.5 0 0 1 2.5 2.5v12A2.5 2.5 0 0 1 49 46H40l-5.5 4.5V46H31a2.5 2.5 0 0 1-2.5-2.5v-12A2.5 2.5 0 0 1 31 29Z" fill="none" stroke="#181D29" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.3"/>
<path d="M35 35h10m-10 5h7" stroke="#181D29" stroke-linecap="round" stroke-width="2"/>
<g fill="#FFF7E7">{''.join(shapes)}</g>
<path d="M286 34l7 7 7-7m-7 7v-13" fill="none" stroke="#F5D58C" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
p=root/'talkshow_comment_cta.svg';p.write_text(svg)
subprocess.run(['inkscape',str(p),'--export-width=984',f'--export-filename={root/"talkshow_comment_cta.png"}'],check=True)
