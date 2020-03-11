"""
Play numpy arrays as audio.

The globally defined functions
```
play(data, rate)
beep(duration, frequeny)
```
use a global instance of the `PlayAudio` class to play a sound
on the default audio output.

Alternatively you may use the `PlayAudio` class directly, like this:
```
with open_audio_player() as audio:
    audio.beep(1.0, 440.0)
```
or without context management:
```
audio = PlayAudio()
audio.beep(1.0, 'a4')
audio.close()
```
The `note2freq()` function converts a musical note, like 'f#4',
to the corresponding frequency.
The `beep()` functions also accept notes for the frequency argument,
and uses `note2freq()` to get the right frequency.

Data can be multiplied with a squared-sine for fading in and out with
`fade_in()`, `fade_out()`, and `fade()`.

For a demo, run the script as:
```
python -m audioio.playaudio
```

See also:
https://wiki.python.org/moin/Audio/
https://docs.python.org/3/library/mm.html

The modules supports the standard modules `ossaudiodev` for Linux and `winsound` for Windows.
However, we recommend to install the `portaudio` library and the `pyaudio` module for
better performance.

On Linux do:
```
sudo apt-get install -y libportaudio2 portaudio19-dev python-pyaudio python3-pyaudio
```
"""

import os
import warnings
import time
import numpy as np
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from multiprocessing import Process
from .audiomodules import *


# default audio device handler:
handle = None


def note2freq(note, a4freq=440.0):
    """Converts textual note to the corresponding frequency.

    Parameters
    ----------
    note: string
        A musical note like 'a4', 'f#3', 'eb5'.
        The first character is the note, it can be
        'a', 'b', 'c', 'd', 'e', 'f', or 'g'.
        The optional second character is either a 'b'
        or a '#' to decrease or increase by half a note.
        The last character specifies the octave.
        'a4' is defined by a4freq.
    a4freq: float
        The frequency of a4.

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
    if note[0] < 'a' or note[0] > 'g':
        raise ValueError('invalid note %s' % note[0])
    # note:
    index = 0
    tonemap = [0, 2, 3, 5, 7, 8, 10]
    tone = tonemap[ord(note[index]) - ord('a')]
    index += 1
    # flat or sharp:
    if index < len(note):
        if note[index] == 'b':
            tone -= 1
            index += 1
        elif note[index] == '#':
            tone += 1
            index += 1
    # octave:
    if index < len(note) and note[index] >= '0' and note[index] <= '9':
        octave = 0
        while index < len(note) and note[index] >= '0' and note[index] <= '9':
            octave *= 10
            octave += ord(note[index]) - ord('0')
            index += 1
    if tone >= 3:
        octave -= 1
    tone += 12*(octave-4)
    # frequency:
    freq = a4freq * 2.0**(tone/12.0)
    return freq


def fade_in(data, rate, fadetime):
    """
    Fade the signal in.

    The first fadetime seconds of the data are multiplied with a squared sine.
    
    Parameters
    ----------
    data: array
        The data to be faded in, either 1-D array for single channel output,
        or 2-day array with first axis time and second axis channel 
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading in in seconds.
    """
    nr = int(np.round(fadetime*rate))
    x = np.arange(float(nr))/float(nr) # 0 to pi/2
    y = np.sin(0.5*np.pi*x)**2.0
    if len(data.shape) > 1:
        data[:nr, :] *= y[:, None]
    else:
        data[:nr] *= y

        
def fade_out(data, rate, fadetime):
    """
    Fade the signal out.

    The last fadetime seconds of the data are multiplied with a squared sine.
    
    Parameters
    ----------
    data: array
        The data to be faded out, either 1-D array for single channel output,
        or 2-day array with first axis time and second axis channel 
    rate: float
        The sampling rate in Hertz
    fadetime: float
        Time for fading out in seconds
    """
    nr = int(np.round(fadetime*rate))
    x = np.arange(float(nr))/float(nr) + 1.0 # pi/2 to pi
    y = np.sin(0.5*np.pi*x)**2.0
    if len(data.shape) > 1:
        data[-nr:, :] *= y[:, None]
    else:
        data[-nr:] *= y


def fade(data, rate, fadetime):
    """
    Fade the signal in and out.

    The first and last fadetime seconds of the data are multiplied with a squared sine.
        
    Parameters
    ----------
    data: array
        The data to be faded, either 1-D array for single channel output,
        or 2-day array with first axis time and second axis channel .
    rate: float
        The sampling rate in Hertz.
    fadetime: float
        Time for fading in and out in seconds.
    """
    fade_in(data, rate, fadetime)
    fade_out(data, rate, fadetime)


class PlayAudio(object):
    
    def __init__(self, verbose=0):
        """Initialize module for playing audio.

        Parameters
        ----------
        verbose: int
            Verbosity level.
        """
        self.verbose = verbose
        self.handle = None
        self._do_play = self._play
        self.close = self._close
        self.stop = self._stop
        self.open()

    def _close(self):
        """Terminate module for playing audio."""
        pass

    def _stop(self):
        """Stop playing."""
        pass

    def _play(self, blocking=True):
        """Default implementation of playing a sound: does nothing."""
        pass

    def play(self, data, rate, scale=None, blocking=True):
        """Play audio data.

        Parameters
        ----------
        data: array
            The data to be played, either 1-D array for single channel output,
            or 2-day array with first axis time and second axis channel.
        rate: float
            The sampling rate in Hertz.
        scale: float
            Multiply data with scale before playing.
            If None scale it to the maximum value, if 1.0 do not scale.
        blocking: boolean
            If False do not block. 

        Raises
        ------
        ValueError: Invalid sampling rate (after some attemps of resampling).
        """
        if self.handle is None:
            self.open()
        else:
            self.stop()
        self.rate = rate
        self.channels = 1
        if len(data.shape) > 1:
            self.channels = data.shape[1]
        # convert data:
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            maxd = np.abs(np.max(rawdata))
            mind = np.abs(np.min(rawdata))
            scale = 1.0/max((mind, maxd))
        rawdata *= scale
        self.data = np.floor(rawdata*(2**15-1)).astype(np.int16)
        self.index = 0
        self._do_play(blocking)

    def beep(self, duration, frequency, amplitude=1.0, rate=44100.0,
             fadetime=0.05, blocking=True):
        """Play a pure tone of a given duration and frequency.

        Parameters
        ----------
        duration: float
            The duration of the tone in seconds.
        frequency: float or string
            If float, the frequency of the tone in Hertz.
            If string, a musical note like 'f#5'.
            See note2freq() for details.
        amplitude: float
            The ampliude of the tone in the range from 0.0 to 1.0.
        rate: float
            The sampling rate in Hertz.
        fadetime: float
            Time for fading in and out in seconds.
        blocking: boolean
            If False do not block.

        Raises
        ------
        ValueError: Invalid sampling rate (after some attemps of resampling).
        
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
        if type(scale) == int:
            if len(self.data.shape) > 1:
                self.data = np.asarray(self.data[::scale, :channels], order='C')
            else:
                self.data = np.asarray(self.data[::scale], order='C')
        else:
            dt0 = 1.0/self.rate
            dt1 = scale/self.rate
            t1 = (len(self.data)+0.5)*dt0
            new_time = np.arange(0.0, t1, dt1)
            old_time = np.arange(0.0, t1, dt0)
            if len(self.data.shape) > 1:
                data = np.zeros((len(newtime), channels))
                for c in range(channels):
                    data[:, c] = np.interp(new_time, old_time, self.data[:, c])
                self.data = data
            else:
                self.data = np.interp(new_time, old_time, self.data)
        if self.verbose:
            print('adapted sampling rate from %g Hz down to %g Hz' %
                  (self.rate, self.rate/scale))
        self.rate /= scale
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
        """Initialize audio output via pyaudio module.

        Raises
        ------
        ImportError: pyaudio module is not available.            

        Documentation
        -------------
        https://people.csail.mit.edu/hubert/pyaudio/

        Installation
        ------------
        ```
        sudo apt-get install -y libportaudio2 portaudio19-dev python-pyaudio python3-pyaudio
        ```
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
        self.index = 0
        self.data = None
        self._do_play = self._play_pyaudio
        self.close = self._close_pyaudio
        self.stop = self._stop_pyaudio
        info = self.handle.get_default_output_device_info()
        self.max_channels = info['maxOutputChannels']
        self.default_rate = info['defaultSampleRate']
        self.device_index = info['index']
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
                if len(self.data.shape) > 1:
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
                        self.data[index+(nr-k-1)] *= np.sin(0.5*np.pi*float(k)/float(nr))**2.0
                time.sleep(2*fadetime)
            if self.stream.is_active():
                self.run = False
                while self.stream.is_active():
                    time.sleep(0.01)
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
        ValueError: Invalid sampling rate (after some attemps of resampling).
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
        rates = [self.rate, scaled_rate, 44100, 22050, self.default_rate]
        scales = [1, scale_fac, None, None, None]
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
                    print('invalid sampling rate of %g Hz' % rate)
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
                time.sleep(0.01)
            self.run = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
    def _close_pyaudio(self):
        """Terminate pyaudio module."""
        self._stop_pyaudio()
        if self.handle is not None:
            self.handle.terminate()
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop


    def open_sounddevice(self):
        """Initialize audio output via sounddevice module.

        Raises
        ------
        ImportError: sounddevice module is not available.            

        Documentation
        -------------
        https://python-sounddevice.readthedocs.io

        Installation
        ------------
        ```
        sudo apt-get install -y libportaudio2 portaudio19-dev
        sudo pip install sounddevice
        ```
        """
        if not audio_modules['sounddevice']:
            raise ImportError
        self.handle = True
        self.index = 0
        self.data = None
        self._do_play = self._play_sounddevice
        self.close = self._close_sounddevice
        self.stop = self._stop_sounddevice
        self.device_index = sounddevice.default.device[1]
        info = sounddevice.query_devices(self.device_index)
        self.max_channels = info['max_output_channels']
        self.default_rate = info['default_samplerate']
        self.stream = None
        return self

    def _callback_sounddevice(self, out_data, frames, time_info, status):
        """Callback for sounddevice for supplying output with data."""
        if status:
            print(status)
        if self.index < len(self.data):
            ndata = len(self.data) - self.index
            if ndata >= frames :
                if len(self.data.shape) <= 1:
                    out_data[:,0] = self.data[self.index:self.index+frames]
                else:
                    out_data[:, :] = self.data[self.index:self.index+frames, :]
                self.index += frames
            else:
                if len(self.data.shape) <= 1:
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
            if len(self.data.shape) <= 1:
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
                        self.data[index+(nr-k-1)] *= np.sin(0.5*np.pi*float(k)/float(nr))**2.0
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
        ValueError: Invalid sampling rate (after some attemps of resampling).
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
        rates = [self.rate, scaled_rate, 44100, 22050, self.default_rate]
        scales = [1, scale_fac, None, None, None]
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
                if pae[1] != -9997:
                    raise
                elif self.verbose > 0:
                    print('invalid sampling rate of %g Hz' % rate)
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
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop


    def open_ossaudiodev(self):
        """Initialize audio output via ossaudiodev module.

        The OSS audio module is part of the python standard library.

        Raises
        ------
        ImportError: ossaudiodev module is not available.

        Documentation
        -------------
        https://docs.python.org/2/library/ossaudiodev.html

        Installation
        ------------
        The ossaudiodev module needs an oss `/dev/dsp` device file.
        Enable an oss emulation via alsa by installing
        ```
        sudo apt-get install -y osspd
        ```
        """
        if not audio_modules['ossaudiodev']:
            raise ImportError
        handle = ossaudiodev.open('w')
        handle.close()
        self.handle = True
        self.osshandle = None
        self.run = False
        self.play_thread = None
        self._do_play = self._play_ossaudiodev
        self.close = self._close_ossaudiodev
        self.stop = self._stop_ossaudiodev
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
            time.sleep(0.5)
            self.osshandle.close()
            self.osshandle = None
            self.run = False
        
    def _play_ossaudiodev(self, blocking=True):
        """
        Play audio data using the ossaudiodev module.

        Raises
        ------
        ValueError: Invalid sampling rate (after some attemps of resampling).

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
        rates = [self.rate, scaled_rate, 44100, 22050, 8000]
        scales = [1, scale_fac, None, None, None]
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
                    print('invalid sampling rate of %g Hz' % rate)
        if not success:
            raise ValueError('No valid sampling rate found')
        if channels != self.channels or scale != 1:
            self._down_sample(channels, scale)
        if blocking:
            self.run = True
            self.osshandle.writeall(self.data)
            time.sleep(0.5)
            self.osshandle.close()
            self.run = False
            self.osshandle = None
        else:
            self.play_thread = Process(target=self._run_play_ossaudiodev)
            self.run = True
            self.play_thread.start()

    def _close_ossaudiodev(self):
        """Close audio output using ossaudiodev module. """
        self._stop_ossaudiodev()
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop

        
    def open_winsound(self):
        """Initialize audio output via winsound module.

        The winsound module is part of the python standard library.

        Raises
        ------
        ImportError: winsound module is not available.

        Documentation
        -------------
        https://docs.python.org/2/library/winsound.html
        https://mail.python.org/pipermail/tutor/2012-September/091529.html
        """
        if not audio_modules['winsound'] or not not audio_modules['wave']:
            raise ImportError
        self.handle = True
        self._do_play = self._play_winsound
        self.close = self._close_winsound
        self.stop = self._stop_winsound
        return self

    def _stop_winsound(self):
        """Stop any ongoing activity of the winsound module."""
        winsound.PlaySound(None, winsound.SND_MEMORY)
    
    
    def _play_winsound(self, blocking=True):
        """
        Play audio data using the winsound module.

        Parameters
        ----------
        blocking: boolean
            If False do not block. 
        """
        # write data as wav file to memory:
        # TODO: check this code!!!
        self.data_buffer = StringIO()
        w = wave.open(self.data_buffer, 'w')
        w.setnchannels(self.channels)
        w.setsampwidth(2)
        w.setframerate(int(self.rate))
        w.setnframes(len(self.data))
        w.writeframesraw(self.data.tostring())
        w.close() # TODO: close here or after PlaySound?
        # play file:
        if blocking:
            winsound.PlaySound(self.data_buffer.getvalue(), winsound.SND_MEMORY)
        else:
            winsound.PlaySound(self.data_buffer.getvalue(),
                               winsound.SND_MEMORY | winsound.SND_ASYNC)
        
    def _close_winsound(self):
        """Close audio output using winsound module. """
        self._stop_winsound()
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop


    def open(self):
        """Initialize the audio module with the best module available."""
        # list of implemented play functions:
        audio_open = [
            ['pyaudio', self.open_pyaudio],
            ['sounddevice', self.open_sounddevice],
            ['ossaudiodev', self.open_ossaudiodev],
            ['winsound', self.open_winsound]
            ]
        # open audio device by trying various modules:
        success = False
        for lib, open_device in audio_open:
            if not audio_modules[lib]:
                if self.verbose > 0:
                    print('module %s not available' % lib)
                continue
            try:
                open_device()
                success = True
                if self.verbose > 0:
                    print('successfully opened %s module for playing' % lib)
                break
            except Exception as e:
                if self.verbose > 0:
                    print('failed to open %s module for playing' % lib)
        if not success:
            warnings.warn('cannot open any device for audio output')
        return self


open_audio_player = PlayAudio
                

def play(data, rate, scale=None, blocking=True, verbose=0):
    """Play audio data.

    Create an PlayAudio instance on the global variable handle.

    Parameters
    ----------
    data: array
        The data to be played, either 1-D array for single channel output,
        or 2-day array with first axis time and second axis channel.
    rate: float
        The sampling rate in Hertz.
    scale: float
        Multiply data with scale before playing.
        If None scale it to the maximum value, if 1.0 do not scale.
    blocking: boolean
        If False do not block. 
    verbose: int
        Verbosity level. 
    """
    global handle
    if handle is None:
        handle = PlayAudio(verbose)
    handle.play(data, rate, scale, blocking)

    
def beep(duration, frequency, amplitude=1.0, rate=44100.0,
         fadetime=0.05, blocking=True, verbose=0):
    """
    Play a tone of a given duration and frequency.

    Create an PlayAudio instance on the globale variable handle.

    Parameters
    ----------
    duration: float
        The duration of the tone in seconds.
    frequency: float or string
        If float the frequency of the tone in Hertz.
        If string, a musical note like 'f#5'.
        See note2freq() for details
    amplitude: float
        The ampliude of the tone from 0.0 to 1.0.
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
    handle.beep(duration, frequency, amplitude, rate, fadetime, blocking)

    
if __name__ == "__main__":
    print('play mono beep 1')
    audio = PlayAudio()
    audio.beep(1.0, 440.0)
    audio.close()
    
    print('play mono beep 2')
    with open_audio_player() as audio:
        audio.beep(1.0, 'b4', 0.75, blocking=False)
        print('  done')
        time.sleep(0.3)
    time.sleep(0.5)

    print('play mono beep 3')
    beep(1.0, 'c5', 0.25, blocking=False)
    print('  done')
    time.sleep(0.5)
            
    print('play stereo beep')
    duration = 1.0
    rate = 44100.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.zeros((len(t),2))
    data[:,0] = np.sin(2.0*np.pi*note2freq('a4')*t)
    data[:,1] = 0.25*np.sin(2.0*np.pi*note2freq('e5')*t)
    fade(data, rate, 0.1)
    play(data, rate)

    exit()

    print('play notes')
    o = 6
    for oo in range(4):
        for t in range(7):
            if t == 2:
                o += 1
            tone = '%s%d' % (chr(ord('a')+t), o)
            print('%-3s %7.1f Hz' % (tone, note2freq(tone)))
            beep(0.5, tone)
