"""Re-time edited shots and refresh readable planning docs from the manifest."""
import _bootstrap
import json
import re
from scamfilm.project import ROOT, shots, config, validate

def main():
    ss=shots(); c=config(); cursor=0
    for s in ss:
        s['duration_frames']=round(s['duration']*c['fps'])
        s['duration']=s['duration_frames']/c['fps']
        s['timeline_start']=round(cursor,6)
        cursor+=s['duration']
        s['timeline_end']=round(cursor,6)
        s['image_to_video_prompt']=re.sub(r'^[0-9.]+-second restrained continuous take\.',
            'One restrained continuous take with clean still handles.',s['image_to_video_prompt'])
    c['runtime_seconds']=round(cursor,6)
    report=validate(ss,c)  # Validate before committing any derived output.
    (ROOT/'prompts/shots.json').write_text(json.dumps(ss,indent=2,ensure_ascii=False)+'\n')
    (ROOT/'config/project.json').write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
    old_scenes=json.loads((ROOT/'prompts/scenes.json').read_text())
    for scene in old_scenes:
        group=[s for s in ss if s['scene_number']==scene['scene_number']]
        scene.update(start=group[0]['timeline_start'],duration=round(sum(s['duration'] for s in group),6),shots=[s['id'] for s in group])
    (ROOT/'prompts/scenes.json').write_text(json.dumps(old_scenes,indent=2)+'\n')
    script=['# Full timed dialogue script\n\nComplete concise master script. Local cue timings and stable IDs also support translation.\n']
    shot_doc=['# Complete shot list and AI prompts\n\nThese are edit durations; generate longer 5/10-second master takes where required by a provider. Post-produced cards, split frames and freezes need no model call.\n']
    for s in ss:
        script.append(f"## {s['id']} — {s['timeline_start']:g}–{s['timeline_end']:g}s\n\n")
        if not s['cues']: script.append('No speech.\n\n')
        for cue in s['cues']:
            script.append(f"- {cue['speaker']} ({cue['start']:g}–{cue['end']:g}s local): “{cue['text']}” [ID: {cue['id']}]\n")
        if s['screen_text']: script.append('\nScreen: '+' / '.join(s['screen_text'])+'\n\n')
        if s['silence_intervals']: script.append('TOTAL SILENCE: '+str(s['silence_intervals'])+'\n\n')
        shot_doc.append(f"## {s['id']} / {s['filename']}\n\n")
        for field in ['scene_number','shot_number','duration','purpose','camera_angle','framing','character_action','facial_expression','environmental_sound','music_direction','transition','reverse_compatible','kind','source','reverse_range']:
            shot_doc.append(f"**{field}:** {s[field]}\n\n")
        shot_doc.append('**Dialogue / VO / subtitles:** '+json.dumps(s['cues'],ensure_ascii=False)+'\n\n')
        for field in ['text_to_image_prompt','image_to_video_prompt','negative_prompt']:
            shot_doc.append(f"**{field}:** {s[field]}\n\n")
    (ROOT/'docs/dialogue_script.md').write_text(''.join(script))
    (ROOT/'docs/shot_list_and_prompts.md').write_text(''.join(shot_doc))
    story=['# Complete storyboard\n\n**It Began Here:** 180 seconds, 1080p, 24fps. The identity question is the turning point. Madam Lim is capable and careful; friendship, urgency, modest hope and loss aversion influence her judgment. She is never blamed.\n\n“A scammer only needs one moment when emotion becomes stronger than caution.”\n\n']
    for scene in old_scenes:
        group=[s for s in ss if s['scene_number']==scene['scene_number']]
        story.append(f"## Scene {scene['scene_number']} — {scene['title']} ({scene['start']:g}–{scene['start']+scene['duration']:g}s)\n\n")
        story.append(' '.join(s['purpose']+'. '+s['character_action']+'.' for s in group)+'\n\n')
    story.append('## Runtime and financial continuity\n\nThe concise master retains all story beats. Generated takes are normally 5/10 seconds, trimmed to their edit duration. The signature rewind is the deliberate fast-edit exception: selected 0.6–2-second fragments, then two seconds of complete silence. Warning cards hold 9–10 seconds; the educational ending has 53 seconds. Final text holds four seconds on black. Phone UI is repeated in large overlays. Review with senior viewers and extend the cut if needed; never accelerate spoken performances.\n\n$5,000 + $3,000 + $22,000 repeated payments + $2,000 + $4,000 + $6,000 = $42,000 sent. $42,860 − $42,000 = $860. The original illustrative figures did not reconcile; the extra repeated payments are explicitly labelled. Rewind restores the exact chronological ledger.\n')
    (ROOT/'docs/storyboard.md').write_text(''.join(story))
    scene9=[s for s in ss if s['scene_number']==9]
    start=scene9[0]['timeline_start']
    rewind=['# Scene 9 — signature rewind plan\n\nAn editorial thought experiment, not an actual bank refund. Reverse selected bounded source takes, never the completed movie.\n\n| Local time | Picture/source | Movement and sound |\n|---|---|---|\n']
    for s in scene9:
        rewind.append(f"| {s['timeline_start']-start:.3f}–{s['timeline_end']-start:.3f}s | {s['source'] or 'black card'} | {s['purpose']}; {s['environmental_sound']} |\n")
    freeze=next(s for s in scene9 if s['kind']=='freeze')
    rewind.append('\nAt the first-call freeze all audio is cut for two seconds. The quote “You really don’t remember me?” stays on screen. Then the narrator speaks:\n\n')
    for cue in freeze['cues']:
        rewind.append(f"- {freeze['timeline_start']-start+cue['start']:.2f}–{freeze['timeline_start']-start+cue['end']:.2f}s: “{cue['text']}”\n")
    rewind.append('\nReverse balances: $860 → $6,860 → $10,860 → $12,860 → $34,860 → $37,860 → $42,860. The labelled $22,000 aggregate is part of the exact ledger. Dedicated locked finger gestures have one continuous touch and still handles. Reverse success into confirm, lift fingertip, retract message stack, dissolve modest family hopes, withdraw opportunity, flip calendar backwards and undo initial acceptance. Emotion moves from anxiety to uncertainty to calm. Nine bounded fragments progressively compress time with `trim, reverse, setpts`; isolated generic FX use `atrim, areverse, atempo`. No reversed speech or subtitles. Keep the exact initial call take for the freeze AND safer replay. No music under the pivot narrator. LET’S TRY AGAIN is silent.\n')
    (ROOT/'docs/rewind_plan.md').write_text(''.join(rewind))
    assets=ROOT/'docs/assets.md'
    base=assets.read_text().split('## Per-shot assets')[0].replace('45 seconds of educational ending','53 seconds of educational ending')
    listing=['## Per-shot assets\n\n']
    for s in ss:
        if s['kind']=='generated':
            listing.append(f"- `assets/images/{s['id']}.png` → `assets/video/{s['filename']}` ({s['duration']:g}s edit).\n")
        else:
            listing.append(f"- `{s['id']}` post-composite ({s['kind']}); source: {s['source']}.\n")
        for cue in s['cues']:
            listing.append(f"  - `assets/audio/{cue['id']}.wav` — {cue['speaker']}\n")
    assets.write_text(base+''.join(listing))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
