import pytest
import os
import datetime as dt
import numpy as np
import audioio.audioloader as al
import audioio.audiowriter as aw
import audioio.riffmetadata as rm
import audioio.audiometadata as amd


def generate_data():
    duration=2.0
    rate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    return data, rate

    
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
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'

    with open(filename, 'rb') as sf:
        mdd = al.metadata(sf, False)
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'

    # BEXT:
    md = dict(BEXT=bmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert 'BEXT' in mdd, 'BEXT section exists'
    assert bmd == mdd['BEXT'], 'BEXT section matches'

    # IXML:
    md = dict(IXML=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert 'IXML' in mdd, 'IXML section exists'
    assert xmd == mdd['IXML'], 'IXML section matches'

    # GUANO:
    md = dict(Recording=omd, Production=bbmd, Notes=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    print(md)
    print(mdd)
    assert md == mdd, 'GUANO sections match'
    
    md = dict(INFO=imd, BEXT=bmd, IXML=xmd,
              Recording=omd, Production=bmd, Notes=xmd)
    aw.write_audio(filename, data, rate, md)
    mdd = al.metadata(filename, False)
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'
    assert 'BEXT' in mdd, 'BEXT section exists'
    assert bmd == mdd['BEXT'], 'BEXT section matches'
    assert 'IXML' in mdd, 'IXML section exists'
    assert xmd == mdd['IXML'], 'IXML section matches'
    assert 'Recording' in mdd, 'Recording section exists'
    assert 'Production' in mdd, 'Recording section exists'
    assert 'Notes' in mdd, 'Recording section exists'
    assert md['Notes'] == mdd['Notes'], 'Notes section matches'

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
              eeee=dict(fff=[5, 6, 7], ggg=dict(hh=6)),
              iiii=7)

    fmd = amd.flatten_metadata(md, False)
    fmd = amd.flatten_metadata(md, True)
    amd.unflatten_metadata(fmd)

    amd.print_metadata(md)
    amd.print_metadata(md, '# ')
    amd.print_metadata(md, '# ', 2)
    amd.print_metadata(None)
    
    filename = 'test.txt'
    amd.write_metadata_text(filename, md)
    os.remove(filename)


def test_find_key():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)),
              gggg=dict(hhh=6))
    m, k = amd.find_key(md, 'bbbb.ddd')
    m[k] = 10
    assert md['bbbb']['ddd'] == 10, 'find key-value pair'
    m, k = amd.find_key(md, 'hhh')
    m[k] = 12
    assert md['gggg']['hhh'] == 12, 'find key-value pair'
    m, k = amd.find_key(md, 'bbbb.eee.xx')
    assert k not in md['bbbb']['eee'], 'find non-existing key-value pair'
    m[k] = 42
    assert md['bbbb']['eee']['xx'] == 42, 'find key-value pair'
    m, k = amd.find_key(md, 'eee')
    m[k]['yy'] = 46
    assert md['bbbb']['eee']['yy'] == 46, 'find section'
    m, k = amd.find_key(None, 'aaaa')
    assert len(m) == 0, 'find in None metadata'
    assert k == None, 'find in None metadata'


def test_add_sections():
    md = dict()
    m = amd.add_sections(md, 'Recording.Location')
    m['Country'] = 10
    assert md['Recording']['Location']['Country'] == 10, 'added sections'
    md = dict()
    m, k = amd.add_sections(md, 'Recording.Location', True)
    m[k] = 10
    assert md['Recording']['Location'] == 10, 'added sections and key-value pair'
    md = dict(Recording=dict())
    m, k = amd.find_key(md, 'Recording.Location.Country')
    m, k = amd.add_sections(m, k, True)
    m[k] = 10
    assert md['Recording']['Location']['Country'] == 10, 'added sections to existing section'
    md = dict()
    m = amd.add_sections(md, '')
    assert len(m) == 0, 'added empty section'
    assert len(md) == 0, 'added empty section'
    m, k = amd.add_sections(md, '', True)
    assert len(m) == 0, 'added empty key-value pair'
    assert len(md) == 0, 'added empty key-value pair'
    assert k == '', 'added empty key-value pair'

    
def test_strlist_to_dict():
    mds = amd.strlist_to_dict(None)
    assert mds == {}, 'strlist_to_dict'
    md = dict(aaa=43)
    mds = amd.strlist_to_dict(md)
    assert mds == md, 'strlist_to_dict'
    mds = amd.strlist_to_dict('Artist=John Doe')
    assert len(mds) == 1, 'strlist_to_dict'
    assert mds['Artist'] == 'John Doe', 'strlist_to_dict'
    mds = amd.strlist_to_dict(['Artist=John Doe', 'Recording.Time=late'])
    assert len(mds) == 2, 'strlist_to_dict'
    assert mds['Artist'] == 'John Doe', 'strlist_to_dict'
    assert mds['Recording.Time'] == 'late', 'strlist_to_dict'

    
def test_set_metadata():
     md = dict(Recording=dict(Time='early'))
     amd.set_metadata(md, {'Artist': 'John Doe',
                           'Recording.Time': 'late'})
     assert md['Recording']['Time'] == 'late', 'set_metadata'
     assert len(md) == 1, 'set_metadata'
     assert len(md['Recording']) == 1, 'set_metadata'
     assert md['Recording']['Time'] == 'late'
     amd.set_metadata(md, {'Time': 'very late'})
     assert md['Recording']['Time'] == 'very late'
     amd.set_metadata(None, {'Artist': 'John Doe'})

    
def test_add_metadata():
     md = dict(Recording=dict(Time='early'))
     amd.add_metadata(md, {'Artist': 'John Doe',
                           'Recording.Time': 'late',
                           'Recording.Quality': 'amazing',
                           'Location.Country': 'Lummerland'})
     assert md['Recording']['Time'] == 'late', 'add_metadata'
     assert md['Recording']['Quality'] == 'amazing', 'add_metadata'
     assert md['Artist'] == 'John Doe', 'add_metadata'
     assert md['Location']['Country'] == 'Lummerland', 'add_metadata'
     amd.add_metadata(md, {'Artist': 'John Doe'})
     amd.add_metadata(None, {'Artist': 'John Doe'})

     
def test_move_metadata():
    md = dict(Artist='John Doe', Recording=dict(Gain='1.42mV'))
    m = amd.move_metadata(md, md, 'xxxx')
    assert not m, 'move_metadata()'
    m = amd.move_metadata(md, md['Recording'], 'Artist', 'Experimentalist')
    assert m, 'move_metadata()'
    assert len(md) == 1, 'move_metadata()'
    assert len(md['Recording']) == 2, 'move_metadata()'
    assert 'Experimentalist' in md['Recording'], 'move_metadata()'
    assert md['Recording']['Experimentalist'] == 'John Doe', 'move_metadata()'
    m = amd.move_metadata(md, md, 'Experimentalist')
    assert m, 'move_metadata()'
    assert len(md) == 2, 'move_metadata()'
    assert len(md['Recording']) == 1, 'move_metadata()'
    assert 'Experimentalist' in md, 'move_metadata()'
    assert md['Experimentalist'] == 'John Doe', 'move_metadata()'
    m = amd.move_metadata(None, md, 'xxxx')
    assert not m, 'move_metadata()'

    
def test_parse_number():
    v, u, n = amd.parse_number('42')
    assert v == 42, 'parse integer number'
    assert u == '', 'parse integer number'
    assert n == 0, 'parse integer number'
    v, u, n = amd.parse_number('42ms')
    assert v == 42, 'parse integer number with unit'
    assert u == 'ms', 'parse integer number with unit'
    assert n == 0, 'parse integer number with unit'
    v, u, n = amd.parse_number('42.3')
    assert v == float(42.3), 'parse float number'
    assert u == '', 'parse float number'
    assert n == 1, 'parse float number'
    v, u, n = amd.parse_number('42.3ms')
    assert v == float(42.3), 'parse float number with unit'
    assert u == 'ms', 'parse float number with unit'
    assert n == 1, 'parse float number with unit'
    v, u, n = amd.parse_number('42.3 ms')
    assert v == float(42.3), 'parse float number with space and unit'
    assert u == 'ms', 'parse float number with space and unit'
    assert n == 1, 'parse float number with space and unit'
    v, u, n = amd.parse_number('42.32.ms')
    assert v == float(42.32), 'parse float number with point unit'
    assert u == '.ms', 'parse float number with point unit'
    assert n == 2, 'parse float number with point unit'
    v, u, n = amd.parse_number('ms')
    assert v == None, 'parse string'
    assert u == 'ms', 'parse string'
    assert n == 0, 'parse string'
    v, u, n = amd.parse_number('')
    assert v == None, 'parse empty string'
    assert u == '', 'parse emptystring'
    assert n == 0, 'parse emptystring'
    v, u, n = amd.parse_number(42)
    assert v == 42, 'parse integer'
    assert u == '', 'parse integer'
    assert n == 0, 'parse integer'
    v, u, n = amd.parse_number(42.1)
    assert v == 42.1, 'parse float'
    assert u == '', 'parse float'
    assert n == 5, 'parse float'
    v, u, n = amd.parse_number([42.3])
    assert v == None, 'parse list'
    assert u == '', 'parse list'
    assert n == 0, 'parse list'

     
def test_change_unit():
    v = amd.change_unit(5, '', 'cm')
    assert v == 5.0, 'change unit'
    v = amd.change_unit(5, 'mm', '')
    assert v == 5.0, 'change unit'
    v = amd.change_unit(5, 'mm', 'cm')
    assert v == 0.5, 'change unit'
    v = amd.change_unit(5, 'cm', 'mm')
    assert v == 50.0, 'change unit'
    v = amd.change_unit(4, 'kg', 'g')
    assert v == 4000, 'change unit'
    v = amd.change_unit(12, '%', '')
    assert v == 0.12, 'change unit'
    v = amd.change_unit(1.24, '', '%')
    assert v == 124.0, 'change unit'
    v = amd.change_unit(2.5, 'min', 's')
    assert v == 150.0, 'change unit'
    v = amd.change_unit(3600, 's', 'h')
    assert v == 1.0, 'change unit'
    v = amd.change_unit(5, '', '')
    assert v == 5, 'change unit'

    
def test_get_number_unit():
    md = dict(aaaa='42', bbbb='42.3ms')
    v, u = amd.get_number_unit(md, 'aaaa')
    assert v == 42, 'get integer'
    assert u == '', 'get integer'
    v, u = amd.get_number_unit(md, 'bbbb')
    assert v == 42.3, 'get float with unit'
    assert u == 'ms', 'get float with unit'
    v, u = amd.get_number_unit(md, ['cccc', 'bbbb'])
    assert v == 42.3, 'get two keys'
    assert u == 'ms', 'get two keys'
    v, u = amd.get_number_unit(md, 'cccc')
    assert v == None, 'get invalid key'
    assert u == '', 'get invalid key'
    v, u = amd.get_number_unit(md, 'cccc', default=1.0, default_unit='a.u.')
    assert v == 1.0, 'get defaults'
    assert u == 'a.u.', 'get defaults key'
    v, u = amd.get_number_unit(md, 'bbbb', remove=True)
    assert not 'bbbb' in md
    v, u = amd.get_number_unit(None, 'cccc')
    assert v == None, 'get None from None metadata'
    assert u == '', 'get empty unit from None metadata'


def test_get_number():
    md = dict(aaaa='42', bbbb='42.3ms')
    v = amd.get_number(md, 's', 'bbbb')
    assert v == 0.0423, 'get number in seconds'
    v = amd.get_number(md, 'us', 'bbbb')
    assert v == 42300.0, 'get number in microseconds'
    v = amd.get_number(md, 'Hz', 'aaaa')
    assert v == 42, 'get number without unit'
    v = amd.get_number(md, 's', ['cccc', 'bbbb'])
    assert v == 0.0423, 'get number with two keys'
    v = amd.get_number(md, 's', 'cccc')
    assert v == None, 'get number with invalid key'
    v = amd.get_number(md, 's', 'cccc', default=1.0)
    assert v == 1.0, 'get number with default value'
    v = amd.get_number(None, 's', 'cccc')
    assert v == None, 'get None from None metadata'
    v = amd.get_number(md, 's', 'bbbb', remove=True)
    assert not 'bbbb' in md


def test_get_int():
    md = dict(aaaa='42', bbbb='42.3ms')
    v = amd.get_int(md, 'aaaa')
    assert v == 42, 'get integer'
    v = amd.get_int(md, 'bbbb')
    assert v == None, 'get float instead of int'
    v = amd.get_int(md, ['cccc', 'aaaa'])
    assert v == 42, 'get two keys'
    v = amd.get_int(md, ['bbbb', 'aaaa'])
    assert v == 42, 'get two keys'
    v = amd.get_int(md, 'cccc')
    assert v == None, 'get invalid key'
    v = amd.get_int(md, 'cccc', default=1)
    assert v == 1, 'get default'
    v = amd.get_int(None, 'cccc')
    assert v == None, 'get None from None metadata'
    v = amd.get_int(md, 'bbbb', remove=True)
    assert 'bbbb' in md
    v = amd.get_int(md, 'aaaa', remove=True)
    assert not 'aaaa' in md


def test_bool():
    md = dict(aaaa='TruE', bbbb='No', cccc=0, dddd=1, eeee=True, ffff='ui')
    v = amd.get_bool(md, 'aaaa')
    assert v == True, 'get boolean truth string'
    v = amd.get_bool(md, 'bbbb')
    assert v == False, 'get boolean false string'
    v = amd.get_bool(md, 'cccc')
    assert v == False, 'get boolean false integer'
    v = amd.get_bool(md, 'dddd')
    assert v == True, 'get boolean true integer'
    v = amd.get_bool(md, 'eeee')
    assert v == True, 'get boolean true'
    v = amd.get_bool(md, 'ffff')
    assert v == None, 'get non-boolean string'
    v = amd.get_bool(md, ['cccc', 'aaaa'])
    assert v == True, 'prefer boolean string'
    v = amd.get_bool(md, ['cccc', 'ffff'])
    assert v == False, 'get boolean first match'
    v = amd.get_bool(md, 'ffff', default=False)
    assert v == False, 'get boolean default'
    v = amd.get_bool(None, 'ffff')
    assert v == None, 'get None from None metadata'
    v = amd.get_bool(md, 'cccc', remove=True)
    assert not 'cccc' in md
    v = amd.get_bool(md, 'bbbb', remove=True)
    assert not 'bbbb' in md
    v = amd.get_bool(md, 'aaaa', remove=True)
    assert not 'aaaa' in md


def test_get_datetime():
    md = dict(date='2024-03-02', time='10:42:24',
              datetime='2023-04-15T22:10:00',
              dtdate=dt.date.fromisoformat('2024-03-02'),
              dttime=dt.time.fromisoformat('10:42:24'),
              dtdatetime=dt.datetime.fromisoformat('2023-04-15T22:10:00'),
              xdate=2024, xtime=10, xdatetime=2024)
    v = amd.get_datetime(md, ('date', 'time'))
    assert v == dt.datetime(2024, 3, 2, 10, 42, 24), 'get datetime with pair of date and time strings'
    v = amd.get_datetime(md, ('dtdate', 'dttime'))
    assert v == dt.datetime(2024, 3, 2, 10, 42, 24), 'get datetime with pair of date and time'
    v = amd.get_datetime(md, ('datetime',))
    assert v == dt.datetime(2023, 4, 15, 22, 10), 'get datetime with single datetime string'
    v = amd.get_datetime(md, [('aaaa',), ('date', 'time')])
    assert v == dt.datetime(2024, 3, 2, 10, 42, 24), 'get datetime with invalid key and pair of date and time'
    v = amd.get_datetime(md, ('cccc',))
    assert v == None, 'get datetime with invalid key'
    v = amd.get_datetime(md, ('xdatetime',))
    assert v == None, 'get datetime with invalid type'
    v = amd.get_datetime(md, ('cccc', 'dddd'))
    assert v == None, 'get date and time with invalid key'
    v = amd.get_datetime(md, ('date', 'dddd'))
    assert v == None, 'get date and time with invalid key'
    v = amd.get_datetime(md, ('xdate', 'xtime'))
    assert v == None, 'get date and time with invalid type'
    v = amd.get_datetime(md, ('date', 'xtime'))
    assert v == None, 'get date and time with invalid type'
    v = amd.get_datetime(md, ('cccc', 'dddd'),
                         default=dt.datetime(2022, 2, 22, 22, 2, 12))
    assert v == dt.datetime(2022, 2, 22, 22, 2, 12), 'get default datetime with invalid key'
    v = amd.get_datetime(md, ('date', 'time'), remove=True)
    assert not 'date' in md
    assert not 'time' in md
    v = amd.get_datetime(md, ('dtdate', 'dttime'), remove=True)
    assert not 'dtdate' in md
    assert not 'dttime' in md
    v = amd.get_datetime(md, ('datetime',), remove=True)
    assert not 'datetime' in md
    v = amd.get_datetime(md, ('dtdatetime',), remove=True)
    assert not 'datetime' in md
    v = amd.get_datetime(None, 'ffff')
    assert v == None, 'get None from None metadata'


def test_update_starttime():
    md = dict(DateTimeOriginal='2023-04-15T22:10:00',
              OtherTime='2023-05-16T23:20:10',
              BEXT=dict(OriginationDate='2024-03-02',
                        OriginationTime='10:42:24',
                        TimeReference='123456'))
    r = amd.update_starttime(None, 4.2, 48000)
    assert not r, 'update_starttime() without metadata'
    r = amd.update_starttime(md, 4.2, 48000,
                             time_keys=[['xxx'], ['yyy', 'zzzz'], ['OriginationDate', 'zzzz']] + amd.default_starttime_keys)
    assert r, 'update_starttime() with metadata'
    assert md['DateTimeOriginal'] == '2023-04-15T22:10:04', 'update_starttime() with metadata'
    assert md['BEXT']['OriginationDate'] == '2024-03-02', 'update_starttime() with metadata'
    assert md['BEXT']['OriginationTime'] == '10:42:28', 'update_starttime() with metadata'
    assert md['BEXT']['TimeReference'] == str(123456 + int(4.2*48000)), 'update_starttime() with metadata'
    assert md['OtherTime'] == '2023-05-16T23:20:10', 'update_starttime() with metadata'
    r = amd.update_starttime(md, 4.2, 48000, time_keys=['DateTimeOriginal'],
                             ref_keys='TimeReference')
    assert r, 'update_starttime() with metadata'
    assert md['DateTimeOriginal'] == '2023-04-15T22:10:08', 'update_starttime() with metadata'
    assert md['BEXT']['TimeReference'] == str(123456 + int(2*4.2*48000)), 'update_starttime() with metadata'

    md = dict(DateTimeOriginal=dt.datetime.fromisoformat('2023-04-15T22:10:00'),
              OtherTime=dt.datetime.fromisoformat('2023-05-16T23:20:10'),
              BEXT=dict(OriginationDate=dt.date.fromisoformat('2024-03-02'),
                        OriginationTime=dt.time.fromisoformat('10:42:24'),
                        TimeReference=123456))
    r = amd.update_starttime(md, 4.2, 48000)
    assert r, 'update_starttime() with metadata'
    assert md['DateTimeOriginal'] == dt.datetime.fromisoformat('2023-04-15T22:10:04.200'), 'update_starttime() with metadata'
    assert md['BEXT']['OriginationDate'] == dt.date.fromisoformat('2024-03-02'), 'update_starttime() with metadata'
    assert md['BEXT']['OriginationTime'] == dt.time.fromisoformat('10:42:28.200'), 'update_starttime() with metadata'
    assert md['BEXT']['TimeReference'] == 123456 + int(4.2*48000), 'update_starttime() with metadata'
    assert md['OtherTime'] == dt.datetime.fromisoformat('2023-05-16T23:20:10'), 'update_starttime() with metadata'
    

    
def test_get_str():
    md = dict(aaaa=42, bbbb='hello')
    v = amd.get_str(md, 'bbbb')
    assert v == 'hello', 'get str'
    v = amd.get_str(md, 'aaaa')
    assert v == '42', 'get int as str'
    v = amd.get_str(md, ['cccc', 'bbbb'])
    assert v == 'hello', 'get two keys'
    v = amd.get_str(md, 'cccc')
    assert v == None, 'get invalid key'
    v = amd.get_str(md, 'cccc', default='-')
    assert v == '-', 'get default'
    v = amd.get_str(None, 'cccc')
    assert v == None, 'get None from None metadata'
    v = amd.get_str(md, 'bbbb', remove=True)
    assert not 'bbbb' in md

    
def test_gain():
    md = dict(Gain='1.42mV')
    f, u = amd.get_gain(md)
    assert f == 1.42
    assert u == 'mV'
    r = amd.update_gain(md, 2)
    assert r, 'update_gain()'
    assert md['Gain'] == '0.710mV'
    r = amd.update_gain(md, 2, 'gain')
    assert r, 'update_gain()'
    assert md['Gain'] == '0.3550mV'
    r = amd.update_gain(None, 2)
    assert not r, 'update_gain()'
    
    md = dict(Gain='1.42mV/V')
    f, u = amd.get_gain(md)
    assert f == 1.42
    assert u == 'mV'
    amd.update_gain(md, 2)
    assert md['Gain'] == '0.710mV'
    
    md = dict(Artist='John Doe', Recording=dict(gain='1.4mV'))
    f, u = amd.get_gain(md)
    assert f == 1.4
    assert u == 'mV'
    amd.update_gain(md, 2)
    assert md['Recording']['gain'] == '0.70mV'
    
    md = dict(Gain=1.4)
    f, u = amd.get_gain(md)
    assert f == 1.4
    assert u == ''
    amd.update_gain(md, 2)
    assert md['Gain'] == 0.7
    
    md = dict(Gain=3)
    f, u = amd.get_gain(md)
    assert f == 3
    assert u == ''
    amd.update_gain(md, 2)
    assert md['Gain'] == 1.5
    
    md = dict(Gain='ms')
    f, u = amd.get_gain(md)
    assert f == None
    assert u == 'ms'
    r = amd.update_gain(md, 2)
    assert md['Gain'] == 'ms'
    assert r == False
    
    md = dict(Artist='John Doe', Recording=dict(xgain='1.4mV'))
    f, u = amd.get_gain(md)
    assert f == None
    assert u == ''
    r = amd.update_gain(md, 2)
    assert md['Recording']['xgain'] == '1.4mV'
    assert r == False
    f, u = amd.get_gain(md, 'xgain', remove=True)
    assert not 'xgain' in md['Recording']

    f, u = amd.get_gain(None)
    assert f == None
    assert u == ''

    
def test_bext_history_str():
    s = amd.bext_history_str('PCM_32', 44100, 2)
    assert s == 'A=PCM,F=44100,W=32,M=stereo', 'bext_add_history'
    s = amd.bext_history_str('PCM_32', 44100, 2, 'free')
    assert s == 'A=PCM,F=44100,W=32,M=stereo,T=free', 'bext_add_history'
    s = amd.bext_history_str('PCM_32', 44100, 1)
    assert s == 'A=PCM,F=44100,W=32,M=mono', 'bext_add_history'
    s = amd.bext_history_str('PCM_32', 44100, 3)
    assert s == 'A=PCM,F=44100,W=32', 'bext_add_history'
    s = amd.bext_history_str('PCM_24', 96000, 3)
    assert s == 'A=PCM,F=96000,W=24', 'bext_add_history'
    s = amd.bext_history_str('ALAW', 96000, 1)
    assert s == 'A=ALAW,F=96000,M=mono', 'bext_add_history'

    
def test_add_history():
    r = amd.add_history(None, 'just a snippet')
    assert not r, 'add_history()'
    md = dict(aaa='xyz', BEXT=dict(CodingHistory='original recordings'))
    r = amd.add_history(md, 'just a snippet')
    assert r, 'add_history()'
    assert md['BEXT']['CodingHistory'] == 'original recordings\r\njust a snippet', 'added history'
    md = dict(aaa='xyz', BEXT=dict(CodingHistory='original recordings'))
    r = amd.add_history(md, 'just a snippet', history_keys='CodingHistory')
    assert r, 'add_history()'
    r = amd.add_history(md, 'just a snippet', history_keys='History')
    assert not r, 'add_history()'
    
    md = dict(aaa='xyz', BEXT=dict(OriginationDate='2024-02-12'))
    r = amd.add_history(md, 'just a snippet')
    assert not r, 'add_history() no field'
    
    r = amd.add_history(md, 'just a snippet', 'BEXT.CodingHistory')
    assert r == True, 'add_history() added missing field'
    assert md['BEXT']['CodingHistory'] == 'just a snippet', 'added history'
    
    md = dict(aaa='xyz', BEXT=dict(OriginationDate='2024-02-12'))
    r = amd.add_history(md, 'just a snippet', 'BEXT.CodingHistory', 'original')
    assert r == True, 'add_history() added missing field'
    assert md['BEXT']['CodingHistory'] == 'original\r\njust a snippet', 'added history and pre-history'

     
def test_add_unwrap():
     md = dict(Recording=dict(Time='early'))
     amd.add_unwrap(md, 0.4)
     assert md['UnwrapThreshold'] == '0.40', 'added unwrap threshold'
     amd.add_unwrap(md, 0.6, 0.8)
     assert md['UnwrapThreshold'] == '0.60', 'added unwrap threshold and clip'
     assert md['UnwrapClippedAmplitude'] == '0.80', 'added unwrap threshold and clip'
     amd.add_unwrap(md, 120, 160, 'mV')
     assert md['UnwrapThreshold'] == '120.00mV', 'added unwrap threshold and clip and unit'
     assert md['UnwrapClippedAmplitude'] == '160.00mV', 'added unwrap threshold and clip and unit'
     
     md = dict(INFO=dict(Time='early'))
     amd.add_unwrap(md, 0.4)
     assert md['INFO']['UnwrapThreshold'] == '0.40', 'added unwrap threshold'
     amd.add_unwrap(md, 0.6, 0.8)
     assert md['INFO']['UnwrapThreshold'] == '0.60', 'added unwrap threshold and clip'
     assert md['INFO']['UnwrapClippedAmplitude'] == '0.80', 'added unwrap threshold and clip'

     amd.add_unwrap(None, 0.6, 0.8)
     
     
def test_remove_metadata():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)))
    amd.remove_metadata(md, ('ccc',))
    assert 'ccc' not in md['bbbb'], 'remove metadata'
    amd.remove_metadata(md, ('xxx',))
    amd.remove_metadata(md, 'eee')
    assert 'eee' not in md['bbbb'], 'remove metadata section'
    amd.remove_metadata(None, ('ccc',))

     
def test_cleanup_metadata():
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict()))
    amd.cleanup_metadata(md)
    assert 'eee' not in md['bbbb'], 'cleanup metadata'
    amd.cleanup_metadata(None)


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
    with pytest.raises(SystemExit):
        #amd.main()
        amd.main('-h')
    with pytest.raises(SystemExit):
        amd.main('--help')
    with pytest.raises(SystemExit):
        amd.main('--version')
    amd.main('test.wav')
    amd.main('test.wav', 'test.wav')
    amd.main('-f', 'test.wav')
    amd.main('-m', 'test.wav')
    amd.main('-c', 'test.wav')
    amd.main('-t', 'test.wav')
    amd.main('-t', 'test.wav', 'test.wav')
    amd.main('-m', '-c', 'test.wav')
    aw.write_audio(filename, data, rate, md, locs)
    amd.main('test.wav')
    os.remove('test.wav')


