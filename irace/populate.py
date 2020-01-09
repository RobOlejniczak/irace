"""Populate fills the results directory with JSON results from series races.

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
    --club=<id>          iRacing.com club/league ID [default: 637]
    --car=<id>           car ID in the club to pull results from [default: -1]
    --year=<id>          year to pull results from [default: -1]
    --season=<id>        season to pull results from [default: 47806]
    --week=<id>          week of season to pull results from [default: -1]
    --output=<path>      output directory [default: results]
    --league             populate basic information about the club/league
    --seasons            populate seasons for the club/league
    --members            populate members for the club/league
    --races              populate race and lap data for the club's season
"""


import os
import json

from .stats import Client
from .utils import get_args
from .utils import get_client


def _print_dict(data: dict) -> None:
    """Print the dictionary in a block listing all keys and values."""

    print("{}\n{}\n{}".format(  # XXX temp/debug purposes only...
        "*" * 30,
        json.dumps(data, sort_keys=True, indent=4),
        "*" * 30,
    ))


def _success(args: dict, category: tuple, results: int) -> None:
    """Print the success message at app exit."""

    out_dir = os.path.join(args["--output"], *category)

    if results:
        print("Wrote {:,d} result{} to: {}".format(
            results,
            "s" * int(results != 1),
            out_dir,
        ))
    else:
        print("No results found for: {}".format(out_dir))


def _category(*args) -> tuple:
    """Ensure all category levels are strings."""

    return tuple(str(x) for x in args)


def fetch_league(args: dict, client: Client) -> None:
    """Fetch basic information about the league."""

    category = ("leagues",)
    league = client.league_info(args["--club"])
    if league:
        _write_result(args, category, args["--club"], league)

    _success(args, category, int(league is not None))


def fetch_seasons(args: dict, client: Client) -> None:
    """Main function to list seasons active in the league."""

    category = _category("seasons", args["--club"])
    results = 0

    for season in client.league_seasons(league_id=args["--club"]):
        if season:
            _write_result(args, category, season["league_season_id"], season)
            results += 1

    _success(args, category, results)


def fetch_members(args: dict, client: Client) -> None:
    """Main function to list league members."""

    category = _category("members", args["--club"])
    results = 0

    for member in client.league_members(args["--club"]):
        if member:
            _write_result(args, category, member["custID"], member)
            results += 1

    _success(args, category, results)


def fetch_standings(args: dict, client: Client) -> None:
    """Main function to fetch season standings."""

    # XXX do we need this at all?
    results = client.league_season_standings(
        args["--club"],
        args["--season"],
    )
    print(results)


def fetch_results(args: dict, client: Client) -> None:
    """Main function to fetch league results."""

    events = client.league_season_calendar(args["--club"], args["--season"])

    if events and events["rowcount"] >= 1:

        category = _category("races", args["--club"], args["--season"])
        results = 0

        for event in events["rows"]:
            sub_session_id = event["subsessionid"]
            session_result = client.session_results(sub_session_id)
            if session_result:
                _write_result(args, category, sub_session_id, session_result)
                results += 1
                _fetch_laps(args, client, session_result)

        _success(args, category, results)

    else:
        raise SystemExit("Could not fetch any results :(\n{!r}".format(args))


def _fetch_laps(args: dict, client: Client, session: dict) -> None:
    """Fetch laps for all drivers in the session."""

    _id = session["subsessionid"]
    category = _category("laps", args["--club"], args["--season"], _id)
    results = 0

    fetched = []
    for driver in session["rows"]:
        if driver["groupid"] in fetched:
            # the same driver will appear up to 3 times in rows, due
            # to entries for practice, qualify and race...
            continue
        fetched.append(driver["groupid"])

        laps = client.session_laps(_id, driver["groupid"])
        if laps:
            results += 1
            _write_result(args, category, driver["custid"], laps)

    _success(args, category, results)


def _write_result(args: dict, category: tuple, _id: str, obj: object) -> None:
    """Write the result to file."""

    if category:
        directory = os.path.join(args["--output"], *category)
    else:
        directory = args["--output"]

    _file = os.path.join(_ensure_directory(directory), "{}.json".format(_id))
    with open(_file, "w") as open_results:
        open_results.write(json.dumps(obj, sort_keys=True, indent=4))


def _ensure_directory(file_path: str) -> str:
    """Ensures the directory at file_path exists.

    Returns:
        string absolute file_path
    """

    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    if os.path.exists(file_path) and not os.path.isdir(file_path):
        raise SystemExit(
            "Output directory {} already exists, as a file. Bailing.".format(
                file_path
            )
        )

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    return file_path


def validate_integer_arguments(args) -> None:
    """Ensure all integer arguments passed are valid.

    Args:
        args: docopt arguments dictionary, modifies integer keys
    """

    for arg in ("--car", "--club", "--season", "--week", "--year"):
        try:
            args[arg] = int(args[arg])
        except ValueError:
            raise SystemExit("Invalid value for {}: {}".format(arg, args[arg]))


def main() -> None:
    """Command line entry point."""

    args = get_args(__doc__)

    validate_integer_arguments(args)
    _ensure_directory(args["--output"])

    client = get_client(args)
    if args.pop("--league"):
        fetch_league(args, client)
    elif args.pop("--seasons"):
        fetch_seasons(args, client)
    elif args.pop("--members"):
        fetch_members(args, client)
    elif args.pop("--races"):
        fetch_results(args, client)
    else:
        fetch_league(args, client)
        fetch_members(args, client)
        fetch_seasons(args, client)
        fetch_results(args, client)


if __name__ == "__main__":
    main()
