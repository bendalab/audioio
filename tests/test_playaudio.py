from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_raises
import numpy as np
import audioio.playaudio as ap
import audioio.audiomodules as am


def test_playaudio_beep():
    ap.beep()
    for lib in am.installed_modules('device'):
        print('')
        print('%s module:' % lib)
        am.select_module(lib)
        ap.beep()
        am.enable_module()
