import pytest
import os
import numpy as np

from pathlib import Path

import audioio.audiowriter as aw
import audioio.audioloader as al
import audioio.audiometadata as amd
import audioio.audiomodules as am


def test_formats_encodings():
    am.enable_module()
    min_formats = {'wave': 1, 'ewave': 2, 'scipy.io.wavfile': 1,
                   'soundfile': 23, 'wavefile': 6, 'wavpack': 1, 'pydub': 10}
    for (module, formats_func), (m, encodings_func) in zip(aw.audio_formats_funcs, aw.audio_encodings_funcs):
        if aw.audio_modules[module]:
            min_f = min_formats[module]
            formats = formats_func()
            assert len(formats) >= min_f, 'formats_%s() did not return enough formats' % module.split('.')[-1]
            for f in formats:
                encodings = encodings_func(f)
                assert len(encodings) >= 1, 'encodings_%s() did not return enough encodings for format %s' % (module.split('.')[-1], f)
            encodings = encodings_func('xxx')
            assert len(encodings) == 0, 'encodings_%s() returned encodings for invalid format xxx' % module.split('.')[-1]
            encodings = encodings_func('')
            assert len(encodings) == 0, 'encodings_%s() returned encodings for empty format xxx' % module.split('.')[-1]

    formats = aw.available_formats()
    assert len(formats) >= 1, 'available_formats() did not return enough formats'
    for f in formats:
        encodings = aw.available_encodings(f)
        assert len(encodings) >= 1, 'available_encodings() did not return enough encodings for format %s' % f

        
def test_write_read():

    def check(rate_write, data_write, rate_read, data_read, lib, encoding):
        assert rate_write == pytest.approx(rate_read), 'rates differ for module %s with encoding %s' % (lib, encoding)
        assert len(data_write) == len(data_read), 'frames %d %d differ for module %s with encoding %s' % (len(data_write), len(data_read), lib, encoding)
        assert len(data_read.shape) == 2, 'shape differs from 2 for module %s with encoding %s' % (lib, encoding)
        chs = data_write.shape[1] if len(data_write.shape) > 1 else 1
        assert data_read.shape[1] == chs, f'read in data must be a 2-D array with {chs} columns'
        assert data_write.shape[0] == data_read.shape[0], 'shape[0] differs for module %s with encoding %s' % (lib, encoding)
        assert data_read.dtype == np.float64, 'read in data are not doubles for module %s with encoding %s' % (lib, encoding)
        if data_write.ndim == 1:
            data_write = data_write.reshape((-1, 1))
        print(data_write.shape, data_read.shape)
        n = min([len(data_write), len(data_read)])
        max_error = np.max(np.abs(data_write[:n] - data_read[:n]))
        print('maximum error = %g' % max_error)
        assert max_error < 0.05, 'values differ for module %s with encoding %s by up to %g' % (lib, encoding, max_error)
        
    am.enable_module()
    # generate data:
    rate = 44100.0
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration

    # modules, formats, and encodings:
    write_modules = am.installed_modules('fileio') + ['audioio']
    write_modules.remove('audioread')
    read_modules = list(write_modules)
    formats = [['WAV'] for _ in range(len(write_modules))]
    encodings = [['PCM_16', 'PCM_24', 'PCM_32', 'PCM_64', 'FLOAT', 'DOUBLE', 'PCM_U8'] for _ in range(len(write_modules))]
    if 'pydub' in write_modules:
        i = write_modules.index('pydub')
        read_modules[i] = 'audioread'
        #formats[i] = ['MP3']
        #encodings[i] = ['']
    if 'wavpack' in write_modules:
        i = write_modules.index('wavpack')
        formats[i] = ['WV']
        encodings[i] = ['']
    if 'soundfile' in write_modules:
        i = write_modules.index('soundfile')
        formats[i].append('OGG')
        encodings[i].append('VORBIS')
    formats[-1].append('OGG')
    encodings[-1].append('VORBIS')
    
    # encodings_with_read_error = ['G721_32', 'GSM610', ''] # soundfile: raise ValueError("frames must be specified for non-seekable files") in sf.read()
    # encodings_with_seek_error = ['IMA_ADPCM', 'MS_ADPCM', ''] # soundfile: RuntimeError: Internal psf_fseek() failed.

    for channels in [0, 1, 2, 4, 8, 16]:

        # generate data:
        if channels == 0:
            channels = 1
        elif channels == 1:
            data = data.reshape((-1, 1))
        else:
            for k in range(data.shape[1], channels):
                data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
        print(f'channels = {channels}')

        # write, read, and check:
        for wlib, rlib, fmts, encs in zip(write_modules, read_modules, formats, encodings):
            print()
            print(f'{wlib} module:')
            for format in fmts:
                if wlib == 'audioio':
                    am.enable_module()
                else:
                    am.select_module(wlib)
                if not format in aw.available_formats():
                    continue
                filename = Path('test.' + format.lower())
                for encoding in encs:
                    if encoding != '' and not encoding in aw.available_encodings(format):
                        continue
                    print(encoding)
                    # pathlib:
                    if wlib != 'audioio':
                        am.select_module(wlib)
                    aw.write_audio(filename, data, rate, format=format, encoding=encoding)
                    if wlib != 'audioio':
                        am.select_module(rlib)
                    data_read, rate_read = al.load_audio(filename)
                    check(rate, data, rate_read, data_read, wlib, encoding)
                    # str filename:
                    if wlib != 'audioio':
                        am.select_module(wlib)
                    aw.write_audio(os.fspath(filename), data, rate, format=format, encoding=encoding)
                    if wlib != 'audioio':
                        am.select_module(rlib)
                    data_read, rate_read = al.load_audio(os.fspath(filename))
                filename.unlink(True)
                am.enable_module()


def test_write_modules():
    am.enable_module()
    # generate data:
    rate = 44100.0
    duration = 10.0
    t = np.arange(int(duration*rate))/rate
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    # test for wrong formats:
    for lib, write_func in aw.audio_writer_funcs:
        filename = Path('test.wav')
        format = 'wav'
        if lib in ['wavpack']:
            filename = Path('test.wv')
            format = 'wv'
        if not am.select_module(lib):
            continue
        with pytest.raises(ValueError):
            write_func(filename, data, rate, format='xxx')
        write_func(filename, data, rate, format='')
        filename.unlink(True)
        with pytest.raises(ValueError):
            write_func(filename, data, rate, encoding='xxx')
        write_func(filename, data, rate, encoding='')
        filename.unlink(True)
        am.enable_module()
    filename = Path('test.wav')
    format = 'wav'
    with pytest.raises(IOError):
        aw.write_audio(filename, data, rate, format='xxx')
    aw.write_audio(filename, data, rate, format='')
    filename.unlink(True)
    with pytest.raises(IOError):
        aw.write_audio(filename, data, rate, encoding='xxx')
    aw.write_audio(filename, data, rate, encoding='')
    filename.unlink(True)
    # test for not available modules:
    for lib, write_func in aw.audio_writer_funcs:
        filename = Path('test.wav')
        format = 'wav'
        if lib in ['wavpack']:
            filename = Path('test.wv')
            format = 'wv'
        am.disable_module(lib)
        with pytest.raises(ImportError):
            write_func(filename, data, rate)
        am.enable_module(lib)
    for lib, encodings_func in aw.audio_encodings_funcs:
        am.disable_module(lib)
        enc = encodings_func(format)
        assert len(enc) == 0, 'no encoding should be returned for disabled module %s' % lib
        am.enable_module(lib)
    for lib, formats_func in aw.audio_formats_funcs:
        am.disable_module(lib)
        formats = formats_func()
        assert len(formats) == 0, 'no format should be returned for disabled module %s' % lib
        am.enable_module(lib)


def test_write_metadata():
    am.enable_module()
    # generate data:
    rate = 44100.0
    duration = 10.0
    t = np.arange(int(duration*rate))/rate
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    md = dict(Amplifier='Teensy_Amp', Location='Beach', Time='future')
    # test storage of metadata in wave files:
    filename = 'test.wav'
    for lib, write_func in aw.audio_writer_funcs:
        if not am.select_module(lib):
            continue
        if not 'WAV' in aw.available_formats():
            continue
        write_func(filename, data, rate, md)
        mmd = al.metadata(filename)
        Path(filename).unlink(True)
        assert md == mmd, 'metadata for wavefiles'
        am.enable_module()
    # test storage of metadata in ogg files:
    filename = 'test.ogg'
    for lib, write_func in aw.audio_writer_funcs:
        if lib == 'pydub':
            continue
        if not am.select_module(lib):
            continue
        if not 'OGG' in aw.available_formats():
            continue
        write_func(filename, data, rate, md, encoding='VORBIS')
        mmd = al.metadata(filename)
        Path(filename).unlink(True)
        assert len(mmd) == 0, 'metadata for ogg files'
        am.enable_module()
    # test storage of metadata in mp3 files:
    if am.audio_modules['pydub']:
        filename = 'test.mp3'
        aw.write_pydub(filename, data, rate, md)
        mmd = al.metadata(filename)
        Path(filename).unlink(True)
        assert len(mmd) == 0, 'metadata for mp3 files'
    am.enable_module()
    # test storage of metadata in wavpack files:
    if am.audio_modules['wavpack']:
        filename = 'test.wv'
        aw.write_wavpack(filename, data, rate, md)
        mmd = al.metadata(filename)
        Path(filename).unlink(True)
        assert md == mmd, 'metadata for wavpack'
        am.enable_module()

        
def test_extensions():
    f = aw.format_from_extension(None)
    assert f is None, 'None filepath'
    f = aw.format_from_extension('file')
    assert f is None, 'filepath withouth extension'
    f = aw.format_from_extension('file.')
    assert f is None, 'filepath withouth extension'
    f = aw.format_from_extension('file.wave')
    assert f == 'WAV', 'filepath with wave'
    f = aw.format_from_extension('file.wav')
    assert f == 'WAV', 'filepath with wav'
    f = aw.format_from_extension('file.ogg')
    assert f == 'OGG', 'filepath with wav'
    f = aw.format_from_extension('file.mpeg4')
    assert f == 'MP4', 'filepath with wav'


def test_demo():
    am.enable_module()
    filename = 'test.wav'
    aw.demo(filename)
    aw.demo(filename, channels=1)
    aw.demo(filename, channels=2, encoding='PCM_16')
    Path(filename).unlink(True)


def test_main():
    am.enable_module()
    filename = 'test.wav'
    aw.main('-h')
    aw.main(filename)
    aw.main('-m', 'wave', filename)
    aw.main('-m', 'wave', '-n', '1', filename)
    aw.main('-m', 'wave', filename, 'PCM_16')
    Path(filename).unlink(True)
