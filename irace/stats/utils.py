"""Stats module utilities."""


import json
import time

from datetime import datetime


def format_results(results, header):
    """Re-arrange the results into a more manageable data structure."""

    return [{header[k]: v} for row in results for k, v in row]


def get_irservice_var(key, resp, appear=1):
    """Parse the value for a key from the text response."""

    # this function should not exist. iRacing needs to provide this
    # information in a more sane fashion. string parsing javascript
    # inside of html is not a long-term nor stable solution.

    str2find = "var " + key + " = extractJSON('"
    ind1 = -1
    for _ in range(appear):
        ind1 = resp.index(str2find, ind1+1)

    loaded = json.loads(resp[
        ind1 + len(str2find): resp.index("');", ind1)
    ].replace("+", " "))  # XXX is this a lazy urlplus decode?

    if key in ("SeasonListing", "YearAndQuarterListing"):
        return loaded

    return {x["id"]: x for x in loaded}


def as_timestamp(time_string):
    """Convert the time string into a timestamp."""

    return time.mktime(
        datetime.strptime(time_string, "%Y-%m-%d").timetuple()
    ) * 1000
