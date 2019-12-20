"""Stats module utilities."""


import json
import time

from datetime import datetime
from functools import wraps
from urllib.parse import unquote_plus

from .logger import log
from .constants import Pages


def untested(func):  # XXX remove me!
    """Wrap for untested functionality."""

    @wraps(func)
    def _untested(*args, **kwargs):
        """Warn the user they're about to use an untested function."""

        log.warning(
            "Function %s is untested! Please report bugs to "
            "https://github.com/a-tal/irace/issues thanks!",
            func.__name__,
        )
        return func(*args, **kwargs)

    return _untested


def format_results(results, header):
    """Re-arrange the results into a more manageable data structure."""

    return [{header[k]: v for k, v in row.items()} for row in results]


def format_strings(results: dict) -> None:
    """Blindly clean all string values in the dictionary (recursive)."""

    if isinstance(results, (list, tuple)):
        for result in results:
            format_strings(result)
        return

    for key, value in results.items():
        if isinstance(value, str):
            # iRacing.com double plus encodes their strings...
            # so um. just... go ahead and double undo that here
            results[key] = unquote_plus(unquote_plus(results[key]))
        elif isinstance(value, (list, tuple)):
            for nested in value:
                format_strings(nested)
        elif isinstance(value, dict):
            format_strings(value)


def format_season_race(race: dict) -> None:
    """Format the keys inside the race dictionary.

    Context here is only for the League Seasons return.
    """

    format_strings(race)
    race["cars"] = json.loads(race["cars"])


def get_irservice_var(key, resp, appear=1):
    """Parse the value for a key from the text response."""

    # this function should not exist. iRacing needs to provide this
    # information in a more sane fashion. string parsing javascript
    # inside of html is not a long-term nor stable solution.

    str2find = "var " + key + " = extractJSON('"
    ind1 = -1
    for _ in range(appear):
        ind1 = resp.index(str2find, ind1 + 1)

    loaded = json.loads(resp[
        ind1 + len(str2find): resp.index("');", ind1)
    ].replace("+", " "))

    if key in ("SeasonListing", "YearAndQuarterListing"):
        return loaded

    return {x["id"]: x for x in loaded}


def as_timestamp(time_string):
    """Convert the time string into a timestamp."""

    return time.mktime(
        datetime.strptime(time_string, "%Y-%m-%d").timetuple()
    ) * 1000


def page_bounds(page: int = 1) -> (int, int):
    """Return the lower and upper bounds given the page number."""

    lower = Pages.NUM_ENTRIES * (page - 1) + 1
    return lower, lower + Pages.NUM_ENTRIES
