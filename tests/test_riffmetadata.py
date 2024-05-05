import pytest
import os
import numpy as np
import audioio.riffmetadata as rm


def generate_data():
    duration = 2.0
    rate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    return data, rate


def test_write():
    data, rate = generate_data()
    filename = 'test.wav'
    for encoding in ['PCM_16', 'PCM_32']:
        rm.write_wave(filename, data, rate, None, encoding=encoding)
    with pytest.raises(ValueError):
        rm.write_wave('', data, rate, None, encoding=encoding)
    with pytest.raises(ValueError):
        rm.write_wave(filename, data, rate, None, encoding='XYZ')
    with open(filename, 'wb') as df:
        rm.write_riff_chunk(df, 1000)
        rm.write_riff_chunk(df)
        rm.write_riff_chunk(df, 1000, '1234')
        with pytest.raises(ValueError):
            rm.write_riff_chunk(df, 2000, tag='12345')
        rm.write_chunk_name(df, 12, '1234')
        with pytest.raises(ValueError):
            rm.write_chunk_name(df, 12, '123456')
        n, t = rm.write_info_chunk(df, None)
        assert n == 0, 'no info chunk'
        assert len(t) == 0, 'no info chunk'
        n, t = rm.write_info_chunk(df, dict(INFO=dict(IART='John Doe', TITLX='TLDR')))
        assert n == 0, 'no info chunk'
        assert len(t) == 0, 'no info chunk'
        n, t = rm.write_bext_chunk(df, None)
        assert n == 0, 'no bext chunk'
        assert len(t) == 0, 'no bext chunk'
        n, t = rm.write_ixml_chunk(df, None)
        assert n == 0, 'no ixml chunk'
        assert len(t) == 0, 'no ixml chunk'
        n, t = rm.write_guano_chunk(df, None)
        assert n == 0, 'no guano chunk'
        assert len(t) == 0, 'no odml chunk'
        n = rm.write_cue_chunk(df, None)
        assert n == 0, 'no cue chunk'
        with pytest.raises(IndexError):
            rm.append_markers_riff(df, np.ones((4, 2)), np.zeros(3))
    with pytest.raises(ValueError):
        rm.append_riff('')
    with pytest.raises(IndexError):
        rm.append_riff(filename, None, np.ones((4, 2)), np.zeros(3))
    md = dict(Artist='John Doe')
    rm.append_riff(filename, md, np.ones((4, 2), dtype=int), np.zeros(4))
    rm.append_riff(filename, md, np.ones((4, 2), dtype=int), np.zeros(4))
    os.remove(filename)


def test_read():
    data, rate = generate_data()
    md = dict(Artist='John Doe')
    filename = 'test.wav'
    rm.write_wave(filename, data, rate, md)
    with open(filename, 'rb') as sf:
        n = rm.read_riff_header(sf)
        assert n > 0, 'riff header'
    with open(filename, 'rb') as sf:
        n = rm.read_riff_header(sf, 'WAVE')
        assert n > 0, 'riff header'
    with open(filename, 'rb') as sf:
        with pytest.raises(ValueError):
            rm.read_riff_header(sf, 'XYZ ')
    chunks = rm.read_chunk_tags(filename)
    assert len(chunks) == 3, 'chunk tags'
    with open(filename, 'rb') as sf:
        chunks = rm.read_chunk_tags(sf)
        assert len(chunks) == 3, 'chunk tags'
    os.remove(filename)

    
def test_metadata():
    data, rate = generate_data()
    filename = 'test.wav'
    imd = dict(IENG='John Doe', ICRD='2024-01-24', RATE=9,
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
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, False)
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'
    with open(filename, 'rb') as sf:
        mdd = rm.metadata_riff(sf, False)
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'
    md['INFO']['IENG'] = ''
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, True)
    assert 'INFO' in mdd, 'INFO section exists'
    md['INFO']['IENG'] = 'John Doe'

    # BEXT:
    md = dict(BEXT=bmd)
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, False)
    assert 'BEXT' in mdd, 'BEXT section exists'
    assert bmd == mdd['BEXT'], 'BEXT section matches'
    mdd = rm.metadata_riff(filename, True)
    assert 'BEXT' in mdd, 'BEXT section exists'

    # IXML:
    md = dict(IXML=xmd)
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, False)
    assert 'IXML' in mdd, 'IXML section exists'
    assert xmd == mdd['IXML'], 'IXML section matches'
    md['IXML']['Note'] = ''
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, True)
    assert 'IXML' in mdd, 'IXML section exists'
    md['IXML']['Note'] = 'still testing'

    # GUANO:
    md = dict(GUANO=dict(**iimd))
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, False)
    assert md == mdd, 'GUANO section matches'
    
    md = dict(INFO=iimd, BEXT=bmd, IXML=xmd,
              Recording=omd, Production=bmd, Notes=xmd)
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, False)
    assert 'INFO' in mdd, 'INFO section exists'
    assert iimd == mdd['INFO'], 'INFO section matches'
    assert 'BEXT' in mdd, 'BEXT section exists'
    assert bmd == mdd['BEXT'], 'BEXT section matches'
    assert 'IXML' in mdd, 'IXML section exists'
    assert xmd == mdd['IXML'], 'IXML section matches'
    assert 'Recording' in mdd, 'Recording section exists'
    assert 'Production' in mdd, 'Production section exists'
    assert 'Notes' in mdd, 'Notes section exists'
    assert md['Notes'] == mdd['Notes'], 'Notes section matches'
    md = dict(Recording=omd, Production='', Notes=xmd)
    rm.write_wave(filename, data, rate, md)
    mdd = rm.metadata_riff(filename, True)
    assert len(mdd['Production']) == 0, 'Empty Production value'

    # INFO:
    imd['SUBI'] = bmd
    md = dict(INFO=imd)
    rm.write_wave(filename, data, rate, md)

    # BEXT:
    bmd['xxx'] = 'no bext'
    md = dict(BEXT=bmd)
    rm.write_wave(filename, data, rate, md)
    
    rm.metadata_riff(filename, True)
    os.remove(filename)

    
def test_markers():
    data, rate = generate_data()
    locs = np.random.randint(10, len(data)-10, (5, 2))
    locs = locs[np.argsort(locs[:,0]),:]
    locs[:,1] = np.random.randint(0, 20, len(locs))
    labels = np.zeros((len(locs), 2), dtype=np.object_)
    for i in range(len(labels)):
        labels[i,0] = chr(ord('a') + i % 26)
        labels[i,1] = chr(ord('A') + i % 26)*5
    filename = 'test.wav'
    
    rm.write_wave(filename, data, rate, None, locs)
    llocs, llabels = rm.markers_riff(filename)
    assert len(llabels) == 0, 'no labels'
    assert np.all(locs == llocs), 'same locs'
    
    rm.write_wave(filename, data, rate, None, locs[:,0])
    llocs, llabels = rm.markers_riff(filename)
    assert len(llabels) == 0, 'no labels'
    assert len(llocs) == len(locs), 'same number of locs'
    assert np.all(locs[:,0] == llocs[:,0]), 'same locs'
    
    rm.write_wave(filename, data, rate, None, locs, labels)
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels == llabels), 'same labels'
    
    rm.write_wave(filename, data, rate, None, locs, labels, marker_hint='cue')
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs == llocs), 'same locs in cue lists'
    assert np.all(labels == llabels), 'same labels in cue lists'

    with open(filename, 'rb') as sf:
        llocs, llabels = rm.markers_riff(sf)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels == llabels), 'same labels'
    
    rm.write_wave(filename, data, rate, None, locs, labels, marker_hint='lbl')
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs == llocs), 'same locs in lbl chunk'
    assert np.all(labels[:,1] == llabels[:,1]), 'same texts in lbl chunk'
    assert np.all(llabels[llocs[:,1] > 0,0] == 'M'), 'M labels in lbl chunk'
    assert np.all(llabels[llocs[:,1] == 0,0] == labels[llocs[:,1] == 0,0]), 'same labels in lbl chunk'
    
    with pytest.raises(IndexError):
        rm.write_wave(filename, data, rate, None, locs, labels[:-2,:])
    
    rm.write_wave(filename, data, rate, None, locs, labels[:,0])
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels[:,0] == llabels[:,0]), 'same labels'
    
    rm.write_wave(filename, data, rate, None, locs[:,0], labels[:,0])
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs[:,0] == llocs[:,0]), 'same locs'
    assert np.all(labels[:,0] == llabels[:,0]), 'same labels'
    
    labels = np.zeros((len(locs), 2), dtype=np.object_)
    rm.write_wave(filename, data, rate, None, locs, labels)
    llocs, llabels = rm.markers_riff(filename)
    assert np.all(locs == llocs), 'same locs'
    assert len(llabels) == 0, 'no labels'

    locs[:,-1] = 0
    rm.write_wave(filename, data, rate, None, locs)
    llocs, llabels = rm.markers_riff(filename)
    assert len(llabels) == 0, 'no labels'
    assert np.all(locs == llocs), 'same locs'

    os.remove(filename)

    
def test_main():
    rm.main('-h')
    rm.main()
    rm.main('test.wav')
    os.remove('test.wav')


