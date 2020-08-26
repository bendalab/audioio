from nose.tools import assert_true, assert_equal, assert_less, assert_almost_equal, assert_raises
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
    t = np.arange(int(duration*samplerate))/samplerate
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
        audio_funcs = [
            ['soundfile', aw.write_soundfile, al.load_soundfile, aw.encodings_soundfile],
            ['scikits.audiolab', aw.write_audiolab, al.load_audiolab, aw.encodings_audiolab],
            ['wavefile', aw.write_wavefile, al.load_wavefile, aw.encodings_wavefile],
            ['wave', aw.write_wave, al.load_wave, aw.encodings_wave],
            ['ewave', aw.write_ewave, al.load_ewave, aw.encodings_ewave],
            ['scipy.io.wavfile', aw.write_wavfile, al.load_wavfile, aw.encodings_wavfile]
            ]
            
        for lib, write_file, load_file, encodings_func in audio_funcs:
            if not aw.audio_modules[lib]:
                continue
            print('')
            print(lib)
            for encoding in encodings:
                encoding = encoding.upper()
                if encoding == '' or encoding in encodings_func(format):
                    print(encoding)
                    write_file(filename, data, samplerate, format=format, encoding=encoding)
                    data_read, samplerate_read = load_file(filename, verbose=2)
                    check(samplerate, data, samplerate_read, data_read, lib, encoding)

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
    audio_funcs = [
        ['soundfile', aw.write_soundfile, al.load_soundfile, aw.encodings_soundfile, aw.formats_soundfile],
        ['scikits.audiolab', aw.write_audiolab, al.load_audiolab, aw.encodings_audiolab, aw.formats_audiolab],
        ['wavefile', aw.write_wavefile, al.load_wavefile, aw.encodings_wavefile, aw.formats_wavefile],
        ['wave', aw.write_wave, al.load_wave, aw.encodings_wave, aw.formats_wave],
        ['ewave', aw.write_ewave, al.load_ewave, aw.encodings_ewave, aw.formats_ewave],
        ['scipy.io.wavfile', aw.write_wavfile, al.load_wavfile, aw.encodings_wavfile, aw.formats_wavfile]
        ]
    # generate data:
    filename = 'test.wav'
    format = 'wav'
    samplerate = 44100.0
    duration = 10.0
    t = np.arange(int(duration*samplerate))/samplerate
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    for lib, write_file, load_file, encodings_func, formats_func in audio_funcs:
        am.disable_module(lib)
        assert_raises(ImportError, write_file, filename, data, samplerate)
        assert_raises(ImportError, load_file, filename)
        enc = encodings_func(format)
        assert_equal(len(enc), 0, 'no encoding should be returned for disabled module %s' % lib)
        formats = formats_func()
        assert_equal(len(formats), 0, 'no format should be returned for disabled module %s' % lib)
        am.enable_module(lib)
