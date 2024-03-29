"""
Platform independent interfacing of numpy arrays with audio files and devices.
"""

import sys

# avoid double inclusion of audioio modules if called as modules,
# e.g. python -m audioio.audiowriter`:
if not '-m' in sys.argv:
    
    from .version import __version__
    
    __all__ = ['audiomodules',
               'audioloader',
               'audiotools',
               'riffmetadata',
               'audiometadata',
               'audiomarkers',
               'audiowriter',
               'playaudio']
    
    # make all important functions available in the audioio namespace:
    from .audiomodules import list_modules, installed_modules
    from .audiomodules import available_modules, unavailable_modules
    from .audiomodules import disable_module, enable_module, select_module
    from .audiomodules import missing_modules, missing_modules_instructions
    from .audiomodules import installation_instruction
    from .audioloader import load_audio, AudioLoader, blocks
    from .audioloader import metadata, markers
    from .audiotools import despike, unwrap
    from .audiometadata import flatten_metadata, unflatten_metadata
    from .audiometadata import write_metadata_text, print_metadata
    from .audiometadata import find_key, add_sections, add_metadata
    from .audiometadata import remove_metadata, cleanup_metadata
    from .audiometadata import parse_number, change_unit, get_number
    from .audiometadata import get_number_unit, get_int, get_bool, get_str
    from .audiometadata import get_gain, update_gain, add_unwrap
    from .audiomarkers import write_markers, print_markers
    from .audiowriter import write_audio, available_formats, available_encodings
    from .playaudio import play, beep, PlayAudio
    from .playaudio import note2freq, fade_in, fade_out, fade
