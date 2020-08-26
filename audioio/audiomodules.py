"""
Query available audio modules.

`list_modules()`, `available_modules()` and `unavailable_modules()`
let you query which audio modules are installed and available
and which modules are not availbale on your system.

Call `missing_modules()` for a list of module names that should be
installed.  The `missing_modules_instructions()` functions prints
installation instructions for packages you should install for better
performance.  For installing instructions on a specific module call
'installation_instruction(module_name)'

`disable_module()` disables specific audio modules,
`enable_module()` re-enables a module, provided it is installed.

For an overview on available python modules regarding file I/O see, for example,
http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/audio-files/index.ipynb

For an overview on packages for palying and recording audio, see
https://realpython.com/playing-and-recording-sound-python/

Run this module as a script
```
> python -m audioio.auidomodules
```
or, when the audioio package is installed on your system, simply
```
audiomodules
```
for an overview of audio packages, their installation status, and recommendations on
how to install further audio packages. The output looks like this:
```plain
tatus of audio packages on this machine:
-----------------------------------------

wave              is  installed (F)
ewave             is  installed (F)
scipy.io.wavfile  is  installed (F)
soundfile         is  installed (F)
wavefile          is  installed (F)
scikits.audiolab  not installed (F)
audioread         NOT installed (F)
pyaudio           is  installed (D)
sounddevice       not installed (D)
simpleaudio       is  installed (D)
ossaudiodev       is  installed (D)
winsound          not installed (D)

F: file I/O, D: audio device

There is no need to install additional audio packages.
```

For instructions on specific packages run `audiomodules` with the name of
the package supplied as argument:
```
audiomodules soundfile
```
This produces something like this:
```plain
...
Installation instructions for the soundfile module:
---------------------------------------------------
The soundfile package is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

sudo apt-get install -y libsndfile1 libsndfile1-dev libffi-dev
sudo pip install SoundFile

See http://pysoundfile.readthedocs.org for a documentation of the soundfile package
and http://www.mega-nerd.com/libsndfile for details on the sndfile library.
```
"""

from sys import platform, argv, exit
from os.path import exists
from .version import __version__, __year__


""" Dictionary with availability of various audio modules.
Keys are the module names, values are booleans.
Based on this dictionary audioio employs functions of installed audio modules. """
audio_modules = {}

""" List of installed audio modules. """
audio_installed = []

""" Dictionary with installation instructions of all supported audio modules.
Keys are the module names, values are the instructions. """
audio_instructions = {}

""" List of audio modules used for reading and writing audio files. """
audio_fileio = []
""" List of audio modules used for playing and recording sounds on audio devices. """
audio_device = []


# probe for available audio modules:

audio_fileio.append('wave')
try:
    import wave
    audio_modules['wave'] = True
    audio_installed.append('wave')
except ImportError:
    audio_modules['wave'] = False
audio_instructions['wave'] = """The wave module is part of the standard python library 
and there should be no need to install it manually.

See https://docs.python.org/2/library/wave.html for documentation of the wave module."""

audio_fileio.append('ewave')
try:
    import ewave
    audio_modules['ewave'] = True
    audio_installed.append('ewave')
except ImportError:
    audio_modules['ewave'] = False
audio_instructions['ewave'] = """The ewave package supports more types of WAV-files than the standard wave module.

Get the ewave package from github:

git clone https://github.com/melizalab/py-ewave
cd py-ewave
BUILDSETUP
INSTALLSETUP

See https://github.com/melizalab/py-ewave for documentation of the ewave package."""

audio_fileio.append('scipy.io.wavfile')
try:
    from scipy.io import wavfile
    audio_modules['scipy.io.wavfile'] = True
    audio_installed.append('scipy.io.wavfile')
except ImportError:
    audio_modules['scipy.io.wavfile'] = False
audio_instructions['scipy.io.wavfile'] = """The scipy package provides very basic functions for reading WAV files.

Install scipy using

INSTALLPACKAGE python3-scipy

See http://docs.scipy.org/doc/scipy/reference/io.html for a documentation."""

audio_fileio.append('soundfile')
try:
    import soundfile
    audio_modules['soundfile'] = True
    audio_installed.append('soundfile')
except ImportError:
    audio_modules['soundfile'] = False
audio_instructions['soundfile'] = """The soundfile package is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

INSTALLPACKAGE libsndfile1 libsndfile1-dev libffi-dev
INSTALLPIP SoundFile

See http://pysoundfile.readthedocs.org for a documentation of the soundfile package
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""

audio_fileio.append('wavefile')
try:
    import wavefile
    audio_modules['wavefile'] = True
    audio_installed.append('wavefile')
except ImportError:
    audio_modules['wavefile'] = False
audio_instructions['wavefile'] = """The wavefile package is a wrapper of the sndfile library, which
supports many different audio file formats.

Install the library and the wrapper using

INSTALLPACKAGE libsndfile1 libsndfile1-dev libffi-dev
INSTALLPIP wavefile

See https://github.com/vokimon/python-wavefile for documentation of the wavefile package
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""

audio_fileio.append('scikits.audiolab')
try:
    import scikits.audiolab as audiolab
    audio_modules['scikits.audiolab'] = True
    audio_installed.append('scikits.audiolab')
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
        
audio_fileio.append('audioread')
try:
    import audioread
    audio_modules['audioread'] = True
    audio_installed.append('audioread')
except ImportError:
    audio_modules['audioread'] = False
audio_instructions['audioread'] = """The audioread package uses ffmpeg and friends to make mp3 files readable.

Install the package using

INSTALLPACKAGE libav-tools python3-audioread

See https://github.com/sampsyo/audioread for documentation of the audioread package."""
        
audio_device.append('pyaudio')
try:
    import pyaudio
    audio_modules['pyaudio'] = True
    audio_installed.append('pyaudio')
except ImportError:
    audio_modules['pyaudio'] = False
audio_instructions['pyaudio'] = """The pyaudio package is a wrapper of the portaudio library.

Install the package using

INSTALLPACKAGE libportaudio2 portaudio19-dev python3-pyaudio

On Windows, download an appropriate (latest version, 32 or 64 bit) wheel from
<https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio>.  Install this file with pip,
that is go to the folder where the wheel file is downloaded and run

INSTALLPIP PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl

replace the wheel file name by the one you downloaded.

See https://people.csail.mit.edu/hubert/pyaudio/ for documentation of the pyaudio package."""
        
audio_device.append('sounddevice')
try:
    import sounddevice
    audio_modules['sounddevice'] = True
    audio_installed.append('sounddevice')
except ImportError:
    audio_modules['sounddevice'] = False
audio_instructions['sounddevice'] = """The sounddevice package is a wrapper of the portaudio library. 
If you have trouble with pyaudio, try this as an alternative.
Install the package using

INSTALLPACKAGE libportaudio2 portaudio19-dev python3-cffi
INSTALLPIP sounddevice

See https://python-sounddevice.readthedocs.io for
documentation of the sounddevice package."""
        
audio_device.append('simpleaudio')
try:
    import simpleaudio
    audio_modules['simpleaudio'] = True
    audio_installed.append('simpleaudio')
except ImportError:
    audio_modules['simpleaudio'] = False
audio_instructions['simpleaudio'] = """The simpleaudio package is a lightweight package
for cross-platform audio playback.

Install the package via

INSTALLPIP simpleaudio

On Linux also install

INSTALLPACKAGE python3-dev libasound2-dev

See https://simpleaudio.readthedocs.io
for documentation of the simpleaudio package."""
        
audio_device.append('ossaudiodev')
try:
    import ossaudiodev
    audio_modules['ossaudiodev'] = True
    audio_installed.append('ossaudiodev')
except ImportError:
    audio_modules['ossaudiodev'] = False
audio_instructions['ossaudiodev'] = """The OSS audio module is part of the python standard library and
provides simple support for sound playback under Linux. If possible,
install the soundfile package in addition for better performance.

You need, however, to enable the /dev/dsp device for OSS support by installing

INSTALLPACKAGE osspd

See https://docs.python.org/2/library/ossaudiodev.html for
documentation of the OSS audio module."""
        
audio_device.append('winsound')
try:
    import winsound
    audio_modules['winsound'] = True
    audio_installed.append('winsound')
except ImportError:
    audio_modules['winsound'] = False
audio_instructions['winsound'] = """The winsound module is part of the python standard library and
provides simple support for sound playback under Windows. If possible,
install the sounddevice package in addition for better performance.

See https://docs.python.org/3.6/library/winsound.html and
https://mail.python.org/pipermail/tutor/2012-September/091529.html
for documentation of the winsound module."""
    

def available_modules():
    """
    Returns list of installed audio modules.
    
    Returns
    -------
    mods: list of strings
        Sorted list of installed audio modules.
    """
    mods = []
    for module, available in audio_modules.items():
        if available:
            mods.append(module)
    return sorted(mods)


def unavailable_modules():
    """
    Returns list of audio modules that are not installed on your system.
    
    Returns
    -------
    mods: list of strings
        Sorted list of not installed audio modules.
    """
    mods = []
    for module, available in audio_modules.items():
        if not available:
            mods.append(module)
    return sorted(mods)


def disable_module(module):
    """
    Disable an audio module so that it is not used by the audioio functions and classes.

    This can ony be used right after importing audioio before any
    audioio functions are called.
    
    Parameters
    ----------
    module: string
        Name of the module to be disabled as it appears in available_modules()

    See also
    --------
    enable_module(), list_modules()
    """
    if module in audio_modules:
        audio_modules[module] = False


def enable_module(module):
    """
    Enable an audio module if it is installed.
    
    Parameters
    ----------
    module: string
        Name of the module to be (re)enabled.

    See also
    --------
    disable_module(), list_modules()
    """
    if module in audio_modules:
        audio_modules[module] = (module in audio_installed)


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
    def print_module(module, missing):
        audio_type = ''
        if module in audio_fileio:
            audio_type += 'F'
        if module in audio_device:
            audio_type += 'D'
        if len(audio_type) > 0:
            audio_type = ' (%s)' % audio_type
        if audio_modules[module]:
            print('%-17s is  installed%s' % (module, audio_type))
        elif module in missing:
            print('%-17s NOT installed%s' % (module, audio_type))
        else:
            print('%-17s not installed%s' % (module, audio_type))

    missing = missing_modules()
    if module is not None:
        print_module(module, missing)
    else:
        modules = sorted(audio_modules.keys())
        for module in audio_fileio:
            print_module(module, missing)
            modules.remove(module)
        for module in audio_device:
            print_module(module, missing)
            modules.remove(module)
        for module in modules:
            print_module(module, missing)


def missing_modules():
    """
    Returns list of missing audio modules that are recommended to be installed.
    
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
        mods.append('sounddevice')
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
        print('There is no need to install additional audio packages.')


def installation_instruction(module):
    """ Instructions on how to install a specific audio module.
    
    Returns
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


def main():
    if len(argv) > 1 :
        if argv[1] == '--version':
            print('version', __version__, 'by Benda-Lab (2015-%s)' % __year__)
            exit(0)
        if argv[1] == '--help':
            print('usage: audiomodules [--version] [--help] [PACKAGE]')
            print('')
            print('Installation status and instructions of python audio packages.')
            print('')
            print('optional arguments:')
            print('  --help      show this help message and exit')
            print('  --version   show version number and exit')
            print('  PACKAGE     show installation instructions for PACKAGE')
            print('')
            print('version', __version__, 'by Benda-Lab (2015-%s)' % __year__)
            exit(0)
    print('')
    print('Status of audio packages on this machine:')
    print('-'*41)
    print('')
    list_modules()
    print('')
    print('F: file I/O, D: audio device')
    print('')
    missing_modules_instructions()
    print('')

    if len(argv) > 1 :
        mod = argv[1]
        if mod in audio_modules:
            print('Installation instructions for the %s module:' % mod )
            print('-'*(42+len(mod)))
            print(installation_instruction(mod))
            print('')


if __name__ == "__main__":
    main()
