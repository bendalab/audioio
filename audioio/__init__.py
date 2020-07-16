"""
Platform independent interfacing of numpy arrays with audio files and devices.

See the documentation in the modules for an overview:

- `audioio.audioloader`: reading audio files
- `audioio.audiowriter`: writing audio files
- `audioio.playaudio`: play a sound through your audio board
- `audioio.audiomodules`: query installed modules

"""

from .version import __version__

__all__ = ['audiomodules',
           'audioloader',
           'audiowriter',
           'playaudio']

# make all important functions available in the audioio namespace:
from audioio.audiomodules import list_modules, available_modules, disable_module
from audioio.audiomodules import missing_modules, missing_modules_instructions
from audioio.audiomodules import installation_instruction
from audioio.audioloader import load_audio, unwrap, open_audio_loader, AudioLoader
from audioio.audiowriter import write_audio, available_formats, available_encodings
from audioio.playaudio import play, beep, open_audio_player, PlayAudio
from audioio.playaudio import note2freq, fade_in, fade_out, fade

