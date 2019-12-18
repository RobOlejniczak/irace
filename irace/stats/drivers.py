"""Classes in this module serve to help find drivers (client.driver_search)."""


from .search import SortOptions
from .constants import Pages
from .constants import Sorting
from .constants import Locations
from .constants import RaceTypes
from .constants import LicenseClass


class Drivers:
    """Filter for drivers based on license, location, active and race type."""

    def __init__(self, license_levels=LicenseClass.ALL, location=Locations.ALL,
                 race_type=RaceTypes.ROAD, active=False):
        self.license_levels = license_levels
        self.location = location
        self.race_type = race_type
        self.active = active


class Averages:
    """Filter for drivers based on averages."""

    def __init__(self, start=(0, Pages.ALL), finish=(0, Pages.ALL),
                 points=(0, Pages.ALL), incidents=(0, Pages.ALL)):
        self.start = start
        self.finish = finish
        self.points = points
        self.incidents = incidents


class Ratings:
    """Filter for drivers based on iRatings."""

    def __init__(self, irating=(0, Pages.ALL), ttrating=(0, Pages.ALL)):
        self.irating = irating
        self.ttrating = ttrating


class DriverSearch():
    """Top level class for filtering to find drivers."""

    def __init__(self, averages: Averages = None, ratings: Ratings = None,
                 drivers: Drivers = None, sort_options: SortOptions = None):

        if sort_options is None:
            sort_options = SortOptions(Sorting.IRATING)

        self.sort = sort_options
        self.averages = averages or Averages()
        self.ratings = ratings or Ratings()
        self.drivers = drivers or Drivers()


def post_data(customer_id: int, query: DriverSearch, page: int) -> dict:
    """Master function for generating the POST data to search for drivers."""

    query = query or DriverSearch()

    lower = Pages.NUM_ENTRIES * (page - 1) + 1
    upper = lower + Pages.NUM_ENTRIES - 1

    return {
        "custid": customer_id,
        "search": "null",
        "friend": Pages.ALL,  # TODO
        "watched": Pages.ALL,  # TODO
        "country": query.drivers.location,
        "recent": Pages.ALL,  # TODO
        "category": query.drivers.race_type,
        "classlow": query.drivers.license_levels[0],
        "classhigh": query.drivers.license_levels[1],
        "iratinglow": query.ratings.irating[0],
        "iratinghigh": query.ratings.irating[1],
        "ttratinglow": query.ratings.ttrating[0],
        "ttratinghigh": query.ratings.ttrating[1],
        "avgstartlow": query.averages.start[0],
        "avgstarthigh": query.averages.start[1],
        "avgfinishlow": query.averages.finish[0],
        "avgfinishhigh": query.averages.finish[1],
        "avgpointslow": query.averages.points[0],
        "avgpointshigh": query.averages.points[1],
        "avgincidentslow": query.averages.incidents[0],
        "avgincidentshigh": query.averages.incidents[1],
        "lowerbound": lower,
        "upperbound": upper,
        "sort": query.sort.sort,
        "order": query.sort.order,
        "active": int(query.drivers.active)
    }
