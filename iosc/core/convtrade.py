"""Converts comtrade file between ASCII and BINARY
:todo: exceptions
"""
# 1. std
from typing import Optional
import sys
import pathlib
import math
import re
# 2. 3rd
import chardet
# x. const
NO_PRN_RE = r'[\x00-\x20]+'  # or r'[^\x21-\x7F]+'
CH_NUM_RE = r'^\s*(\d{1,7}),\s*(\d{1,6})A,\s*(\d{1,6})D$'


class ConvertError(RuntimeError):
    """Exception with a text msg"""
    msg: str

    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        return f"Convert error: {self.msg}"


def __cfg_xfer(sfname: pathlib.Path, dfname: pathlib.Path, enc: str) -> (Optional[tuple[int, ...]], Optional[bool]):
    ch_num: Optional[tuple[int, ...]] = None
    to_bin: Optional[bool] = None
    with open(sfname, 'rt', encoding=enc) as infile, open(dfname.with_suffix('.cfg'), 'wt', encoding=enc) as outfile:
        for i, line in enumerate(infile):
            line = line.strip()
            if i == 1:
                raw = re.findall(CH_NUM_RE, line)
                if not raw:
                    raise ConvertError("2nd line not found")
                ch_num = tuple(map(int, raw[0]))
            elif line in {'ASCII', 'BINARY'}:  # TODO: re
                to_bin = (line.strip() == 'ASCII')
                line = {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[line]
            print(line, file=outfile, end="\r\n")
    return ch_num, to_bin


def __ascii2bin(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    with open(sfile, 'rt', encoding='ascii') as infile, open(dfile, 'wb') as outfile:
        for i, line in enumerate(infile):
            line = re.sub(NO_PRN_RE, '', line)
            if not line:
                continue  # skip empty/garbage
            data = [s for s in line.split(',')]
            if len(data) != (ch_num[0] + 2):
                raise ConvertError(f"Too few/many channels in row #{i + 1}: {len(data)}")
            # 1. no, timestamp as (uint32)
            outfile.write(int(data[0]).to_bytes(4, 'little'))
            outfile.write(int(data[1]).to_bytes(4, 'little'))
            # 2. analog (as int16[]):
            if ch_num[1]:
                for j, a in enumerate(data[2:2 + (ch_num[1])]):  # TODO: replace with map or [a:b:c]
                    try:
                        outfile.write(int(a).to_bytes(2, 'little', signed=True))
                    except OverflowError as e:
                        raise ConvertError(f"Line #{i}, int#{j}: {str(e)}")
            # 3. digital (as uint16[]) FIXME:
            if ch_num[2]:
                words = math.ceil(ch_num[2] / 16)  # 16-bit words
                # join back | reverse | pad left side | int | bytes
                outfile.write(
                    int(''.join(data[ch_num[1] + 2:])[::-1].rjust(words * 16, '0'), 2).to_bytes(words * 2, 'little'))


def __bin2ascii(sfile: pathlib.Path, dfile: pathlib.Path, ch_num: tuple[int, ...]):
    chunk_size = 8 + ch_num[1] * 2 + math.ceil(ch_num[2] / 16) * 2
    sfsize = sfile.stat().st_size
    if sfsize % chunk_size:
        raise ConvertError(f"File size {sfsize} is not multiple of {chunk_size}")
    with open(sfile, 'rb') as infile, open(dfile, 'wt') as outfile:
        while True:
            line = infile.read(chunk_size)
            if not line:  # eof
                break
            out_list = [str(int.from_bytes(line[0:4], 'little')), str(int.from_bytes(line[4:8], 'little'))]
            for a in range(ch_num[1]):
                out_list.append(str(int.from_bytes(line[8 + a * 2:8 + a * 2 + 2], 'little', signed=True)))
            # select | int | bitstring | cut | pad left | list
            # IndexError: string index out of range
            out_list.extend(
                list(bin(int.from_bytes(line[8 + ch_num[1] * 2:], 'little'))[2:][-ch_num[2]:].rjust(ch_num[2], '0')))
            print(','.join(out_list), file=outfile, end="\r\n")


def convert(sfname: pathlib.Path, dfname: pathlib.Path):
    """Convert comtrade file between ASCII and BINARY.
    :param sfname: Source *.cfg file path
    :type sfname: pathlib.Path
    :param dfname: Dest file path
    :note: cfg only
    """
    # 0. checks
    if sfname.suffix.lower() == 'cff':
        raise ConvertError(f"CFF export not supported yet")
    if not sfname.is_file():
        raise ConvertError(f"Src '{sfname}' not exists")
    if sfname.with_suffix('') == dfname.with_suffix(''):
        raise ConvertError(f"Same src and dst")
    # 1. detect encoding
    # enc: Optional[str] = None
    with open(sfname, 'rb') as infile:
        enc = chardet.detect(infile.read())['encoding']
    # 2. transfere *.cfg + get channel number and src file type
    ch_num, to_bin = __cfg_xfer(sfname, dfname, enc)
    if to_bin is None:
        raise ConvertError("It is not ASCII nor BINARY")
    if ch_num is None:
        raise ConvertError("Channel numbers not recognized")
    if ch_num[0] != (ch_num[1] + ch_num[2]):
        raise ConvertError(f"Impossible channels num: {ch_num[0]} = {ch_num[1]}A + {ch_num[2]}D")
    # 3. transfere *.dat
    # print("Summary:", ch_num, to_bin)
    if to_bin:
        __ascii2bin(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)
    else:
        __bin2ascii(sfname.with_suffix('.dat'), dfname.with_suffix('.dat'), ch_num)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <in_cfg_file> <out_file_or_dir")
        sys.exit()
    sf = pathlib.Path(sys.argv[1])
    df = pathlib.Path(sys.argv[2])
    if df.is_dir():
        df = df.joinpath(sf.name)
    try:
        convert(sf, df)
    except ConvertError as e:
        sys.exit(str(e))


if __name__ == '__main__':
    main()