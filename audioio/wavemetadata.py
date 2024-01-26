"""Read meta data and cue lists from wave files.

- `metadata_wave()`: read metadata of a wave file.


## Documentation of wave file format

- https://de.wikipedia.org/wiki/RIFF_WAVE

For wave chunks see:

- https://sites.google.com/site/musicgapi/technical-documents/wav-file-format#cue
- http://fhein.users.ak.tu-berlin.de/Alias/Studio/ProTools/audio-formate/wav/overview.html
- http://www.gallery.co.uk/ixml/

For tag names see:

- see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
"""

import struct
import numpy as np
import xml.etree.ElementTree as ET


# see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
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


def metadata_wave(file, store_empty=False, verbose=0):
    """ Read metadata of a wave file.

    Parameters
    ----------
    file: string or file handle
        The wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.
    verbose: int
        Verbosity level.

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
    cues: list of dict
        Cues contained in the wave file. Each item in the list provides

        - 'id': Id of the cue.
        - 'pos': Position of the cue in samples.
        - 'length': Number of samples the cue covers (optional, from PLST or LTXT chunk).
        - 'repeats': How often the cue segment should be repeated (optional, from PLST chunk).
        - 'label': Label of the cue (optional, from LABL chunk).
        - 'note': Note on the cue (optional, from NOTE chunk).
        - 'text': Description of cue segment (optional, from LTXT chunk).

    Raises
    ------
    ValueError
        Not a wave file.
    """

    def riff_chunk(sf):
        """ Read and check the RIFF file header. """
        str1 = sf.read(4).decode('latin-1')
        if str1 != 'RIFF':
            raise ValueError("Not a wave file.")
        fsize = struct.unpack('<I', sf.read(4))[0] + 8
        str2 = sf.read(4).decode('latin-1')
        if str2 != 'WAVE':
            raise ValueError("Not a wave file.")
        return fsize

    def skip_chunk(sf):
        """ Skip over unknown chunk. """
        data = sf.read(4)
        size = struct.unpack('<I', data)[0]
        size += size % 2 
        sf.seek(size, 1)

    def cue_chunk(sf, cues):
        """ Read in cue ids and positions from cue chunk. """
        size, n = struct.unpack('<II', sf.read(8))
        for c in range(n):
            id, pos = struct.unpack('<II', sf.read(8))
            datachunkid = sf.read(4).decode('latin-1').rstrip(' \x00').upper()
            chunkstart, blockstart, offset = struct.unpack('<III', sf.read(12))
            c = dict(id=id, pos=pos)
            cues.append(c)

    def playlist_chunk(sf, cues):
        """ Read in cue length and repeats from playlist chunk. """
        size, n = struct.unpack('<II', sf.read(8))
        for p in range(n):
            id, length, repeats = struct.unpack('<III', sf.read(12))
            for c in cues:
                if c['id'] == id:
                    c['length'] = length
                    c['repeats'] = repeats
                    break

    def info_chunks(sf, list_size, store_empty):
        """ Read in meta data from info list chunk. """
        md = {}
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
        if list_size > 0:
            sf.seek(list_size, 1)
        return md

    def list_chunk(sf, cues, verbose=0):
        """ Read in list chunk. """
        md = {}
        list_size = struct.unpack('<I', sf.read(4))[0]
        list_type = sf.read(4).decode('latin-1').upper()
        list_size -= 4
        if list_type == 'INFO':
            md = info_chunks(sf, list_size, store_empty)
        elif list_type == 'ADTL':
            while list_size >= 8:
                key = sf.read(4).decode('latin-1').rstrip(' \x00').upper()
                size, id = struct.unpack('<II', sf.read(8))
                size += size % 2 - 4
                if key == 'LABL':
                    label = sf.read(size).decode('latin-1').rstrip(' \x00')
                    for c in cues:
                        if c['id'] == id:
                            c['label'] = label
                            break
                elif key == 'NOTE':
                    note = sf.read(size).decode('latin-1').rstrip(' \x00')
                    for c in cues:
                        if c['id'] == id:
                            c['note'] = note
                            break
                elif key == 'LTXT':
                    length = struct.unpack('<I', sf.read(4))[0]
                    sf.read(12)
                    text = sf.read(size - 4 - 12).decode('latin-1').rstrip(' \x00')
                    for c in cues:
                        if c['id'] == id:
                            c['length'] = length
                            c['text'] = text
                            break
                else:
                    if verbose > 0:
                        print('  skip', key, size, list_size)
                    sf.read(size)
                list_size -= 12 + size
            if list_size > 0:
                sf.seek(list_size, 1)
        else:
            print('ERROR: unknown list type', list_type)
        return md

    def bext_chunk(sf, store_empty=True):
        """ Read in meta-data from the broadcast-audio extension chunk.

        See https://tech.ebu.ch/docs/tech/tech3285.pdf for specifications.

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
        s = sf.read(size).decode('latin-1').rstrip(' \x00')
        if s or store_empty:
            md['CodingHistory'] = s
        return md

    def parse_xml(element):
        md = {}
        for e in element:
            if not e.text is None:
                md[e.tag] = e.text
            elif len(e.getchildren()) > 0:
                md[e.tag] = parse_xml(e)
            elif store_empty:
                md[e.tag] = ''
        return md

    def ixml_chunk(sf):
        size = struct.unpack('<I', sf.read(4))[0]
        size += size % 2
        xmls = sf.read(size).decode('latin-1').rstrip(' \x00')
        root = ET.fromstring(xmls)
        md = {root.tag: parse_xml(root)}
        return md
            
    meta_data = {}
    cues = []
    sf = file
    file_pos = None
    if hasattr(file, 'read'):
        file_pos = sf.tell()
        sf.seek(0, 0)
    else:
        sf = open(file, 'rb')
    fsize = riff_chunk(sf)
    while (sf.tell() < fsize - 8):
        chunk = sf.read(4).decode('latin-1').upper()
        if chunk == 'LIST':
            md = list_chunk(sf, cues, verbose)
            if len(md) > 0:
                meta_data['INFO'] = md
        elif chunk == 'CUE ':
            cue_chunk(sf, cues)
        elif chunk == 'PLST':
            playlist_chunk(sf, cues)
        elif chunk == 'BEXT':
            md = bext_chunk(sf, store_empty)
            meta_data['BEXT'] = md
        elif chunk == 'IXML':
            md = ixml_chunk(sf)
            meta_data['IXML'] = md
        else:
            if verbose > 0:
                print('skip', chunk)
            skip_chunk(sf)
            if verbose > 1:
                print(f' file size={fsize}, file position={sf.tell()}')
    if file_pos is None:
        sf.close()
    else:
        sf.seek(file_pos, 0)
    return meta_data, cues


def write_riff_chunk(df, filesize=0):
    """ Write the RIFF file header. """
    if filesize < 8:
        filesize = 8
    df.write(b'RIFF')
    df.write(struct.pack('<I', filesize - 8))
    df.write(b'WAVE')
    return 12


def write_filesize(df, filesize):
    """ Write the file size into the RIFF file header. """
    pos = df.tell()
    df.seek(4, 0)
    df.write(struct.pack('<I', filesize - 8))
    df.seek(pos, 0)


def write_fmt_chunk(df, channels, frames, samplerate, bits=16):
    """ Write the FMT chunk. """
    blockalign = channels * (bits//8)
    byterate = int(samplerate) * blockalign
    df.write(b'fmt ')
    df.write(struct.pack('<IHHIIHH', 16, 1, channels, int(samplerate),
                         byterate, blockalign, bits))
    return 8 + 16


def write_data_chunk(df, data, bits=16):
    df.write(b'data')
    df.write(struct.pack('<I', data.size * (bits//8)))
    buffer = data * 2**(bits-1)
    n = df.write(buffer.astype(f'<i{bits//8}').tobytes('C'))
    return 8 + n


def write_info_chunk(df, metadata):
    if metadata is None or len(metadata) == 0:
        return 0
    tags = {v: k for k, v in info_tags.items()}
    n = 0
    for k in metadata:
        n += 8 + len(metadata[k]) + len(metadata[k]) % 2
    df.write(b'LIST')
    df.write(struct.pack('<I', n + 4))
    df.write(b'INFO')
    for k in metadata:
        kn = tags[k] if k in tags else k
        df.write(f'{kn:<4s}'.encode('latin-1'))
        ns = len(metadata[k]) + len(metadata[k]) % 2
        df.write(struct.pack('<I', ns))
        df.write(f'{metadata[k]:<{ns}s}'.encode('latin-1'))
    return 12 + n

    
def write_wave(filepath, data, samplerate, metadata=None):
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
        Meta data as key-value pairs.
    """
    bits = 16
    n = 0
    with open(filepath, 'wb') as df:
        n += write_riff_chunk(df)
        if data.ndim == 1:
            n += write_fmt_chunk(df, 1, len(data), samplerate, bits)
        else:
            n += write_fmt_chunk(df, data.shape[1], data.shape[0],
                                 samplerate, bits)
        n += write_info_chunk(df, metadata)
        n += write_data_chunk(df, data, bits)
        write_filesize(df, n)


def main(args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv
    """
    if len(args) <= 1 or args[1] == '-h' or args[1] == '--help':
        print('')
        print('Usage:')
        print('  python -m audioio.wavemetadata [--help] <audio/file.wav>')
        return

    # read meta data:
    meta_data, cues = metadata_wave(args[1], store_empty=False, verbose=1)
    
    # print meta data:
    print()
    print('meta data:')
    for sk in meta_data:
        md = meta_data[sk]
        if isinstance(md, dict):
            print(f'{sk}:')
            for k in md:
                print(f'  {k:22}: {md[k]}')
        else:
            print(f'{sk}:\n  {md}')
            
    # print cue table:
    if len(cues) > 0:
        print()
        print(f'{"cue":4} {"position":10} {"length":8} {"label":10} {"note":10} {"text":10}')
        for c in cues:
            print(f'{c["id"]:4} {c["pos"]:10} {c.get("length", 0):8} {c.get("label", ""):10} {c.get("note", ""):10} {c.get("text", ""):10}')


if __name__ == "__main__":
    import sys
    #main(sys.argv)
    rate = 44100
    t = np.arange(0, 2, 1/rate)
    x = np.sin(2*np.pi*440*t)
    m = dict(IENG='JB', ICRD='2024-01-24', Comment='this is test1')
    write_wave('test.wav', x, rate, m)
