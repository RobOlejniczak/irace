"""Lap data parsing utilities."""


from collections import namedtuple

from .utils import time_string
from .utils import as_timedelta


Flag = namedtuple("Flag", ("name", "mask"))
FLAGS = (
    Flag("invalid", 1),
    Flag("pitted", 2),
    Flag("off track", 4),
    Flag("black flag", 8),
    Flag("car reset", 16),
    Flag("contact", 32),
    Flag("car contact", 64),
    Flag("lost control", 128),
    Flag("discontinuity", 256),
    Flag("interpolated crossing", 512),
    Flag("clock smash", 1024),
    Flag("tow", 2048),
)


def _get_flags(flags: int) -> tuple:
    """Return a tuple of applicable `Flag`s."""

    flag_objs = []
    for flag in FLAGS:
        if flags & flag.mask:
            flag_objs.append(flag)

    return tuple(flag_objs)


class Lap:
    """Parsed lap object."""

    def __init__(self, data: dict, prev: int):
        self.flags = _get_flags(data["flags"])
        self.flag_names = tuple([x.name for x in self.flags])
        self.lap = data["lap_num"]
        self.time_int = data["ses_time"] - prev
        self.time = as_timedelta(self.time_int)

    @property
    def summary(self) -> dict:
        """Return a summary of this lap."""

        _summary = {
            "lap": self.lap,
            "time": "--:--" if self.lap == 0 else time_string(self.time),
            "time_int": self.time_int,
        }
        if self.flags:
            _summary["flags"] = self.flag_names
        return _summary


class Laps:
    """Parsed laps object.

    Instatiate with the loaded JSON return from `stats.Client.session_laps`.
    """

    def __init__(self, data: dict):
        self.drivers = data["drivers"]
        self.race = data["header"]

        laps = []
        prev = 0
        for lap in data["lapData"]:
            laps.append(Lap(lap, prev))
            prev = lap["ses_time"]

        self.laps = tuple(laps)

    @property
    def average(self) -> float:
        """Average lap time.

        If the return is < 0, there is no average time.
        """

        total_lap_time, valid_laps = self._lap_totals()

        if valid_laps:  # avoid divide by zero
            return total_lap_time / valid_laps

        return -1.0

    @property
    def average_string(self) -> str:
        """Average lap time, as a string."""

        return time_string(self.average)

    @property
    def fast_lap(self) -> int:
        """Lap number of fastest lap.

        If the return is < 0, there is no fast lap.
        """

        best_lap_time = None
        best_lap = -1

        for driver in self.drivers:
            if best_lap_time is None or driver["bestlaptime"] < best_lap_time:
                best_lap_time = driver["bestlaptime"]
                best_lap = driver["bestlapnum"]

        return best_lap

    @property
    def fastest_lap(self) -> float:
        """Fastest lap time (in seconds).

        If the return is < 0, there is no fastest lap.
        """

        best_lap_time = None

        for driver in self.drivers:
            if best_lap_time is None or driver["bestlaptime"] < best_lap_time:
                best_lap_time = driver["bestlaptime"]

        if best_lap_time > 0:
            return as_timedelta(best_lap_time).total_seconds()

        return -1.0

    @property
    def fastest_lap_string(self) -> str:
        """Fastest lap time (in seconds) as a string."""

        return time_string(self.fastest_lap)

    @property
    def total_time(self) -> float:
        """Total lap time of all laps."""

        return sum(x.time.total_seconds() for x in self.laps)

    @property
    def total_time_string(self) -> str:
        """Total lap time of all laps as a string."""

        return time_string(self.total_time)

    @property
    def total_valid_time(self) -> float:
        """Total lap time of all valid laps."""

        return self._lap_totals()[0]

    @property
    def total_valid_time_string(self) -> str:
        """Total lap time of all valid laps as a string."""

        return time_string(self.total_valid_time)

    @property
    def valid_laps(self) -> int:
        """Number of valid laps turned."""

        return self._lap_totals()[1]

    @property
    def total_laps(self) -> int:
        """Number of totals laps turned."""

        return len(self.laps)

    @property
    def flagged_laps(self) -> dict:
        """Returns a dictionary of lap number to flag (by name)."""

        incidents = {}
        for lap in self.laps:
            if lap.flags:
                incidents[lap.lap] = tuple(x.name for x in lap.flags)
        return incidents

    def _lap_totals(self) -> (float, int):
        """Sum the total lap time and count of valid laps."""

        total_lap_time = 0.0
        valid_laps = 0
        for lap in self.laps:
            if lap.lap == 0:
                continue
            lap_is_valid = True
            for flag in lap.flags:
                if flag.mask == 1:  # invalid lap
                    lap_is_valid = False
                    break

            if lap_is_valid:
                valid_laps += 1
                total_lap_time += lap.time.total_seconds()

        return total_lap_time, valid_laps

    @property
    def fastest_driver(self) -> str:
        """Returns the name of the driver with the fastest lap."""

        fastest_driver = ""
        fastest_time = -1.0
        for driver in self.drivers:
            lap_time = driver["bestlaptime"]
            if lap_time > 0 and (fastest_time < 0 or lap_time < fastest_time):
                fastest_time = lap_time
                fastest_driver = driver["displayname"]
        return fastest_driver

    @property
    def driver(self) -> str:
        """Returns the name of the only driver.

        If more than one driver is present in the lap data,
        this will return an empty string
        """

        if len(self.drivers) == 1:
            return self.drivers[0]["displayname"]
        return ""

    @property
    def driver_id(self) -> int:
        """Returns the ID of the only driver.

        If more than one driver is present in the lap data,
        this will return zero
        """

        if len(self.drivers) == 1:
            return self.drivers[0]["custid"]
        return 0

    @property
    def summary(self) -> dict:
        """Returns a summary of the laps driven."""

        return {
            "num_laps": max(x.lap for x in self.laps) if self.laps else 0,
            "average_lap": self.average_string,
            "fastest_lap": self.fastest_lap_string,
            "fast_lap": self.fast_lap,
            "laps": [lap.summary for lap in self.laps],
        }
