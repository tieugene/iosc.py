"""Comtrade wrapper
:todo: exceptions
"""
import cmath
import math
# 1. std
from typing import Union, Optional, List
import pathlib
# 2. 3rd
import chardet
import numpy as np
# 3. local
from .comtrade import Comtrade, Channel

# x. const
ERR_DSC_FREQ = "Oscillogramm freq. must be 50 or 60 Hz.\nWe have %d"
ERR_DSC_NRATES = "Oscillogramm must use excatly 1 sample rate.\nWe have %d"
ERR_DSC_RATE_ODD = "Rate freq. must be devided by line freq.\nWe have %d/%d"
ERR_DSC_GAPL = "Oscillogramm must starts at least %.3f ms before trigger time.\nWe have %.3f"
ERR_DSC_GAPR = "Oscillogramm must ends at least %.3f ms after trigger time.\nWe have %.3f"


class SanityChkError(RuntimeError):
    """Exception with a text msg"""
    msg: str

    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        return f"Sanity check error: {self.msg}"


class Wrapper:
    _raw: Comtrade

    def __init__(self, raw: Comtrade):
        self._raw = raw

    @property
    def raw(self) -> Comtrade:
        return self._raw


class Signal(Wrapper):
    """Signal base."""
    _i_: int
    _is_bool: bool
    _raw2: Channel
    _value: np.array  # list of values

    def __init__(self, raw: Comtrade, raw2: Channel, i: int):
        super().__init__(raw)
        self.__i = i
        self._raw2 = raw2

    @property
    def i(self) -> int:
        return self.__i

    @property
    def raw2(self) -> Channel:
        return self._raw2

    @property
    def sid(self) -> str:
        return self._raw2.name

    @property
    def time(self) -> np.array:  # FIXME: rm
        return self._raw.time

    @property
    def is_bool(self) -> bool:
        return self._is_bool


class StatusSignal(Signal):
    _is_bool = True

    def __init__(self, raw: Comtrade, i: int):
        super().__init__(raw, raw.cfg.status_channels[i], i)
        self._value = self._raw.status[i]

    @property
    def value(self) -> np.array:
        return self._value


class AnalogSignal(Signal):
    _is_bool = False
    __mult: tuple[float, float]
    __uu_orig: str  # original uu (w/o m/k)
    __value_shifted: np.array

    def __init__(self, raw: Comtrade, i: int):
        super().__init__(raw, raw.cfg.analog_channels[i], i)
        self._value = self._raw.analog[i]
        self.__value_shifted = self._value - np.average(self._value)
        # pri/sec multipliers
        if self._raw2.uu.startswith('m'):
            uu = 0.001
            self.__uu_orig = self._raw2.uu[1:]
        elif self._raw2.uu.startswith('k'):
            uu = 1000
            self.__uu_orig = self._raw2.uu[1:]
        else:
            uu = 1
            self.__uu_orig = self._raw2.uu
        if bool(self._raw2.primary) and bool(self._raw2.secondary):
            if self._raw2.pors.lower() == 'p':
                pri = 1
                sec = self._raw2.secondary / self._raw2.primary
            else:
                pri = self._raw2.primary / self._raw2.secondary
                sec = 1
        else:  # trivial
            pri = sec = 1
        self.__mult = (pri * uu, sec * uu)

    @property
    def value(self) -> np.array:
        return self.__value_shifted if self._raw.x_shifted else self._value

    @property
    def v_min(self) -> float:
        return min(self.value)

    @property
    def v_max(self) -> float:
        return max(self.value)

    def get_mult(self, ps: bool) -> float:
        """
        Get multiplier between pri/sec
        :param ps: False=primary, True=secondary
        :return: Multiplier
        """
        return self.__mult[int(ps)]

    @property
    def uu_orig(self):
        return self.__uu_orig

    def as_str(self, y: float, pors: bool):
        """
        :param y: Signal value (real)
        :param pors: False=primary, True=secondary
        :return: String repr of signal.
        """
        pors_y = y * self.get_mult(pors)
        uu = self.uu_orig
        if abs(pors_y) < 1:
            pors_y *= 1000
            uu = 'm' + uu
        elif abs(pors_y) > 1000:
            pors_y /= 1000
            uu = 'k' + uu
        return "%.3f %s" % (pors_y, uu)

    def as_str_full(self, v: Union[float, complex], pors: bool):
        """
        :param v: Signal value
        :param pors: False=primary, True=secondary
        :return: String repr of signal (any form)
        """
        if isinstance(v, complex):  # hrm1
            return "%s / %.3f°" % (self.as_str(abs(v), pors), math.degrees(cmath.phase(v)))
        else:
            return self.as_str(v, pors)


class MyComtrade(Wrapper):
    path: pathlib.Path
    x: np.array
    y: List[Union[StatusSignal, AnalogSignal]]

    def __init__(self, path: pathlib.Path):
        super().__init__(Comtrade())
        self.path = path
        self.__load()
        self.__sanity_check()
        self.__setup()
        self._raw.x_shifted = False  # FIXME: hacking xtra-var injection

    def __load(self):
        encoding = None
        if self.path.suffix.lower() == '.cfg':
            with open(self.path, 'rb') as infile:
                if (enc := chardet.detect(infile.read())['encoding']) not in {'ascii', 'utf-8'}:
                    encoding = enc
        if encoding:
            self._raw.load(str(self.path), encoding=encoding)
        else:
            self._raw.load(str(self.path))

    def chk_gap_l(self) -> Optional[str]:
        """Check that OMP fits (left sife)"""
        # FIXME: _sample.bad/short_L/live/R001_124-2014_05_26_05_09_46.cfg
        # __gap_real: float = (self._raw.trigger_timestamp - self._raw.start_timestamp).total_seconds()
        __gap_real = self._raw.trigger_time - self._raw.time[0]
        __gap_min: float = 1 / self._raw.frequency
        if __gap_real < __gap_min:
            return ERR_DSC_GAPL % (__gap_min * 1000, __gap_real * 1000)

    def chk_gap_r(self) -> Optional[str]:
        """Check that OMP fits (right sife)"""
        __gap_real = self._raw.time[-1] - self._raw.trigger_time
        __gap_min = 2 / self._raw.frequency
        if __gap_real < __gap_min:
            return ERR_DSC_GAPR % (__gap_min * 1000, __gap_real * 1000)

    def __sanity_check(self):
        """
        - rates (1, raw.total_samples, ?frequency)
        - null values
        :return:
        """

        def __chk_freq() -> Optional[str]:
            """Check freq = 50/60"""
            if self._raw.cfg.frequency not in {50, 60}:
                return ERR_DSC_FREQ % self._raw.cfg.frequency

        def __chk_nrate() -> Optional[str]:  # nrates
            """Check that only 1 rate"""
            if (nrates := self._raw.cfg.nrates) != 1:
                return ERR_DSC_NRATES % nrates

        def __chk_rate_odd() -> Optional[str]:
            """Check that rate is deviding by main freq"""
            if self.rate % self._raw.cfg.frequency:
                return ERR_DSC_RATE_ODD % (self.rate, self._raw.cfg.frequency)

        if e := __chk_freq():
            raise SanityChkError(e)
        if e := __chk_nrate():
            raise SanityChkError(e)
        if e := __chk_rate_odd():
            raise SanityChkError(e)
        # if e := self.chk_gap_l():
        #    raise SanityChkError(e)
        # if e := self.chk_gap_r():
        #    raise SanityChkError(e)
        # TODO: xz == sample ±½
        # TODO: Δ samples == ±½ sample
        # TODO: no null

    def __setup(self):
        """Translate loaded data into app usable"""
        self.x = [1000 * (t - self._raw.trigger_time) for t in self._raw.time]
        self.y = list()
        for i in range(self._raw.analog_count):
            self.y.append(AnalogSignal(self._raw, i))
        for i in range(self._raw.status_count):
            self.y.append(StatusSignal(self._raw, i))

    @property
    def x_min(self) -> float:  # mS
        return self.x[0]

    @property
    def x_max(self) -> float:  # mS
        return self.x[-1]

    @property
    def x_size(self) -> float:  # mS
        return self.x[-1] - self.x[0]

    @property
    def rate(self) -> float:
        return self._raw.cfg.sample_rates[0][0]

    @property
    def spp(self) -> int:
        """Samples per period"""
        return int(round(self.rate / self._raw.frequency))

    @property
    def shifted(self):
        return self._raw.x_shifted

    @shifted.setter
    def shifted(self, v: bool):
        """Switch all signals between original and shifted modes"""
        self._raw.x_shifted = v
