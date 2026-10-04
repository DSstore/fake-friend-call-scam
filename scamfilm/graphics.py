"""Readable graphics added AFTER generation; text is never entrusted to a model."""
import hashlib
import textwrap
from pathlib import Path
from .project import ROOT, config
from .media import dimensions, escape_filter_path, ffmpeg, normal_filter

def text_file(text):
    folder=ROOT/'output/cache/text'
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(hashlib.sha256(text.encode()).hexdigest()[:20]+'.txt')
    path.write_text(text,encoding='utf-8')
    return path

def draw_text(text,x,y,size,color='white',enable=None):
    font=Path(config()['font'])
    if not font.exists():
        raise ValueError('Set config/project.json font to an installed TrueType/OpenType font.')
    result=(f"drawtext=fontfile='{escape_filter_path(font)}':textfile='{escape_filter_path(text_file(text))}':"
            f'fontsize={size}:fontcolor={color}:x={x}:y={y}:line_spacing=12:fix_bounds=1')
    if enable:
        result+=f":enable='{enable}'"
    return result

def watermark(preview=False):
    if not preview: return []
    w,h,_=dimensions(preview)
    return [draw_text('ANIMATIC / NO AI FOOTAGE / GUIDE AUDIO', '(w-text_w)/2', h-18, max(12,round(w/64)), '0xf5d09d')]

def lines_for(texts,width=62):
    lines=[]
    for paragraph in texts:
        lines+=textwrap.wrap(paragraph,width=width,break_long_words=False,break_on_hyphens=False) or ['']
    return lines

def slate(shot,output,preview=False):
    """Offline storyboard clip: honest labelled placeholder, not generated imagery."""
    w,h,fps=dimensions(preview)
    small=max(14,round(w/56))
    body=max(18,round(w/43))
    lines=lines_for([shot['purpose'],shot['character_action']],58)[:6]
    top=round(h*.25)
    filters=[draw_text(shot['id'],'(w-text_w)/2',round(h*.14),body,'0xf5d09d')]
    filters += [draw_text(line,'(w-text_w)/2',top+i*round(body*1.6),body) for i,line in enumerate(lines)]
    filters += [draw_text(f"DAY {shot['day']}  |  {shot['duration']:g}s  |  {shot['framing']}",
                         '(w-text_w)/2',round(h*.73),small)]
    # A travelling cue dot makes time direction visible even in an offline slate.
    filters += [draw_text('●',f'40+(w-100)*t/{shot["duration"]}',round(h*.81),body,'0xf5d09d')]
    color='0x193a40' if shot['day']<4 else '0x232d3c'
    ffmpeg(['-f','lavfi','-i',f'color=c={color}:s={w}x{h}:r={fps}'],output,','.join(filters),shot['duration'],preview)

def card(shot,output,preview=False,tea_source=None):
    w,h,fps=dimensions(preview)
    size=round(config()['card_font_size']*w/config()['width'])
    texts=lines_for(shot['screen_text'],62)
    line_height=round(size*1.65)
    y=round((h-line_height*len(texts))/2)
    filters=[draw_text(line,'(w-text_w)/2',y+i*line_height,size,
                       '0xf5d09d' if i==0 else 'white') for i,line in enumerate(texts)]
    filters+=watermark(preview)
    if tea_source:
        # First two seconds warm tea, then black; text has a full four-second static black hold.
        base=normal_filter(preview)+f',tpad=stop_mode=clone:stop_duration={shot["duration"]},fade=t=out:st=1.3:d=0.7,'+\
             "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='gte(t,2)'"
        ffmpeg(['-i',tea_source],output,base+','+','.join(filters),shot['duration'],preview)
    else:
        color='black' if shot['scene_number']==9 else '0x101b2a'
        ffmpeg(['-f','lavfi','-i',f'color=c={color}:s={w}x{h}:r={fps}'],output,','.join(filters),shot['duration'],preview)

def overlay_filters(shot,preview=False):
    w,h,_=dimensions(preview)
    size=round(40*w/1920)
    filters=[]
    if shot.get('ui_states'):
        filters.append(f'drawbox=x=0:y=0:w=iw:h={round(size*5)}:color=black@0.78:t=fill')
        for state in shot['ui_states']:
            for i,line in enumerate(state['lines']):
                filters.append(draw_text(line,'(w-text_w)/2',round(size*.7+i*size*1.5),size,
                    enable=f'gte(t,{state["start"]})*lt(t,{state["end"]})'))
    elif shot['screen_text']:
        # Upper panel keeps phone screens and subtitles legible on independent layers.
        texts=lines_for(shot['screen_text'],61)
        panel_height=min(round(h*.40),round((len(texts)+1)*size*1.6))
        filters.append(f'drawbox=x=0:y=0:w=iw:h={panel_height}:color=black@0.78:t=fill')
        for i,line in enumerate(texts):
            filters.append(draw_text(line,'(w-text_w)/2',round(size*.7+i*size*1.5),size))
    if shot['kind']=='reverse':
        if shot['shot_number']==1:
            balances=config()['rewind_balance_frames']
            step=shot['duration']/len(balances)
            for i,balance in enumerate(balances):
                filters.append(draw_text(f'${balance:,.0f}','(w-text_w)/2',round(h*.55),round(size*2),
                   '0xf5d09d',f'gte(t,{i*step:.6f})*lt(t,{(i+1)*step:.6f})'))
        elif shot['shot_number'] in (4,5):
            # Reverse a transfer-state UI deliberately rather than backwards lettering.
            for line,a,b in [('TRANSFER SUCCESSFUL',0,shot['duration']*.45),
                             ('CONFIRM TRANSFER',shot['duration']*.45,shot['duration'])]:
                filters.append(draw_text(line,'(w-text_w)/2',round(h*.25),size,'white',f'gte(t,{a})*lt(t,{b})'))
        elif shot['shot_number'] in (2,3):
            for i,line in enumerate(["Don't tell anyone first.",'Trust me.','Last payment.']):
                filters.append(draw_text(line,'(w-text_w)/2',round(h*.25+i*size*1.5),size,
                                         enable=f'lt(t,{shot["duration"]*(.3+.3*i)})'))
    if shot['kind']=='freeze':
        filters.append(f'drawbox=x={round(w*.62)}:y={round(h*.35)}:w={round(w*.20)}:h={round(h*.35)}:color=0xf5d09d@0.5:t=2')
    filters+=watermark(preview)
    return filters

def apply_overlay(shot,input_file,output_file,preview=False):
    filters=overlay_filters(shot,preview)
    if 'dissolve' in shot['transition']:
        filters+=['fade=t=in:d=0.35',f'fade=t=out:st={shot["duration"]-.35}:d=0.35']
    ffmpeg(['-i',input_file],output_file,','.join(filters) or 'null',shot['duration'],preview)
