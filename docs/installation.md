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

For playing sounds [simpleaudio](https://simpleaudio.readthedocs.io)
provides direct support of the native sound systems.


## Debian-based Linux

```sh
sudo apt install libsndfile1 libsndfile1-dev libffi-dev
sudo pip install SoundFile
sudo apt install ffmpeg python3-audioread python3-pydub
sudo pip install simpleaudio
```

## Fedora-based Linux

```sh
dnf install libsndfile libsndfile-devel libffi-devel
pip install SoundFile
dnf install ffmpeg ffmpeg-devel python3-audioread python3-pydub
pip install simpleaudio
```

## Windows

```sh
pip install SoundFile
pip install simpleaudio
```
