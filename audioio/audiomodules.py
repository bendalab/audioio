"""
`list_modules()` and `available_modules()` let you query which audio modules
are installed and available.

`disable_module()` disables specific audio modules.

For further information and installing instructions of missing modules,
see the documentation of the respective `load_*()` functions of the `audioloader` module.

For an overview on available python modules see
http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/audio-files/index.ipynb
"""

# probe for available audio modules:
audio_modules = {}

try:
    import wave
    audio_modules['wave'] = True
except ImportError:
    audio_modules['wave'] = False

try:
    import ewave
    audio_modules['ewave'] = True
except ImportError:
    audio_modules['ewave'] = False

try:
    from scipy.io import wavfile
    audio_modules['scipy.io.wavfile'] = True
except ImportError:
    audio_modules['scipy.io.wavfile'] = False

try:
    import soundfile
    audio_modules['soundfile'] = True
except ImportError:
    audio_modules['soundfile'] = False

try:
    import wavefile
    audio_modules['wavefile'] = True
except ImportError:
    audio_modules['wavefile'] = False

try:
    import scikits.audiolab as audiolab
    audio_modules['scikits.audiolab'] = True
except ImportError:
    audio_modules['scikits.audiolab'] = False
        
try:
    import audioread
    audio_modules['audioread'] = True
except ImportError:
    audio_modules['audioread'] = False
        
try:
    import pyaudio
    audio_modules['pyaudio'] = True
except ImportError:
    audio_modules['pyaudio'] = False
        
try:
    import ossaudiodev
    audio_modules['ossaudiodev'] = True
except ImportError:
    audio_modules['ossaudiodev'] = False
        
try:
    import winsound
    audio_modules['winsound'] = True
except ImportError:
    audio_modules['winsound'] = False
    

def available_modules():
    """
    Returns
    -------
    mods: list of strings
        List of installed audio modules.
    """
    mods = []
    for module, available in audio_modules.items():
        if available:
            mods.append(module)
    return mods


def disable_module(module):
    """
    Disable an audio module so that it is not used by the audioio functions and classes.
    
    Parameters
    ----------
    module: string
        Name of the module to be disabled as it appears in available_modules()
    """
    if module in audio_modules:
        audio_modules[module] = False


def list_modules(module=None):
    """Print list of all supported modules and whether they are available.

    Parameters
    ----------
    module: None or string
        If None list all modules.
        If string list only the specified module.
    """
    def print_module(module, available):
        if available:
            print('%-16s is     installed' % module)
        else:
            print('%-16s is not installed' % module)

    if module is not None:
        print_module(module, audio_modules[module])
    else:
        for module, available in audio_modules.items():
            print_module(module, available)


if __name__ == "__main__":
    print("Checking audiomodules module ...")
    print('')
    list_modules()
    print('')
    print('available modules:')
    print('  %s' % '\n  '.join(available_modules()))
    print('')
    module = 'wave'
    print('disable %s module:' % module)
    list_modules(module)
    disable_module(module)
    list_modules(module)
