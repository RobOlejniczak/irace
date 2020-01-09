"""Race data parsing.

With no options will detail the most recent race ID, numerically.

Usage:
    irace-result [options]

Options:
    -h --help            show this message
    --version            display version information
    --list               list available race IDs
    --list-seasons       list available season IDs
    --race <ID>          race ID to parse
    --input <PATH>       JSON input directory [default: results]
    --league <ID>        limit races to a league by ID
    --season <ID>        limit races to a season by ID
    --all                aggregate all races in the season
"""


import os
from glob import glob

from .utils import get_args
from .utils import read_json
from .parse import Laps
from .parse import Race
from .parse import Season


def _laps_path(args: dict, race_id: int = 0) -> str:
    """Return the filepath to the laps JSON."""

    return os.path.join(
        args["--input"],
        "laps",
        args["--league"] or "*",
        args["--season"] or "*",
        *[str(race_id), "*"] if race_id else ["*"],
    )


def _available_races(args: dict) -> list:
    """Return a list of available races by ID."""

    return [int(os.path.split(x)[1]) for x in glob(_laps_path(args))]


def _available_seasons(args: dict) -> list:
    """Return a list of available seasons by ID."""

    return [int(os.path.split(x)[1]) for x in glob(os.path.join(
        args["--input"],
        "laps",
        args["--league"] or "*",
        args["--season"] or "*",
    ))]


def _get_laps(args: dict, race_id: int) -> list:
    """Return a list of Laps objects for the given race ID."""

    laps = []
    for filepath in glob(_laps_path(args, race_id)):
        laps.append(Laps(read_json(filepath)))
    return laps


def _get_race_data(args: dict, race_id: int) -> dict:
    """Load the race JSON from disk."""

    files = glob(os.path.join(
        args["--input"],
        "races",
        args["--league"] or "*",
        args["--season"] or "*",
        "{}.json".format(race_id),
    ))
    if len(files) != 1:
        raise SystemExit("Unable to load race data for {}".format(race_id))
    return read_json(files[0])


def _get_season_data(args: dict, season_id: int) -> dict:
    """Load the season JSON from disk."""

    files = glob(os.path.join(
        args["--input"],
        "seasons",
        args["--league"] or "*",
        "{}.json".format(season_id),
    ))
    if len(files) != 1:
        raise SystemExit("Unable to load season data for {}".format(season_id))
    return read_json(files[0])


def list_races(args: dict) -> None:
    """Print a list of race IDs available to parse."""

    ids = _available_races(args)
    if ids:
        print("Available races:\n{}".format("\n".join([
            "    {}".format(x) for x in ids
        ])))
    else:
        print("Could not find any races in {}".format(args["--input"]))


def list_seasons(args: dict) -> None:
    """Print a list of available season IDs to parse."""

    seasons = _available_seasons(args)
    if seasons:
        print("Available seasons:\n{}".format("\n".join([
            "    {}".format(x) for x in seasons
        ])))
    else:
        print("Could not find any seasons in {}".format(args["--input"]))


def detail_race(args: dict) -> None:
    """Print details about a race by loading a parsing object."""

    race_id = args["--race"] or max(_available_races(args))
    race = Race(_get_laps(args, race_id), _get_race_data(args, race_id))
    print("{}\n{}".format(
        race.race["track_name"],
        "\n".join(" {}. {}".format(
            driver["finishpos"] + 1,
            driver["displayname"],
        ) for driver in race.results),
    ))


def season_standings(args: dict) -> None:
    """List season standings."""

    if args["--season"] is None:
        available = _available_seasons(args)
        if available:
            args["--season"] = str(max(available))
        else:
            raise SystemExit("No season data found in {}".format(
                args["--input"]
            ))

    try:
        season_id = int(args["--season"])
    except ValueError:
        raise SystemExit("invalid --season ID")

    season = Season(
        races=[
            Race(_get_laps(args, race_id), _get_race_data(args, race_id))
            for race_id in _available_races(args)
        ],
        season=_get_season_data(args, season_id),
    )
    print("{}\n{}".format(
        season.season["league_season_name"],
        "\n".join(" {}. {} ({} points)".format(
            i + 1,
            driver.driver,
            driver.points,
        ) for i, driver in enumerate(season.standings)),
    ))


def main() -> None:
    """Command line entry point."""

    args = get_args(__doc__)
    if args["--list"]:
        list_races(args)
    elif args["--list-seasons"]:
        list_seasons(args)
    elif args["--all"]:
        season_standings(args)
    else:
        detail_race(args)


if __name__ == "__main__":
    main()
