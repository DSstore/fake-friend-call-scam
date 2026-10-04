"""Checks editorial guarantees, provider boundaries and real FFmpeg reversal."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from scamfilm.project import config, shots, validate
from scamfilm.subtitles import timestamp, escape_ass, wrap
from scamfilm.providers.fal import model_duration, queue_url
from scamfilm.rewind import reverse_clip, reverse_audio
from scamfilm.media import duration, run
from scamfilm.audio import tone, write_wave

class ManifestTests(unittest.TestCase):
    def test_plan_reconciles_and_is_frame_aligned(self):
        self.assertEqual(validate()['duration'],180)
        self.assertEqual(config()['ledger']['closing'],860)
        for s in shots():
            self.assertAlmostEqual(s['duration']*24,round(s['duration']*24))

    def test_wrong_ledger_is_rejected(self):
        c=config(); c['ledger']['transfers'][0]=4999
        with self.assertRaisesRegex(ValueError,'ledger'): validate(settings=c)

    def test_voice_cannot_overlap_signature_silence(self):
        ss=shots()
        freeze=next(s for s in ss if s['kind']=='freeze')
        freeze['cues'][0]['start']=1
        with self.assertRaisesRegex(ValueError,'silence'): validate(ss)

    def test_unplanned_reverse_source_is_rejected(self):
        ss=shots()
        next(s for s in ss if s['id']=='scene_04_shot_03')['reverse_compatible']=False
        with self.assertRaisesRegex(ValueError,'planned for reverse'): validate(ss)

    def test_replay_and_freeze_share_first_call(self):
        freeze=next(s for s in shots() if s['kind']=='freeze')
        replay=next(s for s in shots() if s['kind']=='reuse')
        self.assertEqual(freeze['source'],replay['source'])
        self.assertEqual(freeze['source'],'scene_01_shot_02')
        self.assertEqual(freeze['silence_intervals'],[[0,2]])

    def test_caption_rollover_and_override_neutralization(self):
        self.assertEqual(timestamp(59.9996),'00:01:00,000')
        self.assertNotIn('{',escape_ass(r'{\pos(1,2)}Untrusted caption'))
        for s in shots():
            for cue in s['cues']: self.assertLessEqual(len(wrap(cue['text']).splitlines()),2)
        self.assertEqual(len(wrap('请先停下来核实来电人的身份不要立即转账给陌生人').splitlines()),2)

    def test_fal_duration_and_credential_host_boundary(self):
        self.assertEqual(model_duration(6,config()),10)
        self.assertEqual(model_duration(4,config()),5)
        with self.assertRaises(ValueError): queue_url('https://example.com/status')
        with self.assertRaises(ValueError): queue_url('http://queue.fal.run/status')

class MediaTests(unittest.TestCase):
    def test_selected_reverse_first_frame_is_end_of_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'test.mkv'; out=Path(temp)/'reverse.mp4'
            run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=s=192x108:r=24',
                 '-t','2','-c:v','ffv1','-threads','1',source])
            reverse_clip(source,out,.5,1.5,1,True)
            self.assertAlmostEqual(duration(out),1,places=2)
            def frame(path,index):
                return subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vf',
                    f'trim=start_frame={index}:end_frame={index+1},format=rgb24',
                    '-frames:v','1','-threads','1','-f','rawvideo','-'],check=True,capture_output=True).stdout
            actual=frame(out,0); expected=frame(source,35)
            self.assertEqual(len(actual),len(expected))
            mae=sum(abs(a-b) for a,b in zip(actual,expected))/len(actual)
            self.assertLess(mae,5,'First reversed frame must come from selected source end, not whole movie end.')

    def test_reverse_effect_speed_and_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'tone.wav'; out=Path(temp)/'reverse.wav'
            write_wave(source,tone(.4,220,.2,100))
            reverse_audio(source,out,0,.4,.2)
            self.assertAlmostEqual(duration(out),.2,places=2)

if __name__=='__main__': unittest.main()
