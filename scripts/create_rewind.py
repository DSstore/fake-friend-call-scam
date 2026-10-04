"""Create only the signature rewind scene and its isolated reversed effects."""
import _bootstrap
import argparse
from scamfilm.assembly import assemble_scene
from scamfilm.audio import generate_effects
from scamfilm.project import ROOT, shots, validate
from scamfilm.rewind import reverse_audio

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    validate()
    effects=generate_effects()
    for shot in shots():
        if shot['kind']=='reverse':
            reverse_audio(effects/'reverse_seed.wav',ROOT/'output/cache/audio'/(shot['id']+'_reverse_fx.wav'),0,6,shot['duration'])
    print('Visual scene intermediate (audio is mixed at final assembly):',assemble_scene(9,args.preview,args.force))
