"""Converts comtrade file between ASCII and BINARY
:todo: exceptions
"""
import math
# 1. std
from typing import Optional
import pathlib
import re

# 2. 3rd
import chardet


class ConvertError(RuntimeError):
    """Exception with a text msg"""
    msg: str

    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        return f"Convert error: {self.msg}"


def __ascii2bin(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    # print("ASCII => BIN")
    with open(sfile, 'rt') as infile, open(dfile, 'wb') as outfile:
        for i, line in enumerate(infile):
            data = line.strip().split(',')
            if len(data) != (ch_num[0] + 2):
                raise ConvertError(f"Too few/many channels in row #{i + 1}")
            # 1. no, timestamp as (uint32)
            outfile.write(int(data[0]).to_bytes(4, 'little'))
            outfile.write(int(data[1]).to_bytes(4, 'little'))
            # 2. analog (as int16[]):
            if ch_num[1]:
                for a in data[2:2 + (ch_num[1])]:
                    outfile.write(int(a).to_bytes(2, 'little', signed=True))
            # 3. digital (as uint16[]) FIXME:
            if ch_num[2]:
                words = math.ceil(ch_num[2] / 16)  # 16-bit words
                # join back | reverse | pad left side | int | bytes
                outfile.write(
                    int(''.join(data[ch_num[1] + 2:])[::-1].rjust(words * 16, '0'), 2).to_bytes(words * 2, 'little'))


def __bin2ascii(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    print("BIN => ASCII")
    # to the end:
    # get #
    # get timestamp
    # get As
    # unpack Ds
    # print all


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
                    raise ConvertError("2nd line not found")
                ch_num = tuple(map(int, raw[0]))
            elif line in {'ASCII', 'BINARY'}:  # TODO: re
                to_bin = (line.strip() == 'ASCII')
                line = {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[line]
            # TODO: write to outfile
            print(line, file=outfile)
    if ch_num is None:
        raise ConvertError("Channel numbers not recognized")
    if to_bin is None:
        raise ConvertError("It is not ASCII nor BINARY")
    # 3. transfere *.dat
    # print("Summary:", ch_num, to_bin)
    if to_bin:
        __ascii2bin(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)
    else:
        __bin2ascii(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)
