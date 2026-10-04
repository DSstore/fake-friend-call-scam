"""Original guide sounds and deterministic speech/score scheduling at 48 kHz."""
import math
import wave
from array import array
from pathlib import Path
from .project import ROOT, config, shots
from .media import run, duration
from .rewind import reverse_audio

RATE=48000

def write_wave(path,samples):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    pcm=array('h',(max(-32767,min(32767,round(x*32767))) for x in samples))
    with wave.open(str(path),'wb') as wav:
        wav.setparams((1,2,RATE,0,'NONE','not compressed'))
        wav.writeframes(pcm.tobytes())

def tone(seconds,frequency=440,gain=.1,sweep=0):
    count=round(seconds*RATE)
    values=array('f')
    for i in range(count):
        t=i/RATE
        envelope=min(1,t/.02,(seconds-t)/.05)
        values.append(gain*max(0,envelope)*math.sin(2*math.pi*(frequency*t+.5*sweep*t*t)))
    return values

def read_wave(path):
    with wave.open(str(path),'rb') as wav:
        if wav.getnchannels()!=1 or wav.getsampwidth()!=2 or wav.getframerate()!=RATE:
            raise ValueError('Internal audio must be mono 48kHz PCM16 WAV.')
        pcm=array('h')
        pcm.frombytes(wav.readframes(wav.getnframes()))
        return array('f',(x/32768 for x in pcm))

def normalized_audio(path):
    target=ROOT/'output/cache/audio'/(Path(path).stem+'.wav')
    target.parent.mkdir(parents=True,exist_ok=True)
    run(['ffmpeg','-y','-v','error','-i',path,'-ar',RATE,'-ac','1','-c:a','pcm_s16le',target])
    return read_wave(target)

def add(target,source,offset,gain=1,limit=None):
    offset=round(offset*RATE)
    length=min(len(source),len(target)-offset,round(limit*RATE) if limit is not None else len(source))
    for i in range(max(0,length)):
        target[offset+i]+=source[i]*gain

def generate_effects(force=False):
    folder=ROOT/'assets/audio/fx'
    folder.mkdir(parents=True,exist_ok=True)
    sounds={'ring':(.7,660,180),'message':(.20,740,150),'confirm':(.35,880,220),
            'failed':(.5,330,-80),'reverse_seed':(6,690,-85)}
    for name,(seconds,freq,sweep) in sounds.items():
        if force or not (folder/(name+'.wav')).exists():
            samples=tone(seconds,freq,.4,sweep)
            if name=='reverse_seed':
                # Descending source becomes a rising reverse swell; isolated clock clicks.
                for second in range(6):
                    add(samples,tone(.03,1100,.18,-1500),second+.5)
            write_wave(folder/(name+'.wav'),samples)
    return folder

def assemble_audio(preview=False):
    c=config()
    master=array('f',[0])*round(c['runtime_seconds']*RATE)
    effects=generate_effects()
    speakers={'madam_lim':520,'fake_david':310,'real_david':380,'narrator':440}
    beds={}
    for name in ('normal','hopeful','tension','safe'):
        path=ROOT/'assets/music'/(name+'.wav')
        if path.exists(): beds[name]=normalized_audio(path)
    for s in shots():
        start=s['timeline_start']
        if s['music_direction']!='none':
            bed_name='normal' if s['scene_number']<4 else 'hopeful' if s['scene_number']==4 else 'tension' if s['scene_number']<9 else 'safe'
            if bed_name in beds:
                bed=beds[bed_name]
                repeated=bed*math.ceil(s['duration']*RATE/len(bed))
                add(master,repeated,start,c['music_gain'],s['duration'])
            else:
                # An original minimalist tonal bed, not a commercially generated score.
                frequency=110 if bed_name=='tension' else 196
                add(master,tone(s['duration'],frequency,.024),start)
        if 'none' not in s['environmental_sound']:
            add(master,tone(s['duration'],61,.004),start)
        if s['id']=='scene_01_shot_01':
            add(master,read_wave(effects/'ring.wav'),start+1.8,c['sfx_gain'])
        if s['id']=='scene_10_shot_01':
            add(master,read_wave(effects/'ring.wav'),start,c['sfx_gain'])
        if s['scene_number'] in (4,5,6) and 'TRANSFER' in ' '.join(s['screen_text']):
            add(master,read_wave(effects/'confirm.wav'),start+min(1.8,s['duration']-.4),c['sfx_gain'])
        if s['scene_number']==6:
            add(master,read_wave(effects/'message.wav'),start+.2,c['sfx_gain'])
        if s['kind']=='reverse':
            reverse_path=ROOT/'output/cache/audio'/(s['id']+'_reverse_fx.wav')
            reverse_audio(effects/'reverse_seed.wav',reverse_path,0,6,s['duration'])
            add(master,read_wave(reverse_path),start,c['sfx_gain'])
        for cue in s['cues']:
            slot=cue['end']-cue['start']
            path=ROOT/'assets/audio'/(cue['id']+'.wav')
            if preview:
                # Soft identifiable guide pulses, deliberately not synthetic spoken dialogue.
                voice=tone(min(slot,.22),speakers[cue['speaker']],.10)
            else:
                if not path.exists():
                    raise FileNotFoundError(f'Missing voice cue: {path}. Generate or import it before final export.')
                actual=duration(path)
                if actual>slot+.02:
                    raise ValueError(f'Voice {cue["id"]} lasts {actual:.2f}s but slot is {slot:.2f}s. Shorten delivery or extend/re-time the cut; never truncate or speed it up.')
                voice=normalized_audio(path)
            add(master,voice,start+cue['start'],c['voice_gain'])
    # Master silence masks apply LAST, after music, ambience, FX and speech scheduling.
    for s in shots():
        for a,b in s['silence_intervals']:
            i=round((s['timeline_start']+a)*RATE)
            j=round((s['timeline_start']+b)*RATE)
            master[i:j]=array('f',[0])*(j-i)
    peak=max((abs(v) for v in master),default=1)
    if peak>.95:
        gain=.95/peak
        master=array('f',(v*gain for v in master))
    target=ROOT/'output'/('preview_mix.wav' if preview else 'film_mix.wav')
    write_wave(target,master)
    return target
