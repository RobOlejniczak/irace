"""Helper utilities common in irace scripts."""


import io
import os
import json
from getpass import getpass

from docopt import docopt

from . import __version__
from .stats import Client


ENV_FILE = os.environ.get("IRACE_ENV", ".env")


def read_json(filepath: str) -> object:
    """Reads the JSON object at filepath."""

    return json.loads(read_file(filepath))


def read_file(filepath: str) -> str:
    """Reads the content at filepath."""

    with io.open(filepath, "r", encoding="utf-8") as openfile:
        return openfile.read()


def get_args(doc: str) -> dict:
    """Perform the initial docopt parsing for help, version, etc."""

    read_environment_file()
    args = docopt(
        doc,
        version="iRace {}".format(__version__),
    )

    args.pop("--version")
    args.pop("--help")

    return args


def config_client(args) -> None:
    """Configures the stats.Client with the credentials passed."""

    args["--user"] = args["--user"] or os.getenv("IRACING_USERNAME")
    args["--passwd"] = args["--passwd"] or os.getenv("IRACING_PASSWORD")

    while not args["--user"]:
        try:
            args["--user"] = input("iRacing.com username? ")
        except KeyboardInterrupt:
            raise SystemExit("Interrupted")

    Client.set_debug(args["--debug"])

    if args["--passwd"]:
        Client.set_credentials(args["--user"], args["--passwd"])
    else:
        Client.set_credentials(args["--user"], getpass())

    args.pop("--user")
    args.pop("--passwd")
    args.pop("--debug")

    return Client


def ensure_directory(file_path: str) -> str:
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


def read_environment_file() -> None:
    """Injects environment variables from the IRACE_ENV file."""

    if os.path.exists(ENV_FILE) and os.path.isfile(ENV_FILE):
        for line in read_file(ENV_FILE).splitlines():
            if not line or line.startswith("#"):
                continue
            try:
                key, value = line.split("=", 1)
            except ValueError:
                pass
            else:
                os.environ[key] = value
