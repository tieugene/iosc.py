"""Comtrade wrapper
:todo: exception
:todo: use Ccomtrade.cfg.analog_signal[]
"""
# 1. std
import datetime
import pathlib
from enum import IntEnum
from typing import Optional
# 2. 3rd
import chardet
# 3. local
from comtrade import Comtrade
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


class Meta(Wrapper):

    def __init__(self, raw: Comtrade):
        super(Meta, self).__init__(raw)

    @property
    def filepath(self) -> str:
        return self._raw.cfg.filepath

    @property
    def station_name(self):
        return self._raw.station_name

    @property
    def rec_dev_id(self) -> str:
        return self._raw.rec_dev_id

    @property
    def rev_year(self) -> int:
        return self._raw.rev_year

    @property
    def ft(self) -> str:
        return self._raw.ft

    @property
    def frequency(self) -> float:
        return self._raw.frequency

    @property
    def start_timestamp(self) -> datetime.datetime:
        return self._raw.start_timestamp

    @property
    def trigger_timestamp(self) -> datetime.datetime:
        return self._raw.trigger_timestamp

    @property
    def trigger_time(self) -> float:
        return self._raw.trigger_time

    @property
    def timemult(self) -> float:
        return self._raw.cfg.timemult

    @property
    def time_base(self) -> float:
        return self._raw.time_base

    @property
    def total_samples(self) -> int:
        return self._raw.total_samples

    @property
    def time(self) -> list:
        return self._raw.time


class Signal(Wrapper):
    """Signal base.
    :todo: add chart specific fields: color, line type
    """
    _meta: Meta
    _i: int  # signal order no in signal list
    _value: list[list[float]]  # list of values list
    _id_ptr: list[str]  # signal name list
    _is_bool: bool
    _line_type: ELineType
    _color: Optional[int]

    def __init__(self, raw: Comtrade, i: int):
        super(Signal, self).__init__(raw)
        self._meta = Meta(self._raw)
        self._i = i
        self._line_type = ELineType.Solid
        self._color = None

    @property
    def meta(self) -> Meta:
        return self._meta

    @property
    def sid(self) -> str:
        return self._id_ptr[self._i]

    @property
    def time(self) -> list:
        return self._raw.time

    @property
    def value(self) -> list[float]:
        return self._value[self._i]

    @property
    def is_bool(self) -> bool:
        return self._is_bool

    @property
    def i(self) -> int:
        return self._i

    @property
    def line_type(self) -> ELineType:
        return self._line_type

    @line_type.setter
    def line_type(self, v: ELineType):
        self._line_type = v

    @property
    def color(self) -> int:
        """
        :fixme: replace with comtrade.AnalogChannel.ph (phase)
        :return:
        """
        if self._color is None:  # set default color on demand
            if self.sid and len(self.sid) >= 2 and self.sid[0].lower() in {'i', 'u'}:
                self._color = DEFAULT_SIG_COLOR.get(self.sid[1].lower(), UNKNOWN_SIG_COLOR)
            else:
                self._color = UNKNOWN_SIG_COLOR
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


class AnalogSignal(Signal):
    _is_bool = False

    def __init__(self, raw: Comtrade, i: int):
        super(AnalogSignal, self).__init__(raw, i)
        self._value = self._raw.analog
        self._id_ptr = self._raw.analog_channel_ids


class DiscretSignal(Signal):
    _is_bool = True

    def __init__(self, raw: Comtrade, i: int):
        super(DiscretSignal, self).__init__(raw, i)
        self._value = self._raw.status
        self._id_ptr = self._raw.status_channel_ids


class SignalList(Meta):
    _count: int
    _list: list[Signal]

    def __init__(self, raw: Comtrade):
        super().__init__(raw)
        self._count = 0
        self._list = []

    def __len__(self) -> int:
        return self._count

    @property
    def count(self) -> int:
        return self._count

    def __getitem__(self, i: int) -> Signal:
        return self._list[i]


class DiscretSignalList(SignalList):

    def __init__(self, raw: Comtrade):
        super(DiscretSignalList, self).__init__(raw)

    def reload(self):
        self._count = self._raw.status_count
        self._list.clear()
        for i in range(self._count):
            self._list.append(DiscretSignal(self._raw, i))


class AnalogSignalList(SignalList):

    def __init__(self, raw: Comtrade):
        super(AnalogSignalList, self).__init__(raw)

    def reload(self):
        self._count = self._raw.analog_count
        self._list.clear()
        for i in range(self._count):
            self._list.append(AnalogSignal(self._raw, i))


class RateList(Wrapper):
    def __init__(self, raw: Comtrade):
        super(RateList, self).__init__(raw)

    def __len__(self) -> int:
        return self._raw.cfg.nrates

    @property
    def count(self) -> int:
        return self._raw.cfg.nrates

    def __getitem__(self, i: int) -> list:
        return self._raw.cfg.sample_rates[i]


class MyComtrade(Wrapper):
    __meta: Meta
    __analog: AnalogSignalList
    __discret: DiscretSignalList
    __rate: RateList

    # TODO: __rate: SampleRateList

    def __init__(self):
        super(MyComtrade, self).__init__(Comtrade())
        self.__meta = Meta(self._raw)
        self.__analog = AnalogSignalList(self._raw)
        self.__discret = DiscretSignalList(self._raw)
        self.__rate = RateList(self._raw)

    @property
    def meta(self) -> Meta:
        return self.__meta

    @property
    def analog(self) -> AnalogSignalList:
        return self.__analog

    @property
    def discret(self) -> DiscretSignalList:
        return self.__discret

    @property
    def rate(self) -> RateList:
        return self.__rate

    def load(self, path: pathlib.Path):
        encoding = None
        if path.suffix.lower() == '.cfg':
            with open(path, 'rb') as infile:
                if (enc := chardet.detect(infile.read())['encoding']) not in {'ascii', 'utf-8'}:
                    encoding = enc
        if encoding:
            self._raw.load(str(path), encoding=encoding)
        else:
            self._raw.load(str(path))
        self.__analog.reload()
        self.__discret.reload()
