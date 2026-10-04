"""Reverse only a selected bounded shot and isolated original effects."""
from pathlib import Path
from .media import duration, dimensions, ffmpeg, run

def reverse_clip(input_file,output_file,start,end,target_seconds,preview=False):
    actual=duration(input_file)
    if not 0 <= start < end <= actual+.05:
        raise ValueError('Selected rewind interval is outside source duration.')
    _,_,fps=dimensions(preview)
    ratio=target_seconds/(end-start)
    # Bound first; reverse keeps this short selection in memory, not the whole movie.
    vf=f'trim=start={start}:end={end},setpts=PTS-STARTPTS,reverse,setpts={ratio}*PTS,fps={fps},tpad=stop_mode=clone:stop_duration=0.1'
    ffmpeg(['-i',input_file],output_file,vf,target_seconds,preview)

def tempo_filters(speed):
    if speed <= 0: raise ValueError('Audio speed must be positive.')
    filters=[]
    while speed>2:
        filters.append('atempo=2')
        speed/=2
    while speed<.5:
        filters.append('atempo=0.5')
        speed/=.5
    filters.append(f'atempo={speed:.8f}')
    return ','.join(filters)

def reverse_audio(input_file,output_file,start,end,target_seconds):
    if not 0 <= start < end <= duration(input_file)+.05:
        raise ValueError('Selected reverse-audio interval is outside source duration.')
    Path(output_file).parent.mkdir(parents=True,exist_ok=True)
    af=(f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS,areverse,'+
        tempo_filters((end-start)/target_seconds)+',apad')
    run(['ffmpeg','-y','-v','error','-i',input_file,'-af',af,'-t',target_seconds,
         '-ar','48000','-ac','1','-c:a','pcm_s16le',output_file])
