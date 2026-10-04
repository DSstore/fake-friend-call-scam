"""OpenAI image-reference editing and cue-based speech adapters."""
import base64
import json
import os
from pathlib import Path
from .http import request, json_request, multipart, download
from ..project import require_key, config, characters

BASE='https://api.openai.com/v1'

class OpenAIImage:
    def generate_image(self,prompt,output,references=()):
        key=require_key('IMAGE_API_KEY')
        payload={'model':os.getenv('IMAGE_MODEL',config()['image_model']),
                 'prompt':prompt,'size':'1536x1024','quality':'medium','n':1}
        headers={'Authorization':'Bearer '+key}
        if references:
            data,content_type=multipart(payload,[('image[]',p) for p in references])
            result=json.loads(request(BASE+'/images/edits',data,{**headers,'Content-Type':content_type}))
        else:
            result=json_request(BASE+'/images/generations',payload,headers)
        output=Path(output)
        output.parent.mkdir(parents=True,exist_ok=True)
        item=result['data'][0]
        if 'b64_json' in item:
            output.write_bytes(base64.b64decode(item['b64_json']))
        else:
            download(item['url'],output)
        return output

class OpenAIVoice:
    def generate_voice(self,text,speaker,output):
        key=require_key('VOICE_API_KEY')
        voice=characters()[speaker]['voice']
        payload={'model':os.getenv('VOICE_MODEL',config()['voice_model']),
                 'voice':os.getenv('VOICE_'+speaker.upper(),voice['provider_voice']),
                 'input':text,'instructions':voice['instructions']+' Clear unhurried delivery. No added words.',
                 'response_format':'wav'}
        output=Path(output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(request(BASE+'/audio/speech',json.dumps(payload).encode(),
            {'Authorization':'Bearer '+key,'Content-Type':'application/json'}))
        return output
