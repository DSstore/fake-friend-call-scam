import _bootstrap
import argparse
from scamfilm.subtitles import create_subtitles

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Generate SRT, ASS and translation cue catalog.')
    parser.add_argument('--translation',help='JSON with translations keyed by stable cue ID')
    parser.add_argument('--language',default='en')
    args=parser.parse_args()
    print(create_subtitles(args.translation,args.language))
