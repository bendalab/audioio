import pytest
import os
import numpy as np
import audioio.audioloader as al
import audioio.audiowriter as aw
import audioio.audiomarkers as am


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
    
    aw.write_audio(filename, data, rate, None, locs)
    llocs, llabels = al.markers(filename)
    assert len(llabels) == 0, 'no labels'
    assert np.all(locs == llocs), 'same locs'
    
    aw.write_audio(filename, data, rate, None, locs[:,0])
    llocs, llabels = al.markers(filename)
    assert len(llabels) == 0, 'no labels'
    assert np.all(locs[:,0] == llocs[:,0]), 'same locs'
    
    aw.write_audio(filename, data, rate, None, locs, labels)
    llocs, llabels = al.markers(filename)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels == llabels), 'same labels'

    with open(filename, 'rb') as sf:
        llocs, llabels = al.markers(sf)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels == llabels), 'same labels'
    
    with pytest.raises(IndexError):
        aw.write_audio(filename, data, rate, None, locs,
                       labels[:-2,:])
    
    aw.write_audio(filename, data, rate, None, locs, labels[:,0])
    llocs, llabels = al.markers(filename)
    assert np.all(locs == llocs), 'same locs'
    assert np.all(labels[:,0] == llabels[:,0]), 'same labels'
    
    aw.write_audio(filename, data, rate, None, locs[:,0], labels[:,0])
    llocs, llabels = al.markers(filename)
    assert np.all(locs[:,0] == llocs[:,0]), 'same locs'
    assert np.all(labels[:,0] == llabels[:,0]), 'same labels'

    labels = np.zeros((len(locs), 2), dtype=np.object_)
    aw.write_audio(filename, data, rate, None, locs, labels)
    llocs, llabels = al.markers(filename)
    assert np.all(locs == llocs), 'same locs'
    assert len(llabels) == 0, 'no labels'

    locs[:,-1] = 0
    aw.write_audio(filename, data, rate, None, locs)
    llocs, llabels = al.markers(filename)
    assert len(llabels) == 0, 'no labels'
    assert np.all(locs == llocs), 'same locs'

    os.remove(filename)

    filename = 'test.xyz'
    with open(filename, 'wb') as df:
        df.write(b'XYZ!')
    mmd = al.metadata(filename)
    llocs, llabels = al.markers(filename)

    os.remove(filename)

    am.print_markers(locs[:,0])
    am.print_markers(locs)
    am.print_markers(locs, labels[:,0])
    am.print_markers(locs, labels)
    filename = 'test.txt'
    am.write_markers(filename, locs, labels)
    os.remove(filename)

