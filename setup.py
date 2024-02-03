from setuptools import setup, find_packages

exec(open('audioio/version.py').read())

long_description = """
# AudioIO 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio) |
[API Reference](https://bendalab.github.io/audioio/api)

The AudioIO modules try to use whatever audio packages are installed
on your system to achieve their tasks. AudioIO, however, adds own code
for handling metadata and marker lists.

See [installation](https://bendalab.github.io/audioio/installation)
for further instructions and recommendations on additional audio packages.

## Features


- Audio data are always *numpy arrays of floats* (`np.float64`) with values ranging between -1 and 1 ...
- ... independent of how the data are stored in an audio file.
- [`load_audio()`](https://bendalab.github.io/audioio/api/audioloader.html#audioio.audioloader.load_audio) function for loading a whole audio file.
- *Blockwise random-access* loading of large audio files ([`class AudioLoader`](https://bendalab.github.io/audioio/api/audioloader.html#audioio.audioloader.AudioLoader)).
- [`blocks()`](https://bendalab.github.io/audioio/api/audioloader.html#audioio.audioloader.blocks) generator for iterating over blocks of data with optional overlap.
- [`write_audio()`](https://bendalab.github.io/audioio/api/audiowriter.html#audioio.audiowriter.write_audio) function for writing data, metadata, and markers to an audio file. 
- Read [`metadata()`](https://bendalab.github.io/audioio/api/audiometadata.html#audioio.audiometadata.metadata) as nested dictionaries of key-value pairs.
- Read [`markers()`](https://bendalab.github.io/audioio/api/audiometadata.html#audioio.audiometadata.markers), i.e. cue points with spans, labels, and descriptions.
- Platform independent, synchronous (blocking) and asynchronous (non blocking) playback of numpy arrays  via [`play()`](https://bendalab.github.io/audioio/api/playaudio.html#audioio.playaudio.play).
- Automatic resampling of data for playback to match supported sampling rates.
- Detailed and *platform specific installation instructions* (pip, conda, Debian and RPM based Linux packages, homebrew for MacOS) for all supported audio packages ([audiomodules](https://bendalab.github.io/audioio/api/audiomodules.html)).
"""

setup(
    name = 'audioio',
    version = __version__,
    author = 'Jan Benda, Jörg Henninger',
    author_email = "jan.benda@uni-tuebingen.de",
    description = "Platform independent interfacing of numpy arrays of floats with audio files and devices.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/bendalab/audioio",
    license = "GPLv3",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    packages = find_packages(exclude = ['contrib', 'docs', 'tests*']),
    entry_points = {
        'console_scripts': [
            'audioconverter = audioio.audioconverter:main',
            'audiometadata = audioio.audiometadata:main',
            'audiomodules = audioio.audiomodules:main',
        ]},
    install_requires = ['numpy']
)
