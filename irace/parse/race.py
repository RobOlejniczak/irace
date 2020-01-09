"""Race data parsing utilities."""


from collections import namedtuple


Driver = namedtuple("Driver", ("name", "id"))


class Race:
    """Parsed race object.

    Instatiate with a list of Laps objects.
    """

    def __init__(self, laps: list, race: dict):
        self.laps = laps
        self.race = race
        self.results = sorted(  # ensure sorted by finish position
            [x for x in race["rows"] if x["simsesname"] == "RACE"],
            key=lambda x: x["finishpos"],
        )

    @property
    def fastest_lap(self) -> Driver:
        """Returns the Driver with the overall fastest lap."""

        fastest = -1.0
        obj = None
        for lap in self.laps:
            _fastest = lap.fastest_lap
            if _fastest > 0 and (fastest < 0 or _fastest < fastest):
                fastest = _fastest
                obj = lap

        if obj:
            return Driver(obj.driver, obj.driver_id)

        return Driver("", 0)
