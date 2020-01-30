"""iRace league search tool.

Displays basic information about a league by name or ID.

Usage:
    irace-league [options] <SEARCH>

Options:
    -h --help            show this message
    --version            display version information
    --debug              enable debug output
    --user=<user>        iRacing.com username
    --passwd=<passwd>    iRacing.com password (insecure, better to be prompted)
"""


import json

from .stats import Client
from .utils import get_args
from .utils import config_client


def main():
    """Command line entry point."""

    args = get_args(__doc__)
    config_client(args)

    try:
        res = Client.league_info(int(args["<SEARCH>"]))
    except ValueError:
        res = Client.league_search(args["<SEARCH>"])

    print(json.dumps(res, sort_keys=True, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
