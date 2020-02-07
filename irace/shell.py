"""Interactive shell utility for docker entry.

Usage:
    irace-shell [options]

Options:
    -h --help            show this message
    --version            display version information
"""


import os
import code

from . import __version__
from .utils import get_args
from .utils import ENV_FILE


def main():
    """drop into an interactive shell."""

    get_args(__doc__)

    if not os.path.exists(ENV_FILE) or not os.path.isfile(ENV_FILE):
        raise SystemExit("IRACE_ENV file {} does not exist".format(ENV_FILE))

    # some helpful imports...
    # pylint: disable=import-outside-toplevel,possibly-unused-variable
    from .storage import Server  # noqa: F401
    from .storage import Databases  # noqa: F401
    from .parse import Laps  # noqa: F401
    from .parse import Race  # noqa: F401
    from .parse import Season  # noqa: F401
    from .parse import League  # noqa: F401
    from .stats import Client  # noqa: F401
    from .stats.logger import log  # noqa: F401

    code.interact(
        banner="iRace {}".format(__version__),
        local=locals(),
    )


if __name__ == "__main__":
    main()
