"""Play numpy arrays as audio.

- `play()`: playback audio data.
- `beep()`: playback a tone.
- `close()`: close the global PlayAudio instance.
- `PlayAudio()`: audio playback.
- `fade_in()`: fade in a signal in place.
- `fade_out()`: fade out a signal in place.
- `fade()`: fade in and out a signal in place.
- `note2freq()`: convert textual note to corresponding frequency.

Accepted data for playback are 1-D or 2-D (frames, channels) numpy
arrays with values ranging from -1 to 1.
If necessary data are downsampled automatically to match supported
sampling rates.

The globally defined functions `play()` and `beep()` use the global
instance `handle` of the `PlayAudio` class to play a sound on the
default audio output device.

Alternatively you may use the `PlayAudio` class directly, like this:
```
with PlayAudio() as audio:
    audio.beep()
```
or without context management:
```
audio = PlayAudio()
audio.beep(1.0, 'a4')
audio.close()
```

You might need to install additional packages for better audio output.
See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.

For a demo, run the script as:
```
python -m src.audioio.playaudio
```

"""

from sys import platform
import os
import warnings
import numpy as np
from scipy.signal import decimate
from time import sleep
from io import BytesIO
from multiprocessing import Process
from .audiomodules import *


handle = None
"""Default audio device handler.

Defaults to `None`. Will get a PlayAudio instance assigned via
`play()` or `beep()`.
"""


def note2freq(note, a4freq=440.0):
    """Convert textual note to corresponding frequency.

    Parameters
    ----------
    note: string
        A musical note like 'a4', 'f#3', 'eb5'.
        The first character is the note, it can be
        'a', 'b', 'c', 'd', 'e', 'f', or 'g'.
        The optional second character is either a 'b'
        or a '#' to decrease or increase by half a note.
        The last character specifies the octave.
        'a4' is defined by `a4freq`.
    a4freq: float
        The frequency of a4 in Hertz.

    Returns
    -------
    freq: float
        The frequency of the note in Hertz.

    Raises
    ------
    ValueError:
        No or an invalid note was specified.
    """
    freq = a4freq
    tone = 0
    octave = 4
    if not isinstance(note, str) or len(note) == 0:
        raise ValueError('no note specified')
    # note:
    if note[0] < 'a' or note[0] > 'g':
        raise ValueError('invalid note', note[0])
    index = 0
    tonemap = [0, 2, 3, 5, 7, 8, 10]
    tone = tonemap[ord(note[index]) - ord('a')]
    index += 1
    # flat or sharp:
    flat  = False
    sharp = False
    if index < len(note):
        if note[index] == 'b':
            flat = True
            tone -= 1
            index += 1
        elif note[index] == '#':
            sharp = True
            tone += 1
            index += 1
    # octave:
    if index < len(note) and note[index] >= '0' and note[index] <= '9':
        octave = 0
        while index < len(note) and note[index] >= '0' and note[index] <= '9':
            octave *= 10
            octave += ord(note[index]) - ord('0')
            index += 1
    # remaining characters:
    if index < len(note):
        raise ValueError('invalid characters in note', note)
    # compute frequency:
    if (tone >= 3 and not sharp) or (tone == 2 and flat):
        octave -= 1
    tone += 12*(octave-4)
    # frequency:
    freq = a4freq * 2.0**(tone/12.0)
    return freq


def fade_in(data, rate, fadetime):
    """Fade in a signal in place.

    The first `fadetime` seconds of the data are multiplied with a
    squared sine in place. If `fadetime` is larger than half the
    duration of the data, then `fadetime` is reduced to half of the
    duration.
    
    Parameters
    ----------
    data: array
        The data to be faded in, either 1-D array for single channel output,
        or 2-D array with first axis time and second axis channel.
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading in in seconds.
    """
    if len(data) < 4:
        return
    nr = min(int(np.round(fadetime*rate)), len(data)//2) 
    x = np.arange(float(nr))/float(nr) # 0 to pi/2
    y = np.sin(0.5*np.pi*x)**2.0
    if data.ndim > 1:
        data[:nr, :] *= y[:, None]
    else:
        data[:nr] *= y

        
def fade_out(data, rate, fadetime):
    """Fade out a signal in place.

    The last `fadetime` seconds of the data are multiplied with a
    squared sine in place. If `fadetime` is larger than half the
    duration of the data, then `fadetime` is reduced to half of the
    duration.
    
    Parameters
    ----------
    data: array
        The data to be faded out, either 1-D array for single channel output,
        or 2-D array with first axis time and second axis channel.
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading out in seconds.
    """
    if len(data) < 4:
        return
    nr = min(int(np.round(fadetime*rate)), len(data)//2) 
    x = np.arange(float(nr))/float(nr) + 1.0 # pi/2 to pi
    y = np.sin(0.5*np.pi*x)**2.0
    if data.ndim > 1:
        data[-nr:, :] *= y[:, None]
    else:
        data[-nr:] *= y


def fade(data, rate, fadetime):
    """Fade in and out a signal in place.

    The first and last `fadetime` seconds of the data are multiplied
    with a squared sine in place. If `fadetime` is larger than half the
    duration of the data, then `fadetime` is reduced to half of the
    duration.
        
    Parameters
    ----------
    data: array
        The data to be faded, either 1-D array for single channel output,
        or 2-D array with first axis time and second axis channel.
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading in and out in seconds.
    """
    fade_in(data, rate, fadetime)
    fade_out(data, rate, fadetime)


class PlayAudio(object):
    """ Audio playback.

    Parameters
    ----------
    verbose: int
        Verbosity level.
    lib: string
        The library used for playback.

    Methods
    -------
    - `play(data, rate, scale=None, blocking=True)`: Playback audio data.
    - `beep(duration=0.5, frequency=880.0, amplitude=0.5, rate=44100.0, fadetime=0.05, blocking=True)`: Playback a pure tone.
    - `open()`: Initialize the PlayAudio class with the best module available.
    - `close()`: Terminate module for playing audio.
    - `stop()`:  Stop any playback in progress.

    Examples
    --------
    ```
    from audioio import PlayAudio
    
    with PlayAudio() as audio:
        audio.beep()
    ```
    or without context management:
    ```
    audio = PlayAudio()
    audio.beep(1.0, 'a4')
    audio.close()
    ```
    """
    
    def __init__(self, verbose=0):
        self.verbose = verbose
        self.handle = None
        self._do_play = self._play
        self.close = self._close
        self.stop = self._stop
        self.lib = None
        self.open()

    def _close(self):
        """Terminate PlayAudio class for playing audio."""
        self.handle = None
        self._do_play = self._play
        self.close = self._close
        self.stop = self._stop
        self.lib = None

    def _stop(self):
        """Stop any playback in progress."""
        pass

    def _play(self, blocking=True):
        """Default implementation of playing a sound: does nothing."""
        pass

    def play(self, data, rate, scale=None, blocking=True):
        """Playback audio data.

        Parameters
        ----------
        data: array
            The data to be played, either 1-D array for single channel output,
            or 2-D array with first axis time and second axis channel.
            Data values range between -1 and 1.
        rate: float
            The sampling rate in Hertz.
        scale: float
            Multiply data with scale before playing.
            If `None` scale it to the maximum value, if 1.0 do not scale.
        blocking: boolean
            If False do not block. 

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        FileNotFoundError
            No audio device for playback.
        """
        if self.handle is None:
            self.open()
        else:
            self.stop()
        self.rate = rate
        self.channels = 1
        if data.ndim > 1:
            self.channels = data.shape[1]
        # convert data:
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            scale = 1.0/np.max(np.abs(rawdata))
        rawdata *= scale
        self.data = np.floor(rawdata*(2**15-1)).astype(np.int16, order='C')
        self.index = 0
        self._do_play(blocking)

    def beep(self, duration=0.5, frequency=880.0, amplitude=0.5, rate=44100.0,
             fadetime=0.05, blocking=True):
        """Playback a pure tone.

        Parameters
        ----------
        duration: float
            The duration of the tone in seconds.
        frequency: float or string
            If float, the frequency of the tone in Hertz.
            If string, a musical note like 'f#5'.
            See `note2freq()` for details.
        amplitude: float
            The ampliude (volume) of the tone in the range from 0.0 to 1.0.
        rate: float
            The sampling rate in Hertz.
        fadetime: float
            Time for fading in and out in seconds.
        blocking: boolean
            If False do not block.

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        FileNotFoundError
            No audio device for playback.
        
        See also
        --------
        https://mail.python.org/pipermail/tutor/2012-September/091529.html
        for fourier series based construction of waveforms.  
        """
        # frequency
        if isinstance(frequency, str):
            frequency = note2freq(frequency)
        # sine wave:
        time = np.arange(0.0, duration, 1.0/rate)
        data = amplitude*np.sin(2.0*np.pi*frequency*time)
        # fade in and out:
        fade(data, rate, fadetime)
        # # final click for testing (mono only):
        # data = np.hstack((data, np.sin(2.0*np.pi*1000.0*time[0:int(np.ceil(4.0*rate/1000.0))])))
        # play:
        self.play(data, rate, scale=1.0, blocking=blocking)

    def _down_sample(self, channels, scale=1):
        """Sample the data down and adapt maximum channel number."""
        iscale = 1
        rscale = scale
        if isinstance(scale, int):
            iscale = scale
            rscale = 1.0
        elif scale > 2:
            iscale = int(np.floor(scale))
            rscale = scale/iscale
        
        if iscale > 1:
            data = decimate(self.data, iscale, axis=0)
            if self.data.ndim > 1:
                self.data = np.asarray(data[:,:channels],
                                       dtype=np.int16, order='C')
            else:
                self.data = np.asarray(data, dtype=np.int16, order='C')
            if self.verbose > 0:
                print(f'decimated sampling rate from {self.rate:.1f}Hz down to {self.rate/iscale:.1f}Hz')
            self.rate /= iscale

        if rscale != 1.0:
            dt0 = 1.0/self.rate
            dt1 = rscale/self.rate
            old_time = np.arange(len(self.data))*dt0
            new_time = np.arange(0.0, old_time[-1]+0.5*dt0, dt1)
            if self.data.ndim > 1:
                data = np.zeros((len(new_time), channels), order='C')
                for c in range(channels):
                    data[:,c] = np.interp(new_time, old_time, self.data[:,c])
            else:
                data = np.interp(new_time, old_time, self.data)
            self.data = np.asarray(data, dtype=self.data.dtype, order='C')
            if self.verbose > 0:
                print(f'adapted sampling rate from {self.rate:.1f}Hz to {self.rate/rscale:.1f}Hz')
            self.rate /= rscale
        self.channels = channels

    def __del__(self):
        """Terminate the audio module."""
        self.close()

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, tb):
        self.__del__()
        return value

            
    def open_pyaudio(self):
        """Initialize audio output via PyAudio module.

        Raises
        ------
        ImportError
            PyAudio module is not available.
        FileNotFoundError
            Failed to open audio device.

        Documentation
        -------------
        https://people.csail.mit.edu/hubert/pyaudio/
        http://www.portaudio.com/

        Installation
        ------------
        ```
        sudo apt install -y libportaudio2 portaudio19-dev python-pyaudio python3-pyaudio
        ```
        
        On Windows, download an appropriate (latest version, 32 or 64 bit) wheel from
        <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio>.  Install this file with pip,
        that is go to the folder where the wheel file is downloaded and run
        ```
        pip install PyAudio-0.2.11-cp39-cp39-win_amd64.whl
        ```
        replace the wheel file name by the one you downloaded.
        """
        if not audio_modules['pyaudio']:
            raise ImportError
        oldstderr = os.dup(2)
        os.close(2)
        tmpfile = 'tmpfile.tmp'
        os.open(tmpfile, os.O_WRONLY | os.O_CREAT)
        self.handle = pyaudio.PyAudio()
        self.stream = None
        os.close(2)
        os.dup(oldstderr)
        os.close(oldstderr)
        os.remove(tmpfile)
        try:
            info = self.handle.get_default_output_device_info()
            self.max_channels = info['maxOutputChannels']
            self.default_rate = info['defaultSampleRate']
            self.device_index = info['index']
            self.handle.is_format_supported(48000, output_device=self.device_index,
                                            output_channels=1, output_format=pyaudio.paInt16)
        except Exception as e:
            if self.verbose > 0:
                print(str(e))
            self.handle.terminate()
            self._close()
            raise FileNotFoundError('failed to initialize audio device')
        self.index = 0
        self.data = None
        self.close = self._close_pyaudio
        self.stop = self._stop_pyaudio
        self._do_play = self._play_pyaudio
        self.lib = 'pyaudio'
        return self

    def _callback_pyaudio(self, in_data, frames, time_info, status):
        """Callback for pyaudio for supplying output with data."""
        flag = pyaudio.paContinue
        if not self.run:
            flag = pyaudio.paComplete
        if self.index < len(self.data):
            out_data = self.data[self.index:self.index+frames]
            self.index += len(out_data)
            # zero padding:
            if len(out_data) < frames:
                if self.data.ndim > 1:
                    out_data = np.vstack((out_data,
                      np.zeros((frames-len(out_data), self.channels), dtype=np.int16)))
                else:
                    out_data = np.hstack((out_data, np.zeros(frames-len(out_data), dtype=np.int16)))
            return (out_data, flag)
        else:
            # we need to play more to make sure everything is played!
            # This is because of an ALSA bug and might be fixed in newer versions,
            # see http://music.columbia.edu/pipermail/portaudio/2012-May/013959.html
            out_data = np.zeros(frames*self.channels, dtype=np.int16)
            self.index += frames
            if self.index >= len(self.data) + 2*self.latency:
                flag = pyaudio.paComplete
            return (out_data, flag)

    def _stop_pyaudio(self):
        """Stop any ongoing activity of the pyaudio module."""
        if self.stream is not None:
            if self.stream.is_active():
                # fade out:
                fadetime = 0.1
                nr = int(np.round(fadetime*self.rate))
                index = self.index+nr
                if nr > len(self.data) - index:
                    nr = len(self.data) - index
                else:
                    self.data[index+nr:] = 0
                if nr > 0:
                    for k in range(nr) :
                        self.data[index+(nr-k-1)] = np.array(self.data[index+(nr-k-1)] *
                                np.sin(0.5*np.pi*float(k)/float(nr))**2.0, np.int16, order='C')
                try:
                    sleep(2*fadetime)
                except SystemError:
                    # pyaudio interferes with sleep in python 3.10
                    pass
            if self.stream.is_active():
                self.run = False
                while self.stream.is_active():
                    try:
                        sleep(0.01)
                    except SystemError:
                        # pyaudio interferes with sleep in python 3.10
                        pass
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _play_pyaudio(self, blocking=True):
        """Play audio data using the pyaudio module.

        Parameters
        ----------
        blocking: boolean
            If False do not block.

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        """
        # check channel count:
        channels = self.channels
        if self.channels > self.max_channels:
            channels = self.max_channels
        # check sampling rate:
        scale_fac = 1
        scaled_rate = self.rate
        max_rate = 48000.0
        if self.rate > max_rate:
            scale_fac = int(np.ceil(self.rate/max_rate))
            scaled_rate = int(self.rate//scale_fac)
        rates = [self.rate, scaled_rate, 44100, 48000, 22050, self.default_rate]
        scales = [1, scale_fac, None, None, None, None]
        success = False
        for rate, scale in zip(rates, scales):
            try:
                if self.handle.is_format_supported(int(rate),
                                                   output_device=self.device_index,
                                                   output_channels=channels,
                                                   output_format=pyaudio.paInt16):
                    if scale is None:
                        scale = self.rate/float(rate)
                    success = True
                    break
            except Exception as e:
                if self.verbose > 0:
                    print(f'invalid sampling rate of {rate}Hz')
                if e.args[1] != pyaudio.paInvalidSampleRate:
                    raise
        if not success:
            raise ValueError('No valid sampling rate found')
        if channels != self.channels or scale != 1:
            self._down_sample(channels, scale)
        
        # play:
        self.run = True
        self.stream = self.handle.open(format=pyaudio.paInt16, channels=self.channels,
                                        rate=int(self.rate), output=True,
                                        stream_callback=self._callback_pyaudio)
        self.latency = int(self.stream.get_output_latency()*self.rate)
        self.stream.start_stream()
        if blocking:
            while self.stream.is_active():
                try:
                    sleep(0.01)
                except (ValueError, SystemError):
                    # pyaudio interferes with sleep in python 3.10
                    pass
            self.run = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
    def _close_pyaudio(self):
        """Terminate pyaudio module."""
        self._stop_pyaudio()
        if self.handle is not None:
            self.handle.terminate()
        self._close()


    def open_sounddevice(self):
        """Initialize audio output via sounddevice module.

        Raises
        ------
        ImportError
            sounddevice module is not available.            
        FileNotFoundError
            Failed to open audio device.

        Documentation
        -------------
        https://python-sounddevice.readthedocs.io

        Installation
        ------------
        ```
        sudo apt install -y libportaudio2 portaudio19-dev
        sudo pip install sounddevice
        ```
        """
        if not audio_modules['sounddevice']:
            raise ImportError
        self.handle = True
        self.index = 0
        self.data = None
        self.stream = None
        try:
            self.device_index = sounddevice.default.device[1]
            info = sounddevice.query_devices(self.device_index)
            self.max_channels = info['max_output_channels']
            self.default_rate = info['default_samplerate']
            sounddevice.check_output_settings(device=self.device_index,
                                              channels=1, dtype=np.int16,
                                              samplerate=48000)
        except Exception as e:
            if self.verbose > 0:
                print(str(e))
            self._close()
            raise FileNotFoundError('failed to initialize audio device')
        self.close = self._close_sounddevice
        self.stop = self._stop_sounddevice
        self._do_play = self._play_sounddevice
        self.lib = 'sounddevice'
        return self

    def _callback_sounddevice(self, out_data, frames, time_info, status):
        """Callback for sounddevice for supplying output with data."""
        if status:
            print(status)
        if self.index < len(self.data):
            ndata = len(self.data) - self.index
            if ndata >= frames :
                if self.data.ndim <= 1:
                    out_data[:,0] = self.data[self.index:self.index+frames]
                else:
                    out_data[:, :] = self.data[self.index:self.index+frames, :]
                self.index += frames
            else:
                if self.data.ndim <= 1:
                    out_data[:ndata, 0] = self.data[self.index:]
                    out_data[ndata:, 0] = np.zeros(frames-ndata, dtype=np.int16)
                else:
                    out_data[:ndata, :] = self.data[self.index:, :]
                    out_data[ndata:, :] = np.zeros((frames-ndata, self.channels),
                                                   dtype=np.int16)
                self.index += frames
        else:
            # we need to play more to make sure everything is played!
            # This is because of an ALSA bug and might be fixed in newer versions,
            # see http://music.columbia.edu/pipermail/portaudio/2012-May/013959.html
            if self.data.ndim <= 1:
                out_data[:, 0] = np.zeros(frames, dtype=np.int16)
            else:
                out_data[:, :] = np.zeros((frames, self.channels), dtype=np.int16)
            self.index += frames
            if self.index >= len(self.data) + 2*self.latency:
                raise sounddevice.CallbackStop
        if not self.run:
            raise sounddevice.CallbackStop

    def _stop_sounddevice(self):
        """Stop any ongoing activity of the sounddevice module."""
        if self.stream is not None:
            if self.stream.active:
                # fade out:
                fadetime = 0.1
                nr = int(np.round(fadetime*self.rate))
                index = self.index+nr
                if nr > len(self.data) - index:
                    nr = len(self.data) - index
                else:
                    self.data[index+nr:] = 0
                if nr > 0:
                    for k in range(nr) :
                        self.data[index+(nr-k-1)] = np.array(self.data[index+(nr-k-1)] *
                                np.sin(0.5*np.pi*float(k)/float(nr))**2.0, np.int16, order='C')
                sounddevice.sleep(int(2000*fadetime))
            if self.stream.active:
                self.run = False
                while self.stream.active:
                    sounddevice.sleep(10)
                self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def _play_sounddevice(self, blocking=True):
        """Play audio data using the sounddevice module.

        Parameters
        ----------
        blocking: boolean
            If False do not block.

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        """
        # check channel count:
        channels = self.channels
        if self.channels > self.max_channels:
            channels = self.max_channels
        # check sampling rate:
        scale_fac = 1
        scaled_rate = self.rate
        max_rate = 48000.0
        if self.rate > max_rate:
            scale_fac = int(np.ceil(self.rate/max_rate))
            scaled_rate = int(self.rate//scale_fac)
        rates = [self.rate, scaled_rate, 44100, 48000, 22050, self.default_rate]
        scales = [1, scale_fac, None, None, None, None]
        success = False
        for rate, scale in zip(rates, scales):
            try:
                sounddevice.check_output_settings(device=self.device_index,
                                                  channels=channels,
                                                  dtype=np.int16,
                                                  samplerate=rate)
                if scale is None:
                    scale = self.rate/float(rate)
                success = True
                break
            except sounddevice.PortAudioError as pae:
                if pae.args[1] != -9997:
                    raise
                elif self.verbose > 0:
                    print(f'invalid sampling rate of {rate}Hz')
        if not success:
            raise ValueError('No valid sampling rate found')
        if channels != self.channels or scale != 1:
            self._down_sample(channels, scale)
        
        # play:
        self.stream = sounddevice.OutputStream(samplerate=self.rate,
                                               device=self.device_index,
                                               channels=self.channels,
                                               dtype=np.int16,
                                               callback=self._callback_sounddevice)
        self.latency = self.stream.latency*self.rate
        self.run = True
        self.stream.start()
        if blocking:
            while self.stream.active:
                sounddevice.sleep(10)
            self.run = False
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
    def _close_sounddevice(self):
        """Terminate sounddevice module."""
        self._stop_sounddevice()
        self._close()

        
    def open_simpleaudio(self):
        """Initialize audio output via simpleaudio package.

        Raises
        ------
        ImportError
            simpleaudio module is not available.

        Documentation
        -------------
        https://simpleaudio.readthedocs.io
        """
        if not audio_modules['simpleaudio']:
            raise ImportError
        self.handle = True
        self._do_play = self._play_simpleaudio
        self.close = self._close_simpleaudio
        self.stop = self._stop_simpleaudio
        self.lib = 'simpleaudio'
        return self

    def _stop_simpleaudio(self):
        """Stop any ongoing activity of the simpleaudio package."""
        if self.handle is not None and self.handle is not True:
            self.handle.stop()
    
    def _play_simpleaudio(self, blocking=True):
        """Play audio data using the simpleaudio package.

        Parameters
        ----------
        blocking: boolean
            If False do not block. 

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        FileNotFoundError
            No audio device for playback.
        """
        rates = [self.rate, 44100, 48000, 22050]
        scales = [1, None, None, None]
        success = False
        for rate, scale in zip(rates, scales):
            if scale is None:
                scale = self.rate/float(rate)
            if scale != 1:
                self._down_sample(self.channels, scale)
            try:
                self.handle = simpleaudio.play_buffer(self.data, self.channels,
                                                      2, int(self.rate))
                success = True
                break
            except ValueError as e:
                if self.verbose > 0:
                    print(f'invalid sampling rate of {rate}Hz')
            except simpleaudio._simpleaudio.SimpleaudioError as e:
                if self.verbose > 0:
                    print('simpleaudio SimpleaudioError:', str(e))
                if 'Error opening' in str(e):
                    raise FileNotFoundError('No audio device found')
            except Exception as e:
                if self.verbose > 0:
                    print('simpleaudio Exception:', str(e))
        if not success:
            raise ValueError('No valid sampling rate found')
        elif blocking:
            self.handle.wait_done()
        
    def _close_simpleaudio(self):
        """Close audio output using simpleaudio package."""
        self._stop_simpleaudio()
        simpleaudio.stop_all()
        self._close()

        
    def open_soundcard(self):
        """Initialize audio output via soundcard package.

        Raises
        ------
        ImportError
            soundcard module is not available.
        FileNotFoundError
            Failed to open audio device.

        Documentation
        -------------
        https://github.com/bastibe/SoundCard
        """
        if not audio_modules['soundcard']:
            raise ImportError
        try:
            self.handle = soundcard.default_speaker()
        except IndexError:
            raise FileNotFoundError('No audio device found')
        except Exception as e:
            print('soundcard Exception:', type(e).__name__, str(e))
        if self.handle is None:
            raise FileNotFoundError('No audio device found')
        self._do_play = self._play_soundcard
        self.close = self._close_soundcard
        self.stop = self._stop_soundcard
        self.lib = 'soundcard'
        return self

    def _stop_soundcard(self):
        """Stop any ongoing activity of the soundcard package."""
        pass
    
    def _play_soundcard(self, blocking=True):
        """Play audio data using the soundcard package.

        Parameters
        ----------
        blocking: boolean
            If False do not block.
            Non-blocking playback not supported by soundcard.
            Return immediately without playing sound.

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).
        """
        if not blocking:
            warnings.warn('soundcard module does not support non-blocking playback')
            return
        rates = [self.rate, 44100, 48000, 22050]
        scales = [1, None, None, None]
        success = False
        for rate, scale in zip(rates, scales):
            if scale is None:
                scale = self.rate/float(rate)
            if scale != 1:
                self._down_sample(self.channels, scale)
            try:
                self.handle.play(self.data, samplerate=int(self.rate))
                success = True
                break
            except RuntimeError as e:
                if 'invalid sample spec' in str(e):
                    if self.verbose > 0:
                        print(f'invalid sampling rate of {rate}Hz')
                else:
                    if self.verbose > 0:
                        print('soundcard error:', type(e).__name__, str(e))
            except Exception as e:
                if self.verbose > 0:
                    print('soundcard error:', type(e).__name__, str(e))
        if not success:
            raise ValueError('No valid sampling rate found')
    
    def _close_soundcard(self):
        """Close audio output using soundcard package."""
        self._stop_soundcard()
        self._close()

                
    def open_ossaudiodev(self):
        """Initialize audio output via ossaudiodev module.

        The OSS audio module is part of the python standard library.

        Raises
        ------
        ImportError
            ossaudiodev module is not available.
        FileNotFoundError
            Failed to open audio device.

        Documentation
        -------------
        https://docs.python.org/2/library/ossaudiodev.html

        Installation
        ------------
        The ossaudiodev module needs an oss `/dev/dsp` device file.
        Enable an oss emulation via alsa by installing
        ```
        sudo apt install -y osspd
        ```
        """
        if not audio_modules['ossaudiodev']:
            raise ImportError
        self.handle = True
        self.osshandle = None
        self.run = False
        self.play_thread = None
        try:
            handle = ossaudiodev.open('w')
            handle.close()
        except Exception as e:
            if self.verbose > 0:
                print(str(e))
            self._close()
            raise FileNotFoundError('failed to initialize audio device')
        self.close = self._close_ossaudiodev
        self.stop = self._stop_ossaudiodev
        self._do_play = self._play_ossaudiodev
        self.lib = 'ossaudiodev'
        return self

    def _stop_ossaudiodev(self):
        """Stop any ongoing activity of the ossaudiodev module."""
        if self.osshandle is not None:
            self.run = False
            self.osshandle.reset()
            if self.play_thread is not None:
                if self.play_thread.is_alive():
                    self.play_thread.join()
                self.play_thread = None
            self.osshandle.close()
            self.osshandle = None

    def _run_play_ossaudiodev(self):
        """Play the data using the ossaudiodev module."""
        self.osshandle.writeall(self.data)
        if self.run:
            sleep(0.5)
            self.osshandle.close()
            self.osshandle = None
            self.run = False
        
    def _play_ossaudiodev(self, blocking=True):
        """Play audio data using the ossaudiodev module.

        Raises
        ------
        ValueError
            Invalid sampling rate (after some attemps of resampling).

        Parameters
        ----------
        blocking: boolean
            If False do not block. 
        """
        self.osshandle = ossaudiodev.open('w')
        self.osshandle.setfmt(ossaudiodev.AFMT_S16_LE)
        # set and check channel count:
        channels = self.osshandle.channels(self.channels)
        # check sampling rate:
        scale_fac = 1
        scaled_rate = self.rate
        max_rate = 48000.0
        if self.rate > max_rate:
            scale_fac = int(np.ceil(self.rate/max_rate))
            scaled_rate = int(self.rate//scale_fac)
        rates = [self.rate, scaled_rate, 44100, 48000, 22050, 8000]
        scales = [1, scale_fac, None, None, None, None]
        success = False
        for rate, scale in zip(rates, scales):
            set_rate = self.osshandle.speed(int(rate))
            if abs(set_rate - rate) < 2:
                if scale is None:
                    scale = self.rate/float(set_rate)
                success = True
                break
            else:
                if self.verbose > 0:
                    print(f'invalid sampling rate of {rate}Hz')
        if not success:
            raise ValueError('No valid sampling rate found')
        if channels != self.channels or scale != 1:
            self._down_sample(channels, scale)
        if blocking:
            self.run = True
            self.osshandle.writeall(self.data)
            sleep(0.5)
            self.osshandle.close()
            self.run = False
            self.osshandle = None
        else:
            self.play_thread = Process(target=self._run_play_ossaudiodev)
            self.run = True
            self.play_thread.start()

    def _close_ossaudiodev(self):
        """Close audio output using ossaudiodev module."""
        self._stop_ossaudiodev()
        self._close()

        
    def open_winsound(self):
        """Initialize audio output via winsound module.

        The winsound module is part of the python standard library.

        Raises
        ------
        ImportError
            winsound module is not available.

        Documentation
        -------------
        https://docs.python.org/3.6/library/winsound.html
        https://mail.python.org/pipermail/tutor/2012-September/091529.html
        """
        if not audio_modules['winsound'] or not audio_modules['wave']:
            raise ImportError
        self.handle = True
        self._do_play = self._play_winsound
        self.close = self._close_winsound
        self.stop = self._stop_winsound
        self.audio_file = ''
        self.lib = 'winsound'
        return self

    def _stop_winsound(self):
        """Stop any ongoing activity of the winsound module."""
        try:
            winsound.PlaySound(None, winsound.SND_MEMORY)
        except Exception as e:
            pass
        
    def _play_winsound(self, blocking=True):
        """Play audio data using the winsound module.

        Parameters
        ----------
        blocking: boolean
            If False do not block. 
        """
        # play file:
        if blocking:
            # write data as wav file to memory:
            self.data_buffer = BytesIO()
            w = wave.open(self.data_buffer, 'w')
            w.setnchannels(self.channels)
            w.setsampwidth(2)
            w.setframerate(int(self.rate))
            w.setnframes(len(self.data))
            try:
                w.writeframes(self.data.tobytes())
            except AttributeError:
                w.writeframes(self.data.tostring())
            w.close()
            try:
                winsound.PlaySound(self.data_buffer.getvalue(), winsound.SND_MEMORY)
            except Exception as e:
                if self.verbose > 0:
                    print(str(e))
                return
        else:
            if self.verbose > 0:
                print('Warning: asynchronous playback is limited to playing wav files by the winsound module. Install an alternative package as recommended by the audiomodules script. ')
            # write data as wav file to file:
            self.audio_file = 'audioio-async_playback.wav'
            w = wave.open(self.audio_file, 'w')
            w.setnchannels(self.channels)
            w.setsampwidth(2)
            w.setframerate(int(self.rate))
            w.setnframes(len(self.data))
            try:
                w.writeframes(self.data.tobytes())
            except AttributeError:
                w.writeframes(self.data.tostring())
            w.close()
            try:
                winsound.PlaySound(self.audio_file, winsound.SND_ASYNC)
            except Exception as e:
                if self.verbose > 0:
                    print(str(e))
                return
        
    def _close_winsound(self):
        """Close audio output using winsound module."""
        self._stop_winsound()
        self.handle = None
        if len(self.audio_file) > 0 and os.path.isfile(self.audio_file):
            os.remove(self.audio_file)
        self._close()


    def open(self):
        """Initialize the PlayAudio class with the best module available."""
        # list of implemented play functions:
        audio_open = [
            ['sounddevice', self.open_sounddevice],
            ['pyaudio', self.open_pyaudio],
            ['simpleaudio', self.open_simpleaudio],
            ['soundcard', self.open_soundcard],
            ['ossaudiodev', self.open_ossaudiodev],
            ['winsound', self.open_winsound]
            ]
        if platform[0:3] == "win":
            sa = audio_open.pop(2)
            audio_open.insert(0, sa)
        # open audio device by trying various modules:
        success = False
        for lib, open_device in audio_open:
            if not audio_modules[lib]:
                if self.verbose > 0:
                    print(f'module {lib} not available')
                continue
            try:
                open_device()
                success = True
                if self.verbose > 0:
                    print(f'successfully opened {lib} module for playing')
                break
            except Exception as e:
                if self.verbose > 0:
                    print(f'failed to open {lib} module for playing:',
                          type(e).__name__, str(e))
        if not success:
            warnings.warn('cannot open any device for audio output')
        return self


def play(data, rate, scale=None, blocking=True, verbose=0):
    """Playback audio data.

    Create a `PlayAudio` instance on the global variable `handle`.

    Parameters
    ----------
    data: array
        The data to be played, either 1-D array for single channel output,
        or 2-D array with first axis time and second axis channel.
        Data values range between -1 and 1.
    rate: float
        The sampling rate in Hertz.
    scale: float
        Multiply data with scale before playing.
        If `None` scale it to the maximum value, if 1.0 do not scale.
    blocking: boolean
        If False do not block. 
    verbose: int
        Verbosity level. 
    """
    global handle
    if handle is None:
        handle = PlayAudio(verbose)
    handle.verbose = verbose
    handle.play(data, rate, scale, blocking)

    
def beep(duration=0.5, frequency=880.0, amplitude=0.5, rate=44100.0,
         fadetime=0.05, blocking=True, verbose=0):
    """Playback a tone.

    Create a `PlayAudio` instance on the global variable `handle`.

    Parameters
    ----------
    duration: float
        The duration of the tone in seconds.
    frequency: float or string
        If float the frequency of the tone in Hertz.
        If string, a musical note like 'f#5'.
        See `note2freq()` for details
    amplitude: float
        The ampliude (volume) of the tone from 0.0 to 1.0.
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading in and out in seconds.
    blocking: boolean
        If False do not block.
    verbose: int
        Verbosity level. 
    """
    global handle
    if handle is None:
        handle = PlayAudio(verbose)
    handle.verbose = verbose
    handle.beep(duration, frequency, amplitude, rate, fadetime, blocking)


def close():
    """Close the global PlayAudio instance.
    """
    global handle
    if handle is not None:
        handle.close()
        handle = None


def demo():
    """ Demonstrate the playaudio module."""
    print('play mono beep 1')
    audio = PlayAudio(verbose=2)
    audio.beep(1.0, 440.0)
    audio.close()
    
    print('play mono beep 2')
    with PlayAudio() as audio:
        audio.beep(1.0, 'b4', 0.75, blocking=False)
        print('  done')
        sleep(0.3)
    sleep(0.5)

    print('play mono beep 3')
    beep(1.0, 'c5', 0.25, blocking=False)
    print('  done')
    sleep(0.5)
            
    print('play stereo beep')
    duration = 1.0
    rate = 44100.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.zeros((len(t),2))
    data[:,0] = np.sin(2.0*np.pi*note2freq('a4')*t)
    data[:,1] = 0.25*np.sin(2.0*np.pi*note2freq('e5')*t)
    fade(data, rate, 0.1)
    play(data, rate, verbose=2)


def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    help = False
    mod = False
    for arg in args:
        if mod:
            if not select_module(arg):
                print(f'module {arg} not installed. Exit!')
                return
            mod = False
        elif arg == '-h':
            help = True
            break
        elif arg == '-m':
            mod = True
        else:
            break

    if help:
        print('')
        print('Usage:')
        print('  python -m src.audioio.playaudio [-m <module>]')
        print('  -m: audio module to be used')
        return
        
    demo()

            
if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
