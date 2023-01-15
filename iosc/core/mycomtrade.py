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

    @property
    def value(self) -> np.array:
        """:return: Sample values.

        Used:
        - export_to_csv()  # entry
        - StatusSignalSuit.sig2str_i()  # entry
        - ValueTable.__init__()  # entry
        """
        return self._value

    def values(self, _=None) -> List[float]:
        """Get values.

        :param _: Y-centered
        :return: Values
        :todo: slice
        Used:
        - SignalSuit.v_slice() | xGraphItem  # slice; | normalize
        - StatusSignalSuit._data_y()  # list; | normalize
        """
        return self._value


class AnalogSignal(__Signal):
    """Analog signal wrapper."""

    _is_bool = False
    __parent: 'MyComtrade'
    __mult: tuple[float, float]
    __uu_orig: str  # original uu (w/o m/k)
    __value_shifted: np.array
    __y_center: float  # just cache

    def __init__(self, raw: Comtrade, i: int, parent: 'MyComtrade'):
        """Init AnalogSignal object."""
        super().__init__(raw.cfg.analog_channels[i], i)
        self._value = raw.analog[i]
        self.__parent = parent
        self.__y_center = np.average(self._value)
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

    @property
    def value(self) -> np.array:
        """:return: Sample values depending on 'shifted' state.
        :todo: f(i, y_centered, pors, func)

        Used:
        - export_to_csv()  # entry; [yc?,] pors [, func=0]
        - AnalogSignalSuit:
          + sig2str_i()  # entry; pors, func
          + hrm()  # entry; [yc?,] [pors,] func
        - ValueTable.__init__()  # entry; [yc?,] [pors?] func
        - OMPMapWindow._h1()  # entry; yc=False, pors, func=h1
        """
        return self.__value_shifted if self.__parent.shifted else self._value

    def values(self, y_centered: bool) -> List[float]:
        """Get values.

        :param y_centered: Y-centered
        :return: Adjusted Values
        :todo: slice
        Used:
        - SignalSuit.v_slice() | xGraphItem  # slice; | normalize
        - AnalogSignalSuit._data_y()  # list; | normalize
        """
        return [v - self.__y_center for v in self._value] if y_centered else self._value

    def avalues(self, y_centered: bool) -> List[float]:
        """Get adjusted values: -1 <= (y_min,y_max) <= 1.

        :param y_centered: Y-centered
        :return: Adjusted Values
        :todo: slice
        """

    def v_min(self, y_centered: bool) -> float:
        """Get min value.

        :return: Minimal sample value.
        :todo: f(y_centered, pors)
        Used:
        - AnalogSignalSuit.v_min()
        - ValueTable.__init__()
        """
        retvalue = min(self._value)
        return retvalue - self.__y_center if y_centered else retvalue

    def v_max(self, y_centered: bool) -> float:
        """Get max value.

        :return: Maximal sample value.
        :todo: f(shift, pors)
        Used:
        - AnalogSignalSuit.v_max()
        - ValueTable.__init__()
        """
        retvalue = max(self._value)
        return retvalue - self.__y_center if y_centered else retvalue

    def as_str(self, y: float, pors: bool) -> str:
        """Get string representation of signal value (real only).

        :param y: Signal value (real)
        :param pors: False=primary, True=secondary
        :return: String repr of signal.
        Used:
        - self.as_str_full()
        - AnalogSignalSuit.sig2str()
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

    def as_str_full(self, v: Union[float, complex], pors: bool) -> str:
        """Get string representation of signal value (real or complex).

        :param v: Signal value
        :param pors: False=primary, True=secondary
        :return: String repr of signal (any form)
        Used:
        - AnalogSignalSuit.sig2str_i()
        - ValueTable.__init__()
        - OMPMapWindow.__h1_str()
        """
        if isinstance(v, complex):  # hrm1
            return "%s / %.3f°" % (self.as_str(abs(v), pors), math.degrees(cmath.phase(v)))
        else:
            return self.as_str(v, pors)


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

    def chk_gap_l(self) -> Optional[str]:
        """Check that OMP fits (left sife)."""
        # FIXME: _sample.bad/short_L/live/R001_124-2014_05_26_05_09_46.cfg
        # __gap_real: float = (self._raw.trigger_timestamp - self._raw.start_timestamp).total_seconds()
        __gap_real = self._raw.trigger_time - self._raw.time[0]
        __gap_min: float = 1 / self._raw.frequency
        if __gap_real < __gap_min:
            return ERR_DSC_GAPL % (__gap_min * 1000, __gap_real * 1000)

    def chk_gap_r(self) -> Optional[str]:
        """Check that OMP fits (right side)."""
        __gap_real = self._raw.time[-1] - self._raw.trigger_time
        __gap_min = 2 / self._raw.frequency
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
        # if e := self.chk_gap_l():
        #    raise SanityChkError(e)
        # if e := self.chk_gap_r():
        #    raise SanityChkError(e)
        # TODO: xz == sample ±½
        # TODO: Δ samples == ±½ sample
        # TODO: no null

    def __setup(self):
        """Translate loaded data into app usable."""
        self.x = [1000 * (t - self._raw.trigger_time) for t in self._raw.time]
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
