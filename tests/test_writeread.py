from nose.tools import assert_true, assert_equal, assert_less, assert_almost_equal, assert_raises, nottest
import os
import numpy as np
import audioio.audiowriter as aw
import audioio.audioloader as al
import audioio.audiomodules as am


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
            if lib == 'audioread':
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

        am.enable_module()
        print('')
        print('audioio')
        for encoding in encodings:
            encoding = encoding.upper()
            if encoding == '' or encoding in aw.available_encodings(format):
                print(encoding)
                aw.write_audio(filename, data, samplerate, format=format, encoding=encoding)
                data_read, samplerate_read = al.load_audio(filename, verbose=2)
                check(samplerate, data, samplerate_read, data_read, 'audioio', encoding)
    os.remove(filename)


def test_write_read_modules():
    # generate data:
    filename = 'test.wav'
    format = 'wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(int(duration*samplerate))/samplerate
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
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



def test_demo():
    filename = 'test.wav'
    aw.demo(filename)
    os.remove(filename)


def test_main():
    filename = 'test.wav'
    aw.main(['prog', '-h'])
    aw.main(['prog', filename])
    aw.main(['prog', '-m', 'soundfile', filename])
    os.remove(filename)
