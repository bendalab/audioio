from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_raises, nottest
import time
import numpy as np
import audioio.playaudio as ap
import audioio.audiomodules as am


def test_playaudio_beep():
    print()
    print('default module...')
    ap.beep(blocking=True)
    ap.beep(0.5, 'a4', blocking=True)
    ap.beep(rate=233000.0, blocking=True) # force downsampling
    ap.beep(blocking=False)
    time.sleep(2.0)
    ap.handle.close()
    for lib in am.installed_modules('device'):
        print('%s module...' % lib)
        am.select_module(lib)
        ap.beep(blocking=True)
        ap.beep(blocking=False)
        time.sleep(2.0)
        ap.handle.close()
        am.enable_module()


def test_playaudio_play():
    print()
    # sine wave:
    rate = 44100.0
    t = np.arange(0.0, 0.5, 1.0/rate)
    mono_data = np.sin(2.0*np.pi*800.0*t)
    stereo_data = np.tile(mono_data, (2, 1)).T
    # fade in and out:
    ap.fade(mono_data, rate, 0.1)
    ap.fade(stereo_data, rate, 0.1)
    print('default module mono...')
    ap.play(mono_data, rate, blocking=True)
    ap.play(mono_data, rate, blocking=False)
    time.sleep(2.0)
    print('default module stereo...')
    ap.play(stereo_data, rate, blocking=True)
    ap.play(stereo_data, rate, blocking=False)
    time.sleep(2.0)
    ap.handle.close()
    for lib in am.installed_modules('device'):
        print('%s module mono...' % lib)
        am.select_module(lib)
        ap.play(mono_data, rate, blocking=True)
        ap.play(mono_data, rate, blocking=False)
        time.sleep(2.0)
        print('%s module stereo...' % lib)
        ap.play(stereo_data, rate, blocking=True)
        ap.play(stereo_data, rate, blocking=False)
        time.sleep(2.0)
        ap.handle.close()
        am.enable_module()
