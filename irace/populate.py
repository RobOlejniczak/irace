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
    --seasons            populate seasons for the club/league
    --members            populate members for the club/league
"""


import os
import json
from getpass import getpass

from docopt import docopt

from . import __version__
from .stats import Client


def _print_dict(data: dict) -> None:
    """Print the dictionary in a block listing all keys and values."""

    print("{}\n{}\n{}".format(  # XXX temp/debug purposes only...
        "*" * 30,
        json.dumps(data, sort_keys=True, indent=4),
        "*" * 30,
    ))


def _success(args: dict, category: tuple, results: int) -> None:
    """Print the success message at app exit."""

    print("Wrote {:,d} results to: {}".format(
        results,
        os.path.join(args["--output"], *category),
    ))


def _category(*args) -> tuple:
    """Ensure all category levels are strings."""

    return tuple(str(x) for x in args)


def list_seasons(client: Client, args: dict):
    """Main function to list seasons active in the league."""

    category = _category("seasons", args["--club"])
    results = 0

    for season in client.league_seasons(league_id=args["--club"]):
        _write_result(args, category, season["league_season_id"], season)
        results += 1

    _success(args, category, results)


def list_members(client: Client, args: dict):
    """Main function to list league members."""

    category = _category("members", args["--club"])
    results = 0

    for member in client.league_members(args["--club"]):
        _write_result(args, category, member["custID"], member)
        results += 1

    _success(args, category, results)


def fetch_standings(client: Client, args: dict):
    """Main function to fetch season standings."""

    # XXX do we need this at all?
    results = client.league_season_standings(
        args["--club"],
        args["--season"],
    )
    print(results)


def fetch_results(client: Client, args: dict):
    """Main function to fetch league results."""

    events = client.league_season_calendar(args["--club"], args["--season"])

    if events and events["rowcount"] >= 1:
        sessions = {}

        for event in events["rows"]:
            sessions[event["sessionid"]] = client.event_results(
                event["sessionid"]
            )

        # XXX not sure what these returns look like yet...
        category = _category("races", args["--club"], args["--season"])
        results = 0

        for session_id, result in sessions.items():
            _write_result(args, category, session_id, repr(result))
            results += 1

        _success(args, category, results)

    else:
        raise SystemExit("Could not fetch any results :(\n{!r}".format(args))


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


def validate_integer_arguments(args):
    """Ensure all integer arguments passed are valid.

    Args:
        args: docopt arguments dictionary, modifies integer keys
    """

    for arg in ("--car", "--club", "--season", "--week", "--year"):
        try:
            args[arg] = int(args[arg])
        except ValueError:
            raise SystemExit("Invalid value for {}: {}".format(arg, args[arg]))


def get_client(args) -> Client:
    """Creates the stats.Client with the credentials passed."""

    args["--user"] = args["--user"] or os.getenv("IRACING_USERNAME")
    args["--passwd"] = args["--passwd"] or os.getenv("IRACING_PASSWORD")

    while not args["--user"]:
        try:
            args["--user"] = input("iRacing.com username? ")
        except KeyboardInterrupt:
            raise SystemExit("Interrupted")

    if args["--passwd"]:
        client = Client(args["--user"], args["--passwd"], args["--debug"])
    else:
        client = Client(args["--user"], getpass(), args["--debug"])

    args.pop("--user")
    args.pop("--passwd")
    args.pop("--debug")

    return client


def main():
    """Command line entry point."""

    args = docopt(__doc__)

    if args["--version"]:
        print("iRace {}".format(__version__))
        raise SystemExit

    args.pop("--version")
    args.pop("--help")

    validate_integer_arguments(args)
    _ensure_directory(args["--output"])

    client = get_client(args)
    if args.pop("--seasons"):
        list_seasons(client, args)
    elif args.pop("--members"):
        list_members(client, args)
    else:
        fetch_results(client, args)


if __name__ == "__main__":
    main()
