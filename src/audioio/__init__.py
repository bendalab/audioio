"""
Platform independent interfacing of numpy arrays of floats with audio
files and devices for scientific data analysis.
"""

import sys

# avoid double inclusion of audioio modules if called as modules,
# e.g. python -m src.audioio.audiowriter`:
if len(sys.argv) > 0 and sys.argv[0] != '-m':
    
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
    from .bufferedarray import blocks, BufferedArray
    from .audioloader import load_audio, AudioLoader
    from .audioloader import metadata, markers
    from .audiotools import despike, unwrap
    from .audiometadata import flatten_metadata, unflatten_metadata
    from .audiometadata import write_metadata_text, print_metadata
    from .audiometadata import find_key, add_sections
    from .audiometadata import set_metadata, add_metadata, move_metadata
    from .audiometadata import remove_metadata, cleanup_metadata
    from .audiometadata import parse_number, change_unit, get_number
    from .audiometadata import get_number_unit, get_int, get_bool
    from .audiometadata import get_datetime, update_starttime, get_str
    from .audiometadata import get_gain, update_gain, add_unwrap
    from .audiometadata import bext_history_str, add_history
    from .audiometadata import default_starttime_keys, default_timeref_keys
    from .audiometadata import default_gain_keys, default_history_keys
    from .audiomarkers import write_markers, print_markers
    from .audiowriter import write_audio, available_formats, available_encodings
    from .playaudio import play, beep, PlayAudio
    from .playaudio import note2freq, fade_in, fade_out, fade
