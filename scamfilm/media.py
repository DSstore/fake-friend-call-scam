"""Explicit FFmpeg calls. Commands are argument lists, never shell strings."""
import json
import shutil
import subprocess
from pathlib import Path
from .project import config

def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:] or result.stdout[-5000:])
    return result.stdout

def preflight():
    for name in ('ffmpeg','ffprobe'):
        if not shutil.which(name):
            raise RuntimeError(f'{name} is required. Install FFmpeg with libass and drawtext.')
    filters = run(['ffmpeg','-hide_banner','-filters'])
    for name in ('subtitles','drawtext','reverse','areverse'):
        if name not in filters:
            raise RuntimeError(f'FFmpeg lacks {name}. Install a full build.')

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',path]))

def duration(path):
    return float(probe(path)['format']['duration'])

def dimensions(preview=False):
    c = config()
    return (c['preview_width'],c['preview_height'],c['preview_fps']) if preview else (c['width'],c['height'],c['fps'])

def codec(preview=False):
    return ['-c:v','libx264','-preset','ultrafast' if preview else 'fast',
            '-crf','25' if preview else '18','-pix_fmt','yuv420p','-threads','2','-an']

def ffmpeg(inputs, output, vf=None, seconds=None, preview=False, extra=()):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    args = ['ffmpeg','-y','-v','error','-filter_threads','2','-filter_complex_threads','2',*inputs]
    if vf:
        args += ['-vf',vf]
    if seconds is not None:
        args += ['-t',str(seconds)]
    run(args + list(extra) + codec(preview) + [output])

def escape_filter_path(path):
    # Filter expressions have their own parser even when no shell is involved.
    return str(path).replace('\\','\\\\').replace(':','\\:').replace("'", "'\\''")

def normal_filter(preview=False):
    w,h,fps=dimensions(preview)
    return f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps}'

def normalize(input_file, output_file, seconds, preview=False):
    actual = duration(input_file)
    if actual < 1 or actual < seconds-.25:
        raise ValueError(f'Video too short: {input_file} is {actual:.2f}s; needs {seconds:.2f}s. Regenerate a longer source.')
    ffmpeg(['-i',input_file],output_file,
           normal_filter(preview)+',tpad=stop_mode=clone:stop_duration=0.25',seconds,preview)

def concatenate(files, output, preview=False):
    output = Path(output)
    listing = output.with_suffix('.concat.txt')
    # Our artifact names are generated IDs; reject unsafe concat paths.
    if any("'" in str(p) or '\n' in str(p) for p in files):
        raise ValueError('Concat file paths may not contain apostrophes/newlines.')
    listing.write_text(''.join(f"file '{Path(p).resolve()}'\n" for p in files))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',listing,
         '-c','copy','-movflags','+faststart',output])
