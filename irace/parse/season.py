"""Race data parsing utilities."""


from collections import defaultdict


def _incidents_per_corner(race: dict, result: dict) -> float:
    """Calculate the average incidents per corner for the race."""

    # XXX corners complete isn't exposed as far as I can tell...
    corners_complete = race["cornersperlap"] * result["lapscomplete"]
    if corners_complete:
        return result["incidents"] / corners_complete
    return -1.0


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
        self._incidents_per_corner = []

    def add(self, race: dict, result: dict) -> None:
        """Add the race result to our totals."""

        self.driver = result["displayname"]
        self.driver_id = result["custid"]

        self.races += 1
        self.points += result["league_points"]
        self.wins += 1 if result["finishpos"] == 0 else 0
        self.podiums += 1 if result["finishpos"] < 3 else 0
        self.top5 += 1 if result["finishpos"] < 5 else 0
        self.top10 += 1 if result["finishpos"] < 10 else 0
        self.incidents += result["incidents"]
        self.laps += result["lapscomplete"]

        self._starts.append(result["startpos"] + 1)
        self._finishes.append(result["finishpos"] + 1)
        self._incidents_per_corner.append(_incidents_per_corner(
            race,
            result
        ))

    @property
    def incidents_per_corner(self) -> float:
        """Average our incidents per corner over all races."""

        legit = [x for x in self._incidents_per_corner if x > 0]
        if legit:
            return sum(legit) / len(legit)
        return 0.0

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


class Season:
    """Parsed season object.

    Instatiate with a list of Race objects and the season info.
    """

    def __init__(self, races: list, season: dict):
        self.races = races
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
