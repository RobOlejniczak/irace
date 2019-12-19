"""Populate fills the results directory with JSON results from series races.

This script requires iRacing.com credentials to use. The intention is to
provide further processing of populated results via other scripts, which
would then not need credentials.

Usage:
    irace-populate [options]

Options:
    -h --help            show this message
    --version            display version information
    --user=<user>        iRacing.com username
    --passwd=<passwd>    iRacing.com password (insecure, better to be prompted)
    --club=<id>          iRacing.com club/league ID [default: 637]
    --car=<id>           car ID in the club to pull results from [default: -1]
    --year=<id>          year to pull results from [default: -1]
    --season=<id>        season to pull results from [default: 47806]
    --week=<id>          week of season to pull results from [default: -1]
    --output=<path>      output directory [default: results]
    --list-seasons       list the active seasons in the club/league
    --list-members       list the members in the club/league
    --debug              enable debug output
"""


import os
from getpass import getpass

from docopt import docopt

from . import __version__
from .stats import Client


def list_seasons(client: Client, args: dict):
    """Main function to list seasons active in the league."""

    for season in client.league_seasons(league_id=args["--club"]):
        # XXX most of this is useless, trim down to useful only...
        print("{}\n{}\n{}".format(
            "*" * 30,
            "\n".join("{}: {}".format(k, v) for k, v in season.items()),
            "*" * 30,
        ))


def list_members(client: Client, args: dict):
    """Main function to list league members."""

    results = client.league_members(args["--club"])
    print(results)
    # XXX broken atm


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
        results = {}

        for event in events["rows"]:
            results[event["sessionid"]] = client.event_results(
                event["sessionid"]
            )

        # XXX not sure what these returns look like yet...
        for session_id, result in results.items():
            write_result(args, session_id, repr(result))

    else:
        raise SystemExit("Could not fetch any results :(\n{!r}".format(args))


def write_result(args, page, result):
    """Write the result to file."""

    file_name = os.path.join(args["--output"], "{}.json".format(page))
    with open(file_name, "w") as open_results:
        open_results.write(result)


def ensure_output_directory(args):
    """Ensures the results directory exists.

    Args:
        args: dictionary of docopt arguments, modifies `--output` key
    """

    if os.path.isabs(args["--output"]):
        results = args["--output"]
    else:
        results = os.path.abspath(args["--output"])

    if os.path.exists(results) and not os.path.isdir(results):
        raise SystemExit("Results directory is an existing file? Bailing now.")

    if not os.path.exists(results):
        os.makedirs(results)

    args["--output"] = results


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
    ensure_output_directory(args)

    client = get_client(args)
    if args.pop("--list-seasons"):
        list_seasons(client, args)
    elif args.pop("--list-members"):
        list_members(client, args)
    else:
        fetch_results(client, args)


if __name__ == "__main__":
    main()
