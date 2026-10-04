import _bootstrap
import argparse
from scamfilm.assembly import assemble_final_video

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Offline watermarked storyboard animatic with guide tones, not generated film.')
    parser.add_argument('--force',action='store_true',help='Rebuild intermediate clips')
    args=parser.parse_args()
    print(assemble_final_video(preview=True,force=args.force))
