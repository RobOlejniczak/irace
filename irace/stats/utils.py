"""Stats module utilities."""


import json
import time

from urllib.parse import unquote_plus
from datetime import datetime

from .constants import Pages


def format_results(results, header):
    """Re-arrange the results into a more manageable data structure."""

    return [{header[k]: v for k, v in row.items()} for row in results]


def format_strings(results: list, keys: tuple) -> list:
    """Clean up the string key values in results."""

    for result in results:
        _format_strings(result, keys)

    return results


def _format_strings(result: dict, keys: tuple) -> None:
    """Munge the keys in the result dictionary."""

    for key in keys:
        # iRacing.com double plus encodes their strings...
        # so um. just... go ahead and double undo that here
        result[key] = unquote_plus(unquote_plus(result[key]))


def format_season_race(race: dict) -> None:
    """Format the keys inside the race dictionary.

    Context here is only for the League Seasons return.
    """

    _format_strings(race, ("config_name", "track_name"))
    race["cars"] = json.loads(unquote_plus(unquote_plus(race["cars"])))  # lol


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
