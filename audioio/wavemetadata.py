"""
Read meta data and cue lists from wave files.

- `metadata_wave()`: read metadata of a wave file.


## Documentation of wave file format

For wave chunks see:

- https://sites.google.com/site/musicgapi/technical-documents/wav-file-format#cue
- http://fhein.users.ak.tu-berlin.de/Alias/Studio/ProTools/audio-formate/wav/overview.html
- http://www.gallery.co.uk/ixml/

For tag names see:

- see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
"""

import struct
import xml.etree.ElementTree as ET


# see https://exiftool.org/TagNames/RIFF.html#Info%20for%20valid%20info%20tags
info_tags = dict(AGES='Rated',
                 CMNT='Comment',
                 CODE='EncodedBy',
                 DTIM='DateTimeOriginal',
                 GENR='Genre',
                 IART='Artist',
                 ICMT='Comment',
                 ICNT='Country',
                 ICOP='Copyright',
                 ICRD='DateCreated',
                 IDIT='DateTimeOriginal',
                 IENC='EncodedBy',
                 IENG='Engineer',
                 IGNR='Genre',
                 IKEY='Keywords',
                 ILNG='Language',
                 IMIT='MoreInfoText',
                 IMIU='MoreInfoURL',
                 IMUS='MusicBy',
                 INAM='Title',
                 IPRD='Product',
                 IRTD='Rating',
                 ISBJ='Subject',
                 ISFT='Software',
                 ISRC='Source',
                 ITCH='Technician',
                 ITRK='TrackNumber',
                 IWRI='WrittenBy',
                 LANG='Language',
                 LOCA='Location',
                 TAPE='TapeName',
                 TITL='Title',
                 TLEN='Length',
                 TRCK='TrackNumber',
                 TVER='Version',
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
    main(sys.argv)
