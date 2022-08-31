"""Comtrade wrapper
:todo: exception
:todo: use Ccomtrade.cfg.analog_signal[]
"""
# 1. std
import pathlib
from enum import IntEnum
from typing import Optional
# 2. 3rd
import chardet
# 3. local
from comtrade import Comtrade, Channel
# x. const
# orange (255, 127, 39), green (0, 128, 0), red (198, 0, 0)
DEFAULT_SIG_COLOR = {'a': 16744231, 'b': 32768, 'c': 12976128}
UNKNOWN_SIG_COLOR = 0  # 'black'


class ELineType(IntEnum):
    Solid = 0
    Dot = 1
    DashDot = 2


class Wrapper:
    _raw: Comtrade

    def __init__(self, raw: Comtrade):
        self._raw = raw

    @property
    def raw(self) -> Comtrade:
        return self._raw


class Signal(Wrapper):
    """Signal base."""
    _raw2: Channel
    _value: list[float]  # list of values
    _is_bool: bool
    _line_type: ELineType
    _color: Optional[int]

    def __init__(self, raw: Comtrade, raw2: Channel):
        super().__init__(raw)
        self._raw2 = raw2
        self._line_type = ELineType.Solid
        self._color = None

    @property
    def sid(self) -> str:
        return self._raw2.name

    @property
    def time(self) -> list[float]:
        return self._raw.time

    @property
    def value(self) -> list[float]:
        return self._value

    @property
    def is_bool(self) -> bool:
        return self._is_bool

    @property
    def i(self) -> int:
        """Channel no in list, 0-based"""
        return self._raw2.n - 1

    @property
    def line_type(self) -> ELineType:
        return self._line_type

    @line_type.setter
    def line_type(self, v: ELineType):
        self._line_type = v

    @property
    def color(self) -> int:
        if self._color is None:  # set default color on demand
            return DEFAULT_SIG_COLOR.get(self._raw2.ph.lower(), UNKNOWN_SIG_COLOR)
        return self._color

    @color.setter
    def color(self, v: int):
        self._color = v

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.color >> 16) & 255, (self.color >> 8) & 255, self.color & 255

    @rgb.setter
    def rgb(self, v: tuple[int, int, int]):
        self._color = v[0] << 16 | v[1] << 8 | v[2]


class StatusSignal(Signal):
    _is_bool = True

    def __init__(self, raw: Comtrade, i: int):
        super().__init__(raw, raw.cfg.status_channels[i])
        self._value = self._raw.status[i]


class AnalogSignal(Signal):
    _is_bool = False

    def __init__(self, raw: Comtrade, i: int):
        super().__init__(raw, raw.cfg.analog_channels[i])
        self._value = self._raw.analog[i]


class SignalList(Wrapper):
    _count: int
    _list: list[Signal]

    def __init__(self, raw: Comtrade):
        super().__init__(raw)
        self._count = 0
        self._list = []

    def __len__(self) -> int:
        return self._count

    def __getitem__(self, i: int) -> Signal:
        return self._list[i]


class StatusSignalList(SignalList):
    def __init__(self, raw: Comtrade):
        super().__init__(raw)
        self._count = self._raw.status_count
        for i in range(self._count):
            self._list.append(StatusSignal(self._raw, i))


class AnalogSignalList(SignalList):
    def __init__(self, raw: Comtrade):
        super().__init__(raw)
        self._count = self._raw.analog_count
        for i in range(self._count):
            self._list.append(AnalogSignal(self._raw, i))


class RateList(Wrapper):
    def __init__(self, raw: Comtrade):
        super().__init__(raw)

    def __len__(self) -> int:
        return self._raw.cfg.nrates

    def __getitem__(self, i: int) -> tuple[float, int]:  # hz, points
        return self._raw.cfg.sample_rates[i]


class MyComtrade(Wrapper):
    __analog: AnalogSignalList
    __status: StatusSignalList
    __rate: RateList  # TODO: __rate: SampleRateList

    def __init__(self, path: pathlib.Path):
        super().__init__(Comtrade())
        # loading
        encoding = None
        if path.suffix.lower() == '.cfg':
            with open(path, 'rb') as infile:
                if (enc := chardet.detect(infile.read())['encoding']) not in {'ascii', 'utf-8'}:
                    encoding = enc
        if encoding:
            self._raw.load(str(path), encoding=encoding)
        else:
            self._raw.load(str(path))
        self.__analog = AnalogSignalList(self._raw)
        self.__status = StatusSignalList(self._raw)
        self.__rate = RateList(self._raw)

    @property
    def analog(self) -> AnalogSignalList:
        return self.__analog

    @property
    def status(self) -> StatusSignalList:
        return self.__status

    @property
    def rate(self) -> RateList:
        return self.__rate
