"""Animate approved stills, or inspect a generation plan without API calls."""
import _bootstrap
import argparse
from scamfilm.project import ROOT, shots, validate, config, load_env
from scamfilm.providers import video_provider
from scamfilm.providers.fal import model_duration

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',default=config()['providers']['video'])
    parser.add_argument('--shot')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    validate(); load_env()
    provider=None if args.dry_run else video_provider(args.provider)
    chosen=[s for s in shots() if s['kind']=='generated' and (not args.shot or s['id']==args.shot)]
    if not chosen: parser.error('No matching generated source shot.')
    for s in chosen:
        out=ROOT/'assets/video'/s['filename']
        if out.exists() and not args.force:
            print('Already exists:',s['id']); continue
        purchased=model_duration(s['duration'],config())
        print(f"{s['id']}: edit={s['duration']}s, provider_take={purchased}s",flush=True)
        if args.dry_run: continue
        image=ROOT/'assets/images'/(s['id']+'.png')
        if not image.exists(): raise FileNotFoundError(f'Generate and approve still first: {image}')
        # --force reruns download/resumes saved job, never silently purchases another one.
        provider.generate_video(image,f'Generate a {purchased}-second source take. '+s['image_to_video_prompt']+' Avoid: '+s['negative_prompt'],out,s['duration'])

if __name__=='__main__': main()
