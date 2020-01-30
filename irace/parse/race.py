"""Race data parsing utilities."""


from datetime import datetime
from collections import namedtuple

from .utils import suffix
from .utils import time_string_raw
from ..stats import Client


Driver = namedtuple("Driver", ("name", "id"))


class Race:  # pylint: disable=too-many-instance-attributes
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

        classes = set(x["ccNameShort"] for x in self.results)
        self.multiclass = len(classes) > 1
        self.class_laps_completed = {
            car_class: max(
                x["lapscomplete"]
                for x in self.results if x["ccNameShort"] == car_class
            ) for car_class in classes
        }

        date = datetime.strptime(race["start_time"], "%Y-%m-%d %H:%M:%S")
        self.race_day = date.strftime("%B {}{}, %Y").format(
            date.day,
            suffix(date.day),
        )
        if self.results:
            self.winner = self.results[0]["displayname"]
            self.winner_id = self.results[0]["custid"]
        else:
            self.winner = "N/A"
            self.winner_id = 0
        self.subsessionid = race["subsessionid"]

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

    def summary(self, driver_id: int) -> dict:
        """Returns a race summary including the laps summary."""

        for laps in self.laps:
            if laps.driver_id == driver_id:
                _summary = dict(laps.summary)
                for res in self.results:
                    if res["custid"] == driver_id:
                        _summary.update({
                            "league_id": self.race["leagueid"],
                            "season_id": self.race["league_season_id"],
                            "race_id": self.race["subsessionid"],
                            "incidents": res["incidents"],
                            "start": res["startpos"] + 1,
                            "finish": res["finishpos"] + 1,
                            "points": res["league_points"],
                            "sof": self.race["eventstrengthoffield"],
                            "interval": time_string_raw(res["interval"]) if (
                                res["interval"] > 0 or
                                res["finishpos"] == 0
                            ) else "{:,d}L".format(
                                res["lapscomplete"] -
                                self.race["eventlapscomplete"]
                            ),
                            "race_day": self.race_day,
                            "car": Client.cache["cars"].get(
                                res["carid"],
                                {"abbrevname": "N/A"}
                            )["abbrevname"],
                            "car_id": res["carid"],
                            "drivers": len(self.results),
                            "track": self.race["track_name"],
                            "track_config": self.race["track_config_name"],
                        })

                        if self.multiclass:
                            _summary.update({
                                "class_name": res["ccNameShort"],
                                "class_finish": res["finishposinclass"] + 1,
                                "class_interval": time_string_raw(
                                    res["classinterval"]
                                ) if (
                                    res["classinterval"] > 0 or
                                    res["finishposinclass"] == 0
                                ) else "{:,d}L".format(
                                    res["lapscomplete"] -
                                    self.class_laps_completed[
                                        res["ccNameShort"]
                                    ]
                                ),
                                "class_drivers": len([
                                    x for x in self.results
                                    if x["ccNameShort"] == res["ccNameShort"]
                                ]),
                            })
                return _summary
        return {}
