"""Converts comtrade file between ASCII and BINARY"""
import pathlib


def convert(sfname: pathlib.Path, dfname: pathlib.Path, force_write: bool = False):
    """Convert comtrade file between ASCII and BINARY.
    :param sfname: Source *.cfg file path
    :type sfname: pathlib.Path
    :param dfname: Dest file path
    :param force_write:
    """
    # 1. detect encoding
    # 2. check/prepare destination
    # 3. transfere *.cfg + get channel number and src file type
    # 4. transfere *.dat
    print("Let's go!")
