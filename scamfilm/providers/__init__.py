from .openai import OpenAIImage, OpenAIVoice
from .fal import FalVideo

def image_provider(name):
    if name=='openai': return OpenAIImage()
    raise ValueError('Choose --provider openai, or import approved PNGs manually.')

def video_provider(name):
    if name=='fal': return FalVideo()
    raise ValueError('Choose --provider fal, or import approved MP4s manually.')

def voice_provider(name):
    if name=='openai': return OpenAIVoice()
    raise ValueError('Choose --provider openai, or import approved cue WAVs manually.')
