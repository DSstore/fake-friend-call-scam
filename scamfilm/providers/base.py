"""Swap providers without changing the editor or shot data."""
from typing import Protocol
from pathlib import Path

class ImageProvider(Protocol):
    def generate_image(self, prompt: str, output: Path, references=()): ...

class VideoProvider(Protocol):
    def generate_video(self, image: Path, prompt: str, output: Path, duration: float): ...

class VoiceProvider(Protocol):
    def generate_voice(self, text: str, speaker: str, output: Path): ...
