"""League parsing utilities."""


class League:
    """Parsed league object.

    Instatiate with the league info and a list of season dictionaries
    """

    def __init__(self, league: dict, seasons: list):
        self.league = league
        self.seasons = seasons

    @property
    def info(self) -> dict:
        """Return top level information about this league."""

        return {
            "name": self.league["leaguename"],
            "id": self.league["leagueid"],
        }

    @property
    def summary(self) -> dict:
        """Return a summary of all seasons in this league."""

        return {
            "league": self.info,
            "seasons": [season.league_summary for season in self.seasons],
        }
