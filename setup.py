from setuptools import setup, find_packages

exec(open('audioio/version.py').read())

long_description = """
# AudioIO 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio) |
[API Reference](https://bendalab.github.io/audioio/api)

The AudioIO modules try to use whatever audio modules installed on
your system to achieve their tasks. The AudioIO package does not
provide own code for decoding files and accessing audio hardware.

See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.

## Feaures

- Audio data are always numpy arrays of floats with values ranging between -1 and 1 ...
- ... independent of how the data are stored in an audio file.
- Platform independent interface for loading and writing audio files.
- Simple `load_audio()` function for loading a whole audio file.
- Support for blockwise random-access loading of large audio files (`class AudioLoader`).
- Simple `write_audio()` function for writing data to an audio file. 
- Platform independent playback of numpy arrays (`play()`).
- Support of synchronous (blocking) and asynchronous (non blocking) playback.
- Automatic resampling of data for playback to match supported sampling rates.
- Detailed and platform specific installation instructions for audio packages.
"""

setup(
    name = 'audioio',
    version = __version__,
    author = 'Jan Benda, Joerg Henninger',
    author_email = "jan.benda@uni-tuebingen.de",
    description = "Platform independent interfacing of numpy arrays of floats with audio files and devices.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/bendalab/audioio",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    packages = find_packages(exclude = ['contrib', 'docs', 'tests*']),
    entry_points = {
        'console_scripts': [
            'audioconverter = audioio.audioconverter:main',
            'audiomodules = audioio.audiomodules:main',
        ]},
    install_requires = ['numpy']
)
