import _bootstrap
import argparse
from scamfilm.assembly import assemble_final_video

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Export approved production assets to output/final_video.mp4.')
    parser.add_argument('--force',action='store_true',help='Rebuild intermediate clips')
    args=parser.parse_args()
    print(assemble_final_video(force=args.force))
