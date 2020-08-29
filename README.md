[![Build Status](https://travis-ci.com/bendalab/audioio.svg?branch=master)](https://travis-ci.com/bendalab/audioio)
[![codecov](https://codecov.io/gh/bendalab/audioio/branch/master/graph/badge.svg)](https://codecov.io/gh/bendalab/audioio)
[![PyPI version](https://badge.fury.io/py/audioio.svg)](https://badge.fury.io/py/audioio)

# AudioIO 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio) |
[API Reference](https://bendalab.github.io/audioio/api)

The audioio modules try to use whatever available audio module to achieve
their tasks. The audioio package does not provide own code for decoding files
and accessing audio hardware.


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
files. If you need support for other audio file formats or for better
sound output, you need to install additional packages.

See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.


## Usage

```
import audioio as aio
```

### Loading audio data

Load an audio file into a numpy array:
```
data, samplingrate = aio.load_audio('audio/file.wav')
```
	
The data are numpy arrays of floats ranging between -1 and 1.
The arrays are 2-day arrays with first axis time and second axis channel.

You can also randomly access chunks of data of an audio file, without
loading the entire file into memory. This is really handy for
analysing very long sound recordings:
```
# open audio file with a buffer holding 60 seconds of data:
with aio.open_audio_loader('audio/file.wav', 60.0) as data:
     block = 1000
     rate = data.samplerate
     for i in range(len(data)/block):
     	 x = data[i*block:(i+1)*block]
     	 # ... do something with x and rate
```


### Writing audio data

Write a 1-D or 2-D numpy array into an audio file:
```
aio.write_audio('audio/file.wav', data, samplerate)
```


### Converting audio files

audioio provides a simple command line script to convert audio files:
```
> audioconverter -o test.wav test.mp3
```


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


### Managing audio modules

Simply run in your terminal
```sh
> audiomodules
```
to see which audio modules you have already installed on your system,
which ones are recommended to install, and how to install them.


## Alternatives

All the audio modules AudioIO is using.

For file I/O:
[wave](https://docs.python.org/3.8/library/wave.html),
[ewave](https://github.com/melizalab/py-ewave),
[scipy.io.wavfile](http://docs.scipy.org/doc/scipy/reference/io.html),
[SoundFile](http://pysoundfile.readthedocs.org),
[wavefile](https://github.com/vokimon/python-wavefile),
[scikits.audiolab](http://cournape.github.io/audiolab),
[audioread](https://github.com/beetbox/audioread).

For playing sounds:
[sounddevice](https://python-sounddevice.readthedocs.io),
[pyaudio](https://people.csail.mit.edu/hubert/pyaudio),
[simpleaudio](https://simpleaudio.readthedocs.io),
[ossaudiodev](https://docs.python.org/3.8/library/ossaudiodev.html),
[winsound](https://docs.python.org/3.6/library/winsound.html).
