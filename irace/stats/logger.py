"""Logging functionality."""


import logging


logging.basicConfig(
    format=(
        "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] "
        "%(message)s"
    ),
    datefmt="%Y-%m-%d:%H:%M:%S",
)
log = logging.getLogger(__name__)  # pylint: disable=C0103


def set_log_level(debug: bool = False) -> None:
    """Set the log level to debug or error."""

    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)
