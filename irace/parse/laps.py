"""Lap data parsing utilities."""


from datetime import timedelta
from collections import namedtuple


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


def _as_timedelta(timestamp: float) -> timedelta:
    """Convert whatever timestamps iRacing is using into standard."""

    # NB: not microseconds nor milliseconds, unfortunately
    return timedelta(seconds=timestamp / 10000.0)


def _as_time_string(timestamp) -> str:
    """Convert the timestamp to a decent looking time string."""

    if isinstance(timestamp, timedelta):
        return str(timestamp)

    return str(timedelta(seconds=timestamp))


class Lap:
    """Parsed lap object."""

    def __init__(self, data: dict, prev: int):
        self.flags = _get_flags(data["flags"])
        self.lap = data["lap_num"]
        self.time = _as_timedelta(data["ses_time"] - prev)
        self.time_string = _as_time_string(self.time)


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

        return _as_time_string(self.average)

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

        if best_lap_time:
            return _as_timedelta(best_lap_time).total_seconds()

        return -1.0

    @property
    def fastest_lap_string(self) -> str:
        """Fastest lap time (in seconds) as a string."""

        return _as_time_string(self.fastest_lap)

    @property
    def total_time(self) -> float:
        """Total lap time of all valid laps."""

        return self._lap_totals()[0]

    @property
    def total_time_string(self) -> str:
        """Total lap time of all valid laps as a string."""

        return _as_time_string(self.total_time)

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
            lap_is_valid = True
            for flag in lap.flags:
                if flag.mask == 1:  # invalid lap
                    lap_is_valid = False
                    break

            if lap_is_valid:
                valid_laps += 1
                total_lap_time += lap.time.total_seconds()

        return total_lap_time, valid_laps
