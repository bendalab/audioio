[![PyPI license](https://img.shields.io/pypi/l/audioio.svg)](https://pypi.python.org/pypi/audioio/)
[![Build Status](https://travis-ci.com/bendalab/audioio.svg?branch=master)](https://travis-ci.com/bendalab/audioio)
[![codecov](https://codecov.io/gh/bendalab/audioio/branch/master/graph/badge.svg)](https://codecov.io/gh/bendalab/audioio)
[![PyPI version](https://badge.fury.io/py/audioio.svg)](https://badge.fury.io/py/audioio)
<!-- [![PyPI pyversions](https://img.shields.io/pypi/pyversions/audioio.svg)](https://pypi.python.org/pypi/audioio/) -->
<!-- [![PyPI download total](https://img.shields.io/pypi/dt/audioio.svg)](https://pypi.python.org/pypi/audioio/) see https://github.com/Naereen/badges#pypi-downloads -->

# AudioIO 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio) |
[API Reference](https://bendalab.github.io/audioio/api)

The AudioIO modules try to use whatever audio packages are installed
on your system to achieve their tasks. AudioIO itself does not provide
own code for decoding files and accessing audio hardware.


## Features

- Audio data are always *numpy arrays of floats* (`np.float64`) with values ranging between -1 and 1 ...
- ... independent of how the data are stored in an audio file.
- `load_audio()` function for loading a whole audio file.
- *Blockwise random-access* loading of large audio files (`class AudioLoader`).
- `blocks()` generator for iterating over blocks of data with optional overlap.
- `write_audio()` function for writing data to an audio file. 
- Platform independent playback of numpy arrays (`play()`).
- *Synchronous* (blocking) and *asynchronous* (non blocking) playback.
- *Automatic resampling* of data for playback to match supported sampling rates.
- Detailed and *platform specific installation instructions* (pip, conda, Debian and RPM based Linux packages, homebrew for MacOS) for all supported audio packages.


## Installation

Simply run (as superuser):
```
pip install audioio
```

Then you can use already installed audio packages for reading and
writing audio files and for playing audio data. However, audio file
formats supported by the python standard library are limited to basic
wave files and playback capabilities are poor. If you need support for
additional audio file formats or proper sound output, you need to
install additional packages.

See [installation](https://bendalab.github.io/audioio/installation)
for further instructions and recommendations on additional audio
packages.


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
The read in data are always numpy arrays of floats ranging between -1 and 1.
The arrays are always 2-D arrays with first axis time and second axis channel,
even for single channel data.

Plot the first channel:
```
import numpy as np
import matplotlib.pyplot as plt

time = np.arange(len(data))/samplingrate
plt.plot(time, data[:,0])
plt.show()
```

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

Even simpler, iterate in blocks over the file with overlap:
```
from scipy.signal import spectrogram
nfft = 2048
with aio.AudioLoader('some/audio.wav') as data:
    for x in data.blocks(100*nfft, nfft//2):
        f, t, Sxx = spectrogram(x, nperseg=nfft, noverlap=nfft//2)
```

See API documentation of the
[audioloader](https://bendalab.github.io/audioio/api/audioloader.html)
module for details.



### Writing audio data

Write a 1-D or 2-D numpy array into an audio file (data values between -1 and 1):
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

Fade in and out and play a 1-D or 2-D numpy array as a sound
(first axis is time and second axis the channel):
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

Reading and writing audio files:

- [wave](https://docs.python.org/3.8/library/wave.html): simple wave file interface of the python standard library.
- [ewave](https://github.com/melizalab/py-ewave): extended wave files. 
- [scipy.io.wavfile](http://docs.scipy.org/doc/scipy/reference/io.html): simple scipy wave file interface.
- [SoundFile](http://pysoundfile.readthedocs.org): support of many open source audio file formats via [libsndfile](http://www.mega-nerd.com/libsndfile).
- [wavefile](https://github.com/vokimon/python-wavefile): support of many open source audio file formats via [libsndfile](http://www.mega-nerd.com/libsndfile).
- [audioread](https://github.com/beetbox/audioread): mpeg file support.
- [Pydub](https://github.com/jiaaro/pydub): mpeg support for reading and writing, playback via simlpeaudio or pyaudio.
- [scikits.audiolab](http://cournape.github.io/audiolab): seems to be no longer active.

Playing sounds:

- [sounddevice](https://python-sounddevice.readthedocs.io): wrapper for [portaudio](http://www.portaudio.com).
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio): wrapper for [portaudio](http://www.portaudio.com).
- [simpleaudio](https://simpleaudio.readthedocs.io): uses ALSA on Linux, runs well on windows.
- [ossaudiodev](https://docs.python.org/3.8/library/ossaudiodev.html): playback via the outdated OSS interface of the python standard library.
- [winsound](https://docs.python.org/3.6/library/winsound.html): native windows audio playback of the python standard library, asynchronous playback only with wave files.
- [SoundCard](https://github.com/bastibe/SoundCard): Uses native audio libraries.

Related audio software:

- [diapason](https://github.com/Soundphy/diapason): musical notes like `playaudio.note2freq`.
- [librosa](https://librosa.org/): audio and music processing in python.
- [TimeView](https://github.com/j9ac9k/timeview): GUI application to view and analyze time series signal data.
