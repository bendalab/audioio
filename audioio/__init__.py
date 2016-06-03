"""
Platform independent interfacing of numpy arrays with audio files and devices.
"""

__all__ = ['audiomodules', 'audioloader', 'playaudio']

# make all important functions available in the audioio namespace:
from audioio.audiomodules import list_modules, available_modules
from audioio.audioloader import load_audio, open_audio_loader, AudioLoader
from audioio.playaudio import play, beep, open_audio_player, PlayAudio

