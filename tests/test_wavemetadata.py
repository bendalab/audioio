from nose.tools import assert_true, assert_false, assert_equal, assert_raises
import os
import numpy as np
import audioio.wavemetadata as wm


def generate_data():
    duration=2.0
    samplerate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    return data, samplerate


def test_write():
    data, rate = generate_data()
    filename = 'test.wav'
    for encoding in ['PCM_16', 'PCM_32']:
        wm.write_wave(filename, data, rate, None, encoding=encoding)
    assert_raises(ValueError, wm.write_wave, '', data, rate,
                  None, encoding=encoding)
    assert_raises(ValueError, wm.write_wave, filename, data, rate,
                  None, encoding='XYZ')
    os.remove(filename)

    
def test_metadata():
    data, rate = generate_data()
    filename = 'test.wav'
    imd = dict(IENG='JB', ICRD='2024-01-24', RATE=9,
               Comment='this is test1')
    iimd = {wm.info_tags.get(k, k): str(v) for k, v in imd.items()}
    bmd = dict(Description='a recording',
               OriginationDate='2024:01:24', TimeReference=123456,
               Version=42, CodingHistory='Test1\nTest2')
    bbmd = {k: str(v).replace('\n', '.') for k, v in bmd.items()}
    xmd = dict(Project='Record all', Note='still testing')

    # INFO:
    md = dict(INFO=imd)
    wm.write_wave(filename, data, rate, md)
    mdd = wm.metadata_wave(filename, False)
    assert_true('INFO' in mdd, 'INFO section exists')
    assert_equal(iimd, mdd['INFO'], 'INFO section matches')

    # BEXT:
    md = dict(BEXT=bmd)
    wm.write_wave(filename, data, rate, md)
    mdd = wm.metadata_wave(filename, False)
    assert_true('BEXT' in mdd, 'BEXT section exists')
    assert_equal(bmd, mdd['BEXT'], 'BEXT section matches')

    # IXML:
    md = dict(IXML=xmd)
    wm.write_wave(filename, data, rate, md)
    mdd = wm.metadata_wave(filename, False)
    assert_true('IXML' in mdd, 'IXML section exists')
    assert_equal(xmd, mdd['IXML'], 'IXML section matches')

    # ODML:
    md = dict(Recording=iimd, Production=bbmd, Notes=xmd)
    wm.write_wave(filename, data, rate, md)
    mdd = wm.metadata_wave(filename, False)
    assert_equal(md, mdd, 'ODML sections match')
    
    md = dict(INFO=imd, BEXT=bmd, IXML=xmd,
              Recording=imd, Production=bmd, Notes=xmd)
    wm.write_wave(filename, data, rate, md)
    mdd = wm.metadata_wave(filename, False)
    assert_true('INFO' in mdd, 'INFO section exists')
    assert_equal(iimd, mdd['INFO'], 'INFO section matches')
    assert_true('BEXT' in mdd, 'BEXT section exists')
    assert_equal(bmd, mdd['BEXT'], 'BEXT section matches')
    assert_true('IXML' in mdd, 'IXML section exists')
    assert_equal(xmd, mdd['IXML'], 'IXML section matches')
    assert_true('Recording' in mdd, 'Recording section exists')
    assert_true('Production' in mdd, 'Recording section exists')
    assert_true('Notes' in mdd, 'Recording section exists')
    assert_equal(md['Notes'], mdd['Notes'], 'Notes section matches')
    os.remove(filename)


def test_main():
    wm.main('-h')
    wm.main()
    wm.main('test.wav')
    os.remove('test.wav')


