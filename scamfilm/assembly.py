"""Shot builders and final editing. Preview and production never share sources."""
import hashlib
import json
from pathlib import Path
from .project import ROOT, config, shots, validate
from .media import (preflight, normalize, ffmpeg, run, dimensions, normal_filter,
                    concatenate, escape_filter_path, duration)
from .graphics import slate, card, apply_overlay, draw_text
from .rewind import reverse_clip
from .audio import assemble_audio
from .subtitles import create_subtitles

def cache_folder(preview):
    files=[ROOT/'assets/video'/s['filename'] for s in shots() if s['kind']=='generated']
    stamps=[(str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in files if p.exists()]
    key=hashlib.sha256(json.dumps([shots(),config(),stamps],sort_keys=True).encode()).hexdigest()[:12]
    folder=ROOT/'output/cache'/('preview' if preview else 'film')/key
    folder.mkdir(parents=True,exist_ok=True)
    return folder

def build_sources(preview=False,force=False):
    folder=cache_folder(preview)/'sources'
    folder.mkdir(parents=True,exist_ok=True)
    result={}
    for s in shots():
        if s['kind']!='generated': continue
        output=folder/s['filename']
        if force or not output.exists():
            print(f"Building source {s['id']}",flush=True)
            if preview:
                slate(s,output,True)
            else:
                source=ROOT/'assets/video'/s['filename']
                if not source.exists():
                    raise FileNotFoundError(f'Missing approved source {source}; generate or import it. Use build_preview.py for offline review.')
                normalize(source,output,s['duration'])
        result[s['id']]=output
    return result

def build_shots(preview=False,force=False):
    sources=build_sources(preview,force)
    folder=cache_folder(preview)/'shots'
    folder.mkdir(parents=True,exist_ok=True)
    result={}
    w,h,fps=dimensions(preview)
    for s in shots():
        output=folder/s['filename']
        if force or not output.exists():
            print(f"Editing {s['id']} ({s['kind']})",flush=True)
            temporary=folder/(s['id']+'_base.mp4')
            kind=s['kind']
            if kind=='card':
                tea=sources['scene_01_shot_01'] if s['scene_number']==13 and s['shot_number']==6 else None
                card(s,output,preview,tea)
                result[s['id']]=output
                continue
            if kind=='generated':
                temporary=sources[s['id']]
            elif kind=='reuse':
                normalize(sources[s['source']],temporary,s['duration'],preview)
            elif kind=='reverse':
                reverse_clip(sources[s['source']],temporary,*s['reverse_range'],s['duration'],preview)
            elif kind=='freeze':
                frame=folder/(s['id']+'.png')
                run(['ffmpeg','-y','-v','error','-ss','2','-i',sources[s['source']],
                     '-frames:v','1','-threads','1',frame])
                ffmpeg(['-loop','1','-i',frame],temporary,f'fps={fps}',s['duration'],preview)
            elif kind=='split':
                left,right=[sources[sid] for sid in s['source']]
                filters=(f'[0:v]scale={w//2}:{h}:force_original_aspect_ratio=increase,crop={w//2}:{h},'
                         f'tpad=stop_mode=clone:stop_duration=5,fps={fps},setsar=1[l];'
                         f'[1:v]scale={w//2}:{h}:force_original_aspect_ratio=increase,crop={w//2}:{h},'
                         f'tpad=stop_mode=clone:stop_duration=5,fps={fps},setsar=1[r];'
                         '[l][r]hstack=inputs=2[v]')
                ffmpeg(['-i',left,'-i',right,'-filter_complex',filters,'-map','[v]'],
                       temporary,None,s['duration'],preview)
            else:
                raise ValueError(f'Unknown shot type {kind}')
            apply_overlay(s,temporary,output,preview)
        result[s['id']]=output
    return result

def assemble_scene(scene_number,preview=False,force=False):
    """Normalized visual scene intermediate; final assembly handles dialogue/audio."""
    items=build_shots(preview,force)
    selected=[items[s['id']] for s in shots() if s['scene_number']==scene_number]
    if not selected: raise ValueError('Unknown scene.')
    target=cache_folder(preview)/f'scene_{scene_number:02d}.mp4'
    concatenate(selected,target,preview)
    return target

def assemble_final_video(preview=False,force=False):
    validate()
    preflight()
    # Fail before expensive visual editing if any production asset is absent or too long.
    if not preview:
        missing=[]
        for s in shots():
            if s['kind']=='generated' and not (ROOT/'assets/video'/s['filename']).exists():
                missing.append(s['filename'])
            for cue in s['cues']:
                path=ROOT/'assets/audio'/(cue['id']+'.wav')
                if not path.exists(): missing.append(path.name)
                elif duration(path)>cue['end']-cue['start']+.02:
                    raise ValueError(f'Voice cue does not fit: {cue["id"]}; revise timing before rendering.')
        if missing:
            raise FileNotFoundError(f'Final export requires approved assets. Missing {len(missing)} files; first: '+', '.join(missing[:5])+'. Local preview: python scripts/build_preview.py')
    items=build_shots(preview,force)
    silent=cache_folder(preview)/'picture.mp4'
    concatenate([items[s['id']] for s in shots()],silent,preview)
    audio=assemble_audio(preview)
    c=config()
    language=c.get('subtitle_language','en')
    if language=='en':
        subtitles=create_subtitles()
    else:
        subtitles=ROOT/'assets/subtitles'/(language+'.ass')
        if not subtitles.exists():
            raise FileNotFoundError('Generate reviewed translated subtitles before export; see README section 6.')
    output=ROOT/(c['preview_output'] if preview else c['final_output'])
    vf=f"subtitles='{escape_filter_path(subtitles)}'"
    # The last preview watermark occupies a separate strip below caption baseline.
    args=['ffmpeg','-y','-v','error','-filter_threads','2','-i',silent,'-i',audio,
          '-map','0:v:0','-map','1:a:0','-vf',vf,'-af','loudnorm=I=-16:TP=-1.5:LRA=11',
          '-c:v','libx264','-preset','ultrafast' if preview else 'fast','-crf','25' if preview else '18',
          '-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
          '-t',str(c['runtime_seconds']),'-movflags','+faststart',output]
    run(args)
    actual=duration(output)
    if abs(actual-c['runtime_seconds'])>.1:
        raise RuntimeError(f'Unexpected export runtime {actual:.3f}s.')
    report={'output':str(output.relative_to(ROOT)),'mode':'animatic' if preview else 'production',
            'duration':actual,'width':dimensions(preview)[0],'height':dimensions(preview)[1],
            'audio':'guide tones; no spoken performance' if preview else 'provided voice cues',
            'validation':validate()}
    (output.with_suffix('.json')).write_text(json.dumps(report,indent=2)+'\n')
    return output
