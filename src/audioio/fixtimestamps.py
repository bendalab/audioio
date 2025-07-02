"""Fix time stamps.

Change time stamps in the metadata (of wave files) and file names without rewriting the entire file.


## Command line script

The module can be run as a script from the command line:

```sh
> fixtimestamps -s 20250701T173420 logger-*.wav
```

"""


import re
import os
import sys
import argparse
import datetime as dt
from pathlib import Path
from .version import __version__, __year__
from .riffmetadata import read_riff_header, read_chunk_tags, read_format_chunk
from .riffmetadata import read_info_chunks, read_bext_chunk, read_ixml_chunk, read_guano_chunk
from .riffmetadata import write_info_chunk, write_bext_chunk, write_ixml_chunk, write_guano_chunk
from .audiometadata import get_datetime, set_starttime


def parse_starttime(string, name_pattern):
    """Parse stem of a file path for a date time.

    Parameters
    ----------
    string: str
        String to be parsed
    name_pattern: str or None
        Pattern indicating where a datetime string is embedded into the stem of the file name.
        Patterns indicating date and times are SDATETIME, DATETIME, SDATE, DATE, STIME, and TIME.
        Text indicated by a wildcard '*' can be any text.

    Returns
    -------
    dtime: datetime
        The date and time parsed from the string.
    """
    name_pattern = name_pattern.replace('*', '.*')
    if name_pattern is None:
        name_pattern = '*-SDATETIME'
    for pattern in ['SDATETIME', 'DATETIME']:
        if pattern in name_pattern:
            name_pattern = name_pattern.replace(pattern, f'(?P<{pattern}>\\w+)')
            break
    else:
        for pattern in ['SDATE', 'DATE']:
            if pattern in name_pattern:
                name_pattern = name_pattern.replace(pattern, f'(?P<{pattern}>\\w+)')
                break
        for pattern in ['STIME', 'TIME']:
            if pattern in name_pattern:
                name_pattern = name_pattern.replace(pattern, f'(?P<{pattern}>\\w+)')
                break
    m = re.fullmatch(name_pattern, string)
    r = m.groupdict()
    dtime = None
    if 'SDATETIME' in r:
        dts = r['SDATETIME']
        dts = f'{dts[0:4]}-{dts[4:6]}-{dts[6:8]}T{dts[9:11]}:{dts[11:13]}:{dts[13:15]}'
        dtime = dt.datetime.fromisoformat(dts)
    elif 'DATETIME' in r:
        dtime = dt.datetime.fromisoformat(r['DATETIME'])
    if dtime is None:
        date = None
        if 'SDATE' in r:
            dts = r['SDATE']
            dts = f'{dts[0:4]}-{dts[4:6]}-{dts[6:8]}'
            dtime = dt.date.fromisoformat(dts)
        elif 'DATE' in r:
            dtime = dt.date.fromisoformat(r['DATE'])
        time = None
        if 'STIME' in r:
            dts = r['STIME']
            dts = f'{dts[9:11]}:{dts[11:13]}:{dts[13:15]}'
            dtime = dt.time.fromisoformat(dts)
        elif 'TIME' in r:
            dtime = dt.time.fromisoformat(r['TIME'])
        dtime = dt.datetime.combine(date, time)
    return dtime
    

def demo(start_time, name_pattern, file_pathes):
    """Modify time stamps of audio files.

    Parameters
    ----------
    start_time: str
        Time stamp of the first file.
    name_pattern: str or None
        Pattern indicating where a datetime string is embedded into the stem of the file name.
        Patterns indicating date and times are SDATETIME, DATETIME, SDATE, DATE, STIME, and TIME.
        Text indicated by a wildcard '*' is kept when renaming the file.
    file_pathes: list of str
        Pathes of audio files.
    """
    if name_pattern is None:
        name_pattern = '*-SDATETIME'
    file_time = None
    start_time = dt.datetime.fromisoformat(start_time)
    store_empty = False
    for fp in file_pathes:
        orig_time = None
        duration = dt.timedelta(seconds=0)
        """
        with open(fp, 'r+b') as sf:
            try:
                fsize = read_riff_header(sf)
            except ValueError:
                raise ValueError(f'"{fp}" is not a valid RIFF/WAVE file, time stamps cannot be modified.')
            tags = read_chunk_tags(sf)
            if 'FMT ' not in tags:
                raise ValueError(f'missing FMT chunk in "{fp}".')
            sf.seek(tags['FMT '][0] - 4, os.SEEK_SET)
            channels, rate, bits = read_format_chunk(sf)
            if 'DATA' not in tags:
                raise ValueError(f'missing DATA chunk in "{fp}".')
            dsize = tags['DATA'][1]
            duration = dt.timedelta(seconds=(dsize//channels)/rate)
            for chunk in tags:
                sf.seek(tags[chunk][0] - 4, os.SEEK_SET)
                md = {}
                if chunk == 'LIST-INFO':
                    md['INFO'] = read_info_chunks(sf, store_empty)
                    orig_time = get_datetime(md)
                    if file_time is not None and orig_time is not None and abs(orig_time - file_time) > dt.timedelta(seconds=1):
                        raise ValueError(f'"{fp}" start time is {orig_time} but should be {file_time} for a continuous recording.')
                    if set_starttime(md, start_time):
                        sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                        write_info_chunk(sf, md, tags[chunk][1])
                elif chunk == 'BEXT':
                    md['BEXT'] = read_bext_chunk(sf, store_empty)
                    orig_time = get_datetime(md)
                    if set_starttime(md, start_time):
                        sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                        write_bext_chunk(sf, md)
                elif chunk == 'IXML':
                    md['IXML'] = read_ixml_chunk(sf, store_empty)
                    orig_time = get_datetime(md)
                    if set_starttime(md, start_time):
                        sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                        write_ixml_chunk(sf, md)
                elif chunk == 'GUAN':
                    md['GUANO'] = read_guano_chunk(sf)
                    orig_time = get_datetime(md)
                    if set_starttime(md, start_time):
                        sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                        write_guano_chunk(sf, md['GUANO'])
        """
        if orig_time is None:
            orig_time = parse_starttime(Path(fp).stem, name_pattern)
        if file_time is None:
            file_time = orig_time
        print(f'{fp}: {orig_time} -> {start_time}')
        """
        TODO: rename file
        Path(fp).with_stem(stem & name_pattern:TRANSLATED WITH START_TIME)
        start_time += duration
        file_time += duration
        """

            
def main(*cargs):
    """Call demo with command line arguments.

    Parameters
    ----------
    cargs: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    # command line arguments:
    parser = argparse.ArgumentParser(add_help=True,
        description='Fix time stamps.',
        epilog=f'version {__version__} by Benda-Lab (2020-{__year__})')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-s', dest='starttime', default=None, type=str, required=True,
                        help='start time of the first file')
    parser.add_argument('-p', dest='pattern', default='*-SDATETIME', type=str,
                        help='pattern of the file name, may contain SDATETIME, DATETIME, SDATE, DATE, STIME, and TIME to indicate date and time strings.')
    parser.add_argument('files', type=str, nargs='+',
                        help='audio files')
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)

    demo(args.starttime, args.pattern, args.files)


if __name__ == "__main__":
    main(*sys.argv[1:])
