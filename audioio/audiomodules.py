"""
Query available audio modules.

`list_modules()`, `available_modules()` and `unavailable_modules()`
let you query which audio modules are installed and available
and which modules are not availbale on your system.

Call `missing_modules()` for a list of module names that should be installed.
The `missing_modules_instructions()` functions prints installation instructions
for packages you should install for better performance on standard output.
For installing instructions on a specific module call
'installation_instruction(module_name)'

`disable_module()` disables specific audio modules.

For an overview on available python modules regarding file I/O see
http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/audio-files/index.ipynb
"""

from sys import platform
from os.path import exists

# probe for available audio modules:

audio_modules = {}
audio_instructions = {}

try:
    import wave
    audio_modules['wave'] = True
except ImportError:
    audio_modules['wave'] = False
audio_instructions['wave'] = """The wave module is part of the standard python library 
and there should be no need to install it manually.

See https://docs.python.org/2/library/wave.html for documentation of the wave module."""

try:
    import ewave
    audio_modules['ewave'] = True
except ImportError:
    audio_modules['ewave'] = False
audio_instructions['ewave'] = """The ewave package supports more types of WAV-files than the standard wave module.

Get the ewave package from github:

git clone https://github.com/melizalab/py-ewave
cd py-ewave
BUILDSETUP
INSTALLSETUP

See https://github.com/melizalab/py-ewave for documentation of the ewave package."""

try:
    from scipy.io import wavfile
    audio_modules['scipy.io.wavfile'] = True
except ImportError:
    audio_modules['scipy.io.wavfile'] = False
audio_instructions['scipy.io.wavfile'] = """The scipy package provides very basic functions for reading WAV files.

Install scipy using

INSTALLPACKAGE python-scipy

See http://docs.scipy.org/doc/scipy/reference/io.html for a documentation."""

try:
    import soundfile
    audio_modules['soundfile'] = True
except ImportError:
    audio_modules['soundfile'] = False
audio_instructions['soundfile'] = """The pysoundfile package is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

INSTALLPACKAGE libsndfile1 libsndfile1-dev libffi-dev
INSTALLPIP pysoundfile

See http://pysoundfile.readthedocs.org for a documentation of the pysoundfile package
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""

try:
    import wavefile
    audio_modules['wavefile'] = True
except ImportError:
    audio_modules['wavefile'] = False
audio_instructions['wavefile'] = """The wavefile package is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

INSTALLPACKAGE libsndfile1 libsndfile1-dev libffi-dev
INSTALLPIP wavefile

See https://github.com/vokimon/python-wavefile for documentation of the wavefile package
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""

try:
    import scikits.audiolab as audiolab
    audio_modules['scikits.audiolab'] = True
except ImportError:
    audio_modules['scikits.audiolab'] = False
audio_instructions['scikits.audiolab'] = """The scikits.audiolab module is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

INSTALLPACKAGE libsndfile1 libsndfile1-dev libffi-dev
INSTALLPIP scikits.audiolab

See http://cournape.github.io/audiolab/ and
https://github.com/cournape/audiolab for documentation of the audiolab module
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""
        
try:
    import audioread
    audio_modules['audioread'] = True
except ImportError:
    audio_modules['audioread'] = False
audio_instructions['audioread'] = """The audioread package uses ffmpeg and friends to make mp3 files readable.

Install the package using

INSTALLPACKAGE libav-tools python-audioread

See https://github.com/sampsyo/audioread for documentation of the audioread package."""
        
try:
    import pyaudio
    audio_modules['pyaudio'] = True
except ImportError:
    audio_modules['pyaudio'] = False
audio_instructions['pyaudio'] = """The pyaudio package is a wrapper of the portaudio library.

Install the package using

INSTALLPACKAGE libportaudio2 portaudio19-dev python-pyaudio python3-pyaudio

See https://people.csail.mit.edu/hubert/pyaudio/ for documentation of the pyaudio package."""
        
try:
    import sounddevice
    audio_modules['sounddevice'] = True
except ImportError:
    audio_modules['sounddevice'] = False
audio_instructions['sounddevice'] = """The sounddevice package is a wrapper of the portaudio library. 
If you have trouble with pyaudio, try this as an alternative.
Install the package using

INSTALLPACKAGE libportaudio2 portaudio19-dev python-cffi python3-cffi
INSTALLPIP sounddevice

See https://python-sounddevice.readthedocs.io for
documentation of the sounddevice package."""
        
try:
    import ossaudiodev
    audio_modules['ossaudiodev'] = True
except ImportError:
    audio_modules['ossaudiodev'] = False
audio_instructions['ossaudiodev'] = """The OSS audio module is part of the python standard library and
provides simple support for sound playback under Linux. If possible,
install the pyaudio package instead for better performance.

You need, however, to enable the /dev/dsp device for OSS support by installing

INSTALLPACKAGE osspd

See https://docs.python.org/2/library/ossaudiodev.html for
documentation of the OSS audio module."""
        
try:
    import winsound
    audio_modules['winsound'] = True
except ImportError:
    audio_modules['winsound'] = False
audio_instructions['winsound'] = """The winsound module is part of the python standard library and
provides simple support for sound playback under Windows. If possible,
install the pyaudio package instead for better performance.

See https://docs.python.org/2/library/winsound.html and
https://mail.python.org/pipermail/tutor/2012-September/091529.html
for documentation of the winsound module."""
    

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


def unavailable_modules():
    """
    Returns
    -------
    mods: list of strings
        List of not installed audio modules.
    """
    mods = []
    for module, available in audio_modules.items():
        if not available:
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
    Modules that are not available but are recommended are marked
    with an all uppercase "NOT installed".

    Parameters
    ----------
    module: None or string
        If None list all modules.
        If string list only the specified module.

    See also
    --------
    missing_modules() and missing_modules_instructions()
    """
    def print_module(module, available, missing):
        if available:
            print('%-17s is  installed' % module)
        elif module in missing:
            print('%-17s NOT installed' % module)
        else:
            print('%-17s not installed' % module)

    missing = missing_modules()
    if module is not None:
        print_module(module, audio_modules[module], missing)
    else:
        for module, available in audio_modules.items():
            print_module(module, available, missing)


def missing_modules():
    """
    Returns
    -------
    mods: list of strings
        List of missing but usefull audio modules.
    """
    mods = []
    # audio file I/O:
    if not audio_modules['soundfile'] and not audio_modules['wavefile'] and not audio_modules['scikits.audiolab'] :
        mods.append('soundfile')
    if not audio_modules['audioread'] :
        mods.append('audioread')
    # audio device I/O:
    if not audio_modules['pyaudio'] and not audio_modules['sounddevice'] :
        mods.append('pyaudio')
    return mods


def missing_modules_instructions():
    """Print installation instructions for missing but useful audio modules.
    """
    mods = missing_modules()
    if len(mods) > 0 :
        print('For better performance you should install the following modules:')
        for mod in mods:
            print('')
            print('%s:' % mod)
            print('-'*(len(mod)+1))
            print(installation_instruction(mod))
    else:
        print('There is no need to install more audio packages.')


def installation_instruction(module):
    """
    Return:
    -------
    msg: multi-line string
        Installation instruction for the requested module.

    Parameters
    ----------
    module: string
        The name of the module for which an instruction should be printed.
    """
    install_package_deb = "sudo apt-get install -y"
    install_package_rpm = "dnf install"
    install_package_osx = "brew install"
    install_package_win = "conda install"
    install_package = install_package_deb

    install_pip_deb = "sudo pip install"
    install_pip_rpm = "pip install"
    install_pip_osx = "pip install"
    install_pip_win = "pip install"
    install_pip = install_pip_deb

    build_setup = "python setup.py build"
    install_setup_deb = "sudo python setup.py install"
    install_setup_rpm = "python setup.py install"
    install_setup_brew = "python setup.py install"
    install_setup_win = "python setup.py install"
    install_setup = install_setup_deb

    # check operating system:
    if platform[0:5] == "linux":
        if exists('/etc/redhat-release') or exists('/etc/fedora-release'):
            install_package = install_package_rpm
            install_pip = install_pip_rpm
            install_setup = install_setup_rpm
    elif platform == "darwin":
        install_package = install_package_brew
        install_pip = install_pip_brew
        install_setup = install_setup_brew
    elif platform[0:3] == "win":
        install_package = install_package_win
        install_pip = install_pip_win
        install_setup = install_setup_win

    msg = audio_instructions[module]
    msg = msg.replace('INSTALLPACKAGE', install_package)
    msg = msg.replace('INSTALLPIP', install_pip)
    msg = msg.replace('BUILDSETUP', build_setup)
    msg = msg.replace('INSTALLSETUP', install_setup)
    return msg


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
    print('')
    print('')
    missing_modules_instructions()
