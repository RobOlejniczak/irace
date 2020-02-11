"""Populate fills the results databases with JSON results from series races.

This script requires iRacing.com credentials to use. The intention is to
provide further processing of populated results via other scripts, which
would then not need credentials.

Usage:
    irace-populate [options]

Options:
    -h --help            show this message
    --version            display version information
    --debug              enable debug output
    --user=<user>        iRacing.com username
    --passwd=<passwd>    iRacing.com password (insecure, better to be prompted)
    --club=<id>          iRacing.com club/league ID
    --car=<id>           car ID in the club to pull results from [default: -1]
    --year=<id>          year to pull results from [default: -1]
    --season=<id>        season to pull results from
    --week=<id>          week of season to pull results from [default: -1]
    --output=<path>      output directory (if not using db) [default: results]
    --league             populate basic information about the club/league
    --seasons            populate seasons for the club/league
    --members            populate members for the club/league
    --races              populate race and lap data for the club's seasons
"""


import os
from functools import wraps

from .stats import Client
from .utils import get_args
from .utils import config_client
from .storage import Server
from .storage import Databases


def _success(database: Databases, results: int) -> None:
    """Print the success message at app exit."""

    if results:
        print("Stored {:,d} result{} for {}".format(
            results,
            "s" * int(results != 1),
            database.name,
        ))


def for_one_or_all(func):
    """Wrap for call the underlying function once or for all leagues."""

    @wraps(func)
    def _for_one_or_all(args: dict):
        if args["--club"] > 0:
            return func(args)
        results = []
        for league in Server.read_all(Databases.leagues):
            args["--club"] = league["leagueid"]
            results.append(func(args))
        return results

    return _for_one_or_all


@for_one_or_all
def fetch_league(args: dict) -> None:
    """Fetch basic information about the league."""

    league = Client.league_info(args["--club"])
    if league:
        Server.write(Databases.leagues, (), args["--club"], league)

    _success(Databases.leagues, int(league is not None))


@for_one_or_all
def fetch_seasons(args: dict) -> list:
    """Main function to list seasons active in the league."""

    season_ids = []
    for season in Client.league_seasons(league_id=args["--club"]):
        if season:
            Server.write(
                Databases.seasons,
                (args["--club"],),
                season["league_season_id"],
                season,
            )
            season_ids.append(season["league_season_id"])

    _success(Databases.seasons, len(season_ids))
    return season_ids


@for_one_or_all
def fetch_members(args: dict) -> None:
    """Main function to list league members."""

    results = 0
    for member in Client.league_members(args["--club"]):
        if member:
            Server.write(
                Databases.members,
                (args["--club"],),
                member["custID"],
                member,
            )
            results += 1

    _success(Databases.members, results)


def fetch_results(args: dict) -> None:
    """Main function to fetch unknown league results."""

    events = Client.league_season_calendar(args["--club"], args["--season"])

    if events and events["rowcount"] >= 1:
        Server.write(
            Databases.calendars,
            (args["--club"],),
            args["--season"],
            events,
        )
        _success(Databases.calendars, 1)

        sub_values = (args["--club"], args["--season"])
        results = 0

        for event in events["rows"]:
            _id = event["subsessionid"]

            if not _id or Server.exists(Databases.races, sub_values, _id):
                continue

            result = Client.session_results(_id)
            if result:
                Server.write(
                    Databases.races,
                    sub_values,
                    _id,
                    result,
                )
                results += 1
                _fetch_laps(args, result)

        _success(Databases.races, results)


def _fetch_laps(args: dict, session: dict) -> None:
    """Fetch laps for all drivers in the session."""

    _id = session["subsessionid"]
    sub_values = (args["--club"], args["--season"], _id)

    results = 0
    fetched = []
    for driver in session["rows"]:
        if driver["groupid"] in fetched:
            # the same driver will appear up to 3 times in rows, due
            # to entries for practice, qualify and race...
            continue

        fetched.append(driver["groupid"])
        laps = Client.session_laps(_id, driver["groupid"])
        if laps:
            results += 1
            Server.write(
                Databases.laps,
                sub_values,
                driver["custid"],
                laps,
            )

    _success(Databases.laps, results)


@for_one_or_all
def fetch_races(args: dict) -> None:
    """Fetch any unknown races in all seasons."""

    seasons = fetch_seasons(args)
    for season in seasons:
        args["--season"] = season
        fetch_results(args)


def validate_integer_arguments(args) -> None:
    """Ensure all integer arguments passed are valid.

    Args:
        args: docopt arguments dictionary, modifies integer keys
    """

    for arg in ("--car", "--club", "--season", "--week", "--year"):
        try:
            args[arg] = int(args[arg] or 0)
        except ValueError:
            raise SystemExit("Invalid value for {}: {}".format(arg, args[arg]))


def main() -> None:
    """Command line entry point."""

    args = get_args(__doc__)

    validate_integer_arguments(args)
    os.environ["IRACE_RESULTS"] = args["--output"]

    config_client(args)

    if args.pop("--league"):
        fetch_league(args)
    elif args.pop("--seasons"):
        fetch_seasons(args)
    elif args.pop("--members"):
        fetch_members(args)
    elif args.pop("--races"):
        if args["--club"] and args["--season"]:
            fetch_results(args)
        else:
            fetch_races(args)
    else:
        fetch_league(args)
        fetch_members(args)
        fetch_races(args)


if __name__ == "__main__":
    main()
