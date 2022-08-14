"""Comtrade wrapper"""
import datetime
import pathlib
import chardet
from comtrade import Comtrade


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


class Signal(Wrapper):
    _meta: Meta
    _i: int
    _value: list[list[float]]
    _id_ptr: list[str]

    def __init__(self, raw: Comtrade, i: int):
        super(Signal, self).__init__(raw)
        self._meta = Meta(self._raw)
        self._i = i

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


class AnalogSignal(Signal):
    def __init__(self, raw: Comtrade, i: int):
        super(AnalogSignal, self).__init__(raw, i)
        self._value = self._raw.analog
        self._id_ptr = self._raw.analog_channel_ids


class DiscretSignal(Signal):

    def __init__(self, raw: Comtrade, i: int):
        super(DiscretSignal, self).__init__(raw, i)
        self._value = self._raw.status
        self._id_ptr = self._raw.status_channel_ids


class SignalList(Wrapper):
    _count: int
    _list: list[Signal]

    def __init__(self, raw: Comtrade):
        super(SignalList, self).__init__(raw)
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


class MyComtrade(Wrapper):
    __meta: Meta
    __analog: AnalogSignalList
    __discret: DiscretSignalList

    # TODO: __rate: SampleRateList

    def __init__(self):
        super(MyComtrade, self).__init__(Comtrade())
        self.__meta = Meta(self._raw)
        self.__analog = AnalogSignalList(self._raw)
        self.__discret = DiscretSignalList(self._raw)

    @property
    def meta(self) -> Meta:
        return self.__meta

    @property
    def analog(self) -> AnalogSignalList:
        return self.__analog

    @property
    def discret(self) -> DiscretSignalList:
        return self.__discret

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
