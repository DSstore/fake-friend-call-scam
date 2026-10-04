"""SRT/ASS captions and stable language-independent translation IDs."""
import json
import textwrap
import unicodedata
from pathlib import Path
from .project import ROOT, shots, config

def wrap(text):
    if any(unicodedata.east_asian_width(c) in ('W','F') for c in text):
        # CJK characters occupy roughly two Latin columns; don't rely on spaces.
        lines=[]; line=''; columns=0
        for char in text:
            width=2 if unicodedata.east_asian_width(char) in ('W','F') else 1
            if columns+width>42:
                lines.append(line); line=''; columns=0
            line+=char; columns+=width
        if line: lines.append(line)
    else:
        lines=textwrap.wrap(text,42,break_long_words=False,break_on_hyphens=False)
    if len(lines)>2:
        raise ValueError('Subtitle requires more than two lines; split the cue or review translation timing.')
    return '\n'.join(lines)

def timestamp(value,ass=False):
    units=round(value*(100 if ass else 1000))
    rate=100 if ass else 1000
    hours,rest=divmod(units,3600*rate)
    minutes,rest=divmod(rest,60*rate)
    seconds,fraction=divmod(rest,rate)
    return f'{hours}:{minutes:02}:{seconds:02}.{fraction:02}' if ass else f'{hours:02}:{minutes:02}:{seconds:02},{fraction:03}'

def escape_ass(text):
    # Neutralize override syntax before adding our own safe line breaks.
    return text.replace('\\','/').replace('{','(').replace('}',')').replace('\n',r'\N')

def create_subtitles(translation=None,language='en'):
    folder=ROOT/'assets/subtitles'
    folder.mkdir(parents=True,exist_ok=True)
    catalog=[]
    template={}
    translated=json.loads(Path(translation).read_text())['translations'] if translation else {}
    for s in shots():
        for c in s['cues']:
            template[c['id']]=c['text']
            if translation and c['id'] not in translated:
                raise ValueError(f"Translation missing {c['id']}")
            catalog.append({**c,'text':translated.get(c['id'],c['text']),
                            'start':s['timeline_start']+c['start'],'end':s['timeline_start']+c['end']})
    catalog.sort(key=lambda c:c['start'])
    srt=[]
    for i,c in enumerate(catalog,1):
        srt.append(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{wrap(c['text'])}\n")
    (folder/f'{language}.srt').write_text('\n'.join(srt),encoding='utf-8')
    c=config()
    ass=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {c['width']}
PlayResY: {c['height']}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{c.get('subtitle_font_family','DejaVu Sans')},{c['font_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,96,96,65,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for line in catalog:
        ass+=f"Dialogue: 0,{timestamp(line['start'],True)},{timestamp(line['end'],True)},Default,,0,0,0,,{escape_ass(wrap(line['text']))}\n"
    (folder/f'{language}.ass').write_text(ass,encoding='utf-8')
    (folder/'cue_catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
    # Do not clobber a user's translation while regenerating subtitles.
    target=folder/'translation_template.json'
    if not target.exists():
        target.write_text(json.dumps({'language':'zh','translations':template},indent=2,ensure_ascii=False)+'\n')
    return folder/f'{language}.ass'
