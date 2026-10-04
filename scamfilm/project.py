"""Configuration, manifest loading and preflight checks; no provider imports."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def config():
    return read_json('config/project.json')

def shots():
    return read_json('prompts/shots.json')

def characters():
    return read_json('prompts/characters.json')

def load_env():
    """Load simple KEY=value lines without overriding inherited credentials."""
    path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, value = line.partition('=')
        if not sep or not key.strip().replace('_', '').isalnum():
            raise ValueError('Invalid .env line; use KEY=value, without shell commands.')
        os.environ.setdefault(key.strip(), value.strip().strip('\"\''))

def require_key(name):
    load_env()
    key = os.getenv(name)
    if not key:
        raise ValueError(f'Set {name} in .env or the process environment; see README.md.')
    return key

def validate(manifest=None, settings=None):
    manifest = shots() if manifest is None else manifest
    settings = config() if settings is None else settings
    ids = {s['id'] for s in manifest}
    if len(ids) != len(manifest):
        raise ValueError('Duplicate shot ID.')
    by_id = {s['id']: s for s in manifest}
    required = {'scene_number','shot_number','duration','purpose','camera_angle','framing',
                'character_action','facial_expression','dialogue','voice_over','environmental_sound',
                'music_direction','text_to_image_prompt','image_to_video_prompt','negative_prompt',
                'transition','subtitle_text','reverse_compatible','kind','cues'}
    cursor = 0.0
    cue_ids = set()
    for s in manifest:
        if not required <= s.keys():
            raise ValueError(f"Missing shot fields in {s['id']}: {required-s.keys()}")
        if s['duration'] <= 0 or abs(s['timeline_start']-cursor) > .001:
            raise ValueError(f"Bad timeline in {s['id']}")
        cursor += s['duration']
        if abs(s['timeline_end']-cursor) > .001:
            raise ValueError(f"Wrong end time in {s['id']}")
        last = 0
        for c in s['cues']:
            if c['id'] in cue_ids or not (last <= c['start'] < c['end'] <= s['duration']):
                raise ValueError(f"Invalid or overlapping cue {c['id']}")
            if c['speaker'] not in characters():
                raise ValueError(f"Unknown speaker in {c['id']}")
            if any(c['start'] < b and c['end'] > a for a,b in s['silence_intervals']):
                raise ValueError(f"Voice cue overlaps required silence: {c['id']}")
            last = c['end']
            cue_ids.add(c['id'])
        for a,b in s['silence_intervals']:
            if not 0 <= a < b <= s['duration']:
                raise ValueError(f"Invalid silence interval in {s['id']}")
        source = s.get('source')
        for ref in (source if isinstance(source, list) else [source] if source else []):
            if ref not in ids or by_id[ref]['timeline_start'] >= s['timeline_start']:
                raise ValueError(f"Invalid source dependency in {s['id']}: {ref}")
        if s['kind'] == 'reverse':
            original = by_id[source]
            if not original['reverse_compatible']:
                raise ValueError(f"Source was not planned for reverse: {source}")
            a,b = s['reverse_range']
            if not 0 <= a < b <= original['duration']:
                raise ValueError(f"Reverse range exceeds source: {s['id']}")
    ledger = settings['ledger']
    if ledger['opening']-sum(ledger['transfers']) != ledger['closing']:
        raise ValueError('Bank ledger does not reconcile.')
    balance = ledger['closing']
    expected = [balance]
    for amount in reversed(ledger['transfers']):
        balance += amount
        expected.append(balance)
    if settings['rewind_balance_frames'] != expected:
        raise ValueError('Rewind balance ladder does not reconcile.')
    if abs(cursor-settings['runtime_seconds']) > .001:
        raise ValueError('Runtime differs from project configuration.')
    if manifest[-1]['duration'] < 4:
        raise ValueError('Final message needs at least four seconds.')
    return {'segments':len(manifest), 'generated_takes':sum(s['kind']=='generated' for s in manifest),
            'speech_cues':len(cue_ids), 'duration':round(cursor,3)}
