"""Query and control installation status and availability of audio modules.

`list_modules()` and `installed_modules()` let you query which audio
modules are currently installed on your system.

Call `missing_modules()` for a list of module names that should be
installed.  The `missing_modules_instructions()` function prints
installation instructions for packages you should install for better
performance.  For installation instructions on a specific module use
`installation_instruction()`.

By default all installed modules are used by the audioio functions.
The `disable_module()`, `enable_module()` and `select_module()`
functions allow to control which of the installed audio modules
should be used by the audioio functions.

`list_modules()`, `available_modules()` and `unavailable_modules()` let
you query which audio modules are installed and available and which
modules are not available on your system.


## Functions

- `installed_modules()`: installed audio modules.
- `available_modules()`: installed and enabled audio modules.
- `unavailable_modules()`: audio modules that are not installed and not enabled.
- `disable_module()`: disable audio module.
- `enable_module()`: enable audio modules provided they are installed.
- `select_module()`: select (enable) a single audio module and disable all others.
- `list_modules()`: print list of all supported modules and their installation status.
- `missing_modules()`: missing audio modules that are recommended to be installed.
- `missing_modules_instructions()`: print installation instructions for missing but useful audio modules.
- `installation_instruction()`: instructions on how to install a specific audio module.
- `main()`: command line program for listing installation status of audio modules.


## Command line script

Run this module as a script
```sh
> python -m src.audioio.auidomodules
```
or, when the audioio package is installed on your system, simply run
```sh
> audiomodules
```
for an overview of audio packages, their installation status, and recommendations on
how to install further audio packages. The output looks like this:

```text
Status of audio packages on this machine:
-----------------------------------------

wave              is  installed (F)
ewave             is  installed (F)
scipy.io.wavfile  is  installed (F)
soundfile         is  installed (F)
wavefile          is  installed (F)
audioread         is  installed (F)
pyaudio           is  installed (D)
sounddevice       not installed (D)
simpleaudio       is  installed (D)
soundcard         is  installed (D)
ossaudiodev       is  installed (D)
winsound          not installed (D)

F: file I/O, D: audio device

There is no need to install additional audio packages.
```

For instructions on specific packages, run `audiomodules` with the name of
the package supplied as argument:

```sh
> audiomodules soundfile
```
This produces something like this:
```text
...
Installation instructions for the soundfile module:
---------------------------------------------------
The soundfile package is a wrapper of the sndfile library,
that supports many different audio file formats.
See http://python-soundfile.readthedocs.org for a documentation of the soundfile python wrapper
and http://www.mega-nerd.com/libsndfile for details on the sndfile library.

First, install the following packages:

sudo apt install libsndfile1 libsndfile1-dev libffi-dev

Install the soundfile module with pip:

sudo pip install SoundFile

or alternatively from your distribution's package:

sudo apt install python3-soundfile
```

Running
```sh
audioconverter --help
```
prints
```text
usage: audiomodules [--version] [--help] [PACKAGE]

Installation status and instructions of python audio packages.

optional arguments:
  --help      show this help message and exit
  --version   show version number and exit
  PACKAGE     show installation instructions for PACKAGE

version 2.0.0 by Benda-Lab (2015-2024)
```

## Links

For an overview on python modules regarding file I/O see, for example,
http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/audio-files/index.ipynb

For an overview on packages for playing and recording audio, see
https://realpython.com/playing-and-recording-sound-python/

"""

import sys
import os
from .version import __version__, __year__


audio_modules = {}
""" Dictionary with availability of various audio modules.
Keys are the module names, values are booleans.
Based on this dictionary audioio employs functions of installed audio modules. """

audio_installed = []
""" List of installed audio modules. """

audio_infos = {}
""" Dictionary with information about all supported audio modules.
Keys are the module names, values are the informations. """

audio_instructions_linux = {}
""" Dictionary with general installation instructions for linux that
are needed in addition to installing some packages.
Keys are the module names, values are the instructions. """

audio_instructions_windows = {}
""" Dictionary with general installation instructions for windows that
are needed in addition to installing some packages.
Keys are the module names, values are the instructions. """

audio_pip_packages = {}
""" Dictionary with pip package names of the audio modules.
Keys are the module names, values are pip package names. """

audio_conda_packages = {}
""" Dictionary with conda package names of the audio modules.
Keys are the module names, values are conda package names,
optionally with a channel specification. """

audio_deb_packages = {}
""" Dictionary with Linux DEB packages of the audio modules.
Keys are the module names, values are the package names. """

audio_rpm_packages = {}
""" Dictionary with Linux RPM packages of the audio modules.
Keys are the module names, values are the package names. """

audio_brew_packages = {}
""" Dictionary with macOS homebrew packages of the audio modules.
Keys are the module names, values are the package (formulae) names. """

audio_required_deb_packages = {}
""" Dictionary with Linux DEB packages required for the audio modules.
Keys are the module names, values are lists of string with package names. """

audio_required_rpm_packages = {}
""" Dictionary with Linux RPM packages required for the audio modules.
Keys are the module names, values are lists of string with package names. """

audio_required_brew_packages = {}
""" Dictionary with macOS homebrew packages required for the audio modules.
Keys are the module names, values are lists of string with package (formulae) names. """

audio_fileio = []
""" List of audio modules used for reading and writing audio files. """

audio_device = []
""" List of audio modules used for playing and recording sounds on audio devices. """


# probe for available audio modules:

audio_fileio.append('wave')
try:
    import wave
    audio_modules['wave'] = True
    audio_installed.append('wave')
except ImportError:
    audio_modules['wave'] = False
audio_infos['wave'] = """The wave module is part of the standard python library.
For documentation see https://docs.python.org/3.8/library/wave.html"""

audio_fileio.append('ewave')
try:
    import ewave
    audio_modules['ewave'] = True
    audio_installed.append('ewave')
except ImportError:
    audio_modules['ewave'] = False
audio_pip_packages['ewave'] = 'ewave'
audio_conda_packages['ewave'] = '-c auto ewave'
audio_infos['ewave'] = """The ewave package supports more types of WAV-files than the standard wave module.
For documentation see https://github.com/melizalab/py-ewave"""

audio_fileio.append('scipy.io.wavfile')
try:
    from scipy.io import wavfile
    audio_modules['scipy.io.wavfile'] = True
    audio_installed.append('scipy.io.wavfile')
except ImportError:
    audio_modules['scipy.io.wavfile'] = False
audio_pip_packages['scipy.io.wavfile'] = 'scipy'
audio_conda_packages['scipy.io.wavfile'] = 'scipy'
audio_deb_packages['scipy.io.wavfile'] = 'python3-scipy'
audio_rpm_packages['scipy.io.wavfile'] = 'python3-scipy'
audio_brew_packages['scipy.io.wavfile'] = 'scipy'
audio_infos['scipy.io.wavfile'] = """The scipy package provides very basic functions for reading WAV files.
For documentation see http://docs.scipy.org/doc/scipy/reference/io.html"""

audio_fileio.append('soundfile')
try:
    import soundfile
    audio_modules['soundfile'] = True
    audio_installed.append('soundfile')
except ImportError:
    audio_modules['soundfile'] = False
audio_pip_packages['soundfile'] = 'SoundFile'
audio_conda_packages['soundfile'] = '-c conda-forge soundfile'
audio_deb_packages['soundfile'] = 'python3-soundfile'
audio_required_deb_packages['soundfile'] = ['libsndfile1', 'libsndfile1-dev', 'libffi-dev']
audio_required_rpm_packages['soundfile'] = ['libsndfile', 'libsndfile-devel', 'libffi-devel']
audio_infos['soundfile'] = """The soundfile package is a wrapper of the sndfile library,
that supports many different audio file formats.
See http://python-soundfile.readthedocs.org for a documentation of the soundfile python wrapper
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""

audio_fileio.append('wavefile')
try:
    import wavefile
    audio_modules['wavefile'] = True
    audio_installed.append('wavefile')
except ImportError:
    audio_modules['wavefile'] = False
audio_pip_packages['wavefile'] = 'wavefile'
audio_required_deb_packages['wavefile'] = ['libsndfile1', 'libsndfile1-dev', 'libffi-dev']
audio_required_rpm_packages['wavefile'] = ['libsndfile', 'libsndfile-devel', 'libffi-devel']
audio_required_brew_packages['wavefile'] = ['libsndfile', 'libffi']
audio_infos['wavefile'] = """The wavefile package is a wrapper of the sndfile library,
that supports many different audio file formats.
See https://github.com/vokimon/python-wavefile for documentation of the wavefile python wrapper
and http://www.mega-nerd.com/libsndfile for details on the sndfile library."""
        
audio_fileio.append('audioread')
try:
    import audioread
    audio_modules['audioread'] = True
    audio_installed.append('audioread')
except ImportError:
    audio_modules['audioread'] = False
audio_pip_packages['audioread'] = 'audioread'
audio_conda_packages['audioread'] = '-c conda-forge audioread'
audio_deb_packages['audioread'] = 'python3-audioread'
audio_rpm_packages['audioread'] = 'python3-audioread'
audio_required_deb_packages['audioread'] = ['ffmpeg', 'libavcodec-extra']
audio_required_rpm_packages['audioread'] = ['ffmpeg', 'ffmpeg-devel', 'libavcodec-extra']
audio_required_brew_packages['audioread'] = ['libav --with-libvorbis --with-sdl --with-theora', 'ffmpeg --with-libvorbis --with-sdl2 --with-theora']
audio_infos['audioread'] = """The audioread package uses libav (https://libav.org/) or ffmpeg (https://ffmpeg.org/) to make mpeg files readable.
Install this package for reading mpeg files.
For documentation see https://github.com/beetbox/audioread"""
        
audio_fileio.append('pydub')
try:
    import pydub
    audio_modules['pydub'] = True
    audio_installed.append('pydub')
except ImportError:
    audio_modules['pydub'] = False
audio_pip_packages['pydub'] = 'pydub'
audio_conda_packages['pydub'] = '-c conda-forge pydub'
audio_deb_packages['pydub'] = 'python3-pydub'
audio_rpm_packages['pydub'] = 'python3-pydub'
audio_required_deb_packages['pydub'] = ['ffmpeg', 'libavcodec-extra']
audio_required_rpm_packages['pydub'] = ['ffmpeg', 'ffmpeg-devel', 'libavcodec-extra']
audio_required_brew_packages['pydub'] = ['libav --with-libvorbis --with-sdl --with-theora', 'ffmpeg --with-libvorbis --with-sdl2 --with-theora']
audio_infos['pydub'] = """The pydub package uses libav (https://libav.org/) or ffmpeg (https://ffmpeg.org/) to make mpeg files readable and writeable.
Install this package if you need to write mpeg files.
For documentation see https://github.com/jiaaro/pydub"""
        
audio_device.append('pyaudio')
try:
    import pyaudio
    audio_modules['pyaudio'] = True
    audio_installed.append('pyaudio')
except ImportError:
    audio_modules['pyaudio'] = False
audio_pip_packages['pyaudio'] = 'PyAudio'
audio_conda_packages['pyaudio'] = 'pyaudio'
audio_deb_packages['pyaudio'] = 'python3-pyaudio  # WARNING: broken on Ubuntu with python 3.10, use pip instead'
audio_rpm_packages['pyaudio'] = 'python3-pyaudio'
audio_required_deb_packages['pyaudio'] = ['libportaudio2', 'portaudio19-dev']
audio_required_rpm_packages['pyaudio'] = ['libportaudio', 'portaudio-devel']
audio_required_brew_packages['pyaudio'] = ['portaudio']
audio_infos['pyaudio'] = """The pyaudio package is a wrapper of the portaudio library (http://www.portaudio.com).
For documentation see https://people.csail.mit.edu/hubert/pyaudio."""
audio_instructions_windows['pyaudio'] = """Download an appropriate (latest version, 32 or 64 bit) wheel from
<https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio>.  Install this file with pip,
that is go to the folder where the wheel file is downloaded and run

pip install PyAudio-0.2.11-cp39-cp39-win_amd64.whl

replace the wheel file name by the one you downloaded."""
        
audio_device.append('sounddevice')
try:
    import sounddevice
    audio_modules['sounddevice'] = True
    audio_installed.append('sounddevice')
except ImportError:
    audio_modules['sounddevice'] = False
audio_pip_packages['sounddevice'] = 'sounddevice'
audio_conda_packages['sounddevice'] = '-c conda-forge python-sounddevice'
audio_required_deb_packages['sounddevice'] = ['libportaudio2', 'portaudio19-dev', 'python3-cffi']
audio_required_rpm_packages['sounddevice'] = ['libportaudio', 'portaudio-devel', 'python3-cffi']
audio_required_brew_packages['sounddevice'] = ['portaudio']
audio_infos['sounddevice'] = """The sounddevice package is a wrapper of the portaudio library (http://www.portaudio.com). 
If you have trouble with pyaudio, try this as an alternative.
For documentation see https://python-sounddevice.readthedocs.io"""
        
audio_device.append('simpleaudio')
try:
    import simpleaudio
    audio_modules['simpleaudio'] = True
    audio_installed.append('simpleaudio')
except ImportError:
    audio_modules['simpleaudio'] = False
audio_pip_packages['simpleaudio'] = 'simpleaudio'
audio_rpm_packages['simpleaudio'] = 'python3-simpleaudio'
audio_required_deb_packages['simpleaudio'] = ['python3-dev', 'libasound2-dev']
audio_required_rpm_packages['simpleaudio'] = ['python3-devel', 'alsa-lib', 'alsa-lib-devel']
audio_infos['simpleaudio'] = """The simpleaudio package is a lightweight package
for cross-platform audio playback.
For documentation see https://simpleaudio.readthedocs.io"""
        
audio_device.append('soundcard')
try:
    import soundcard
    audio_modules['soundcard'] = True
    audio_installed.append('soundcard')
except ImportError:
    audio_modules['soundcard'] = False
except AssertionError:
    audio_modules['soundcard'] = False
audio_pip_packages['soundcard'] = 'soundcard'
audio_infos['soundcard'] = """SoundCard is a library for playing and recording audio without
resorting to a CPython extension. Instead, it is implemented using the
wonderful CFFI and the native audio libraries of Linux, Windows and
macOS.
For documentation see https://github.com/bastibe/SoundCard"""
        
audio_device.append('ossaudiodev')
try:
    import ossaudiodev
    audio_modules['ossaudiodev'] = True
    audio_installed.append('ossaudiodev')
except ImportError:
    audio_modules['ossaudiodev'] = False
audio_required_deb_packages['ossaudiodev'] = ['osspd']
audio_infos['ossaudiodev'] = """The ossaudiodev module is part of the python standard library and
provides simple support for sound playback under Linux based on the (outdated) OSS system.
You most likely want to install the simpleaudio or the soundfile package for better performance.
For documentation see https://docs.python.org/3.8/library/ossaudiodev.html"""
        
audio_device.append('winsound')
try:
    import winsound
    audio_modules['winsound'] = True
    audio_installed.append('winsound')
except ImportError:
    audio_modules['winsound'] = False
audio_infos['winsound'] = """The winsound module is part of the python standard library and
provides simple support for sound playback under Windows. If possible,
install the simpleaudio package in addition for better performance.
For documentation see https://docs.python.org/3.6/library/winsound.html and
https://mail.python.org/pipermail/tutor/2012-September/091529.html"""


def installed_modules(func='all'):
    """Installed audio modules.

    By default all installed modules are available. With
    `disable_module()`, `enable_module()` and `select_module()`
    the availability of installed modules can be controlled.

    Parameters
    ----------
    func: string
        'all': all installed audio modules.
        'fileio': installed audio modules used for file I/O.
        'device': installed audio modules used for playing and recording sounds.
    
    Returns
    -------
    mods: list of strings
        List of installed audio modules of the requested function.

    See Also
    --------
    available_modules()
    """
    if func == 'fileio':
        return [module for module in audio_fileio if module in audio_installed]
    elif func == 'device':
        return [module for module in audio_device if module in audio_installed]
    else:
        return audio_installed


def available_modules(func='all'):
    """Installed and enabled audio modules.

    By default all installed modules are available. With
    `disable_module()`, `enable_module()` and `select_module()`
    the availability of installed modules can be controlled.

    Parameters
    ----------
    func: string
        'all': all installed audio modules.
        'fileio': installed audio modules used for file I/O.
        'device': installed audio modules used for playing and recording sounds.
    
    Returns
    -------
    mods: list of strings
        List of available, i.e. installed and enabled, audio modules
        of the requested function.
    """
    if func == 'fileio':
        return [module for module in audio_fileio if audio_modules[module]]
    elif func == 'device':
        return [module for module in audio_device if audio_modules[module]]
    else:
        return [module for module in audio_installed if audio_modules[module]]


def unavailable_modules(func='all'):
    """Audio modules that are not installed and not enabled.

    Parameters
    ----------
    func: string
        'all': all installed audio modules.
        'fileio': installed audio modules used for file I/O.
        'device': installed audio modules used for playing and recording sounds.
    
    Returns
    -------
    mods: list of strings
        List of not available, i.e. not installed and not enabled, audio modules
        of the requested function.
    """
    if func == 'fileio':
        return [module for module in audio_fileio if not audio_modules[module]]
    elif func == 'device':
        return [module for module in audio_device if not audio_modules[module]]
    else:
        return [module for module in audio_modules.keys() if not audio_modules[module]]


def disable_module(module=None):
    """Disable an audio module.

    A disabled module is not used by the audioio functions and classes.
    To disable all modules except one, call `select_module()`.
    
    Parameters
    ----------
    module: string or None
        Name of the module to be disabled as it appears in `available_modules()`.
        If None disable all installed audio modules.

    See Also
    --------
    enable_module(), select_module(), available_modules(), list_modules()
    """
    if module is None:
        for module in audio_installed:
            audio_modules[module] = False
    elif module in audio_modules:
        audio_modules[module] = False


def enable_module(module=None):
    """Enable audio modules provided they are installed.
    
    Parameters
    ----------
    module: string or None
        Name of the module to be (re)enabled.
        If None enable all installed audio modules.

    See Also
    --------
    disable_module(), available_modules(), list_modules()
    """
    if module is None:
        for module in audio_installed:
            audio_modules[module] = True
    elif module in audio_modules:
        audio_modules[module] = (module in audio_installed)


def select_module(module):
    """Select (enable) a single audio module and disable all others.

    Undo by calling `enable_module()` without arguments.
    
    Parameters
    ----------
    module: string
        Name of the module to be selected.

    Returns
    -------
    selected: bool
        False if the module can not be selected, because it is not installed.
        In this case the other modules are not disabled.

    See Also
    --------
    enable_module(), disable_module(), available_modules(), list_modules()
    """
    if module not in audio_installed:
        return False
    for mod in audio_installed:
        audio_modules[mod] = (mod == module)
    return True


def list_modules(module='all', availability=True):
    """Print list of all supported modules and their installation status.
    
    Modules that are not installed but are recommended are marked
    with an all uppercase "NOT installed".

    Parameters
    ----------
    module: string
        If 'all' list all modules.
        If 'fileio' list all modules used for file I/O.
        If 'device' list all modules used for playing and recording sounds.
        Otherwise list only the specified module.
    availability: bool
        Mark availability of each module by an asterisk.

    See Also
    --------
    installed_modules()
    missing_modules()
    missing_modules_instructions()
    """
    def print_module(module, missing, print_type):
        audio_avail = ''
        if availability:
            audio_avail = '* ' if audio_modules[module] else '  '
        audio_type = ''
        if print_type:
            if module in audio_fileio:
                audio_type += 'F'
            if module in audio_device:
                audio_type += 'D'
            if len(audio_type) > 0:
                audio_type = ' (%s)' % audio_type
        if module in audio_installed:
            print('%s%-17s is  installed%s' % (audio_avail, module, audio_type))
        elif module in missing:
            print('%s%-17s NOT installed%s' % (audio_avail, module, audio_type))
        else:
            print('%s%-17s not installed%s' % (audio_avail, module, audio_type))

    missing = missing_modules()
    if module not in ['all', 'fileio', 'device']:
        print_module(module, missing, True)
    else:
        print_type = (module == 'all')
        modules = sorted(audio_modules.keys())
        if module in ['all', 'fileio']:
            for mod in audio_fileio:
                print_module(mod, missing, print_type)
                modules.remove(mod)
        if module in ['all', 'device']:
            for mod in audio_device:
                if mod in modules:
                    print_module(mod, missing, print_type)
                    modules.remove(mod)
        if module == 'all':
            for mod in modules:
                print_module(mod, missing, print_type)


def missing_modules(func='all'):
    """Missing audio modules that are recommended to be installed.

    Parameters
    ----------
    func: string
        'all': missing audio modules of all functions.
        'fileio': missing audio modules for file I/O.
        'device': missing audio modules for playing and recording sounds.
    
    Returns
    -------
    mods: list of strings
        List of missing audio modules of the requested function.
    """
    mods = []
    if func in ['all', 'fileio']:
        if 'soundfile' not in audio_installed and \
           'wavefile' not in audio_installed:
            mods.append('soundfile')
        if 'audioread' not in audio_installed:
            mods.append('audioread')
        if 'pydub' not in audio_installed:
            mods.append('pydub')
    if func in ['all', 'device']:
        if 'pyaudio' not in audio_installed and \
           'sounddevice' not in audio_installed and \
           'simpleaudio' not in audio_installed:
            mods.append('simpleaudio')
    return mods


def missing_modules_instructions(func='all'):
    """Print installation instructions for missing but useful audio modules.

    Parameters
    ----------
    func: string
        'all': missing audio modules of all functions.
        'fileio': missing audio modules for file I/O.
        'device': missing audio modules for playing and recording sounds.
    """
    mods = missing_modules(func)
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
    """Instructions on how to install a specific audio module.

    Parameters
    ----------
    module: string
        The name of the module for which an instruction should be printed.
    
    Returns
    -------
    msg: multi-line string
        Installation instruction for the requested module.
    """
    install_package_deb = "sudo apt install"
    install_package_rpm = "dnf install"
    install_package_brew = "brew install"
    install_package = None
    package = None
    required_packages = None
    multiline = False
    instruction = None
        
    install_pip_deb = "sudo pip install"
    install_pip_rpm = "pip install"
    install_pip_osx = "pip install"
    install_pip_win = "pip install"
    install_pip = install_pip_deb

    install_conda = "conda install"

    # check operating system:
    if sys.platform[0:5] == "linux":
        if os.path.exists('/etc/redhat-release') or os.path.exists('/etc/fedora-release'):
            install_package = install_package_rpm
            install_pip = install_pip_rpm
            package = audio_rpm_packages.get(module, None)
            required_packages = audio_required_rpm_packages.get(module, None)
        else:
            install_package = install_package_deb
            package = audio_deb_packages.get(module, None)
            required_packages = audio_required_deb_packages.get(module, None)
        instruction = audio_instructions_linux.get(module, None)
    elif sys.platform == "darwin":
        install_package = install_package_brew
        install_pip = install_pip_osx
        package = audio_brew_packages.get(module, None)
        required_packages = audio_required_brew_packages.get(module, None)
        multiline = True
    elif sys.platform[0:3] == "win":
        install_package = ''
        install_pip = install_pip_win
        instruction = audio_instructions_windows.get(module, None)
    # check conda:
    conda = "CONDA_DEFAULT_ENV" in os.environ
    conda_package = audio_conda_packages.get(module, None)
    if conda:
        install_pip = install_pip.replace('sudo ', '')

    pip_package = audio_pip_packages.get(module, None)
        
    req_inst = None
    if required_packages is not None:
        if multiline:
            ps = '\n'.join([install_package + ' ' + p for p in required_packages])
        else:
            ps = install_package + ' ' + ' '.join(required_packages)
        if pip_package is None and package is None:
            req_inst = 'Install the following packages:\n\n' + ps
        else:
            req_inst = 'First, install the following packages:\n\n' + ps
    
    pip_inst = None
    if pip_package is not None:
        pip_inst = 'Install the %s module with pip:\n\n%s %s' % (module, install_pip, pip_package)
        
    dist_inst = None
    if package is not None:
        if pip_inst is None:
            dist_inst = 'Install module from your distribution\'s package:\n\n%s %s' % (install_package, package)
        else:
            dist_inst = 'or alternatively from your distribution\'s package:\n\n%s %s' % (install_package, package)

    conda_inst = None
    if conda and conda_package is not None:
        conda_inst = 'Install the %s module with conda:\n\n%s %s' % (module, install_conda, conda_package)
        req_inst = pip_inst = dist_inst = instruction = None

    info = audio_infos.get(module, None)

    msg = ''
    for s in [info, conda_inst, req_inst, pip_inst, dist_inst, instruction]:
        if s is not None:
            if len(msg) > 0:
                msg += '\n\n'
            msg += s
    
    return msg


def main(*args):
    """ Command line program for listing installation status of audio modules.

    Run this module as a script
    ```
    > python -m src.audioio.auidomodules
    ```
    or, when the audioio package is installed on your system, simply run
    ```sh
    > audiomodules
    ```
    for an overview of audio packages, their installation status, and recommendations on
    how to install further audio packages.

    The '--help' argument prints out a help message:
    ```sh
    > audiomodules --help
    ```

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    if len(args) == 0:
        args = sys.argv[1:]
    if len(args) > 0:
        if args[0] == '--version':
            print('version', __version__, 'by Benda-Lab (2015-%s)' % __year__)
            sys.exit(0)
        if args[0] == '--help' or args[0] == '-h':
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
            return
    print('')
    print('Status of audio packages on this machine:')
    print('-'*41)
    print('')
    list_modules('all', False)
    print('')
    print('F: file I/O, D: audio device')
    print('')
    missing_modules_instructions()
    print('')

    if len(args) > 0 :
        mod = args[0]
        if mod in audio_modules:
            print('Installation instructions for the %s module:' % mod )
            print('-'*(42+len(mod)))
            print(installation_instruction(mod))
            print('')


if __name__ == "__main__":
    main(*sys.argv[1:])
