"""Helper utilities common in irace scripts."""


from docopt import docopt

from . import __version__


def get_args(doc: str) -> dict:
    """Perform the initial docopt parsing for help, version, etc."""

    args = docopt(
        doc,
        version="iRace {}".format(__version__),
    )

    args.pop("--version")
    args.pop("--help")

    return args
