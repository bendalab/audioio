# Installation

AudioIO uses whatever audio module is installed on your
system. However, the python standard library support for reading and
writing audio files and for playing sound is rather poor. You certainly want
to install additional packages for better performance.

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


## Linux

### Reading and writing audio files

For file I/O you might want to install the
[sndfile library](http://www.mega-nerd.com/libsndfile/)
for accessing a wide range of audio file formats.

On Debian based systems:
```sh
sudo apt-get install libsndfile1 libsndfile1-dev libffi-dev
```
on rpm based systems:
```sh
dnf install libsndfile libsndfile-devel libffi-devel
```

Then you can install one of the python wrappers for the sndfile
library, e.g. [SoundFile](http://pysoundfile.readthedocs.org) or
[wavefile](https://github.com/vokimon/python-wavefile):
```sh
sudo pip install SoundFile
sudo pip install wavefile
```

### Reading and writing mpeg files

MPEG and similar formats are supported by libav (https://libav.org)
and ffmpeg (https://ffmpeg.org/) via
[audioread](https://github.com/beetbox/audioread) for reading
and [Pydub](https://github.com/jiaaro/pydub) for writing.
Install them with
```
sudo apt-get install libav-tools python3-audioread python3-pydub
```
on debian based systems and with
```
dnf install ffmpeg ffmpeg-devel python3-audioread python3-pydub
```
on rpm based systems.


### Playback

For playing sounds, the [portaudio library](http://www.portaudio.com)
is the gold standard. Install this library with
```sh
sudo apt-get install libportaudio2 portaudio19-dev
```
on debian based systems or with
```sh
dnf install libportaudio portaudio-devel
```
on rpm based systems.

Then you need to install the python packages [sounddevice](https://python-sounddevice.readthedocs.io) or [PyAudio](https://people.csail.mit.edu/hubert/pyaudio):
```
sudo pip install sounddevice
sudo pip install PyAudio
```


## Windows

For file I/O based on the the [sndfile library](http://www.mega-nerd.com/libsndfile/)
install the [SoundFile](http://pysoundfile.readthedocs.org) module:
```sh
pip install SoundFile
```

For playing sounds install [simpleaudio](https://simpleaudio.readthedocs.io):
```sh
pip install simpleaudio
```
