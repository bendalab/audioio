"""Read and write meta data and marker lists of riff based files.

Container files of the Resource Interchange File Format (RIFF) like
WAVE files may contain sections (called chunks) with metadata and
markers in addition to the timeseries (audio) data and the necessary
specifications of sampling rate, bit depth, etc.

## Metadata

There are various types of chunks for storing metadata, like the [INFO
list](https://www.recordingblogs.com/wiki/list-chunk-of-a-wave-file),
[broadcast-audio extension
(BEXT)](https://tech.ebu.ch/docs/tech/tech3285.pdf) chunk, or
[iXML](http://www.gallery.co.uk/ixml/) chunks. These chunks contain
metadata as key-value pairs.  Since wave files are primarily designed
for music, valid keys in these chunks are restricted to topics from
music and music production. Some keys are usefull also for science,
but there is need for more keys. It is possible to extend the INFO
list keys, but these keys are restricted to four characters and the
INFO list chunk does also not allow for hierarchical metadata. The
other metadata chunks, in particular the BEXT chunk, cannot be
extended. With standard chunks, not all types of metadata can be
stored.

The [GUANO (Grand Unified Acoustic Notation
Ontology)](https://github.com/riggsd/guano-spec), primarily designed
for bat acoustic recordings, has some standard ontologies that are of
much more interest in scientific context.  In addition, GUANO allows
for extensions with arbitray nested keys and string encoded values.
In that respect it is a well defined and easy to handle serialization
of the [odML data model](https://doi.org/10.3389/fninf.2011.00016).
We use GUANO to write all metadata that do not fit into the INFO, BEXT
or IXML chunks into a WAVE file.

To interface the various ways to store and read metadata of RIFF
files, the `riffmetadata` module simply uses nested dictionaries.  The
keys are always strings. Values are strings or integers for key-value
pairs. Value strings can also be numbers followed by a unit. Values
can also be dictionaries for defining subsections of key-value
pairs. The dictionaries can be nested to arbitrary depth.

The `write_wave()` function first tries to write an INFO list
chunk. It checks for a key "INFO" with a flat dictionary of key value
pairs. It then translates all keys of this dictionary using the
`info_tags` mapping. If all the resulting keys have no more than four
characters and there are no subsections, then an INFO list chunk is
written. If no "INFO" key exists, then with the same procedure all
elements of the provided metadata are checked for being valid INFO
tags, and on success an INFO list chunk is written. Then, in similar
ways, `write_wave()` tries to assemble valid BEXT and iXML chunks,
based on the tags in `bext_tags` abd `ixml_tags`. All remaining
metadata are then stored in an GUANO chunk.

When reading metadata from a RIFF file, INFO, BEXT and iXML chunks are
returned as subsections with the respective keys. Metadata from an
GUANO chunk are stored directly in the metadata dictionary without
marking them as GUANO.

## Markers

A number of different chunk types exist for handling markers or cues
that mark specific events or regions in the audio data. In the end,
each marker has a position, a span, a label, and a text.  Position,
and span are handled with 1-D or 2-D arrays of ints, where each row is
a marker and the columns are position and span. The span column is
optional. Labels and texts come in another 1-D or 2-D array of objects
pointing to strings. Again, rows are the markers, first column are the
labels, and second column the optional texts. Try to keep the labels
short, and use text for longer descriptions, if necessary.

## Read metadata and markers

- `metadata_riff()`: read metadata from a RIFF/WAVE file.
- `markers_riff()`: read markers from a RIFF/WAVE file.

## Write data, metadata and markers

- `write_wave()`: write time series, metadata and markers to a WAVE file.
- `append_metadata_riff()`: append metadata chunks to RIFF file.
- `append_markers_riff()`: append marker chunks to RIFF file.
- `append_riff()`: append metadata and markers to an existing RIFF file.

## Helper functions for reading RIFF and WAVE files

- `read_chunk_tags()`: read tags of all chunks contained in a RIFF file.
- `read_riff_header()`: read and check the RIFF file header.
- `skip_chunk()`: skip over unknown RIFF chunk.
- `read_format_chunk()`: read format chunk.
- `read_info_chunks()`: read in meta data from info list chunk.
- `read_bext_chunk()`: read in metadata from the broadcast-audio extension chunk.
- `read_ixml_chunk()`: read in metadata from an IXML chunk.
- `read_guano_chunk()`: read in metadata from a GUANO chunk.
- `read_cue_chunk()`: read in marker positions from cue chunk.
- `read_playlist_chunk()`: read in marker spans from playlist chunk.
- `read_adtl_chunks()`: read in associated data list chunks.
- `read_lbl_chunk()`: read in marker positions, spans, labels, and texts from lbl chunk.

## Helper functions for writing RIFF and WAVE files

- `write_riff_chunk()`: write RIFF file header.
- `write_filesize()`: write the file size into the RIFF file header.
- `write_chunk_name()`: change the name of a chunk.
- `write_format_chunk()`: write format chunk.
- `write_data_chunk()`: write data chunk.
- `write_info_chunk()`: write metadata to LIST INFO chunk.
- `write_bext_chunk()`: write metadata to BEXT chunk.
- `write_ixml_chunk()`: write metadata to iXML chunk.
- `write_guano_chunk()`: write metadata to GUANO chunk.
- `write_cue_chunk()`: write marker positions to cue chunk.
- `write_playlist_chunk()`: write marker spans to playlist chunk.
- `write_adtl_chunks()`: write associated data list chunks.
- `write_lbl_chunk()`: write marker positions, spans, labels, and texts to lbl chunk.

## Demo

- `demo()`: print metadata and marker list of RIFF/WAVE file.
- `main()`: call demo with command line arguments.

## Descriptions of the RIFF/WAVE file format

- https://de.wikipedia.org/wiki/RIFF_WAVE
- http://www.piclist.com/techref/io/serial/midi/wave.html
- https://moddingwiki.shikadi.net/wiki/Resource_Interchange_File_Format_(RIFF) 
- https://www.recordingblogs.com/wiki/wave-file-format
- http://fhein.users.ak.tu-berlin.de/Alias/Studio/ProTools/audio-formate/wav/overview.html
- http://www.gallery.co.uk/ixml/

For INFO tag names see:

- see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags

"""

import io
import os
import sys
import warnings
import struct
import numpy as np
import xml.etree.ElementTree as ET
from .audiometadata import flatten_metadata, unflatten_metadata, find_key


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
                 # extensions from
                 # [TeeGrid](https://github.com/janscience/TeeGrid/):
                 BITS='Bits',
                 PINS='Pins',
                 AVRG='Averaging',
                 CNVS='ConversionSpeed',
                 SMPS='SamplingSpeed',
                 VREF='ReferenceVoltage',
                 GAIN='Gain',
                 UWRP='UnwrapThreshold',
                 UWPC='UnwrapClippedAmplitude',
                 IBRD='uCBoard',
                 IMAC='MACAdress')
"""Dictionary with known tags of the INFO chunk as keys and their description as value.

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
"""Dictionary with tags of the BEXT chunk as keys and their size in bytes as values.

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
"""List with valid tags of the iXML chunk.

See http://www.gallery.co.uk/ixml/
"""


# Read RIFF/WAVE files:

def read_riff_header(sf, tag=None):
    """Read and check the RIFF file header.

    Parameters
    ----------
    sf: stream
        File stream of RIFF/WAVE file.
    tag: None or str
        If supplied, check whether it matches the subchunk tag.
        If it does not match, raise a ValueError.

    Returns
    -------
    filesize: int
        Size of the RIFF file in bytes.

    Raises
    ------
    ValueError
        Not a RIFF file or subchunk tag does not match `tag`.
    """
    riffs = sf.read(4).decode('latin-1')
    if riffs != 'RIFF':
        raise ValueError('Not a RIFF file.')
    fsize = struct.unpack('<I', sf.read(4))[0] + 8
    subtag = sf.read(4).decode('latin-1')
    if tag is not None and subtag != tag:
        raise ValueError(f'Not a {tag} file.')
    return fsize


def skip_chunk(sf):
    """Skip over unknown RIFF chunk.
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.

    Returns
    -------
    size: int
        The size of the skipped chunk in bytes.
    """
    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2 
    sf.seek(size, os.SEEK_CUR)
    return size


def read_chunk_tags(filepath):
    """Read tags of all chunks contained in a RIFF file.

    Parameters
    ----------
    filepath: string or file handle
        The RIFF file.

    Returns
    -------
    tags: dict
        Keys are the tag names of the chunks found in the file. If the
        chunk is a list chunk, then the list type is added with a dash
        to the key, i.e. "LIST-INFO". Values are tuples with the
        corresponding file positions of the data of the chunk (after
        the tag and the chunk size field) and the size of the chunk
        data. The file position of the next chunk is thus the position
        of the chunk plus the size of its data.

    Raises
    ------
    ValueError
        Not a RIFF file.

    """           
    tags = {}
    sf = filepath
    file_pos = None
    if hasattr(filepath, 'read'):
        file_pos = sf.tell()
        sf.seek(0, os.SEEK_SET)
    else:
        sf = open(filepath, 'rb')
    fsize = read_riff_header(sf)
    while (sf.tell() < fsize - 8):
        chunk = sf.read(4).decode('latin-1').upper()
        size = struct.unpack('<I', sf.read(4))[0]
        size += size % 2 
        fp = sf.tell()
        if chunk == 'LIST':
            subchunk = sf.read(4).decode('latin-1').upper()
            tags[chunk + '-' + subchunk] = (fp, size)
            size -= 4
        else:
            tags[chunk] = (fp, size)
        sf.seek(size, os.SEEK_CUR)
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, os.SEEK_SET)
    return tags
    

def read_format_chunk(sf):
    """Read format chunk.

    Parameters
    ----------
    sf: stream
        File stream for reading FMT chunk.

    Returns
    -------
    channels: int
        Number of channels.
    rate: float
        Sampling rate (frames per time) in Hertz.
    bits: int
        Bit resolution.
    """
    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    ccode, channels, rate, byterate, blockalign, bits = struct.unpack('<HHIIHH', sf.read(16))
    if size > 16:
        sf.read(size - 16)
    return channels, float(rate), bits

            
def read_info_chunks(sf, store_empty):
    """Read in meta data from info list chunk.

    The variable `info_tags` is used to map the 4 character tags to
    human readable key names.

    See https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    metadata: dict
        Dictionary with key-value pairs of info tags.

    """
    md = {}
    list_size = struct.unpack('<I', sf.read(4))[0]
    list_type = sf.read(4).decode('latin-1').upper()
    list_size -= 4
    if list_type == 'INFO':
        while list_size >= 8:
            key = sf.read(4).decode('ascii').rstrip(' \x00')
            size = struct.unpack('<I', sf.read(4))[0]
            size += size % 2
            bs = sf.read(size)
            x = np.frombuffer(bs, dtype=np.uint8)
            if np.sum((x >= 0x80) & (x <= 0x9f)) > 0:
                s = bs.decode('windows-1252')
            else:
                s = bs.decode('latin1')
            value = s.rstrip(' \x00\x02')
            list_size -= 8 + size
            if key in info_tags:
                key = info_tags[key]
            if value or store_empty:
                md[key] = value
    if list_size > 0:  # finish or skip
        sf.seek(list_size, os.SEEK_CUR)
    return md


def read_bext_chunk(sf, store_empty=True):
    """Read in metadata from the broadcast-audio extension chunk.

    The variable `bext_tags` lists all valid BEXT fields and their size.

    See https://tech.ebu.ch/docs/tech/tech3285.pdf for specifications.
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    meta_data: dict
        The meta-data of a BEXT chunk are stored in a flat dictionary
        with the following keys:

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
        - 'CodingHistory': description of coding processed applied to the audio data, with comma separated subfields: "A=" coding algorithm, e.g. PCM, "F=" sampling rate in Hertz, "B=" bit-rate for MPEG files, "W=" word length in bits, "M=" mono, stereo, dual-mono, joint-stereo, "T=" free text. 
    """
    md = {}
    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    s = sf.read(256).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['Description'] = s
    s = sf.read(32).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['Originator'] = s
    s = sf.read(32).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['OriginatorReference'] = s
    s = sf.read(10).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['OriginationDate'] = s
    s = sf.read(8).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['OriginationTime'] = s
    reference, version = struct.unpack('<QH', sf.read(10))
    if reference > 0 or store_empty:
        md['TimeReference'] = reference
    if version > 0 or store_empty:
        md['Version'] = version
    s = sf.read(64).decode('ascii').strip(' \x00')
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
    s = sf.read(180).decode('ascii').strip(' \x00')
    if s or store_empty:
        md['Reserved'] = s
    size -= 256 + 32 + 32 + 10 + 8 + 8 + 2 + 64 + 10 + 180
    s = sf.read(size).decode('ascii').strip(' \x00\n\r')
    if s or store_empty:
        md['CodingHistory'] = s
    return md


def read_ixml_chunk(sf, store_empty=True):
    """Read in metadata from an IXML chunk.

    See the variable `ixml_tags` for a list of valid tags.

    See http://www.gallery.co.uk/ixml/ for the specification of iXML.
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    metadata: nested dict
        Dictionary with key-value pairs.
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


def read_guano_chunk(sf):
    """Read in metadata from a GUANO chunk.

    GUANO is the Grand Unified Acoustic Notation Ontology, an
    extensible, open format for embedding metadata within bat acoustic
    recordings. See https://github.com/riggsd/guano-spec for details.

    The GUANO specification allows for the inclusion of arbitrary
    nested keys and string encoded values. In that respect it is a
    well defined and easy to handle serialization of the [odML data
    model](https://doi.org/10.3389/fninf.2011.00016).
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.

    Returns
    -------
    metadata: nested dict
        Dictionary with key-value pairs.

    """
    md = {}
    size = struct.unpack('<I', sf.read(4))[0]
    size += size % 2
    for line in io.StringIO(sf.read(size).decode('utf-8')):
        ss = line.split(':')
        if len(ss) > 1:
            md[ss[0].strip()] = ':'.join(ss[1:]).strip().replace(r'\n', '\n')
    return unflatten_metadata(md, '|')

    
def read_cue_chunk(sf):
    """Read in marker positions from cue chunk.
    
    See https://www.recordingblogs.com/wiki/cue-chunk-of-a-wave-file

    Parameters
    ----------
    sf: stream
        File stream of RIFF file.

    Returns
    -------
    locs: 2-D array of ints
        Each row is a marker with unique identifier in the first column,
        position in the second column, and span in the third column.
        The cue chunk does not encode spans, so the third column is
        initialized with zeros.
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
    """Read in marker spans from playlist chunk.
    
    See https://www.recordingblogs.com/wiki/playlist-chunk-of-a-wave-file

    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
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
    """Read in associated data list chunks.

    See https://www.recordingblogs.com/wiki/associated-data-list-chunk-of-a-wave-file
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
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
        from LABL, NOTE (first column), and LTXT chunks (last column).
    """
    list_size = struct.unpack('<I', sf.read(4))[0]
    list_type = sf.read(4).decode('latin-1').upper()
    list_size -= 4
    if list_type == 'ADTL':
        if len(locs) == 0:
            warnings.warn('read_adtl_chunks() requires markers from a previous cue chunk')
        if len(labels) == 0:
            labels = np.zeros((len(locs), 2), dtype=object)
        while list_size >= 8:
            key = sf.read(4).decode('latin-1').rstrip(' \x00').upper()
            size, cpid = struct.unpack('<II', sf.read(8))
            size += size % 2 - 4
            if key == 'LABL' or key == 'NOTE':
                label = sf.read(size).decode('latin-1').rstrip(' \x00')
                i = np.where(locs[:,0] == cpid)[0]
                if len(i) > 0:
                    i = i[0]
                    if hasattr(labels[i,0], '__len__') and len(labels[i,0]) > 0:
                        labels[i,0] += '|' + label
                    else:
                        labels[i,0] = label
            elif key == 'LTXT':
                length = struct.unpack('<I', sf.read(4))[0]
                sf.read(12)  # skip fields
                text = sf.read(size - 4 - 12).decode('latin-1').rstrip(' \x00')
                i = np.where(locs[:,0] == cpid)[0]
                if len(i) > 0:
                    i = i[0]
                    if hasattr(labels[i,1], '__len__') and len(labels[i,1]) > 0:
                        labels[i,1] += '|' + text
                    else:
                        labels[i,1] = text
                    locs[i,2] = length
            else:
                sf.read(size)
            list_size -= 12 + size
    if list_size > 0:  # finish or skip
        sf.seek(list_size, os.SEEK_CUR)
    return labels


def read_lbl_chunk(sf, rate):
    """Read in marker positions, spans, labels, and texts from lbl chunk.
    
    The proprietary LBL chunk is specific to wave files generated by
    [AviSoft](www.avisoft.com) products.

    The labels (first column of `labels`) have special meanings.
    Markers with a span (a section label in the terminology of
    AviSoft) can be arranged in three levels when displayed:

    - "M": layer 1, the top level section
    - "N": layer 2, sections below layer 1
    - "O": layer 3, sections below layer 2
    - "P": total, section start and end are displayed with two vertical lines.

    All other labels mark single point labels with a time and a
    frequency (that we here discard). See also
    https://www.avisoft.com/Help/SASLab/menu_main_tools_labels.htm
    
    Parameters
    ----------
    sf: stream
        File stream of RIFF file.
    rate: float
        Sampling rate of the data in Hertz.

    Returns
    -------
    locs: 2-D array of ints
        Each row is a marker with unique identifier (simply integers
        enumerating the markers) in the first column, position in the
        second column, and span in the third column.
    labels: 2-D array of string objects
        Labels (first column) and texts (second column) for
        each marker (rows).

    """
    size = struct.unpack('<I', sf.read(4))[0]
    nn = size // 65
    locs = np.zeros((nn, 3), dtype=int)
    labels = np.zeros((nn, 2), dtype=object)
    n = 0
    for c in range(nn):
        line = sf.read(65).decode('ascii')
        fields = line.split('\t')
        if len(fields) >= 4:
            labels[n,0] = fields[3].strip()
            labels[n,1] = fields[2].strip()
            start_idx = int(np.round(float(fields[0].strip('\x00'))*rate))
            end_idx = int(np.round(float(fields[1].strip('\x00'))*rate))
            locs[n,0] = n
            locs[n,1] = start_idx
            if labels[n,0] in 'MNOP':
                locs[n,2] = end_idx - start_idx
            else:
                locs[n,2] = 0
            n += 1
        else:
            # the first 65 bytes are a title string that applies to
            # the whole wave file that can be set from the AVISoft
            # software. The recorder leave this empty.
            pass
    return locs[:n,:], labels[:n,:]


def metadata_riff(filepath, store_empty=False):
    """Read metadata from a RIFF/WAVE file.

    Parameters
    ----------
    filepath: string or file handle
        The RIFF file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    meta_data: nested dict
        Meta data contained in the RIFF file.  Keys of the nested
        dictionaries are always strings.  If the corresponding
        values are dictionaries, then the key is the section name
        of the metadata contained in the dictionary. All other
        types of values are values for the respective key. In
        particular they are strings, or list of strings. But other
        simple types like ints or floats are also allowed.
        First level contains sections of meta data
        (e.g. keys 'INFO', 'BEXT', 'IXML', values are dictionaries).

    Raises
    ------
    ValueError
        Not a RIFF file.

    Examples
    --------
    ```
    from audioio.riffmetadata import riff_metadata
    from audioio import print_metadata

    md = riff_metadata('audio/file.wav')
    print_metadata(md)
    ```
    """           
    meta_data = {}
    sf = filepath
    file_pos = None
    if hasattr(filepath, 'read'):
        file_pos = sf.tell()
        sf.seek(0, os.SEEK_SET)
    else:
        sf = open(filepath, 'rb')
    fsize = read_riff_header(sf)
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
        elif chunk == 'GUAN':
            md = read_guano_chunk(sf)
            if len(md) > 0:
                meta_data.update(md)
        else:
            skip_chunk(sf)
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, os.SEEK_SET)
    return meta_data


def markers_riff(filepath):
    """Read markers from a RIFF/WAVE file.

    Parameters
    ----------
    filepath: string or file handle
        The RIFF file.

    Returns
    -------
    locs: 2-D array of ints
        Marker positions (first column) and spans (second column)
        for each marker (rows).
    labels: 2-D array of string objects
        Labels (first column) and texts (second column)
        for each marker (rows).

    Raises
    ------
    ValueError
        Not a RIFF file.

    Examples
    --------
    ```
    from audioio.riffmetadata import riff_markers
    from audioio import print_markers

    locs, labels = riff_markers('audio/file.wav')
    print_markers(locs, labels)
    ```
    """           
    sf = filepath
    file_pos = None
    if hasattr(filepath, 'read'):
        file_pos = sf.tell()
        sf.seek(0, os.SEEK_SET)
    else:
        sf = open(filepath, 'rb')
    rate = None
    locs = np.zeros((0, 3), dtype=int)
    labels = np.zeros((0, 2), dtype=object)
    fsize = read_riff_header(sf)
    while (sf.tell() < fsize - 8):
        chunk = sf.read(4).decode('latin-1').upper()
        if chunk == 'FMT ':
            rate = read_format_chunk(sf)[1]
        elif chunk == 'CUE ':
            locs = read_cue_chunk(sf)
        elif chunk == 'PLST':
            read_playlist_chunk(sf, locs)
        elif chunk == 'LIST':
            labels = read_adtl_chunks(sf, locs, labels)
        elif chunk == 'LBL ':
            locs, labels = read_lbl_chunk(sf, rate)
        else:
            skip_chunk(sf)
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, os.SEEK_SET)
    # sort markers according to their position:
    if len(locs) > 0:
        idxs = np.argsort(locs[:,-2])
        locs = locs[idxs,:]
        if len(labels) > 0:
            labels = labels[idxs,:]
    return locs[:,1:], labels


# Write RIFF/WAVE file:

def write_riff_chunk(df, filesize=0, tag='WAVE'):
    """Write RIFF file header.

    Parameters
    ----------
    df: stream
        File stream for writing RIFF file header.
    filesize: int
        Size of the file in bytes.
    tag: str
        The type of RIFF file. Default is a wave file.
        Exactly 4 characeters long.

    Returns
    -------
    n: int
        Number of bytes written to the stream.

    Raises
    ------
    ValueError
        `tag` is not 4 characters long.
    """
    if len(tag) != 4:
        raise ValueError(f'file tag "{tag}" must be exactly 4 characters long')
    if filesize < 8:
        filesize = 8
    df.write(b'RIFF')
    df.write(struct.pack('<I', filesize - 8))
    df.write(tag.encode('ascii'))
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
        df.seek(0, os.SEEK_END)
        filesize = df.tell()
    df.seek(4, os.SEEK_SET)
    df.write(struct.pack('<I', filesize - 8))
    df.seek(pos, os.SEEK_SET)


def write_chunk_name(df, pos, tag):
    """Change the name of a chunk.

    Use this to make the content of an existing chunk to be ignored by
    overwriting its name with an unknown one.

    Parameters
    ----------
    df: stream
        File stream.
    pos: int
        Position of the chunk in the file stream.
    tag: str
        The type of RIFF file. Default is a wave file.
        Exactly 4 characeters long.

    Raises
    ------
    ValueError
        `tag` is not 4 characters long.
    """
    if len(tag) != 4:
        raise ValueError(f'file tag "{tag}" must be exactly 4 characters long')
    df.seek(pos, os.SEEK_SET)
    df.write(tag.encode('ascii'))


def write_format_chunk(df, channels, frames, rate, bits=16):
    """Write format chunk.

    Parameters
    ----------
    df: stream
        File stream for writing FMT chunk.
    channels: int
        Number of channels contained in the data.
    frames: int
        Number of frames contained in the data.
    rate: int or float
        Sampling rate (frames per time) in Hertz.
    bits: 16 or 32
        Bit resolution of the data to be written.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    blockalign = channels * (bits//8)
    byterate = int(rate) * blockalign
    df.write(b'fmt ')
    df.write(struct.pack('<IHHIIHH', 16, 1, channels, int(rate),
                         byterate, blockalign, bits))
    return 8 + 16


def write_data_chunk(df, data, bits=16):
    """Write data chunk.

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
    write all metadata items as an INFO chunk. The keys are translated
    via the `info_tags` variable back to INFO tags. If after
    translation any key is left that is longer than 4 characters or
    any key has a dictionary as a value (non-flat metadata), the INFO
    chunk is not written.

    See https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags

    Parameters
    ----------
    df: stream
        File stream for writing INFO chunk.
    metadata: nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Keys written to the INFO chunk.

    """
    if not metadata:
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
                warnings.warn(f'value of key "{k}" in INFO chunk cannot be a dictionary.')
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
    tags (one of the keys listed in the variable `bext_tags`), then
    write the dictionary of that key as a broadcast-audio extension
    chunk.

    See https://tech.ebu.ch/docs/tech/tech3285.pdf for specifications.

    Parameters
    ----------
    df: stream
        File stream for writing BEXT chunk.
    metadata: nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Keys written to the BEXT chunk.

    """
    if not metadata or not 'BEXT' in metadata:
        return 0, []
    metadata = metadata['BEXT']
    for k in metadata:
        if not k in bext_tags:
            warnings.warn(f'no bext tag for key "{k}" found.')
            return 0, []
    n = 0
    for k in bext_tags:
        n += bext_tags[k]
    ch = metadata.get('CodingHistory', '').encode('ascii')
    if len(ch) >= 2 and ch[-2:] != '\r\n':
        ch += b'\r\n'
    nch = len(ch) + len(ch) % 2
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
            df.write(bytes(nch - len(ch)))
        else:
            v = metadata.get(k, '').encode('ascii')
            df.write(v[:bn] + bytes(bn - len(v)))
    return 8 + n, ['BEXT']


def write_ixml_chunk(df, metadata, keys_written=None):
    """Write metadata to iXML chunk.

    If `metadata` contains an IXML key with valid IXML tags (one of
    those listed in the variable `ixml_tags`), or the remaining tags
    in `metadata` are valid IXML tags, then write an IXML chunk.

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
                e.text = str(metadata[k])
            kw.append(k)
        return kw

    if not metadata:
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


def write_guano_chunk(df, metadata, keys_written=None):
    """Write metadata to guan chunk.

    GUANO is the Grand Unified Acoustic Notation Ontology, an
    extensible, open format for embedding metadata within bat acoustic
    recordings. See https://github.com/riggsd/guano-spec for details.

    The GUANO specification allows for the inclusion of arbitrary
    nested keys and string encoded values. In that respect it is a
    well defined and easy to handle serialization of the [odML data
    model](https://doi.org/10.3389/fninf.2011.00016).

    This will write *all* metadata that are not in `keys_written`.

    Parameters
    ----------
    df: stream
        File stream for writing guano chunk.
    metadata: nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    keys_written: list of str
        Keys that have already written to INFO, BEXT, IXML chunk.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    keys_written: list of str
        Top-level keys written to the GUANO chunk.

    """
    if not metadata:
        return 0, []
    md = metadata
    if keys_written:
        md = {k: metadata[k] for k in metadata if not k in keys_written}
    if len(md) == 0:
        return 0, []
    fmd = flatten_metadata(md, True, '|')
    for k in fmd:
        if isinstance(fmd[k], str):
            fmd[k] = fmd[k].replace('\n', r'\n')
    sio = io.StringIO()
    m, k = find_key(md, 'GUANO.Version')
    if k is None:
       sio.write('GUANO|Version:1.0\n')
    for k in fmd:
       sio.write(f'{k}:{fmd[k]}\n')
    bs = sio.getvalue().encode('utf-8')
    if len(bs) % 2 == 1:
        bs += b' '
    n = len(bs)
    df.write(b'guan')
    df.write(struct.pack('<I', n))
    df.write(bs)
    return n, list(md)


def write_cue_chunk(df, locs):
    """Write marker positions to cue chunk.

    See https://www.recordingblogs.com/wiki/cue-chunk-of-a-wave-file

    Parameters
    ----------
    df: stream
        File stream for writing cue chunk.
    locs: None or 2-D array of ints
        Positions (first column) and spans (optional second column)
        for each marker (rows).

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    if locs is None or len(locs) == 0:
        return 0
    df.write(b'CUE ')
    df.write(struct.pack('<II', 4 + len(locs)*24, len(locs)))
    for i in range(len(locs)):
        df.write(struct.pack('<II4sIII', i, locs[i,0], b'data', 0, 0, 0))
    return 12 + len(locs)*24


def write_playlist_chunk(df, locs):
    """Write marker spans to playlist chunk.

    See https://www.recordingblogs.com/wiki/playlist-chunk-of-a-wave-file

    Parameters
    ----------
    df: stream
        File stream for writing playlist chunk.
    locs: None or 2-D array of ints
        Positions (first column) and spans (optional second column)
        for each marker (rows).

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    if locs is None or len(locs) == 0 or locs.shape[1] < 2:
        return 0
    n_spans = np.sum(locs[:,1] > 0)
    if n_spans == 0:
        return 0
    df.write(b'plst')
    df.write(struct.pack('<II', 4 + n_spans*12, n_spans))
    for i in range(len(locs)):
        if locs[i,1] > 0:
            df.write(struct.pack('<III', i, locs[i,1], 1))
    return 12 + n_spans*12


def write_adtl_chunks(df, locs, labels):
    """Write associated data list chunks.

    See https://www.recordingblogs.com/wiki/associated-data-list-chunk-of-a-wave-file
    
    Parameters
    ----------
    df: stream
        File stream for writing adtl chunk.
    locs: None or 2-D array of ints
        Positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (second column) for each marker (rows).

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    """
    if labels is None or len(labels) == 0:
        return 0
    labels_size = 0
    for l in labels[:,0]:
        if hasattr(l, '__len__'):
            n = len(l)
            if n > 0:
                labels_size += 12 + n + n % 2
    text_size = 0
    if labels.shape[1] > 1:
        for t in labels[:,1]:
            if hasattr(t, '__len__'):
                n = len(t)
                if n > 0:
                    text_size += 28 + n + n % 2 
    if labels_size == 0 and text_size == 0:
        return 0
    size = 4 + labels_size + text_size
    spans = locs[:,1] if locs.shape[1] > 1 else None
    df.write(b'LIST')
    df.write(struct.pack('<I', size))
    df.write(b'adtl')
    for i in range(len(labels)):
        # labl sub-chunk:
        l = labels[i,0]
        if hasattr(l, '__len__'):
            n = len(l)
            if n > 0:
                n += n % 2
                df.write(b'labl')
                df.write(struct.pack('<II', 4 + n, i))
                df.write(f'{l:<{n}s}'.encode('latin-1'))
        # ltxt sub-chunk:
        if labels.shape[1] > 1:
            t = labels[i,1]
            if hasattr(t, '__len__'):
                n = len(t)
                if n > 0:
                    n += n % 2
                    span = spans[i] if spans is not None else 0
                    df.write(b'ltxt')
                    df.write(struct.pack('<III', 20 + n, i, span))
                    df.write(struct.pack('<IHHHH', 0, 0, 0, 0, 0))
                    df.write(f'{t:<{n}s}'.encode('latin-1'))
    return 8 + size


def write_lbl_chunk(df, locs, labels, rate):
    """Write marker positions, spans, labels, and texts to lbl chunk.
    
    The proprietary LBL chunk is specific to wave files generated by
    [AviSoft](www.avisoft.com) products.

    The labels (first column of `labels`) have special meanings.
    Markers with a span (a section label in the terminology of
    AviSoft) can be arranged in three levels when displayed:

    - "M": layer 1, the top level section
    - "N": layer 2, sections below layer 1
    - "O": layer 3, sections below layer 2
    - "P": total, section start and end are displayed with two vertical lines.

    All other labels mark single point labels with a time and a
    frequency (that we here discard). See also
    https://www.avisoft.com/Help/SASLab/menu_main_tools_labels.htm

    If a marker has a span, and its label is not one of "M", "N", "O", or "P",
    then its label is set to "M".
    If a marker has no span, and its label is one of "M", "N", "O", or "P",
    then its label is set to "a".

    Parameters
    ----------
    df: stream
        File stream for writing lbl chunk.
    locs: None or 2-D array of ints
        Positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (second column) for each marker (rows).
    rate: float
        Sampling rate of the data in Hertz.

    Returns
    -------
    n: int
        Number of bytes written to the stream.

    """
    if locs is None or len(locs) == 0:
        return 0
    size = (1 + len(locs)) * 65
    df.write(b'LBL ')
    df.write(struct.pack('<I', size))
    # first empty entry (this is ment to be a title for the whole wave file):
    df.write(b' ' * 63)
    df.write(b'\r\n')
    for k in range(len(locs)):
        t0 = locs[k,0]/rate
        t1 = t0
        t1 += locs[k,1]/rate
        ls = 'M' if locs[k,1] > 0 else 'a'
        ts = ''
        if labels is not None and len(labels) > k:
            ls = labels[k,0]
            if ls != 0 and len(ls) > 0:
                ls = ls[0]
                if ls in 'MNOP':
                    if locs[k,1] == 0:
                        ls = 'a'
                else:
                    if locs[k,1] > 0:
                        ls = 'M'
            ts = labels[k,1]
            if ts == 0:
                ts = ''
        df.write(struct.pack('<14sc', f'{t0:e}'.encode('ascii'), b'\t'))
        df.write(struct.pack('<14sc', f'{t1:e}'.encode('ascii'), b'\t'))
        bs = f'{ts:31s}\t{ls}\r\n'.encode('ascii')
        df.write(bs)
    return 8 + size


def append_metadata_riff(df, metadata):
    """Append metadata chunks to RIFF file.

    You still need to update the filesize by calling
    `write_filesize()`.

    Parameters
    ----------
    df: stream
        File stream for writing metadata chunks.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    tags: list of str
        Tag names of chunks written to audio file.
    """
    if not metadata:
        return 0, []
    n = 0
    tags = []
    # metadata INFO chunk:
    nc, kw = write_info_chunk(df, metadata)
    if nc > 0:
        tags.append('LIST-INFO')
    n += nc
    # metadata BEXT chunk:
    nc, bkw = write_bext_chunk(df, metadata)
    if nc > 0:
        tags.append('BEXT')
    n += nc
    kw.extend(bkw)
    # metadata IXML chunk:
    nc, xkw = write_ixml_chunk(df, metadata, kw)
    if nc > 0:
        tags.append('IXML')
    n += nc
    kw.extend(xkw)
    # write remaining metadata to GUANO chunk:
    nc, _ = write_guano_chunk(df, metadata, kw)
    if nc > 0:
        tags.append('GUAN')
    n += nc
    kw.extend(bkw)
    return n, tags


def append_markers_riff(df, locs, labels=None, rate=None,
                        marker_hint='cue'):
    """Append marker chunks to RIFF file.

    You still need to update the filesize by calling
    `write_filesize()`.

    Parameters
    ----------
    df: stream
        File stream for writing metadata chunks.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 1-D or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    rate: float
        Sampling rate of the data in Hertz, needed for storing markers
        in seconds.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
    tags: list of str
        Tag names of chunks written to audio file.
 
    Raises
    ------
    ValueError
        Encoding not supported.
    IndexError
        `locs` and `labels` differ in len.
    """
    if locs is None or len(locs) == 0:
        return 0, []
    if labels is not None and len(labels) > 0 and len(labels) != len(locs):
        raise IndexError(f'locs and labels must have same number of elements.')
    # make locs and labels 2-D:
    if not locs is None and locs.ndim == 1:
        locs = locs.reshape(-1, 1)
    if not labels is None and labels.ndim == 1:
        labels = labels.reshape(-1, 1)
    # sort markers according to their position:
    idxs = np.argsort(locs[:,0])
    locs = locs[idxs,:]
    if not labels is None and len(labels) > 0:
        labels = labels[idxs,:]
    n = 0
    tags = []
    if marker_hint.lower() == 'cue':
        # write marker positions:
        nc = write_cue_chunk(df, locs)
        if nc > 0:
            tags.append('CUE ')
        n += nc
        # write marker spans:
        nc = write_playlist_chunk(df, locs)
        if nc > 0:
            tags.append('PLST')
        n += nc
        # write marker labels:
        nc = write_adtl_chunks(df, locs, labels)
        if nc > 0:
            tags.append('LIST-ADTL')
        n += nc
    elif marker_hint.lower() == 'lbl':
        # write avisoft labels:
        nc = write_lbl_chunk(df, locs, labels, rate)
        if nc > 0:
            tags.append('LBL ')
        n += nc
    else:
        raise ValueError(f'marker_hint "{marker_hint}" not supported for storing markers')
    return n, tags


def write_wave(filepath, data, rate, metadata=None, locs=None,
               labels=None, encoding=None, marker_hint='cue'):
    """Write time series, metadata and markers to a WAVE file.

    Only 16 or 32bit PCM encoding is supported.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 1-D or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    encoding: string or None
        Encoding of the data: 'PCM_32' or 'PCM_16'.
        If None or empty string use 'PCM_16'.
     marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

    Raises
    ------
    ValueError
        Encoding not supported.
    IndexError
        `locs` and `labels` differ in len.

    See Also
    --------
    audioio.audiowriter.write_audio()

    Examples
    --------
    ```
    import numpy as np
    from audioio.riffmetadata import write_wave
    
    rate = 28000.0
    freq = 800.0
    time = np.arange(0.0, 1.0, 1/rate) # one second
    data = np.sin(2.0*np.p*freq*time)        # 800Hz sine wave
    md = dict(Artist='underscore_')          # metadata

    write_wave('audio/file.wav', data, rate, md)
    ```
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
    if locs is not None and len(locs) > 0 and \
       labels is not None and len(labels) > 0 and len(labels) != len(locs):
        raise IndexError(f'locs and labels must have same number of elements.')
    # write WAVE file:
    with open(filepath, 'wb') as df:
        write_riff_chunk(df)
        if data.ndim == 1:
            write_format_chunk(df, 1, len(data), rate, bits)
        else:
            write_format_chunk(df, data.shape[1], data.shape[0],
                               rate, bits)
        append_metadata_riff(df, metadata)
        write_data_chunk(df, data, bits)
        append_markers_riff(df, locs, labels, rate, marker_hint)
        write_filesize(df)


def append_riff(filepath, metadata=None, locs=None, labels=None,
                rate=None, marker_hint='cue'):
    """Append metadata and markers to an existing RIFF file.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 1-D or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    rate: float
        Sampling rate of the data in Hertz, needed for storing markers
        in seconds.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

    Returns
    -------
    n: int
        Number of bytes written to the stream.
 
    Raises
    ------
    IndexError
        `locs` and `labels` differ in len.

    Examples
    --------
    ```
    import numpy as np
    from audioio.riffmetadata import append_riff
    
    md = dict(Artist='underscore_')    # metadata
    append_riff('audio/file.wav', md)  # append them to existing audio file
    ```
    """
    if not filepath:
        raise ValueError('no file specified!')
    if locs is not None and len(locs) > 0 and \
       labels is not None and len(labels) > 0 and len(labels) != len(locs):
        raise IndexError(f'locs and labels must have same number of elements.')
    # check RIFF file:
    chunks = read_chunk_tags(filepath)
    # append to RIFF file:
    n = 0
    with open(filepath, 'r+b') as df:
        tags = []
        df.seek(0, os.SEEK_END)
        nc, tgs = append_metadata_riff(df, metadata)
        n += nc
        tags.extend(tgs)
        nc, tgs = append_markers_riff(df, locs, labels, rate, marker_hint)
        n += nc
        tags.extend(tgs)
        write_filesize(df)
        # blank out already existing chunks:
        for tag in chunks:
            if tag in tags:
                if '-' in tag:
                    xtag = tag[5:7] + 'xx'
                else:
                    xtag = tag[:2] + 'xx'
                write_chunk_name(df, chunks[tag][0], xtag)
    return 0
                

def demo(filepath):
    """Print metadata and markers of a RIFF/WAVE file.

    Parameters
    ----------
    filepath: string
        Path of a RIFF/WAVE file.
    """
    def print_meta_data(meta_data, level=0):
        for sk in meta_data:
            md = meta_data[sk]
            if isinstance(md, dict):
                print(f'{"":<{level*4}}{sk}:')
                print_meta_data(md, level+1)
            else:
                v = str(md).replace('\n', '.').replace('\r', '.')
                print(f'{"":<{level*4}s}{sk:<20s}: {v}')
        
    # read meta data:
    meta_data = metadata_riff(filepath, store_empty=False)
    
    # print meta data:
    print()
    print('metadata:')
    print_meta_data(meta_data)
            
    # read cues:
    locs, labels = markers_riff(filepath)
    
    # print marker table:
    if len(locs) > 0:
        print()
        print('markers:')
        print(f'{"position":10} {"span":8} {"label":10} {"text":10}')
        for i in range(len(locs)):
            if i < len(labels):
                print(f'{locs[i,0]:10} {locs[i,1]:8} {labels[i,0]:10} {labels[i,1]:30}')
            else:
                print(f'{locs[i,0]:10} {locs[i,1]:8} {"-":10} {"-":10}')


def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as returned by sys.argv[1:]
    """
    if len(args) > 0 and (args[0] == '-h' or args[0] == '--help'):
        print()
        print('Usage:')
        print('  python -m src.audioio.riffmetadata [--help] <audio/file.wav>')
        print()
        return

    if len(args) > 0:
        demo(args[0])
    else:
        rate = 44100
        t = np.arange(0, 2, 1/rate)
        x = np.sin(2*np.pi*440*t)
        imd = dict(IENG='JB', ICRD='2024-01-24', RATE=9,
                   Comment='this is test1')
        bmd = dict(Description='a recording',
                   OriginationDate='2024:01:24', TimeReference=123456,
                   Version=42, CodingHistory='Test1\nTest2')
        xmd = dict(Project='Record all', Note='still testing',
                   Sync_Point_List=dict(Sync_Point=1,
                                        Sync_Point_Comment='great'))
        omd = imd.copy()
        omd['Production'] = bmd
        md = dict(INFO=imd, BEXT=bmd, IXML=xmd,
                  Recording=omd, Notes=xmd)
        locs = np.random.randint(10, len(x)-10, (5, 2))
        locs = locs[np.argsort(locs[:,0]),:]
        locs[:,1] = np.random.randint(0, 20, len(locs))
        labels = np.zeros((len(locs), 2), dtype=object)
        for i in range(len(labels)):
            labels[i,0] = chr(ord('a') + i % 26)
            labels[i,1] = chr(ord('A') + i % 26)*5
        write_wave('test.wav', x, rate, md, locs, labels)
        demo('test.wav')

    
if __name__ == "__main__":
    main(*sys.argv[1:])
