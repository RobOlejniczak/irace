"""Race data parsing utilities."""


from collections import defaultdict


class Driver:  # pylint: disable=R0902
    """Season aggregated driver results."""

    def __init__(self):
        self.driver = ""
        self.driver_id = 0
        self.position = -1

        self.races = 0
        self.points = 0
        self.wins = 0
        self.podiums = 0
        self.top5 = 0
        self.top10 = 0
        self.incidents = 0
        self.laps = 0

        self._starts = []
        self._finishes = []
        self.corners = 0

    def add(self, race: dict, result: dict) -> None:
        """Add the race result to our totals."""

        self.driver = result["displayname"]
        self.driver_id = result["custid"]

        self.races += 1
        self.points += (result["league_points"] or 0) if \
            result["league_points"] > 0 else 0
        self.wins += 1 if result["finishpos"] == 0 else 0
        self.podiums += 1 if result["finishpos"] < 3 else 0
        self.top5 += 1 if result["finishpos"] < 5 else 0
        self.top10 += 1 if result["finishpos"] < 10 else 0
        self.incidents += result["incidents"]
        self.laps += result["lapscomplete"]
        self.corners += (race["cornersperlap"] * result["lapscomplete"])

        self._starts.append(result["startpos"] + 1)
        self._finishes.append(result["finishpos"] + 1)

    @property
    def corners_per_incident(self) -> str:
        """Calculate our corners per incidents over all races."""

        if self.incidents:
            return "{:,.2f}".format(self.corners / self.incidents)
        # no floating point distinguishes zero vs one incident
        return "{:,d}".format(self.corners)

    @property
    def avg_start(self) -> float:
        """Calculate our average starting position."""

        return sum(self._starts) / len(self._starts)

    @property
    def avg_finish(self) -> float:
        """Calculate our average finishing position."""

        return sum(self._finishes) / len(self._finishes)


class Leaderboard:
    """Simple leaderboard."""

    def __init__(self):
        self._drivers = defaultdict(Driver)
        self._races = []

    def add(self, race):
        """Add a race to the board."""

        if race.race["subsessionid"] in self._races:
            raise ValueError("Race {} already in leaderboard".format(
                race.race["subsessionid"]
            ))
        self._races.append(race.race["subsessionid"])

        for result in race.results:
            self._drivers[result["custid"]].add(race.race, result)

    @property
    def standings(self) -> list:
        """Returns an ordered list of driver season standings."""

        return sorted(
            self._drivers.values(),
            key=lambda x: x.points,
            reverse=True,
        )

    @property
    def drivers(self) -> int:
        """Returns a count of drivers in the season."""

        return len(self._drivers)

    @property
    def races(self) -> int:
        """Returns a count of races in the season."""

        return len(self._races)


class Season:
    """Parsed season object.

    Instatiate with a list of Race objects and the season info.
    """

    def __init__(self, races: list, season: dict):
        self.races = races
        self.race_data = [x.race for x in self.races]
        self.season = season
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

    def summary(self, driver_id: int) -> dict:
        """Return a summary for the driver in this season."""

        for driver in self.standings:
            if driver.driver_id == driver_id:
                return {
                    "season_id": self.season["league_season_id"],
                    "season_name": self.season["league_season_name"],
                    "league_id": self.season["leagueid"],
                    "position": driver.position,
                    "drivers": self.leaderboard.drivers,
                    "races": self.leaderboard.races,
                    "raced": driver.races,
                    "points": driver.points,
                    "wins": driver.wins,
                    "top5": driver.top5,
                    "top10": driver.top10,
                    "incidents": driver.incidents,
                    "laps": driver.laps,
                    "cpi": driver.corners_per_incident,
                    "avg_start": driver.avg_start,
                    "avg_finish": driver.avg_finish,
                }
        return {}
