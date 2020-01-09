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

from .utils import get_args
from .utils import get_client


def main():
    """Command line entry point."""

    args = get_args(__doc__)
    client = get_client(args)

    try:
        res = client.league_info(int(args["<SEARCH>"]))
    except ValueError:
        res = client.league_search(args["<SEARCH>"])

    print(json.dumps(res, sort_keys=True, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
