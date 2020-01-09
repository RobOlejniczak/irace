"""Helper utilities common in irace scripts."""


import io
import os
import json
from getpass import getpass

from docopt import docopt

from . import __version__
from .stats import Client


def read_json(filepath: str) -> object:
    """Reads the JSON object at filepath."""

    with io.open(filepath, "r", encoding="utf-8") as openfile:
        return json.loads(openfile.read())


def get_args(doc: str) -> dict:
    """Perform the initial docopt parsing for help, version, etc."""

    args = docopt(
        doc,
        version="iRace {}".format(__version__),
    )

    args.pop("--version")
    args.pop("--help")

    return args


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
