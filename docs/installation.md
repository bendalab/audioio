# Installation

AudioIO does not provide own code but rather uses whatever audio
modules are installed on your system. The python standard library
support for reading and writing audio files and for playing sound is
rather poor. You certainly want to install additional packages for
better performance.

Run in your terminal
```sh
> audiomodules
```
to see which audio modules you have already installed on your system,
which ones are recommended to install, and how to install them. By
calling the script with the name of an audio module as an argument you
get platform specific installation instructions for this module. E.g.
```sh
> audiomodules audioread
```

## Recommendations

For accessing a wide range of open source audio file formats install
[sndfile library](http://www.mega-nerd.com/libsndfile/) and the python
wrapper [SoundFile](http://pysoundfile.readthedocs.org).

MPEG and similar formats are supported by libav (https://libav.org)
and ffmpeg (https://ffmpeg.org/) via
[audioread](https://github.com/beetbox/audioread) for reading
and [Pydub](https://github.com/jiaaro/pydub) for writing.

For playing sounds, use the
[sounddevice](https://python-sounddevice.readthedocs.io) package, that
is based on [portaudio](http://www.portaudio.com).
Unfortunately, the simple but powerful
[simpleaudio](https://simpleaudio.readthedocs.io) package is no longer
maintained.

## Debian-based Linux

```sh
sudo apt install libsndfile1 libsndfile1-dev libffi-dev
sudo pip install SoundFile
sudo apt install ffmpeg python3-audioread python3-pydub
sudo apt install libportaudio2 portaudio19-dev python3-cffi
sudo pip install sounddevice
```

## Fedora-based Linux

```sh
dnf install libsndfile libsndfile-devel libffi-devel
pip install SoundFile
dnf install ffmpeg ffmpeg-devel python3-audioread python3-pydub
dnf install libportaudio portaudio-devel python3-cffi
pip install sounddevie
```

## Windows

```sh
pip install SoundFile
pip install sounddevice
```
