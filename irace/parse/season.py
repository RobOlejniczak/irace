"""Season parsing utilities."""


from .leaderboard import Leaderboard


class Season:
    """Parsed season object.

    Instatiate with a list of Race objects and the season info.
    """

    def __init__(self, races: list, season: dict, league: dict):
        self.races = races
        self.race_data = [x.race for x in self.races]
        self.season = season
        self.league = league
        self.leaderboard = Leaderboard()
        for race in self.races:
            self.leaderboard.add(race)

    @property
    def standings(self) -> list:
        """Return a list of driver standings for the season."""

        drivers = self.leaderboard.standings

        previous_points = -1
        previous_position = -1

        for i, driver in enumerate(drivers, 1):
            if driver.points == previous_points:
                driver.position = previous_position
            else:
                driver.position = i
                previous_position = i
            previous_points = driver.points

        return drivers

    def driver_summary(self, driver_id: int, season_info: bool = True) -> dict:
        """Return a summary for the driver in this season."""

        for driver in self.standings:
            if driver.driver_id == driver_id:
                _summary = {
                    "position": driver.position,
                    "raced": driver.races,
                    "points": driver.points,
                    "wins": driver.wins,
                    "podiums": driver.podiums,
                    "top5": driver.top5,
                    "top10": driver.top10,
                    "incidents": driver.incidents,
                    "laps": driver.laps,
                    "cpi": driver.corners_per_incident,
                    "avg_start": driver.avg_start,
                    "avg_finish": driver.avg_finish,
                }
                if season_info:
                    _summary.update({
                        "season": {
                            "id": self.season["league_season_id"],
                            "name": self.season["league_season_name"],
                        },
                        "league": {
                            "id": self.league["leagueid"],
                            "name": self.league["leaguename"],
                        },
                        "drivers": self.leaderboard.drivers,
                        "races": self.leaderboard.races,
                    })
                else:
                    _summary.update({
                        "driver": driver.driver,
                        "driver_id": driver.driver_id,
                    })
                return _summary
        return {}

    def race_summary(self, race_id: int, season_info: bool = True,
                     results: bool = True) -> dict:
        """Return a summary for this race in the season."""

        for race in self.races:
            if race.race["subsessionid"] == race_id:
                _summary = {
                    "id": race.subsessionid,
                    "date": race.race_day,
                    "sim_time": race.race["simulatedstarttime"],
                    "temp": "{}{}".format(
                        race.race["weather_temp_value"],
                        "F"
                        if race.race["weather_temp_units"] == 0 else
                        "C",
                    ),
                    "track": race.race["track_name"],
                    "config": race.race["track_config_name"],
                    "drivers": len(race.results),
                    "sof": race.race["eventstrengthoffield"],
                    "laps": race.race["eventlapscomplete"],
                }

                if results:
                    driver_results = []
                    for driver in race.results:
                        driver_result = race.driver_summary(
                            driver["custid"],
                            race_info=False,
                            driver_info=True,
                            lap_info=True,
                        )
                        if driver_result:
                            driver_results.append(driver_result)

                    if driver_results:
                        _summary["results"] = driver_results
                else:
                    _summary["winner"] = {
                        "name": race.winner,
                        "id": race.winner_id,
                    }

                if race.multiclass:
                    _summary["classes"] = race.class_summary(
                        include_winners=not results,
                    )

                if season_info:
                    info = dict(self._top_level_info)
                    info["race"] = _summary
                    return info

                return _summary

        return {}

    @property
    def _top_level_info(self) -> dict:
        """Return a summary of our league and season details."""

        return {
            "league": {
                "name": self.league["leaguename"],
                "id": self.league["leagueid"],
            },
            "season": {
                "name": self.season["league_season_name"],
                "id": self.season["league_season_id"],
            }
        }

    def summary(self) -> dict:
        """Return a summary of all races in this season."""

        _summary = self._top_level_info
        _summary["races"] = [
            self.race_summary(x.subsessionid, season_info=False, results=False)
            for x in self.races
        ]
        _summary["standings"] = [
            self.driver_summary(x.driver_id, season_info=False)
            for x in self.standings
        ]
        return _summary
