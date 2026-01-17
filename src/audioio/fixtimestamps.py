"""Fix time stamps.

Change time stamps in the metadata (of wave files) and file names
*without rewriting* the entire file.  This is useful in case the
real-time clock of a recorder failed.

## Command line script

Let's assume you have a continous recording spread over the following
four files each covering 3 minutes of the recording:
```txt
logger-20190101T000015.wav
logger-20190101T000315.wav
logger-20190101T000615.wav
logger-20190101T000915.wav
```
However, the recording was actually started at 2025-06-09T10:42:17.
Obviously, the real-time clock failed, since all times in the file name
and the time stamps in the metadata start in the year 2019.

To fix this, run
```sh
> fixtimestamps -s '2025-06-09T10:42:17' logger-2019*.wav
```

Then the files are renamed:
```txt
logger-20190101T000015.wav -> logger-20250609T104217.wav
logger-20190101T000315.wav -> logger-20250609T104517.wav
logger-20190101T000615.wav -> logger-20250609T104817.wav
logger-20190101T000915.wav -> logger-20250609T105117.wav
```
and the time stamps in the meta data are set accordingly.

Supported date formats are "YYYY-MM-DD" or "YYYYMMDD".
Supported time formats are "HH:MM:SS" or "HHMMSS".

Adding the `-n` flag runs the script in dry mode, i.e. it just reports
what it would do without modifying the audio files:

```sh
> fixtimestamps -n -s 20250701T173420 *.wav
```

Alternatively, the script can be run from within the audioio source
tree as:
```
python -m src.audioio.fixtimestamps -s 20250701T173420 *.wav
```

Running
```sh
fixtimestamps --help
```
prints
```text
usage: fixtimestamps [-h] [--version] -s STARTTIME [-n] files [files ...]

Fix time stamps.

positional arguments:
  files         audio files

options:
  -h, --help    show this help message and exit
  --version     show program's version number and exit
  -s STARTTIME  new start time of the first file
  -n            do not modify the files, just report what would be done.

version 2.5.0 by Benda-Lab (2020-2025)
```

## Functions

- `parse_datetime()`: parse string for a date and a time.
- `replace_datetime()`: replace in a string date and time.
- `write_riff_datetime()`: modify time stamps in the metadata of a RIFF/WAVE file.

"""


import re
import os
import sys
import glob
import argparse
import datetime as dt

from pathlib import Path

from .version import __version__, __year__
from .riffmetadata import read_riff_header, read_chunk_tags, read_format_chunk
from .riffmetadata import read_info_chunks, read_bext_chunk, read_ixml_chunk, read_guano_chunk
from .riffmetadata import write_info_chunk, write_bext_chunk, write_ixml_chunk, write_guano_chunk
from .audiometadata import get_datetime, set_starttime


def parse_datetime(string):
    """Parse string for a date and a time.

    Parameters
    ----------
    string: str
        String to be parsed.

    Returns
    -------
    dtime: datetime or None
        The date and time parsed from the string.
        None if neither a date nor a time was found.
    """
    date = None
    time = None
    time_pos = 0
    m = re.search('([123][0-9][0-9][0-9]-[01][0-9]-[0123][0-9])', string)
    if m is not None:
        date = dt.date.fromisoformat(m[0])
        time_pos = m.end()
    else:
        m = re.search('([123][0-9][0-9][0-9][01][0-9][0123][0-9])', string)
        if m is not None:
            dts = m[0]
            dts = f'{dts[0:4]}-{dts[4:6]}-{dts[6:8]}'
            date = dt.date.fromisoformat(dts)
            time_pos = m.end()
    m = re.search('([012][0-9]:[0-5][0-9]:[0-5][0-9])', string[time_pos:])
    if m is not None:
        time = dt.time.fromisoformat(m[0])
    else:
        m = re.search('([012][0-9][0-5][0-9][0-5][0-9])', string[time_pos:])
        if m is not None:
            dts = m[0]
            dts = f'{dts[0:2]}:{dts[2:4]}:{dts[4:6]}'
            time = dt.time.fromisoformat(dts)
    if date is None and time is None:
        return None
    if date is None:
        date = dt.date(1, 1, 1)
    if time is None:
        time = dt.time(0, 0, 0)
    dtime = dt.datetime.combine(date, time)
    return dtime


def replace_datetime(string, date_time):
    """ Replace in a string date and time.

    Parameters
    ----------
    string: str
        String in which date and time are replaced.
    date_time: datetime
        Date and time to write into the string.

    Returns
    -------
    new_string: str
        The `string` with date and time replaced by `date_time`.
    """
    if date_time is None:
        return string
    new_string = string
    time_pos = 0
    dts = date_time.date().isoformat()
    pattern = re.compile('([123][0-9][0-9][0-9]-[01][0-9]-[0123][0-9])')
    m = pattern.search(new_string)
    if m is not None:
        time_pos = m.end()
        new_string = pattern.sub(dts, new_string)
    else:
        pattern = re.compile('([123][0-9][0-9][0-9][01][0-9][0123][0-9])')
        m = pattern.search(new_string)
        if m is not None:
            time_pos = m.end()
            new_string = pattern.sub(dts.replace('-', ''), new_string)
    dts = date_time.time().isoformat()
    pattern = re.compile('([012][0-9]:[0-5][0-9]:[0-5][0-9])')
    m = pattern.search(new_string[time_pos:])
    if m is not None:
        new_string = new_string[:time_pos] + \
            pattern.sub(dts, new_string[time_pos:])
    else:
        pattern = re.compile('([012][0-9][0-5][0-9][0-5][0-9])')
        m = pattern.search(new_string[time_pos:])
        if m is not None:
            new_string = new_string[:time_pos] + \
                pattern.sub(dts.replace(':', ''), new_string[time_pos:])
    return new_string


def write_riff_datetime(path, start_time, file_time=None, no_mod=False):
    """ Modify time stamps in the metadata of a RIFF/WAVE file.

    Parameters
    ----------
    path: str
        Path to a wave file.
    start_time: datetime
        Date and time to which all time stamps should be set.
    file_time: None or date_time
        If provided check whether the time stamp in the metadata
        matches.

    Returns
    -------
    duration: timedelta
        Total duration of the audio data in the file.
    orig_time: date_time or None
        The time stamp found in the metadata.
    no_mod: bool
        Do not modify the files, just report what would be done.    
    """
    def check_starttime(file_orig, time_time, path):
        if file_time is not None and orig_time is not None and \
           abs(orig_time - file_time) > dt.timedelta(seconds=1):
            raise ValueError(f'"{path}" start time is {orig_time} but should be {file_time} for a continuous recording.')

        
    duration = dt.timedelta(seconds=0)
    orig_time = None
    store_empty = False
    with open(path, 'r+b') as sf:
        try:
            fsize = read_riff_header(sf)
        except ValueError:
            raise ValueError(f'"{path}" is not a valid RIFF/WAVE file, time stamps cannot be modified.')
        tags = read_chunk_tags(sf)
        if 'FMT ' not in tags:
            raise ValueError(f'missing FMT chunk in "{path}".')
        sf.seek(tags['FMT '][0] - 4, os.SEEK_SET)
        channels, rate, bits = read_format_chunk(sf)
        bts = 1 + (bits - 1) // 8
        if 'DATA' not in tags:
            raise ValueError(f'missing DATA chunk in "{path}".')
        dsize = tags['DATA'][1]
        duration = dt.timedelta(seconds=(dsize//bts//channels)/rate)
        for chunk in tags:
            sf.seek(tags[chunk][0] - 4, os.SEEK_SET)
            md = {}
            if chunk == 'LIST-INFO':
                md['INFO'] = read_info_chunks(sf, store_empty)
                orig_time = get_datetime(md)
                check_starttime(orig_time, file_time, path)
                if not no_mod and set_starttime(md, start_time):
                    sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                    write_info_chunk(sf, md, tags[chunk][1])
            elif chunk == 'BEXT':
                md['BEXT'] = read_bext_chunk(sf, store_empty)
                orig_time = get_datetime(md)
                check_starttime(orig_time, file_time, path)
                if not no_mod and set_starttime(md, start_time):
                    sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                    write_bext_chunk(sf, md)
            elif chunk == 'IXML':
                md['IXML'] = read_ixml_chunk(sf, store_empty)
                orig_time = get_datetime(md)
                check_starttime(orig_time, file_time, path)
                if not no_mod and set_starttime(md, start_time):
                    sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                    write_ixml_chunk(sf, md)
            elif chunk == 'GUAN':
                md['GUANO'] = read_guano_chunk(sf)
                orig_time = get_datetime(md)
                check_starttime(orig_time, file_time, path)
                if not no_mod and set_starttime(md, start_time):
                    sf.seek(tags[chunk][0] - 8, os.SEEK_SET)
                    write_guano_chunk(sf, md['GUANO'])
    return duration, orig_time


def demo(start_time, file_pathes, no_mod=False):
    """Modify time stamps of audio files.

    Parameters
    ----------
    start_time: str
        Time stamp of the first file.
    file_pathes: list of str
        Pathes of audio files.
    no_mod: bool
        Do not modify the files, just report what would be done.    
    """
    file_time = None
    start_time = dt.datetime.fromisoformat(start_time)
    for fp in file_pathes:
        duration, orig_time = write_riff_datetime(fp, start_time,
                                                  file_time, no_mod)
        name_time = parse_datetime(Path(fp).stem)
        if orig_time is None:
            orig_time = name_time
        if file_time is None:
            file_time = orig_time
        if orig_time is None:
            raise ValueError(f'"{fp}" does not contain any time in its metadata or name.')
        if name_time is not None:
            p = Path(fp)
            np = p.with_stem(replace_datetime(p.stem, start_time))
            if not no_mod:
                os.rename(fp, np)
            print(f'{fp} -> {np}')
        else:
            print(f'{fp}: {orig_time} -> {start_time}')
        start_time += duration
        file_time += duration

            
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
                        help='new start time of the first file')
    parser.add_argument('-n', dest='nomod', action='store_true',
                        help='do not modify the files, just report what would be done.')
    parser.add_argument('files', type=str, nargs='+',
                        help='audio files')
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)
    
    # expand wildcard patterns:
    files = []
    if os.name == 'nt':
        for fn in args.files:
            files.extend(glob.glob(fn))
    else:
        files = args.files

    demo(args.starttime, files, args.nomod)


if __name__ == "__main__":
    main(*sys.argv[1:])
