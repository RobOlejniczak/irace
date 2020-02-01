"""Race data parsing utilities."""


from collections import defaultdict

from .driver import Driver


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
