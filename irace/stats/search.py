"""Helpers related to search functionality."""


from .utils import as_timestamp
from .constants import Pages
from .constants import Events
from .constants import Sorting
from .constants import Official
from .constants import RaceTypes
from .constants import LicenseClass


EVENT_ARGS = {
    Events.RACE: "showraces",
    Events.QUALIFY: "showquals",
    Events.PRACTICE: "showops",
    Events.TIME_TRIAL: "showtts"
}

LICENSE_ARGS = {
    LicenseClass.ROOKIE: "showrookie",
    LicenseClass.A: "showclassa",
    LicenseClass.B: "showclassb",
    LicenseClass.C: "showclassc",
    LicenseClass.D: "showclassd",
    LicenseClass.PRO: "showpro",
    LicenseClass.PRO_WC: "showprowc"
}


class DriverOptions:
    """Search options for license levels, car and track."""

    def __init__(self, license_levels=LicenseClass.ALL, car=Pages.ALL,
                 track=Pages.ALL, active=False):
        self.license_levels = license_levels
        self.car = car
        self.track = track
        self.active = active


class RaceOptions:
    """Search options for race/event types, official or series."""

    def __init__(self, race_type=RaceTypes.ROAD, event_types=Events.ALL,
                 official=Official.ALL, series=Pages.ALL):
        self.race_type = race_type
        self.event_types = event_types
        self.official = official
        self.series = series


class DateRange:
    """Search options for seasons or date ranges."""

    def __init__(self, season=(2014, 1, Pages.ALL), date_range=Pages.ALL):
        self.season = season
        self.date_range = date_range


class SortOptions:
    """Search options for sorting and ordering."""

    def __init__(self, sort=Sorting.TIME, order=Sorting.DESC):
        self.sort = sort
        self.order = order


class SessionOptions:
    """Search options for session host and name."""

    def __init__(self, host=None, name=None):
        self.host = host
        self.name = name


class SeasonOptions:
    """Search options for season results.

    Note that `car_class` and `club` are ids.
    """

    def __init__(self, car_class, club=Pages.ALL, race_week=Pages.ALL,
                 division=Pages.ALL):
        self.car_class = car_class
        self.club = club
        self.race_week = race_week
        self.division = division


class Query:
    """Search options top level class."""

    def __init__(self, driver_options: DriverOptions = None,
                 race_options: RaceOptions = None,
                 date_range: DateRange = None,
                 sort_options: SortOptions = None):
        self.driver = driver_options or DriverOptions()
        self.race = race_options or RaceOptions()
        self.date = date_range or DateRange()
        self.sort = sort_options or SortOptions()


def default_data(query: Query, customer_id: int) -> dict:
    """Default POST data before merging most query parameters."""

    return {
        "format": "json",
        "custid": customer_id,
        "seriesid": query.race.series,
        "carid": query.driver.car,
        "trackid": query.driver.track,
        "lowerbound": 0,
        "upperbound": 0,
        "sort": query.sort.sort,
        "order": query.sort.order,
        "category": query.race.race_type,
        "showtts": 0,
        "showraces": 0,
        "showquals": 0,
        "showops": 0,
        "showofficial": 0,
        "showunofficial": 0,
        "showrookie": 0,
        "showclassa": 0,
        "showclassb": 0,
        "showclassc": 0,
        "showclassd": 0,
        "showpro": 0,
        "showprowc": 0
    }


def post_data(query: Query, customer_id: int, page: int) -> dict:
    """Master function to return constructed POST data for searching."""

    if query is None:
        query = Query()

    data = default_data(query, customer_id)
    merge_query(data, query, page)
    return data


def merge_query(data, query, page):
    """Merge all aspects from query into data."""

    merge_pagination(data, page)
    merge_event_types(data, query)
    merge_official(data, query)
    merge_date_range(data, query)
    merge_license_levels(data, query)


def merge_pagination(data, page):
    """Add query data for pagination to the data dictionary."""

    lower = Pages.NUM_ENTRIES * (page - 1) + 1
    upper = lower + Pages.NUM_ENTRIES - 1

    data["lowerbound"] = lower
    data["upperbound"] = upper


def merge_event_types(data, query):
    """Add query data for event_types to the data dictionary."""

    if not isinstance(query.race.event_types, (list, tuple)):
        query.race.event_types = tuple(query.race.event_types)

    for event_type in query.race.event_types:
        if event_type in EVENT_ARGS:
            data[EVENT_ARGS[event_type]] = 1


def merge_official(data, query):
    """Add query data for official vs unofficial to the data dictionary."""

    if query.race.official == Official.ALL:
        data["showofficial"] = 1
        data["showunoofficial"] = 1
    else:
        if not isinstance(query.race.official, (list, tuple)):
            query.race.official = tuple(query.race.official)
        if Official.UNOFFICIAL in query.race.official:
            data["showunofficial"] = 1
        if Official.OFFICIAL in query.race.official:
            data["showofficial"] = 1


def merge_date_range(data, query):
    """Add query data for year/season to the data dictionary."""

    if query.date.date_range == Pages.ALL:
        data["seasonyear"] = query.date.season[0]
        data["seasonquarter"] = query.date.season[1]
        if query.date.season[2] != Pages.ALL:
            data["raceweek"] = query.date.season[2]
    else:
        data["starttime_low"] = as_timestamp(query.date.date_range[0])
        data["starttime_high"] = as_timestamp(query.date.date_range[1])


def merge_license_levels(data, query):
    """Add query data for license classes to the data dictionary."""

    if not isinstance(query.driver.license_levels, (list, tuple)):
        query.driver.license_levels = tuple(query.driver.license_levels)

    for license_level in query.driver.license_levels:
        if license_level in LICENSE_ARGS:
            data[LICENSE_ARGS[license_level]] = 1
