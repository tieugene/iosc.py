"""Comtrade wrapper."""
# 1. std
from typing import Union, Optional, List, Dict, Any, TypeAlias
import pathlib
import cmath
import datetime
import math
# 2. 3rd
import chardet
import numpy as np
# 3. local
from .comtrade import Comtrade, AnalogChannel, StatusChannel
from .sigfunc import func_list

# x. const
ERR_DSC_FREQ = "Oscillogramm freq. must be 50 or 60 Hz.\nWe have %d"
ERR_DSC_NRATES = "Oscillogramm must use excatly 1 sample rate.\nWe have %d"
ERR_DSC_RATE_ODD = "Rate freq. must be devided by line freq.\nWe have %d/%d"
ERR_DSC_GAPL = "Oscillogramm must starts at least %.3f ms before trigger time.\nWe have %.3f"
ERR_DSC_GAPR = "Oscillogramm must ends at least %.3f ms after trigger time.\nWe have %.3f"


class SanityChkError(RuntimeError):
    """Exception with a text msg."""

    msg: str

    def __init__(self, msg: str):
        """Init SanityChkError object."""
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        """:return: String error representation."""
        return f"Sanity check error: {self.msg}"


ABChannel: TypeAlias = Union[AnalogChannel, StatusChannel]


class __Signal:
    """Signal base.

    :todo: add uplink/parent (osc)
    """

    _is_bool: bool
    _raw2: ABChannel
    _i_: int  # Signal order number (through analog > status); FIXME: rm?
    _value: np.array  # list of values
    # __osc: 'MyComtrade'

    def __init__(self, raw2: ABChannel, i: int):
        """Init Signal pbject.

        :param raw2: Raw wrapped comtrade signal object
        :param i: Order number of signal through all
        """
        self._raw2 = raw2
        self.__i = i

    @property
    def is_bool(self) -> bool:
        """:return: Whether signal is binary (bool)."""
        return self._is_bool

    @property
    def i(self) -> int:
        """:return: Order number in common signal list."""
        return self.__i

    @property
    def sid(self) -> str:
        """:return: Signal name."""
        return self._raw2.name

    @property
    def ph(self) -> str:  # transparent
        """:return: Signal phase (A|B|C).

        Used:
        - SignalSuit.__init__()  # color
        """
        return self._raw2.ph


class StatusSignal(__Signal):
    """Binary/Boolean signal wrapper."""

    _is_bool = True

    def __init__(self, raw: Comtrade, i: int):
        """Init StatusSignal object.

        :param raw: Raw comtrade object
        :param i: Order numer of signal through same type (!)
        """
        super().__init__(raw.cfg.status_channels[i], i + raw.cfg.analog_count)
        self._value = raw.status[i]

    def value(self, i: int, _=None, __=None, ___=None) -> int:
        """:return: Sample values.

        Used:
        - export_to_csv()  # entry
        - StatusSignalSuit.sig2str_i()  # entry
        - ValueTable.__init__()  # entry
        """
        return self._value[i]

    def values(self, _=None) -> List[int]:
        """Get values.

        :return: Values
        :todo: slice
        Used:
        - StatusSignalSuit.values() | BGraphItem  # slice; | normalize
        - StatusSignalSuit._data_y()  # list; | normalize
        """
        return self._value


class AnalogSignal(__Signal):
    """Analog signal wrapper."""

    _is_bool = False
    __parent: 'MyComtrade'
    __mult: tuple[float, float]
    __uu_orig: str  # original uu (w/o m/k)
    # cache
    __y_min: float
    __y_max: float
    __y_center: float
    # __value_centered: np.array
    __a_div: float  # divider for adjusted values
    __a_div_centered: float  # divider for adjusted y-centered values
    # __a_min: float
    # __a_max: float

    def __init__(self, raw: Comtrade, i: int, parent: 'MyComtrade'):
        """Init AnalogSignal object."""
        super().__init__(raw.cfg.analog_channels[i], i)
        self._value = raw.analog[i]
        self.__parent = parent
        # caches
        self.__y_min = min(self._value)
        self.__y_max = max(self._value)
        self.__y_center = np.average(self._value)  # TODO: (max+min)/2
        # self.__value_centered = self._value - self.__y_center
        self.__a_div = (a_max := max(0.0, self.__y_max)) - (a_min := min(0.0, self.__y_min)) or 1.0  # w/ /0 protection
        # self.__a_min = a_min / self.__a_div
        # self.__a_max = a_max / self.__a_div
        self.__a_div_centered = self.__y_max - self.__y_min or 1.0
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
    def uu(self) -> str:  # transparent
        """:return: Bundled Unit as is."""
        return self._raw2.uu

    @property
    def uu_orig(self) -> str:
        """:return: Cleaned unit (e.g. kV => V)."""
        return self.__uu_orig

    @property
    def primary(self) -> float:  # transparent
        """:return: Primary multiplier.
        Used:
        - AnalogSignalSuit.info()
        """
        return self._raw2.primary

    @property
    def secondary(self) -> float:  # transparent
        """:return: Secondary multiplier.
        Used:
        - AnalogSignalSuit.info()
        """
        return self._raw2.secondary

    @property
    def pors(self) -> str:  # transparent
        """Get default value type (Primary or Secondary).

        :return: Primary-or-Secondary (main signal value).
        :todo: return True if Secondary
        Used:
        - AnalogSignalSuit.info()
        """
        return self._raw2.pors

    def get_mult(self, ps: bool) -> float:
        """Get multiplier against pri/sec value.

        :param ps: False=primary, True=secondary
        :return: Multiplier
        Used:
        - self.as_str()
        - AnalogSignalSuit.pors_mult()
        - export_to_csv()
        """
        return self.__mult[int(ps)]

    def value(self, i: int, y_centered: bool, pors: bool, func: int = 0) -> Union[float, complex]:
        """Get sample value depending on 'centerd', PorS and function.

        Used:
        - export_to_csv()  # entry; [yc?,] pors [, func=0]
        - AnalogSignalSuit:
          + sig2str_i()  # entry; [yc,] pors, func
          + hrm()  # entry; [yc?,] [pors,] func
        - ValueTable.__init__()  # entry; [yc?,] [pors?] func
        - OMPMapWindow._h1()  # entry; yc=False, pors, func=h1
        :todo: slice
        """
        if func:
            v = func_list[func](self.values(y_centered), i, self.__parent.spp)
        else:
            v = self._value[i] - self.__y_center if y_centered else self._value[i]
        return v * self.get_mult(pors)
        # return self.__value_centered if self.__parent.shifted else self._value

    def values(self, y_centered: bool) -> List[float]:
        """Get raw values.

        :param y_centered: Y-centered
        :return: Adjusted Values
        :todo: slice
        Used:
        - SignalSuit.v_slice() | xGraphItem  # slice; | normalize
        - AnalogSignalSuit._data_y()  # list; | normalize
        """
        return [v - self.__y_center for v in self._value] if y_centered else self._value

    def v_min(self, y_centered: bool) -> float:
        """Get raw min value.

        :return: Minimal sample value.
        :todo: f(y_centered, pors)
        Used:
        - AnalogSignalSuit.v_min()
        - ValueTable.__init__()
        """
        return self.__y_min - self.__y_center if y_centered else self.__y_min

    def v_max(self, y_centered: bool) -> float:
        """Get raw max value.

        :return: Maximal sample value.
        :todo: f(shift, pors)
        Used:
        - AnalogSignalSuit.v_max()
        - ValueTable.__init__()
        """
        return self.__y_max - self.__y_center if y_centered else self.__y_max

    def a_div(self, y_centered: bool) -> float:
        """Get adjust divider.

        Used (ext):
        - ASignalSuit.a_div()
        """
        return self.__a_div_centered if y_centered else self.__a_div

    def a_values(self, y_centered: bool) -> List[float]:
        """Get adjusted values (-1…0.(9) … -0.5…0.5 … 0.(9)…1 … Δ=0…1):
        - -1 <= (y_min,y_max) <= 1
        - Δ(y_min,y_max,0) = 1

        :param y_centered: Y-centered
        :return: Adjusted Values
        Usage (Ext):
        - ASignalSuit.a_values()
        :todo: slice
        """
        divider = self.a_div(y_centered)
        return [v / divider for v in self.values(y_centered)]

    def a_v_min(self, y_centered: bool) -> float:
        """Get adjusted raw min value.

        Usage (ext):
        - ASignalSuit.a_v_min()
        """
        return self.v_min(y_centered) / self.a_div(y_centered)

    def a_v_max(self, y_centered: bool) -> float:
        """Get adjusted raw max value.

        Usage (ext):
        - ASignalSuit.a_v_min()
        """
        return self.v_max(y_centered) / self.a_div(y_centered)

    def a_min(self, y_centered: bool) -> float:
        """Get adjusted min signal y-space (inc. Y=0)."""
        return min(0.0, self.a_v_min(y_centered))

    def a_max(self, y_centered: bool) -> float:
        """Get adjusted max signal y-space (inc. Y=0)."""
        return max(0.0, self.a_v_max(y_centered))

    def as_str(self, y: float) -> str:
        """Get string representation of signal value (real only).

        :param y: Signal value (real)
        :return: String repr of signal.
        Used:
        - self.as_str_full()
        - AnalogSignalSuit.sig2str()
        """
        uu = self.uu_orig
        if abs(y) < 1:
            y *= 1000
            uu = 'm' + uu
        elif abs(y) > 1000:
            y /= 1000
            uu = 'k' + uu
        return "%.3f %s" % (y, uu)

    def as_str_full(self, v: Union[float, complex]) -> str:
        """Get string representation of signal value (real or complex).

        :param v: Signal value
        :return: String repr of signal (any form)
        Used:
        - AnalogSignalSuit.sig2str_i()
        - ValueTable.__init__()
        - OMPMapWindow.__h1_str()
        """
        if isinstance(v, complex):  # hrm1
            return "%s / %.3f°" % (self.as_str(abs(v)), math.degrees(cmath.phase(v)))
        else:
            return self.as_str(v)


ABSignal: TypeAlias = Union[StatusSignal, AnalogSignal]


class MyComtrade:
    """Comtrade wrapper."""

    _raw: Comtrade
    __x_shifted: bool  # FIXME: dynamic
    path: pathlib.Path
    x: np.array
    y: List[ABSignal]

    def __init__(self, path: pathlib.Path):
        """Init MyComtrade object."""
        self._raw = Comtrade()
        self.__x_shifted = False  # TODO: rm
        self.path = path  # TODO: rm
        self.__load()
        self.__sanity_check()
        self.__setup()
        self._raw.x_shifted = False  # FIXME: hacking xtra-var injection

    @property
    def info(self) -> Dict[str, Any]:
        """Misc info for rare (1..2 times) usage."""
        return {
            'rec_dev_id': self._raw.rec_dev_id,
            'station_name': self._raw.station_name,
            'rev_year': self._raw.rev_year,
            'analog_count': self._raw.analog_count,
            'status_count': self._raw.status_count,
            'start_timestamp': self._raw.start_timestamp,
            'timemult': self._raw.cfg.timemult,
            'time_base': self._raw.time_base,
            'frequency': self._raw.frequency
        }

    @property
    def ft(self) -> str:  # transparent
        """File format."""
        return self._raw.ft

    @property
    def filepath(self) -> str:  # transparent
        """.CFG/CFF full path."""
        return self._raw.cfg.filepath

    @property
    def total_samples(self) -> int:  # transparent
        """:return: Samples in signal."""
        return self._raw.total_samples

    @property
    def rate(self) -> float:  # transparent
        """:return: Sample rate, Hz.

        :todo: int
        """
        return self._raw.cfg.sample_rates[0][0]

    @property
    def trigger_timestamp(self) -> datetime.datetime:  # transparent
        """Astronomic trigger time."""
        return self._raw.cfg.trigger_timestamp

    @property
    def spp(self) -> int:
        """:return: Samples per period."""
        return int(round(self.rate / self._raw.frequency))

    @property
    def shifted(self) -> bool:
        """:return: Whether osc switched to shifted mode."""
        return self.__x_shifted

    @shifted.setter
    def shifted(self, v: bool):
        """Switch all signals to original or shifted mode."""
        self.__x_shifted = v

    @property
    def x_min(self) -> float:
        """:return: 1st sample time, ms."""
        return self.x[0]

    @property
    def x_max(self) -> float:
        """:return: Last sample time, ms."""
        return self.x[-1]

    @property
    def x_size(self) -> float:
        """:return: Signal width, ms."""
        return self.x[-1] - self.x[0]

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

    def bad_gap_l(self) -> Optional[str]:
        """Check that OMP fits (left sife).
        :return: True if tmin > -2T
        """
        # FIXME: _sample.bad/short_L/live/R001_124-2014_05_26_05_09_46.cfg
        # __gap_real: float = (self._raw.trigger_timestamp - self._raw.start_timestamp).total_seconds()
        __gap_real = self._raw.trigger_time - self._raw.time[0]
        __gap_min: float = 2 / self._raw.frequency
        if __gap_real < __gap_min:
            return ERR_DSC_GAPL % (__gap_min * 1000, __gap_real * 1000)

    def bad_gap_r(self) -> Optional[str]:
        """Check that OMP fits (right side).
        :return: True if tmax < T
        """
        __gap_real = self._raw.time[-1] - self._raw.trigger_time
        __gap_min = 1 / self._raw.frequency
        if __gap_real < __gap_min:
            return ERR_DSC_GAPR % (__gap_min * 1000, __gap_real * 1000)

    def __sanity_check(self):
        """Check data usability."""
        def __chk_freq() -> Optional[str]:
            """Check freq = 50/60."""
            if self._raw.cfg.frequency not in {50, 60}:
                return ERR_DSC_FREQ % self._raw.cfg.frequency

        def __chk_nrate() -> Optional[str]:  # nrates
            """Check that only 1 rate."""
            if (nrates := self._raw.cfg.nrates) != 1:
                return ERR_DSC_NRATES % nrates

        def __chk_rate_odd() -> Optional[str]:
            """Check that rate is deviding by main freq."""
            if self.rate % self._raw.cfg.frequency:
                return ERR_DSC_RATE_ODD % (self.rate, self._raw.cfg.frequency)

        if e := __chk_freq():
            raise SanityChkError(e)
        if e := __chk_nrate():
            raise SanityChkError(e)
        if e := __chk_rate_odd():
            raise SanityChkError(e)
        # if e := self.bad_gap_l():
        #    raise SanityChkError(e)
        # if e := self.bad_gap_r():
        #    raise SanityChkError(e)
        # TODO: xz == sample ±½
        # TODO: Δ samples == ±½ sample
        # TODO: no null

    def __setup(self):
        """Translate loaded data into app usable."""
        self.x = [1000 * (t - self._raw.trigger_time) for t in self._raw.time]  # us => ms
        self.y = list()
        for i in range(self._raw.analog_count):
            self.y.append(AnalogSignal(self._raw, i, self))
        for i in range(self._raw.status_count):
            self.y.append(StatusSignal(self._raw, i))

    def find_signal(self, s: str) -> Optional[int]:
        """Find signal by name (strict substring)."""
        for i, sig in enumerate(self.y):
            if not sig.is_bool:
                if s in sig.sid:
                    return i
