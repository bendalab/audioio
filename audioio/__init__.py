"""
Platform independent interfacing of numpy arrays with audio files and devices.
"""

from .version import __version__

__all__ = ['audiomodules',
           'audioloader',
           'playaudio']

# make all important functions available in the audioio namespace:
from audioio.audiomodules import list_modules, available_modules, disable_module
from audioio.audioloader import load_audio, open_audio_loader, AudioLoader
from audioio.audiowriter import write_audio
from audioio.playaudio import play, beep, open_audio_player, PlayAudio
from audioio.playaudio import note2freq, fade_in, fade_out, fade

