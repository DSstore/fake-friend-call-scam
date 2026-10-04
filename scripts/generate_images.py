"""Reference generation first, then reference-aware shot stills."""
import _bootstrap
import argparse
from scamfilm.project import ROOT, characters, shots, validate, config
from scamfilm.providers import image_provider

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',default=config()['providers']['image'])
    parser.add_argument('--references',action='store_true')
    parser.add_argument('--shot')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    validate()
    chars=characters()
    jobs=[]
    if args.references:
        for name in ('home','madam_lim'):
            item=chars[name]
            refs=[] if name=='home' else [ROOT/chars['home']['reference_file']]
            jobs.append((name,item['reference_prompt'],ROOT/item['reference_file'],refs))
    else:
        for shot in shots():
            if shot['kind']=='generated' and (not args.shot or args.shot==shot['id']):
                jobs.append((shot['id'],shot['text_to_image_prompt']+' '+shot['negative_prompt'],
                             ROOT/'assets/images'/(shot['id']+'.png'),[ROOT/r for r in shot['references']]))
    if not jobs: parser.error('No matching image jobs.')
    provider=None if args.dry_run else image_provider(args.provider)
    for name,prompt,out,refs in jobs:
        if out.exists() and not args.force:
            print('Already exists:',name)
            continue
        print(('PLAN ' if args.dry_run else 'GENERATE ')+name,flush=True)
        if args.dry_run: continue
        for ref in refs:
            if not ref.exists(): raise FileNotFoundError(f'Approve/create reference first: {ref}')
        provider.generate_image(prompt,out,refs)

if __name__=='__main__': main()
