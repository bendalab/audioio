from nose.tools import assert_true, assert_equal, assert_greater_equal, assert_less, assert_almost_equal, assert_raises
import os
import numpy as np
import audioio.audiowriter as aw
import audioio.audioloader as al
import audioio.audiomodules as am


def test_formats_encodings():
    am.enable_module()
    min_formats = {'wave': 1, 'ewave': 2, 'scipy.io.wavfile': 1,
                   'soundfile': 23, 'wavefile': 23, 'pydub': 10}
    for (module, formats_func), (m, encodings_func) in zip(aw.audio_formats_funcs, aw.audio_encodings_funcs):
        if aw.audio_modules[module]:
            min_f = min_formats[module]
            formats = formats_func()
            assert_greater_equal(len(formats), min_f,
                                 'formats_%s() did not return enough formats' % module.split('.')[-1])
            for f in formats:
                encodings = encodings_func(f)
                assert_greater_equal(len(encodings), 1,
                                     'encodings_%s() did not return enough encodings for format %s' % (module.split('.')[-1], f))
            encodings = encodings_func('xxx')
            assert_equal(len(encodings), 0, 'encodings_%s() returned encodings for invalid format xxx' % module.split('.')[-1])
            encodings = encodings_func('')
            assert_equal(len(encodings), 0, 'encodings_%s() returned encodings for empty format xxx' % module.split('.')[-1])

    formats = aw.available_formats()
    assert_greater_equal(len(formats), 1,
                         'available_formats() did not return enough formats')
    for f in formats:
        encodings = aw.available_encodings(f)
        assert_greater_equal(len(encodings), 1,
                             'available_encodings() did not return enough encodings for format %s' % f)
                

def test_write_read():

    def check(samplerate_write, data_write, samplerate_read, data_read, lib, encoding):
        assert_almost_equal(samplerate_write, samplerate_read, 'samplerates differ for module %s with encoding %s' % (lib, encoding))
        assert_equal(len(data_write), len(data_read), 'frames %d %d differ for module %s with encoding %s' % (len(data_write), len(data_read), lib, encoding))
        assert_equal(len(data_write.shape), len(data_read.shape), 'shape len differs for module %s with encoding %s' % (lib, encoding))
        assert_equal(len(data_read.shape), 2, 'shape differs from 2 for module %s with encoding %s' % (lib, encoding))
        assert_equal(data_write.shape[0], data_read.shape[0], 'shape[0] differs for module %s with encoding %s' % (lib, encoding))
        assert_equal(data_write.shape[1], data_read.shape[1], 'shape[1] differs for module %s with encoding %s' % (lib, encoding))
        assert_equal(data_read.dtype, np.float64, 'read in data are not doubles for module %s with encoding %s' % (lib, encoding))
        n = min([len(data_write), len(data_read)])
        max_error = np.max(np.abs(data_write[:n] - data_read[:n]))
        print('maximum error = %g' % max_error)
        assert_less(max_error, 0.05, 'values differ for module %s with encoding %s by up to %g' % (lib, encoding, max_error))
        
    am.enable_module()
    # generate data:
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))

    # parameter for wav file:
    filename = 'test.wav'
    format = 'wav'
    encodings = ['PCM_16', 'PCM_24', 'PCM_32', 'PCM_64', 'FLOAT', 'DOUBLE', 'PCM_U8', 'ALAW', 'ULAW', '']
    encodings_with_read_error = ['G721_32', 'GSM610', ''] # soundfile: raise ValueError("frames must be specified for non-seekable files") in sf.read()
    encodings_with_seek_error = ['IMA_ADPCM', 'MS_ADPCM', ''] # soundfile: RuntimeError: Internal psf_fseek() failed.

    # parameter for ogg file:
    ## filename = 'test.ogg'
    ## format = 'OGG'
    ## encodings = ['VORBIS']

    mpeg_filename = 'test.mp3'

    # fix parameter:
    format = format.upper()

    for channels in [1, 2, 4, 8, 16]:

        # generate data:
        if channels > 1:
            for k in range(data.shape[1], channels):
                data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
        print('channels = %d' % channels)

        # write, read, and check:
        for lib in am.installed_modules('fileio'):
            if lib in ['audioread', 'pydub']:
                continue
            print('')
            print('%s module:' % lib)
            am.select_module(lib)
            for encoding in encodings:
                encoding = encoding.upper()
                if encoding == '' or encoding in aw.available_encodings(format):
                    print(encoding)
                    aw.write_audio(filename, data, samplerate, format=format, encoding=encoding, verbose=2)
                    data_read, samplerate_read = al.load_audio(filename, verbose=2)
                    check(samplerate, data, samplerate_read, data_read, lib, encoding)

        """
        if 'audioread' in am.installed_modules('fileio') and 'pydub' in am.installed_modules('fileio'):
            am.select_module('pydub')
            aw.write_audio(mpeg_filename, data, samplerate)
            am.select_module('audioread')
            data_read, samplerate_read = al.load_audio(mpeg_filename, verbose=2)
            check(samplerate, data, samplerate_read, data_read, 'pydub', '')
        """ 

        am.enable_module()
        print('')
        print('audioio')
        for encoding in encodings:
            encoding = encoding.upper()
            if encoding == '' or encoding in aw.available_encodings(format):
                print(encoding)
                aw.write_audio(filename, data, samplerate, format=format, encoding=encoding)
                data_read, samplerate_read = al.load_audio(filename, verbose=0)
                check(samplerate, data, samplerate_read, data_read, 'audioio', encoding)
    if os.path.isfile(filename):
        os.remove(filename)
    if os.path.isfile(mpeg_filename):
        os.remove(mpeg_filename)

    
def test_dimensions():
    am.enable_module()
    print('1-D data')
    filename = 'test.wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    for lib in am.installed_modules('fileio'):
        if lib == 'audioread' or (lib == 'pydub' and
                                  'audioread' not in am.installed_modules('fileio')):
            continue
        print('%s module...' % lib)
        am.select_module(lib)
        aw.write_audio(filename, data, samplerate)
        if lib == 'pydub':
            am.select_module('audioread')
        data_read, samplerate_read = al.load_audio(filename)
        assert_equal(len(data_read.shape), 2, 'read in data must be a 2-D array')
        assert_equal(data_read.shape[1], 1, 'read in data must be a 2-D array with one column')

    print('2-D data one channel')
    filename = 'test.wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for lib in am.installed_modules('fileio'):
        if lib == 'audioread' or (lib == 'pydub' and
                                  'audioread' not in am.installed_modules('fileio')):
            continue
        print('%s module...' % lib)
        am.select_module(lib)
        aw.write_audio(filename, data, samplerate)
        if lib == 'pydub':
            am.select_module('audioread')
        data_read, samplerate_read = al.load_audio(filename)
        assert_equal(len(data_read.shape), 2, 'read in data must be a 2-D array')
        assert_equal(data_read.shape[1], 1, 'read in data must be a 2-D array with one column')
        assert_equal(data_read.shape, data.shape, 'input and output data must have same shape')

    print('2-D data two channel')
    filename = 'test.wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 2))
    for lib in am.installed_modules('fileio'):
        if lib == 'audioread' or (lib == 'pydub' and
                                  'audioread' not in am.installed_modules('fileio')):
            continue
        print('%s module...' % lib)
        am.select_module(lib)
        aw.write_audio(filename, data, samplerate)
        if lib == 'pydub':
            am.select_module('audioread')
        data_read, samplerate_read = al.load_audio(filename)
        assert_equal(len(data_read.shape), 2, 'read in data must be a 2-D array')
        assert_equal(data_read.shape[1], 2, 'read in data must be a 2-D array with two columns')
        assert_equal(data_read.shape, data.shape, 'input and output data must have same shape')
    am.enable_module()


def test_write_read_modules():
    am.enable_module()
    # generate data:
    filename = 'test.wav'
    format = 'wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(int(duration*samplerate))/samplerate
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    # test for wrong formats:
    for lib, write_func in aw.audio_writer_funcs:
        if not am.select_module(lib):
            continue
        assert_raises(ValueError, write_func, '', data, samplerate)
        assert_raises(ValueError, write_func, filename, data, samplerate, format='xxx')
        write_func(filename, data, samplerate, format='')
        os.remove(filename)
        assert_raises(ValueError, write_func, filename, data, samplerate, encoding='xxx')
        write_func(filename, data, samplerate, encoding='')
        os.remove(filename)
        am.enable_module()
    assert_raises(ValueError, aw.write_audio, '', data, samplerate)
    assert_raises(IOError, aw.write_audio, filename, data, samplerate, format='xxx')
    aw.write_audio(filename, data, samplerate, format='')
    os.remove(filename)
    assert_raises(IOError, aw.write_audio, filename, data, samplerate, encoding='xxx')
    aw.write_audio(filename, data, samplerate, encoding='')
    os.remove(filename)
    # test for not available modules:
    for lib, write_func in aw.audio_writer_funcs:
        am.disable_module(lib)
        assert_raises(ImportError, write_func, filename, data, samplerate)
        am.enable_module(lib)
    for lib, encodings_func in aw.audio_encodings_funcs:
        am.disable_module(lib)
        enc = encodings_func(format)
        assert_equal(len(enc), 0, 'no encoding should be returned for disabled module %s' % lib)
        am.enable_module(lib)
    for lib, formats_func in aw.audio_formats_funcs:
        am.disable_module(lib)
        formats = formats_func()
        assert_equal(len(formats), 0, 'no format should be returned for disabled module %s' % lib)
        am.enable_module(lib)


def test_extensions():
    f = aw.format_from_extension(None)
    assert_true(f is None, 'None filepath')
    f = aw.format_from_extension('file')
    assert_true(f is None, 'filepath withouth extension')
    f = aw.format_from_extension('file.')
    assert_true(f is None, 'filepath withouth extension')
    f = aw.format_from_extension('file.wave')
    assert_equal(f, 'WAV', 'filepath with wave')
    f = aw.format_from_extension('file.wav')
    assert_equal(f, 'WAV', 'filepath with wav')
    f = aw.format_from_extension('file.ogg')
    assert_equal(f, 'OGG', 'filepath with wav')
    f = aw.format_from_extension('file.mpeg4')
    assert_equal(f, 'MP4', 'filepath with wav')


def test_demo():
    am.enable_module()
    filename = 'test.wav'
    aw.demo(filename)
    aw.demo(filename, channels=1)
    aw.demo(filename, channels=2, encoding='PCM_16')
    os.remove(filename)


def test_main():
    am.enable_module()
    filename = 'test.wav'
    aw.main('-h')
    aw.main(filename)
    aw.main('-m', 'wave', filename)
    aw.main('-m', 'wave', '-n', '1', filename)
    aw.main('-m', 'wave', filename, 'PCM_16')
    os.remove(filename)
