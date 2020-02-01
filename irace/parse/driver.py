"""Parsed driver object."""


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
        points = result["league_points"] or 0
        self.points += points if points > 0 else 0
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
    def corners_per_incident(self) -> float:
        """Calculate our corners per incidents over all races."""

        if self.incidents:
            return "{:,.1f}".format(self.corners / self.incidents)
        # no floating point distinguishes zero vs one incident
        return "{:,d}".format(self.corners)

    @property
    def avg_start(self) -> int:
        """Calculate our average starting position."""

        return int(sum(self._starts) / len(self._starts))

    @property
    def avg_finish(self) -> int:
        """Calculate our average finishing position."""

        return int(sum(self._finishes) / len(self._finishes))
