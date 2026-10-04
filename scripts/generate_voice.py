"""One file per speaker/cue; timings remain independently editable."""
import _bootstrap
import argparse
from scamfilm.project import ROOT, shots, validate, config
from scamfilm.providers import voice_provider
from scamfilm.media import duration

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',default=config()['providers']['voice'])
    parser.add_argument('--speaker')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    validate()
    provider=None if args.dry_run else voice_provider(args.provider)
    for s in shots():
        for cue in s['cues']:
            if args.speaker and args.speaker!=cue['speaker']: continue
            out=ROOT/'assets/audio'/(cue['id']+'.wav')
            slot=cue['end']-cue['start']
            print(f'{cue["id"]}: {cue["speaker"]}, slot={slot:.2f}s',flush=True)
            if args.dry_run: continue
            if args.force or not out.exists():
                provider.generate_voice(cue['text'],cue['speaker'],out)
            actual=duration(out)
            if actual>slot+.02:
                print(f'REVIEW: {actual:.2f}s voice exceeds {slot:.2f}s slot. Re-time script before final assembly.',flush=True)

if __name__=='__main__': main()
