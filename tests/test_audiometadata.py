from nose.tools import assert_true, assert_false, assert_equal, assert_raises
import os
import numpy as np
import audioio.audioloader as al
import audioio.audiowriter as aw
import audioio.riffmetadata as rm
import audioio.audiometadata as amd


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

    
def test_metadata():
    data, rate = generate_data()
    filename = 'test.wav'
    imd = dict(IENG='JB', ICRD='2024-01-24', RATE=9,
               Comment='this is test1')
    iimd = {rm.info_tags.get(k, k): str(v) for k, v in imd.items()}
    bmd = dict(Description='a recording',
               OriginationDate='2024:01:24', TimeReference=123456,
               Version=42, CodingHistory='Test1\nTest2')
    bbmd = {k: str(v).replace('\n', '.') for k, v in bmd.items()}
    xmd = dict(Project='Record all', Note='still testing',
               Sync_Point_List=dict(Sync_Point='1', Sync_Point_Comment='great'))
    omd = iimd.copy()
    omd['Production'] = bbmd

    # INFO:
    md = dict(INFO=imd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert_true('INFO' in mdd, 'INFO section exists')
    assert_equal(iimd, mdd['INFO'], 'INFO section matches')

    with open(filename, 'rb') as sf:
        mdd = al.metadata(sf, False)
    assert_true('INFO' in mdd, 'INFO section exists')
    assert_equal(iimd, mdd['INFO'], 'INFO section matches')

    # BEXT:
    md = dict(BEXT=bmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert_true('BEXT' in mdd, 'BEXT section exists')
    assert_equal(bmd, mdd['BEXT'], 'BEXT section matches')

    # IXML:
    md = dict(IXML=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert_true('IXML' in mdd, 'IXML section exists')
    assert_equal(xmd, mdd['IXML'], 'IXML section matches')

    # ODML:
    md = dict(Recording=omd, Production=bbmd, Notes=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert_equal(md, mdd, 'ODML sections match')
    
    md = dict(INFO=imd, BEXT=bmd, IXML=xmd,
              Recording=omd, Production=bmd, Notes=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
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

    # INFO with nested dict:
    imd['SUBI'] = bmd
    md = dict(INFO=imd)
    aw.write_audio(filename, data, rate, md)

    # BEXT with invalid tag:
    bmd['xxx'] = 'no bext'
    md = dict(BEXT=bmd)
    aw.write_audio(filename, data, rate, md)
    
    al.metadata(filename, True)
    os.remove(filename)


def test_flatten():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4),
              eeee=dict(fff=5, ggg=dict(hh=6)),
              iiii=dict(jjj=7))

    fmd = amd.flatten_metadata(md, False)
    fmd = amd.flatten_metadata(md, True)
    amd.unflatten_metadata(fmd)

    amd.print_metadata(md)
    amd.print_metadata(md, '# ')
    amd.print_metadata(md, '# ', 2)
    
    filename = 'test.txt'
    amd.write_metadata_text(filename, md)
    os.remove(filename)


def test_find_key():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)),
              gggg=dict(hhh=6))
    m, k = amd.find_key(md, 'bbbb__ddd')
    m[k] = 10
    assert_equal(md['bbbb']['ddd'], 10, 'find key-value pair')
    m, k = amd.find_key(md, 'hhh')
    m[k] = 12
    assert_equal(md['gggg']['hhh'], 12, 'find key-value pair')
    m, k = amd.find_key(md, 'bbbb__eee__xx')
    assert_true(k not in md['bbbb']['eee'], 'find non-existing key-value pair')
    m[k] = 42
    assert_equal(md['bbbb']['eee']['xx'], 42, 'find key-value pair')
    m, k = amd.find_key(md, 'eee')
    m['yy'] = 46
    assert_equal(md['bbbb']['eee']['yy'], 46, 'find section')
    m, k = amd.find_key(md, 'gggg__zzz')
    assert_equal(k, 'zzz', 'find non-existing section')
    m[k] = 64
    assert_equal(md['gggg']['zzz'], 64, 'find non-existing section')


def test_add_sections():
    md = dict()
    m = amd.add_sections(md, 'Recording__Location')
    m['Country'] = 10
    assert_equal(md['Recording']['Location']['Country'], 10, 'added sections')
    md = dict()
    m, k = amd.add_sections(md, 'Recording__Location', True)
    m[k] = 10
    assert_equal(md['Recording']['Location'], 10, 'added sections and key-value pair')
    md = dict(Recording=dict())
    m, k = amd.find_key(md, 'Recording__Location__Country')
    m, k = amd.add_sections(m, k, True)
    m[k] = 10
    assert_equal(md['Recording']['Location']['Country'], 10, 'added sections to existing section')
    md = dict()
    m = amd.add_sections(md, '')
    assert_equal(len(m), 0, 'added empty section')
    assert_equal(len(md), 0, 'added empty section')
    m, k = amd.add_sections(md, '', True)
    assert_equal(len(m), 0, 'added empty key-value pair')
    assert_equal(len(md), 0, 'added empty key-value pair')
    assert_equal(k, '', 'added empty key-value pair')

    
def test_add_metadata():
     md = dict(Recording=dict(Time='early'))
     amd.add_metadata(md, ['Artist=John Doe',
                           'Recording__Time=late',
                           'Recording__Quality=amazing',
                           'Location__Country=Lummerland'])
     assert_equal(md['Recording']['Time'], 'late', 'add_metadata')
     assert_equal(md['Recording']['Quality'], 'amazing', 'add_metadata')
     assert_equal(md['Artist'], 'John Doe', 'add_metadata')
     assert_equal(md['Location']['Country'], 'Lummerland', 'add_metadata')

     
def test_parse_number():
    v, u, n = amd.parse_number('42')
    assert_equal(v, 42, 'parse integer number')
    assert_equal(u, '', 'parse integer number')
    assert_equal(n, 0, 'parse integer number')
    v, u, n = amd.parse_number('42ms')
    assert_equal(v, 42, 'parse integer number with unit')
    assert_equal(u, 'ms', 'parse integer number with unit')
    assert_equal(n, 0, 'parse integer number with unit')
    v, u, n = amd.parse_number('42.3')
    assert_equal(v, float(42.3), 'parse float number')
    assert_equal(u, '', 'parse float number')
    assert_equal(n, 1, 'parse float number')
    v, u, n = amd.parse_number('42.3ms')
    assert_equal(v, float(42.3), 'parse float number with unit')
    assert_equal(u, 'ms', 'parse float number with unit')
    assert_equal(n, 1, 'parse float number with unit')
    v, u, n = amd.parse_number('42.3 ms')
    assert_equal(v, float(42.3), 'parse float number with space and unit')
    assert_equal(u, 'ms', 'parse float number with space and unit')
    assert_equal(n, 1, 'parse float number with space and unit')
    v, u, n = amd.parse_number('42.32.ms')
    assert_equal(v, float(42.32), 'parse float number with point unit')
    assert_equal(u, '.ms', 'parse float number with point unit')
    assert_equal(n, 2, 'parse float number with point unit')
    v, u, n = amd.parse_number('ms')
    assert_equal(v, None, 'parse string')
    assert_equal(u, 'ms', 'parse string')
    assert_equal(n, 0, 'parse string')
    v, u, n = amd.parse_number('')
    assert_equal(v, None, 'parse empty string')
    assert_equal(u, '', 'parse emptystring')
    assert_equal(n, 0, 'parse emptystring')

    
def test_update_gain():
    md = dict(Gain='1.42mV')
    amd.update_gain(md, 2)
    assert_equal(md['Gain'], '0.71mV')
    md = dict(Gain='1.42mV/V')
    amd.update_gain(md, 2)
    assert_equal(md['Gain'], '0.71mV')
    md = dict(Artist='John Doe', Recording=dict(gain='1.4mV'))
    amd.update_gain(md, 2)
    assert_equal(md['Recording']['gain'], '0.7mV')
    md = dict(Gain=1.4)
    amd.update_gain(md, 2)
    assert_equal(md['Gain'], 0.7)
    md = dict(Gain=3)
    amd.update_gain(md, 2)
    assert_equal(md['Gain'], 1.5)
    md = dict(Gain='ms')
    r = amd.update_gain(md, 2)
    assert_equal(md['Gain'], 'ms')
    assert_equal(r, False)
    md = dict(Artist='John Doe', Recording=dict(xgain='1.4mV'))
    r = amd.update_gain(md, 2)
    assert_equal(md['Recording']['xgain'], '1.4mV')
    assert_equal(r, False)

    
def test_add_unwrap():
     md = dict(Recording=dict(Time='early'))
     amd.add_unwrap(md, 0.4)
     assert_equal(md['UnwrapThreshold'], '0.40', 'added unwrap threshold')
     amd.add_unwrap(md, 0.6, 0.8)
     assert_equal(md['UnwrapThreshold'], '0.60', 'added unwrap threshold and clip')
     assert_equal(md['UnwrapClippedAmplitude'], '0.80', 'added unwrap threshold and clip')
     
     md = dict(INFO=dict(Time='early'))
     amd.add_unwrap(md, 0.4)
     assert_equal(md['INFO']['UnwrapThreshold'], '0.40', 'added unwrap threshold')
     amd.add_unwrap(md, 0.6, 0.8)
     assert_equal(md['INFO']['UnwrapThreshold'], '0.60', 'added unwrap threshold and clip')
     assert_equal(md['INFO']['UnwrapClippedAmplitude'], '0.80', 'added unwrap threshold and clip')

     
def test_remove_metadata():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)))
    amd.remove_metadata(md, ('ccc',))
    assert_true('ccc' not in md['bbbb'], 'remove metadata')
    amd.remove_metadata(md, ('xxx',))
    amd.remove_metadata(md, ('eee',))
    assert_true('eee' in md['bbbb'], 'do not remove metadata section')

     
def test_cleanup_metadata():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict()))
    amd.cleanup_metadata(md)
    assert_true('eee' not in md['bbbb'], 'cleanup metadata')

    
def test_main():
    data, rate = generate_data()
    filename = 'test.wav'
    md = dict(IENG='JB', ICRD='2024-01-24', RATE=9,
              Comment='this is test1')
    locs = np.random.randint(10, len(data)-10, (5, 2))
    locs = locs[np.argsort(locs[:,0]),:]
    locs[:,1] = np.random.randint(0, 20, len(locs))
    labels = np.zeros((len(locs), 2), dtype=np.object_)
    for i in range(len(labels)):
        labels[i,0] = chr(ord('a') + i % 26)
        labels[i,1] = chr(ord('A') + i % 26)*5
    aw.write_audio(filename, data, rate, md, locs, labels)
    assert_raises(SystemExit, amd.main)
    assert_raises(SystemExit, amd.main, '-h')
    assert_raises(SystemExit, amd.main, '--help')
    assert_raises(SystemExit, amd.main, '--version')
    amd.main('test.wav')
    amd.main('test.wav', 'test.wav')
    amd.main('-f', 'test.wav')
    amd.main('-m', 'test.wav')
    amd.main('-c', 'test.wav')
    amd.main('-m', '-c', 'test.wav')
    aw.write_audio(filename, data, rate, md, locs)
    amd.main('test.wav')
    os.remove('test.wav')


