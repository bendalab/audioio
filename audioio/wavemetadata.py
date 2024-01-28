"""Read meta data and marker lists from wave files.

- `metadata_wave()`: read metadata of a wave file.


## Documentation of wave file format

- https://de.wikipedia.org/wiki/RIFF_WAVE
- http://www.piclist.com/techref/io/serial/midi/wave.html

For wave chunks see:

- https://www.recordingblogs.com/wiki/cue-chunk-of-a-wave-file
- http://fhein.users.ak.tu-berlin.de/Alias/Studio/ProTools/audio-formate/wav/overview.html
- http://www.gallery.co.uk/ixml/

For tag names see:

- see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
"""

import warnings
import struct
import numpy as np
import xml.etree.ElementTree as ET


info_tags = dict(AGES='Rated',
                 CMNT='Comment',
                 CODE='EncodedBy',
                 COMM='Comments',
                 DIRC='Directory',
                 DISP='SoundSchemeTitle',
                 DTIM='DateTimeOriginal',
                 GENR='Genre',
                 IARL='ArchivalLocation',
                 IART='Artist',
                 IAS1='FirstLanguage',
                 IAS2='SecondLanguage',
                 IAS3='ThirdLanguage',
                 IAS4='FourthLanguage',
                 IAS5='FifthLanguage',
                 IAS6='SixthLanguage',
                 IAS7='SeventhLanguage',
                 IAS8='EighthLanguage',
                 IAS9='NinthLanguage',
                 IBSU='BaseURL',
                 ICAS='DefaultAudioStream',
                 ICDS='ConstumeDesigner',
                 ICMS='Commissioned',
                 ICMT='Comment',
                 ICNM='Cinematographer',
                 ICNT='Country',
                 ICOP='Copyright',
                 ICRD='DateCreated',
                 ICRP='Cropped',
                 IDIM='Dimensions',
                 IDIT='DateTimeOriginal',
                 IDPI='DotsPerInch',
                 IDST='DistributedBy',
                 IEDT='EditedBy',
                 IENC='EncodedBy',
                 IENG='Engineer',
                 IGNR='Genre',
                 IKEY='Keywords',
                 ILGT='Lightness',
                 ILGU='LogoURL',
                 ILIU='LogoIconURL',
                 ILNG='Language',
                 IMBI='MoreInfoBannerImage',
                 IMBU='MoreInfoBannerURL',
                 IMED='Medium',
                 IMIT='MoreInfoText',
                 IMIU='MoreInfoURL',
                 IMUS='MusicBy',
                 INAM='Title',
                 IPDS='ProductionDesigner',
                 IPLT='NumColors',
                 IPRD='Product',
                 IPRO='ProducedBy',
                 IRIP='RippedBy',
                 IRTD='Rating',
                 ISBJ='Subject',
                 ISFT='Software',
                 ISGN='SecondaryGenre',
                 ISHP='Sharpness',
                 ISMP='TimeCode',                 
                 ISRC='Source',
                 ISRF='SourceFrom',
                 ISTD='ProductionStudio',
                 ISTR='Starring',
                 ITCH='Technician',
                 ITRK='TrackNumber',
                 IWMU='WatermarkURL',
                 IWRI='WrittenBy',
                 LANG='Language',
                 LOCA='Location',
                 PRT1='Part',
                 PRT2='NumberOfParts',
                 RATE='Rate',
                 START='Starring',
                 STAT='Statistics',
                 TAPE='TapeName',
                 TCDO='EndTimecode',
                 TCOD='StartTimecode',
                 TITL='Title',
                 TLEN='Length',
                 TORG='Organization',
                 TRCK='TrackNumber',
                 TURL='URL',
                 TVER='Version',
                 VMAJ='VegasVersionMajor',
                 VMIN='VegasVersionMinor',
                 YEAR='Year',
                 IBRD='uCBoard',
                 IMAC='MACAdress')
"""Tags of the INFO chunk and their description.

See https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
"""

bext_tags = dict(
    Description=256,
    Originator=32,
    OriginatorReference=32,
    OriginationDate=10,
    OriginationTime=8,
    TimeReference=8,
    Version=2,
    UMID=64,
    LoudnessValue=2,
    LoudnessRange=2,
    MaxTruePeakLevel=2,
    MaxMomentaryLoudness=2,
    MaxShortTermLoudness=2,
    Reserved=180,
    CodingHistory=0)
"""Tags of the BEXT chunk and their size in bytes.

See https://tech.ebu.ch/docs/tech/tech3285.pdf
"""

ixml_tags = [
    'BWFXML',
    'IXML_VERSION',
    'PROJECT',
    'SCENE',
    'TAPE',
    'TAKE',
    'TAKE_TYPE',
    'NO_GOOD',
    'FALSE_START',
    'WILD_TRACK',
    'CIRCLED',
    'FILE_UID',
    'UBITS',
    'NOTE',
    'SYNC_POINT_LIST',
    'SYNC_POINT_COUNT',
    'SYNC_POINT',
    'SYNC_POINT_TYPE',
    'SYNC_POINT_FUNCTION',
    'SYNC_POINT_COMMENT',
    'SYNC_POINT_LOW',
    'SYNC_POINT_HIGH',
    'SYNC_POINT_EVENT_DURATION',
    'SPEED',
    'MASTER_SPEED',
    'CURRENT_SPEED',
    'TIMECODE_RATE',
    'TIMECODE_FLAGS',
    'FILE_SAMPLE_RATE',
    'AUDIO_BIT_DEPTH',
    'DIGITIZER_SAMPLE_RATE',
    'TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_HI',
    'TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_LO',
    'TIMESTAMP_SAMPLE_RATE',
    'LOUDNESS',
    'LOUDNESS_VALUE',
    'LOUDNESS_RANGE',
    'MAX_TRUE_PEAK_LEVEL',
    'MAX_MOMENTARY_LOUDNESS',
    'MAX_SHORT_TERM_LOUDNESS',
    'HISTORY',
    'ORIGINAL_FILENAME',
    'PARENT_FILENAME',
    'PARENT_UID',
    'FILE_SET',
    'TOTAL_FILES',
    'FAMILY_UID',
    'FAMILY_NAME',
    'FILE_SET_INDEX',
    'TRACK_LIST',
    'TRACK_COUNT',
    'TRACK',
    'CHANNEL_INDEX',
    'INTERLEAVE_INDEX',
    'NAME',
    'FUNCTION',
    'PRE_RECORD_SAMPLECOUNT',
    'BEXT',
    'BWF_DESCRIPTION',
    'BWF_ORIGINATOR',
    'BWF_ORIGINATOR_REFERENCE',
    'BWF_ORIGINATION_DATE',
    'BWF_ORIGINATION_TIME',
    'BWF_TIME_REFERENCE_LOW',
    'BWF_TIME_REFERENCE_HIGH',
    'BWF_VERSION',
    'BWF_UMID',
    'BWF_RESERVED',
    'BWF_CODING_HISTORY',
    'BWF_LOUDNESS_VALUE',
    'BWF_LOUDNESS_RANGE',
    'BWF_MAX_TRUE_PEAK_LEVEL',
    'BWF_MAX_MOMENTARY_LOUDNESS',
    'BWF_MAX_SHORT_TERM_LOUDNESS',
    'USER',
    'FULL_TITLE',
    'DIRECTOR_NAME',
    'PRODUCTION_NAME',
    'PRODUCTION_ADDRESS',
    'PRODUCTION_EMAIL',
    'PRODUCTION_PHONE',
    'PRODUCTION_NOTE',
    'SOUND_MIXER_NAME',
    'SOUND_MIXER_ADDRESS',
    'SOUND_MIXER_EMAIL',
    'SOUND_MIXER_PHONE',
    'SOUND_MIXER_NOTE',
    'AUDIO_RECORDER_MODEL',
    'AUDIO_RECORDER_SERIAL_NUMBER',
    'AUDIO_RECORDER_FIRMWARE',
    'LOCATION',
    'LOCATION_NAME',
    'LOCATION_GPS',
    'LOCATION_ALTITUDE',
    'LOCATION_TYPE',
    'LOCATION_TIME',
    ]
"""Valid tags of the iXML chunk.

See http://www.gallery.co.uk/ixml/
"""


# Read wave file:

def read_riff_chunk(sf):
    """ Read and check the RIFF file header.

    Parameters
    ----------
    sf: stream
        File stream of wave file.

    Returns
    -------
    filesize: int
        Size of the wave file in bytes.

    Raises
    ------
    ValueError
        Not a RIFF or WAVE file.
    """
    str1 = sf.read(4).decode('latin-1')
    if str1 != 'RIFF':
        raise ValueError("Not a RIFF file.")
    fsize = struct.unpack('<I', sf.read(4))[0] + 8
    str2 = sf.read(4).decode('latin-1')
    if str2 != 'WAVE':
        raise ValueError("Not a WAVE file.")
    return fsize


def skip_chunk(sf):
    """Skip over unknown chunk.
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    """
    data = sf.read(4)
    size = struct.unpack('<I', data)[0]
    size += size % 2 
    sf.seek(size, 1)

            
def read_info_chunks(sf, store_empty):
    """ Read in meta data from info list chunk.

    See https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    metadata: dict
        Dictinary with key-value pairs of info tags.
    """
    md = {}
    list_size = struct.unpack('<I', sf.read(4))[0]
    list_type = sf.read(4).decode('latin-1').upper()
    list_size -= 4
    if list_type == 'INFO':
        while list_size >= 8:
            key = sf.read(4).decode('latin-1').rstrip(' \x00')
            size = struct.unpack('<I', sf.read(4))[0]
            size += size % 2
            value = sf.read(size).decode('latin-1').rstrip(' \x00')
            list_size -= 8 + size
            if key in info_tags:
                key = info_tags[key]
            if value or store_empty:
                md[key] = value
    if list_size > 0:  # finish or skip
        sf.seek(list_size, 1)
    return md

    
def read_cue_chunk(sf):
    """ Read in marker ids and positions from cue chunk.
    
    See https://www.recordingblogs.com/wiki/cue-chunk-of-a-wave-file

    Parameters
    ----------
    sf: stream
        File stream of wave file.

    Returns
    -------
    locs: 2-D array of ints
        Each row is a marker with unique identifier in the first column,
        position in the second column, and span in the third column.
        The cue chunk does not encde spans, so the third column is
        initilazied with zeros.
    """
    locs = []
    size, n = struct.unpack('<II', sf.read(8))
    for c in range(n):
        cpid, cppos = struct.unpack('<II', sf.read(8))
        datachunkid = sf.read(4).decode('latin-1').rstrip(' \x00').upper()
        chunkstart, blockstart, offset = struct.unpack('<III', sf.read(12))
        if datachunkid == 'DATA':
            locs.append((cpid, cppos, 0))
    return np.array(locs, dtype=int)

        
def read_playlist_chunk(sf, locs):
    """ Read in marker spans from playlist chunk.
    
    See https://www.recordingblogs.com/wiki/playlist-chunk-of-a-wave-file

    Parameters
    ----------
    sf: stream
        File stream of wave file.
    locs: 2-D array of ints
        Markers as returned by the `read_cue_chunk()` function.
        Each row is a marker with unique identifier in the first column,
        position in the second column, and span in the third column.
        The span is read in from the playlist chunk.
    """
    if len(locs) == 0:
        warnings.warn('read_playlist_chunks() requires markers from a previous cue chunk')
    size, n = struct.unpack('<II', sf.read(8))
    for p in range(n):
        cpid, length, repeats = struct.unpack('<III', sf.read(12))
        i = np.where(locs[:,0] == cpid)[0]
        if len(i) > 0:
            locs[i[0], 2] = length


def read_adtl_chunks(sf, locs, labels):
    """ Read in associated data list chunks.

    See https://www.recordingblogs.com/wiki/associated-data-list-chunk-of-a-wave-file
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    locs: 2-D array of ints
        Markers as returned by the `read_cue_chunk()` function.
        Each row is a marker with unique identifier in the first column,
        position in the second column, and span in the third column.
        The span is read in from the LTXT chunk.
    labels: 2-D array of string objects
        Labels (first column) and texts (second column) for each marker (rows)
        from previous LABL, NOTE, and LTXT chunks.

    Returns
    -------
    labels: 2-D array of string objects
        Labels (first column) and texts (second column) for each marker (rows)
        from LABL, NOTE, and LTXT chunks.
    """
    if len(locs) == 0:
        warnings.warn('read_adtl_chunks() requires markers from a previous cue chunk')
    if len(labels) == 0:
        labels = np.zeros((len(locs), 2), dtype=np.object_)
    list_size = struct.unpack('<I', sf.read(4))[0]
    list_type = sf.read(4).decode('latin-1').upper()
    list_size -= 4
    if list_type == 'ADTL':
        while list_size >= 8:
            key = sf.read(4).decode('latin-1').rstrip(' \x00').upper()
            size, cpid = struct.unpack('<II', sf.read(8))
            size += size % 2 - 4
            if key == 'LABL' or key == 'NOTE':
                label = sf.read(size).decode('latin-1').rstrip(' \x00')
                i = np.where(locs[:,0] == cpid)[0]
                if len(i) > 0:
                    i = i[0]
                    if len(labels[i,0]) > 0:
                        labels[i,0] += '|'
                        labels[i,0] += label
            elif key == 'LTXT':
                length = struct.unpack('<I', sf.read(4))[0]
                sf.read(12)  # skip fields
                text = sf.read(size - 4 - 12).decode('latin-1').rstrip(' \x00')
                i = np.where(locs[:,0] == cpid)[0][0]
                if len(i) > 0:
                    i = i[0]
                    if len(labels[i,1]) > 0:
                        labels[i,1] += '|'
                        label[i,1] += text
                        locs[i,2] = length
            else:
                sf.read(size)
            list_size -= 12 + size
    if list_size > 0:  # finish or skip
        sf.seek(list_size, 1)
    return labels


def read_bext_chunk(sf, store_empty=True):
    """ Read in meta-data from the broadcast-audio extension chunk.

    See https://tech.ebu.ch/docs/tech/tech3285.pdf for specifications.
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    meta_data: dict
        - 'Description': a free description of the sequence.
        - 'Originator': name of the originator/ producer of the audio file.
        - 'OriginatorReference': unambiguous reference allocated by the originating organisation.
        - 'OriginationDate': date of creation of audio sequence in yyyy:mm:dd.
        - 'OriginationTime': time of creation of audio sequence in hh:mm:ss.
        - 'TimeReference': first sample since midnight.
        - 'Version': version of the BWF.
        - 'UMID': unique material identifier.
        - 'LoudnessValue': integrated loudness value.
        - 'LoudnessRange':  loudness range.
        - 'MaxTruePeakLevel': maximum true peak value in dBTP.
        - 'MaxMomentaryLoudness': highest value of the momentary loudness level.
        - 'MaxShortTermLoudness': highest value of the short-term loudness level.
        - 'Reserved': 180 bytes reserved for extension.
        - 'CodingHistory': description of coding processed applied to the audio data.
    """
    md = {}
    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    s = sf.read(256).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['Description'] = s
    s = sf.read(32).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['Originator'] = s
    s = sf.read(32).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['OriginatorReference'] = s
    s = sf.read(10).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['OriginationDate'] = s
    s = sf.read(8).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['OriginationTime'] = s
    reference, version = struct.unpack('<QH', sf.read(10))
    if reference > 0 or store_empty:
        md['TimeReference'] = reference
    if version > 0 or store_empty:
        md['Version'] = version
    s = sf.read(64).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['UMID'] = s
    lvalue, lrange, peak, momentary, shortterm = struct.unpack('<hhhhh', sf.read(10))
    if lvalue > 0 or store_empty:
        md['LoudnessValue'] = lvalue
    if lrange > 0 or store_empty:
        md['LoudnessRange'] = lrange
    if peak > 0 or store_empty:
        md['MaxTruePeakLevel'] = peak
    if momentary > 0 or store_empty:
        md['MaxMomentaryLoudness'] = momentary
    if shortterm > 0 or store_empty:
        md['MaxShortTermLoudness'] = shortterm
    s = sf.read(180).decode('latin-1').rstrip(' \x00')
    if s or store_empty:
        md['Reserved'] = s
    size -= 256 + 32 + 32 + 10 + 8 + 8 + 2 + 64 + 10 + 180
    s = sf.read(size).decode('latin-1').rstrip(' \x00\n\r')
    if s or store_empty:
        md['CodingHistory'] = s
    return md


def read_ixml_chunk(sf, store_empty=True):
    """ Read in meta-data from an IXML chunk.

    See http://www.gallery.co.uk/ixml/ for the specification of iXML.
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    metadata: nested dict
        Dictinary with key-value pairs.
    """
    
    def parse_ixml(element, store_empty=True):
        md = {}
        for e in element:
            if not e.text is None:
                md[e.tag] = e.text
            elif len(e) > 0:
                md[e.tag] = parse_ixml(e, store_empty)
            elif store_empty:
                md[e.tag] = ''
        return md

    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    xmls = sf.read(size).decode('latin-1').rstrip(' \x00')
    root = ET.fromstring(xmls)
    md = {root.tag: parse_ixml(root, store_empty)}
    if len(md) == 1 and 'BWFXML' in md:
        md = md['BWFXML']
    return md


def read_odml_chunk(sf, store_empty=True):
    """ Read in meta-data from an ODML chunk.

    For storing any type of nested key-value pairs we define a new 
    ODML chunk holding the metadata as XML according to the odML data model.
    For a description of odML see https://doi.org/10.3389/fninf.2011.00016 and
    https://github.com/G-Node/python-odml
    
    Parameters
    ----------
    sf: stream
        File stream of wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    metadata: nested dict
        Dictinary with key-value pairs.
    """

    def parse_odml(element, store_empty=True):
        print()
        md = {}
        for e in element:
            if e.tag == 'Section':
                md[e.attrib['name']] = parse_odml(e, store_empty)
            elif e.tag == 'Property':
                v = ''
                if len(e) > 0 and e[0].tag == 'Value' and 'value' in e[0].attrib:
                    v = e[0].attrib['value']
                if len(v) > 0 or store_empty:
                    md[e.attrib['name']] = v
        return md

    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    xmls = sf.read(size).decode('latin-1').rstrip(' \x00')
    root = ET.fromstring(xmls)
    md = {root.tag: parse_odml(root, store_empty)}
    if len(md) == 1 and 'odML' in md:
        md = md['odML']
    return md


def metadata_wave(filepath, store_empty=False):
    """ Read metadata of a wave file.

    Parameters
    ----------
    filepath: string or file handle
        The wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    meta_data: nested dict
        Meta data contained in the wave file.  Keys of the nested
        dictionaries are always strings.  If the corresponding
        values are dictionaries, then the key is the section name
        of the metadata contained in the dictionary. All other
        types of values are values for the respective key. In
        particular they are strings, or list of strings. But other
        simple types like ints or floats are also allowed.
        First level contains sections of meta data
        (keys 'INFO' or 'BEXT', values are dictionaries).

    Raises
    ------
    ValueError
        Not a wave file.
    """            
    meta_data = {}
    sf = filepath
    file_pos = None
    if hasattr(filepath, 'read'):
        file_pos = sf.tell()
        sf.seek(0, 0)
    else:
        sf = open(filepath, 'rb')
    fsize = read_riff_chunk(sf)
    while (sf.tell() < fsize - 8):
        chunk = sf.read(4).decode('latin-1').upper()
        if chunk == 'LIST':
            md = read_info_chunks(sf, store_empty)
            if len(md) > 0:
                meta_data['INFO'] = md
        elif chunk == 'BEXT':
            md = read_bext_chunk(sf, store_empty)
            if len(md) > 0:
                meta_data['BEXT'] = md
        elif chunk == 'IXML':
            md = read_ixml_chunk(sf, store_empty)
            if len(md) > 0:
                meta_data['IXML'] = md
        elif chunk == 'ODML':
            md = read_odml_chunk(sf, store_empty)
            if len(md) > 0:
                meta_data.update(md)
        else:
            skip_chunk(sf)
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, 0)
    return meta_data


def markers_wave(filepath):
    """ Read markers from a wave file.

    Parameters
    ----------
    filepath: string or file handle
        The wave file.

    Returns
    -------
    locs: 2-D array of ints
        Positions (first column) and spans (second column)
        for each marker (rows).
    labels: 2-D array of string objects
        Labels (first column) and texts (second column) for each marker (rows).

    Raises
    ------
    ValueError
        Not a wave file.
    """            
    sf = filepath
    file_pos = None
    if hasattr(filepath, 'read'):
        file_pos = sf.tell()
        sf.seek(0, 0)
    else:
        sf = open(filepath, 'rb')
    locs = np.zeros((0, 3), dtype=int)
    labels = np.zeros((0, 2), dtype=np.object_)
    fsize = read_riff_chunk(sf)
    while (sf.tell() < fsize - 8):
        chunk = sf.read(4).decode('latin-1').upper()
        if chunk == 'CUE ':
            locs = read_cue_chunk(sf)
        elif chunk == 'PLST':
            read_playlist_chunk(sf, locs)
        elif chunk == 'LIST':
            labels = read_adtl_chunks(sf, locs, labels)
        else:
            skip_chunk(sf)
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, 0)
    return locs[:,1:], labels


# Write wave file:

def write_riff_chunk(df, filesize=0):
    """ Write RIFF file header.

    Parameters
    ----------
    df: stream
        File stream for writing RIFF file header.
    filesize: int
        Size of the file in bytes.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    if filesize < 8:
        filesize = 8
    df.write(b'RIFF')
    df.write(struct.pack('<I', filesize - 8))
    df.write(b'WAVE')
    return 12


def write_filesize(df, filesize=None):
    """Write the file size into the RIFF file header.

    Parameters
    ----------
    df: stream
        File stream into which to write `filesize`.
    filesize: int
        Size of the file in bytes. If not specified or 0,
        then use current size of the file.
    """
    pos = df.tell()
    if not filesize:
        df.seek(0, 2)
        filesize = df.tell()
    df.seek(4, 0)
    df.write(struct.pack('<I', filesize - 8))
    df.seek(pos, 0)


def write_fmt_chunk(df, channels, frames, samplerate, bits=16):
    """ Write FMT chunk.

    Parameters
    ----------
    df: stream
        File stream for writing FMT chunk.
    channels: int
        Number of channels contained in the data.
    frames: int
        Number of frames contained in the data.
    samplerate: int or float
        Sampling rate (frames per time) in Hertz.
    bits: 16 or 32
        Bit resolution of the data to be written.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    blockalign = channels * (bits//8)
    byterate = int(samplerate) * blockalign
    df.write(b'fmt ')
    df.write(struct.pack('<IHHIIHH', 16, 1, channels, int(samplerate),
                         byterate, blockalign, bits))
    return 8 + 16


def write_data_chunk(df, data, bits=16):
    """ Write data chunk.

    Parameters
    ----------
    df: stream
        File stream for writing data chunk.
    data: 1-D or 2-D array of floats
        Data with first column time (frames) and optional second column
        channels with values between -1 and 1.
    bits: 16 or 32
        Bit resolution of the data to be written.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    df.write(b'data')
    df.write(struct.pack('<I', data.size * (bits//8)))
    buffer = data * 2**(bits-1)
    n = df.write(buffer.astype(f'<i{bits//8}').tobytes('C'))
    return 8 + n


def write_info_chunk(df, metadata):
    """Write metadata to LIST INFO chunk.

    If `metadata` contains an 'INFO' key, then write the flat
    dictionary of this key as an INFO chunk. Otherwise, attempt to
    write all m̀etadata` items as an INFO chunk. The keys are
    translated via `info_tags` back to INFO tags. If after translation
    any key is left that is longer than 4 characters or any key has a
    dictionary as a value (non-flat metadata), the INFO chunk is not
    written.

    See https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags

    Parameters
    ----------
    df: stream
        File stream for writing INFO chunk.
    metadata: nested dict
        Meta-data as key-value pairs. Values can be strings, integers,
        or dictionaries.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Keys written to the INFO chunk.
    """
    if metadata is None or len(metadata) == 0:
        return 0, []
    is_info = False
    if 'INFO' in metadata:
        metadata = metadata['INFO']
        is_info = True
    tags = {v: k for k, v in info_tags.items()}
    n = 0
    for k in metadata:
        kn = tags.get(k, k)
        if len(kn) > 4:
            if is_info:
                warnings.warn(f'no 4-character info tag for key "{k}" found.')
            return 0, []
        if isinstance(metadata[k], dict):
            if is_info:
                warnings.warn(f'value of info tag for key "{k}" must be a string.')
            return 0, []
        v = str(metadata[k])
        n += 8 + len(v) + len(v) % 2
    df.write(b'LIST')
    df.write(struct.pack('<I', n + 4))
    df.write(b'INFO')
    keys_written = []
    for k in metadata:
        kn = tags.get(k, k)
        df.write(f'{kn:<4s}'.encode('latin-1'))
        v = str(metadata[k])
        ns = len(v) + len(v) % 2
        df.write(struct.pack('<I', ns))
        df.write(f'{v:<{ns}s}'.encode('latin-1'))
        keys_written.append(k)
    return 12 + n, ['INFO'] if is_info else keys_written


def write_bext_chunk(df, metadata):
    """Write metadata to BEXT chunk.

    If `metadata` contains a BEXT key, and this contains valid BEXT
    tags, then write the dictionary of that key as a broadcast-audio
    extension chunk.  See https://tech.ebu.ch/docs/tech/tech3285.pdf
    for specifications.

    Parameters
    ----------
    df: stream
        File stream for writing BEXT chunk.
    metadata: nested dict
        Meta-data as key-value pairs. Values can be strings, integers,
        or dictionaries.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Keys written to the BEXT chunk.

    """
    if metadata is None or len(metadata) == 0 or not 'BEXT' in metadata:
        return 0, []
    metadata = metadata['BEXT']
    for k in metadata:
        if not k in bext_tags:
            warnings.warn(f'no bext tag for key "{k}" found.')
            return 0, []
    n = 0
    for k in bext_tags:
        n += bext_tags[k]
    ch = metadata.get('CodingHistory', '').encode('latin-1')
    nch = len(ch) + len(ch) % 2 + 2
    n += nch
    df.write(b'BEXT')
    df.write(struct.pack('<I', n))
    for k in bext_tags:
        bn = bext_tags[k]
        if bn == 2:
            v = metadata.get(k, '0')
            df.write(struct.pack('<H', int(v)))
        elif bn == 8 and k == 'TimeReference':
            v = metadata.get(k, '0')
            df.write(struct.pack('<Q', int(v)))
        elif bn == 0:
            df.write(ch)
            df.write(b'\n\r' + bytes(nch - len(ch) - 2))
        else:
            v = metadata.get(k, '').encode('latin-1')
            df.write(v + bytes(bn - len(v)))
    return 8 + n, ['BEXT']


def write_ixml_chunk(df, metadata, keys_written=None):
    """ Write metadata to iXML chunk.

    If `metadata` contains an IXML key with valid IXML tags,
    or the remaining tags in `metadata` are valid IXML tags,
    then write an IXML chunk.

    See http://www.gallery.co.uk/ixml/ for the specification of iXML.

    Parameters
    ----------
    df: stream
        File stream for writing IXML chunk.
    metadata: nested dict
        Meta-data as key-value pairs. Values can be strings, integers,
        or dictionaries.
    keys_written: list of str
        Keys that have already written to INFO or BEXT chunk.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Keys written to the IXML chunk.
    """
    def check_ixml(metadata):
        for k in metadata:
            if not k.upper() in ixml_tags:
                return False
            if isinstance(metadata[k], dict):
                if not check_ixml(metadata[k]):
                    return False
        return True
        
    def build_xml(node, metadata):
        kw = []
        for k in metadata:
            e = ET.SubElement(node, k)
            if isinstance(metadata[k], dict):
                build_xml(e, metadata[k])
            else:
                e.text = str(metadata[k]).replace('\n', '.')
            kw.append(k)
        return kw

    if metadata is None or len(metadata) == 0:
        return 0, []
    md = metadata
    if keys_written:
        md = {k: metadata[k] for k in metadata if not k in keys_written}
    if len(md) == 0:
        return 0, []
    has_ixml = False
    if 'IXML' in md and check_ixml(md['IXML']):
        md = md['IXML']
        has_ixml = True
    else:
        if not check_ixml(md):
            return 0, []
    root = ET.Element('BWFXML')
    kw = build_xml(root, md)
    bs = bytes(ET.tostring(root, xml_declaration=True,
                           short_empty_elements=False))
    if len(bs) % 2 == 1:
        bs += bytes(1)
    df.write(b'IXML')
    df.write(struct.pack('<I', len(bs)))
    df.write(bs)
    return 8 + len(bs), ['IXML'] if has_ixml else kw


def write_odml_chunk(df, metadata, keys_written=None):
    """ Write metadata to ODML chunk.

    For storing any type of nested key-value pairs we define a new 
    ODML chunk holding the metadata as XML according to the odML data model.
    For odML see https://doi.org/10.3389/fninf.2011.00016 and
    https://github.com/G-Node/python-odml

    This will write *all* metadata that are not in `keys_written`.

    Parameters
    ----------
    df: stream
        File stream for writing ODML chunk.
    metadata: nested dict
        Meta-data as key-value pairs. Values can be strings, integers,
        or dictionaries.
    keys_written: list of str
        Keys that have already written to INFO, BEXT, IXML chunk.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    def build_odml(node, metadata):
        kw = []
        for k in metadata:
            if isinstance(metadata[k], dict):
                sec = ET.SubElement(node, 'Section')
                sec.attrib = dict(name=k)
                build_odml(sec, metadata[k])
            else:
                prop = ET.SubElement(node, 'Property')
                prop.attrib = dict(name=k)
                value = ET.SubElement(prop, 'Value')
                value.attrib = dict(value=str(metadata[k]).replace('\n', '.'))
            kw.append(k)
        return kw

    if metadata is None or len(metadata) == 0:
        return 0, []
    md = metadata
    if keys_written:
        md = {k: metadata[k] for k in metadata if not k in keys_written}
    if len(md) == 0:
        return 0, []
    root = ET.Element('odML')
    kw = build_odml(root, md)
    bs = bytes(ET.tostring(root, xml_declaration=True,
                           short_empty_elements=False))
    if len(bs) % 2 == 1:
        bs += bytes(1)
    df.write(b'ODML')
    df.write(struct.pack('<I', len(bs)))
    df.write(bs)
    return 8 + len(bs), kw


def write_wave(filepath, data, samplerate, metadata=None,
               encoding=None):
    """ Write time series and metadata to a wave file.

    Only 16 or 32bit PCM encoding is supported.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    metadata: nested dict
        Meta-data as key-value pairs. Values can be strings, integers,
        or dictionaries.
    encoding: string or None
        Encoding of the data: 'PCM_32' or 'PCM_16'.
        If None or empty string use 'PCM_16'.
 
    Raises
    ------
    ValueError
        Encoding not supported.
    """
    if not filepath:
        raise ValueError('no file specified!')
    if not encoding:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    bits = 0
    if encoding == 'PCM_16':
        bits = 16
    elif encoding == 'PCM_32':
        bits = 32
    else:
        raise ValueError(f'file encoding {encoding} not supported')
    with open(filepath, 'wb') as df:
        write_riff_chunk(df)
        if data.ndim == 1:
            write_fmt_chunk(df, 1, len(data), samplerate, bits)
        else:
            write_fmt_chunk(df, data.shape[1], data.shape[0],
                            samplerate, bits)
        write_data_chunk(df, data, bits)
        # metadata INFO chunk:
        _, kw = write_info_chunk(df, metadata)
        # metadata BEXT chunk:
        _, bkw = write_bext_chunk(df, metadata)
        kw.extend(bkw)
        # metadata IXML chunk:
        _, xkw = write_ixml_chunk(df, metadata, kw)
        kw.extend(xkw)
        # write remaining metadata to ODML chunk:
        write_odml_chunk(df, metadata, kw)
        write_filesize(df)


def demo(filepath):
    """Print metadata of wave file.

    Parameters
    ----------
    filepath: string
        Path of a wave file.
    """
    # read meta data:
    meta_data = metadata_wave(filepath, store_empty=False)
    
    # print meta data:
    print()
    print('meta data:')
    for sk in meta_data:
        md = meta_data[sk]
        if isinstance(md, dict):
            print(f'{sk}:')
            for k in md:
                v = str(md[k]).replace('\n', '.')
                print(f'  {k:22}: {v}')
        else:
            v = str(md).replace('\n', '.')
            print(f'{sk}:\n  {v}')
            
    # read cues:
    locs, labels = markers_wave(filepath)
    
    # print marker table:
    if len(locs) > 0:
        print()
        print(f'{"position":10} {"span":8} {"label":10} {"text":10}')
        for i in range(len(locs)):
            print(f'{locs[i,0]:10} {locs[i,1]:8} {labels[i,0]:10} {labels[i,1]:10}')


def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        COmmand line arguments as returned by sys.argv
    """
    if len(args) > 1 and (args[1] == '-h' or args[1] == '--help'):
        print()
        print('Usage:')
        print('  python -m audioio.wavemetadata [--help] <audio/file.wav>')
        print()
        return

    if len(args) > 1:
        demo(args[1])
    else:
        rate = 44100
        t = np.arange(0, 2, 1/rate)
        x = np.sin(2*np.pi*440*t)
        imd = dict(IENG='JB', ICRD='2024-01-24', RATE=9,
                   Comment='this is test1')
        bmd = dict(Description='a recording',
                   OriginationDate='2024:01:24', TimeReference=123456,
                   Version=42, CodingHistory='Test1\nTest2')
        xmd = dict(Project='Record all', Note='still testing')
        md = dict(INFO=imd, BEXT=bmd, IXML=xmd,
                  Recording=imd, Production=bmd, Notes=xmd)
        write_wave('test.wav', x, rate, md)
        demo('test.wav')

    
if __name__ == "__main__":
    import sys
    main(*sys.argv)
