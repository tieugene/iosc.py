"""Converts comtrade file between ASCII and BINARY"""
# 1. std
from typing import Optional
import pathlib
import re

# 2. 3rd
import chardet


def __ascii2bin(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    print("ASCII => BIN")
    with open(sfile, 'rt') as infile, open(dfile, 'wt') as outfile:
        for i, line in enumerate(infile):
            ...


def __bin2ascii(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    print("BIN => ASCII")
    ...


def convert(sfname: pathlib.Path, dfname: pathlib.Path):
    """Convert comtrade file between ASCII and BINARY.
    :param sfname: Source *.cfg file path
    :type sfname: pathlib.Path
    :param dfname: Dest file path
    :note: cfg only
    """
    # print("Let's go!", sfname, '=>', dfname)
    # 1. detect encoding
    enc: Optional[str] = None
    with open(sfname, 'rb') as infile:
        enc = chardet.detect(infile.read())['encoding']
    # 2. transfere *.cfg + get channel number and src file type
    ch_num: Optional[tuple[int, ...]] = None
    to_bin: Optional[bool] = None
    with open(sfname, 'rt', encoding=enc) as infile, open(dfname.with_suffix('.cfg'), 'wt', encoding=enc) as outfile:
        for i, line in enumerate(infile):
            line = line.strip()
            if i == 1:
                raw = re.findall(r'^(\d{1,7}),(\d{1,6})A,(\d{1,6})D$', line)
                if not raw:
                    raise "2nd line not found"
                ch_num = tuple(map(int, raw[0]))
            elif line in {'ASCII', 'BINARY'}:  # TODO: re
                to_bin = (line.strip() == 'ASCII')
                line = {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[line]
            # TODO: write to outfile
            # print(line)
    if ch_num is None:
        raise "Channel numbers not recognized"
    if to_bin is None:
        raise "It is not ASCII nor BINARY"
    # 3. transfere *.dat
    print("Summary:", ch_num, to_bin)
    if to_bin:
        __ascii2bin(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)
    else:
        __bin2ascii(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)
