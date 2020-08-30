[![Build Status](https://travis-ci.com/bendalab/audioio.svg?branch=master)](https://travis-ci.com/bendalab/audioio)
[![codecov](https://codecov.io/gh/bendalab/audioio/branch/master/graph/badge.svg)](https://codecov.io/gh/bendalab/audioio)
[![PyPI version](https://badge.fury.io/py/audioio.svg)](https://badge.fury.io/py/audioio)

# AudioIO 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio) |
[API Reference](https://bendalab.github.io/audioio/api)

The AudioIO modules try to use whatever audio modules installed on
your system to achieve their tasks. The AudioIO package does not
provide own code for decoding files and accessing audio hardware.


## Feaures

- Audio data are always numpy arrays of floats with values ranging between -1 and 1 ...
- ... independent of how the data are stored in an audio file.
- Platform independent interface for loading and writing audio files.
- Simple `load_audio()` function for loading a whole audio file.
- Support for blockwise random-access loading of large audio files (`class AudioLoader`).
- Simple `write_audio()` for writing data to an audio file. 
- Platform independent playback of numpy arrays (`play()`).
- Support of synchronous (blocking) and asynchronous (non blocking) playback.
- Detailed and platform specific installation instructions for audio packages.


## Installation

Simply run (as superuser):
```
pip install audioio
```

Then you can use already installed audio packages for reading and
writing audio files and for playing audio data. However, the support
provided by the python standard library is limited to very basic WAV
files and playback support is very limited. If you need support for
other audio file formats or for better sound output, you need to
install additional packages.

See [installation](https://bendalab.github.io/audioio/installation)
for further instructions on additional audio packages.


## Usage

See [API Reference](https://bendalab.github.io/audioio/api) for detailed
information.

```
import audioio as aio
```

### Loading audio data

Load an audio file into a numpy array:
```
data, samplingrate = aio.load_audio('audio/file.wav')
```
	
The data are numpy arrays of floats ranging between -1 and 1.
The arrays are 2-D arrays with first axis time and second axis channel.

You can also randomly access chunks of data of an audio file, without
loading the entire file into memory. This is really handy for
analysing very long sound recordings:
```
# open audio file with a buffer holding 60 seconds of data:
with aio.open_audio_loader('audio/file.wav', 60.0) as data:
     block = 1000
     rate = data.samplerate
     for i in range(len(data)//block):
     	 x = data[i*block:(i+1)*block]
     	 # ... do something with x and rate
```

See API documentation of the
[audioloader](https://bendalab.github.io/audioio/api/audioloader.html)
module for details.



### Writing audio data

Write a 1-D or 2-D numpy array into an audio file:
```
aio.write_audio('audio/file.wav', data, samplerate)
```
Again, in 2-D arrays the first axis (rows) is time and the second axis the channel (columns).

See API documentation of the
[audiowriter](https://bendalab.github.io/audioio/api/audiowriter.html)
module for details.


### Converting audio files

AudioIO provides a simple command line script to convert audio files:
```sh
> audioconverter -e float -o test.wav test.mp3
```

See API documentation of the
[audioconverter](https://bendalab.github.io/audioio/api/audioconverter.html)
module for details.


### Playing sounds

Fade in and out and play a numpy array as a sound:
```
aio.fade(data, samplingrate, 0.2)
aio.play(data, samplingrate)
```

Just beep
```
aio.beep()
```
Beep for half a second and 440 Hz:
```
aio.beep(0.5, 440.0)
aio.beep(0.5, 'a4')
```
Musical notes are translated into frequency with the `note2freq()` function.

See API documentation of the
[playaudio](https://bendalab.github.io/audioio/api/playaudio.html)
module for details.


### Managing audio modules

Simply run in your terminal
```sh
> audiomodules
```
to see which audio modules you have already installed on your system,
which ones are recommended to install, and how to install them.

See API documentation of the
[audiomodules](https://bendalab.github.io/audioio/api/audiomodules.html)
module for details.


## Alternatives

All the audio modules AudioIO is using.

For file I/O:

- [wave](https://docs.python.org/3.8/library/wave.html): simple wav file interface of the python standard library
- [ewave](https://github.com/melizalab/py-ewave): extended WAV files. 
- [scipy.io.wavfile](http://docs.scipy.org/doc/scipy/reference/io.html): simple scipy wav file interface.
- [SoundFile](http://pysoundfile.readthedocs.org): support of many open source audio file formats via [libsndfile](http://www.mega-nerd.com/libsndfile).
- [wavefile](https://github.com/vokimon/python-wavefile): support of many open source audio file formats via [libsndfile](http://www.mega-nerd.com/libsndfile).
- [audioread](https://github.com/beetbox/audioread): MP3 file support
- [scikits.audiolab](http://cournape.github.io/audiolab): no longer active

For playing sounds:

- [sounddevice](https://python-sounddevice.readthedocs.io): wrapper for [portaudio](http://www.portaudio.com)
- [pyaudio](https://people.csail.mit.edu/hubert/pyaudio): wrapper for [portaudio](http://www.portaudio.com)
- [simpleaudio](https://simpleaudio.readthedocs.io): uses ALSA directly, runs well on windows.
- [ossaudiodev](https://docs.python.org/3.8/library/ossaudiodev.html): audio via the outdated OSS of the python standard library
- [winsound](https://docs.python.org/3.6/library/winsound.html): native windows audio of the python standard library
