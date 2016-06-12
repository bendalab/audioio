from nose.tools import assert_greater_equal
import numpy as np
import audioio.audiowriter as aw

def test_formats_encodings():
    audio_formats = [['wave', aw.formats_wave, 1, aw.encodings_wave],
                     ['ewave', aw.formats_ewave, 2, aw.encodings_ewave],
                     ['scipy.io.wavfile', aw.formats_wavfile, 1, aw.encodings_wavfile],
                     ['soundfile', aw.formats_soundfile, 25, aw.encodings_soundfile],
                     ['wavefile', aw.formats_wavefile, 25, aw.encodings_wavefile],
                     ['scikits.audiolab', aw.formats_audiolab, 25, aw.encodings_audiolab]]

    for module, formats_func, min_f, encodings_func in audio_formats:
        if aw.audio_modules[module]:
            formats = formats_func()
            assert_greater_equal(len(formats), min_f,
                                 'formats_%s() did not return enough formats' % module.split('.')[-1])
            for f in formats:
                encodings = encodings_func(f)
                assert_greater_equal(len(encodings), 1,
                                     'encodings_%s() did not return enough encodings for format %s' % (module.split('.')[-1], f))

    formats = aw.available_formats()
    assert_greater_equal(len(formats), 1,
                         'available_formats() did not return enough formats')
    for f in formats:
        encodings = aw.available_encodings(f)
        assert_greater_equal(len(encodings), 1,
                             'available_encodings() did not return enough encodings for format %s' % f)
                
        
    

