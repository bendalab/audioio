[![Build Status](https://travis-ci.com/bendalab/audioio.svg?branch=master)](https://travis-ci.com/bendalab/audioio)
[![codecov](https://codecov.io/gh/bendalab/audioio/branch/master/graph/badge.svg)](https://codecov.io/gh/bendalab/audioio)

# audioio 

Platform independent interfacing of numpy arrays of floats with audio
files and devices.

[Documentation](https://bendalab.github.io/audioio)

[Git Repository](https://github.com/bendalab/audioio)

The audioio modules try to use whatever available audio module to achieve
their tasks. The audioio package does not provide own code for decoding files
and accessing audio hardware.


## Installation

After cloning from github change into the `audioio/` base directory
and run as superuser
```
python setup.py install
```
Then you can use the provided modules for reading and writing audio
files and for playing audio data immediately. However, the support
provided by the python standard library is limited to very basic wav
files. If you need support for other audio file formats or for better
sound output you need to install additional packages:

In the `audioio/` base directory you may run
```
python audiomodules.py
```
to see which audio modules you have already installed on your system,
which ones are recommended to install, and how to install them. By
calling the script with the name of an audio module as an argument you
get specific installation instructions for this module.

In particular, you might need to install the sndfile library for accessing
various audio file formats
```
sudo apt-get install -y libsndfile1 libsndfile1-dev libffi-dev
```
and one of the many python wrappers for the sndfile library,
e.g. pysoundfile, wavefile, or scikits.audiolab:
```
sudo pip install pysoundfile
sudo pip install wavefile
sudo pip install scikits.audiolab
```

For playing sounds, the portaudio library is the gold standard
```
sudo apt-get install libportaudio2 portaudio19-dev
```
that is interfaced by the python packages pyaudio or sounddevice:
```
sudo apt-get install python-pyaudio
sudo pip install sounddevice
```

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
The arrays are either 1-D arrays for single channel data,
or 2-day arrays with first axis time and second axis channel.

You can also randomly access chunks of data of an audio file, without
loading the entire file into memory. This is really handy for
analysing very long sound recordings:
```
with aio.open_audio_loader('audio/file.wav', 60.0) as data:
     block = 1000
     rate = data.samplerate
     for i in range(len(data)/block):
     	 x = data[i*block:(i+1)*block]
     	 # ... do something with x and rate
```

### Writing audio data

Write a numpy array into an audio file:
```
aio.write_audio('audio/file.wav', data, samplerate)
```


### Converting audio files

audioio provides a simple command line script to convert audio files:
```
> audioconverter -o test.wav test.mp3
```


### Playing sounds

Play a numpy array as a sound:
```
aio.play(data, samplingrate)
```

Just beep for half a second and 440 Hz:
```
aio.beep(0.5, 440.0)
aio.beep(0.5, 'a4')
```
