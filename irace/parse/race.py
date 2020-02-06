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

        classes = []  # NB: specifically not using set comp to keep order
        class_winners = []
        for res in self.results:
            if res["ccNameShort"] not in classes:
                classes.append(res["ccNameShort"])
                class_winners.append({
                    "id": res["custid"],
                    "name": res["displayname"]
                })
        self.classes = tuple(classes)
        self.class_winners = tuple(class_winners)

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
    def multiclass(self) -> bool:
        """If this race has more than one class."""

        return len(self.classes) > 1

    @property
    def class_laps_completed(self) -> dict:
        """Mapping of string class to integer laps completed."""

        return {
            cls: max(
                x["lapscomplete"]
                for x in self.results if x["ccNameShort"] == cls
            ) for cls in self.classes
        }

    @property
    def class_drivers(self) -> dict:
        """Mapping of string class to integer count of drivers."""

        return {
            cls: len([
                x for x in self.results if x["ccNameShort"] == cls
            ]) for cls in self.classes
        }

    def class_summary(self, include_winners: bool = False) -> list:
        """Return a per-class summary of this race."""

        all_classes = []
        for i, cls in enumerate(self.classes):
            this_cls = {
                "name": cls,
                "laps": self.class_laps_completed[cls],
                "drivers": self.class_drivers[cls],
            }
            if include_winners:
                this_cls["winner"] = self.class_winners[i]
            all_classes.append(this_cls)

        return all_classes

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

    def _driver_results(self, driver_id: int) -> dict:
        """Return the results dict for the driver by ID."""

        for res in self.results:
            if res["custid"] == driver_id:
                return res
        return {}

    def driver_summary(self, driver_id: int,
                       race_info: bool = True,
                       driver_info: bool = False,
                       lap_info: bool = True) -> dict:
        """Returns a race summary including the laps summary."""

        _summary = {}

        for laps in self.laps:
            if laps.driver_id == driver_id:
                if lap_info:
                    _summary.update(laps.summary)
                else:
                    _summary["laps"] = laps.total_laps

                res = self._driver_results(driver_id)
                if res:
                    _summary.update({
                        "incidents": res["incidents"],
                        "start": res["startpos"] + 1,
                        "finish": res["finishpos"] + 1,
                        "points": res["league_points"],
                        "out": res["reasonout"],
                        "interval": "--:--" if
                                    self.race["eventlapscomplete"] == 0 else
                                    time_string_raw(res["interval"]) if (
                                        res["interval"] > 0 or
                                        res["finishpos"] == 0
                                    ) else "{:,d}L".format(
                                        res["lapscomplete"] -
                                        self.race["eventlapscomplete"]
                                    ),
                        "interval_raw": res["interval"],
                        "car": Client.cache["cars"].get(
                            res["carid"],
                            {"abbrevname": "N/A"}
                        )["abbrevname"],
                        "car_id": res["carid"],
                    })

                    if self.multiclass:
                        _summary["class"] = {
                            "name": res["ccNameShort"],
                            "finish": res["finishposinclass"] + 1,
                            "interval": time_string_raw(
                                res["classinterval"]
                            ) if (
                                res["classinterval"] > 0 or
                                res["finishposinclass"] == 0
                            ) else "{:,d}L".format(
                                res["lapscomplete"] -
                                self.class_laps_completed[res["ccNameShort"]]
                            ),
                            "interval_raw": res["classinterval"],
                        }

                    if race_info:
                        _summary.update({
                            "league": self.race["leagueid"],
                            "season": self.race["league_season_id"],
                            "id": self.race["subsessionid"],
                            "date": self.race_day,
                            "drivers": len(self.results),
                            "track": self.race["track_name"],
                            "config": self.race["track_config_name"],
                            "sof": self.race["eventstrengthoffield"],
                        })

                        if self.multiclass:
                            _summary["class"].update({
                                "laps": self.class_laps_completed[
                                    res["ccNameShort"]
                                ],
                                "drivers": self.class_drivers[
                                    res["ccNameShort"]
                                ],
                            })

                    if driver_info:
                        _summary.update({
                            "driver": {
                                "id": res["custid"],
                                "name": res["displayname"],
                            },
                            "car_num": res["carnum"],
                            "club": res["clubshortname"],
                        })

                break

        return _summary
