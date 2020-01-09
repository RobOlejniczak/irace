"""Lap data parsing.

Usage:
    irace-laps [options]

Options:
    -h --help            show this message
    --version            display version information
    --debug              enable debug output
    --file <FILE>        filepath to lap JSON data (or use stdin)
"""


import os
import json

from .utils import get_args
from .utils import read_json
from .parse.laps import Laps


def _get_json(args) -> dict:
    """Returns the loaded lap JSON data."""

    if args["--file"] and os.path.isfile(args["--file"]):
        return read_json(args["--file"])

    print("Reading JSON data from stdin...")
    try:
        return json.loads(os.sys.stdin.read())
    except KeyboardInterrupt:
        print("Interrupted")
        raise SystemExit
    except Exception as error:
        print("Failed to read JSON data from stdin: {!r}".format(error))
        raise SystemExit


def main():
    """Command line entry point."""

    args = get_args(__doc__)
    laps = Laps(_get_json(args))

    data = [
        ("Driver(s)", ", ".join(x["displayname"] for x in laps.drivers)),
        ("Track", "{} ({})".format(
            laps.race["trackName"],
            laps.race["trackConfig"],
        )),
        ("Fast Lap", laps.fast_lap),
        ("Fast Lap Time", laps.fastest_lap_string),
        ("Average Lap Time", laps.average_string),
        ("Total Time", laps.total_time_string),
        ("Valid Laps", laps.valid_laps),
        ("Total Laps", laps.total_laps),
    ]

    times = []
    for lap in laps.laps:
        lap_time = lap.time_string
        if lap.flags:
            lap_time += " [{}]".format(", ".join(x.name for x in lap.flags))
        times.append(("Lap {}".format(lap.lap), lap_time))

    print("Parsed lap JSON {}:\n{}\n{}\n{}".format(
        args["--file"] or "from STDIN",
        "\n".join("  {}: {}".format(x[0], x[1]) for x in data),
        "  {stars} Laps {stars}".format(stars="*" * 10) if times else "",
        "\n".join("  {}: {}".format(x[0], x[1]) for x in times),
    ))


if __name__ == "__main__":
    main()
