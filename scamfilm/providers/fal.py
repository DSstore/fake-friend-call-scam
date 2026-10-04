"""Configurable fal queue adapter; persist submissions before polling."""
import base64
import json
import math
import os
import time
from urllib.parse import urlparse
from pathlib import Path
from .http import json_request, download
from ..project import require_key, config

def queue_url(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname!='queue.fal.run':
        raise ValueError('Refusing to send a fal credential outside queue.fal.run.')
    return url

def model_duration(seconds,settings):
    supported=settings.get('video_supported_durations',[5,10])
    choices=[d for d in supported if d >= seconds]
    if not choices:
        raise ValueError('Selected video model cannot generate the required duration.')
    return min(choices)

class FalVideo:
    def generate_video(self,image,prompt,output,duration):
        key=require_key('VIDEO_API_KEY')
        settings=config()
        model=os.getenv('VIDEO_MODEL',settings['video_model'])
        if not model or '..' in model or '?' in model or not model.startswith('fal-ai/'):
            raise ValueError('Set VIDEO_MODEL to a fal-ai/... image-to-video model ID from its current API schema.')
        output=Path(output)
        output.parent.mkdir(parents=True,exist_ok=True)
        job=output.parent/'jobs'/(output.stem+'.json')
        headers={'Authorization':'Key '+key}
        if job.exists():
            state=json.loads(job.read_text())
            if state['model'] != model:
                raise ValueError('Existing fal job uses another model. Review/delete that job file before resubmitting.')
        else:
            seconds=model_duration(duration,settings)
            image=Path(image)
            payload={**settings['video_payload'],
                     settings['video_prompt_field']:prompt,
                     settings['video_image_field']:'data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode(),
                     settings['video_duration_field']:str(seconds) if settings['video_duration_format']=='string' else seconds}
            state=json_request('https://queue.fal.run/'+model,payload,headers)
            state['model']=model
            job.parent.mkdir(parents=True,exist_ok=True)
            job.write_text(json.dumps(state,indent=2))
            print(f'Saved fal job for {output.stem}; rerun to resume if interrupted.',flush=True)
        deadline=time.monotonic()+int(os.getenv('VIDEO_TIMEOUT_SECONDS','1800'))
        while time.monotonic()<deadline:
            status=json_request(queue_url(state['status_url']),headers=headers)
            if status['status']=='COMPLETED':
                result=json_request(queue_url(state['response_url']),headers=headers)
                url=(result.get('video') or {}).get('url')
                if not url:
                    raise ValueError('Expected result.video.url; selected model response schema differs. Adapt FalVideo extraction.')
                download(url,output)
                return output
            if status['status'] in ('FAILED','CANCELLED'):
                raise RuntimeError('Video job failed; inspect it in the fal dashboard before creating a replacement.')
            print(f'{output.stem}: {status["status"]}',flush=True)
            time.sleep(5)
        raise TimeoutError('Video job is still pending. Its ID is saved; rerun to resume without paying for a new submission.')
