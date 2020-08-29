from nose.tools import assert_greater_equal
import numpy as np
import audioio.audiowriter as aw

def test_formats_encodings():
    min_formats = {'wave': 1, 'ewave': 2, 'scipy.io.wavfile': 1,
                   'soundfile': 25, 'wavefile': 25}
    for (module, formats_func), (m, encodings_func) in zip(aw.audio_formats_funcs, aw.audio_encodings_funcs):
        if aw.audio_modules[module]:
            min_f =min_formats[module]
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
                
        
    

