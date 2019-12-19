"""Stats client."""


import csv
import json
import atexit
import logging

from io import StringIO
from urllib.parse import urlencode

from requests import Session
from requests import Request
from requests import Response
from requests_throttler import throttler

from . import utils
from . import search
from . import drivers

from .constants import Pages
from .constants import Charts
from .constants import Sorting
from .constants import URLs


logging.basicConfig(
    format=(
        "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] "
        "%(message)s"
    ),
    datefmt="%Y-%m-%d:%H:%M:%S",
)
log = logging.getLogger(__name__)


class RequestOptions:
    """Options for individual requests."""

    def __init__(self, get=False, login=False, json_response=True):
        self.get = get
        self.login = login
        self.json_response = json_response


class _Client:
    """Static client to manage the connection pool."""

    _client = None

    @staticmethod
    def _get():
        """Return and/or create the static throttled HTTP client."""

        if _Client._client is None:
            throttler.logger.level = 40  # set log level to logging.ERROR

            _Client._client = throttler.BaseThrottler(
                name="client",
                delay=0.1,
                session=Session(),
            )
            _Client._client.start()

            atexit.register(_Client.app_exit)

        return _Client._client

    @staticmethod
    def send_request(request: Request) -> Response:
        """Sends a request using our connection pool and rate limiter."""

        response = _Client._get().submit(request)  # async
        return response.get_response(timeout=10)  # sync (when timeout != 0)

    @staticmethod
    def app_exit():
        """Exit function to clean up the throttled client."""

        if _Client._client is not None:
            _Client._client.shutdown()
            _Client._client = None


class Stats:  # pylint: disable=R0904
    """iRacing stats client."""

    def __init__(self, username: str, password: str, debug=False):
        """Create a new stats client."""

        self.cookie = ""
        self.customer_id = 0

        if debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.ERROR)

        self.cache = {
            "tracks": {},
            "cars": {},
            "division": {},
            "car_class": {},
            "club": {},
            "season": None,
            "year_and_quarter": (None, None),
        }

        resp = self._req(
            URLs.IRACING_LOGIN,
            data={
                "username": username,
                "password": password,
                "utcoffset": 300,
                "todaysdate": "",
            },
            options=RequestOptions(login=True, json_response=False),
        )

        # can we please get a normal login procedure? thanks in advance...
        if "irsso_members" in self.cookie:
            # new programmers look away, this is not how you do it
            ind = resp.index("js_custid")
            self.customer_id = int(resp[ind + 11: resp.index(";", ind)])

            self._populate_cache(resp)
        else:
            raise SystemExit("Invalid login for: {}".format(username))

    def __del__(self):
        """Standard destructor method."""

        _Client.app_exit()
        del self

    def _req(self, url, data: dict = None, options: RequestOptions = None):
        """Create and send an HTTP request to iRacing."""

        if options is None:
            options = RequestOptions()

        resp = _Client.send_request(
            self._get_request(url, data=data, options=options)
        )

        resp.raise_for_status()

        if options.login and "Set-Cookie" in resp.headers:
            self.cookie = resp.headers["Set-Cookie"]
            # Must get irsso_members from another header. wtf...
            if "cookie" in resp.request.headers:
                # holy moly...
                self.cookie += ";" + resp.request.headers["cookie"]

        if not options.login:
            log.debug("\n{} {} {}\nheaders: {!r}\ncontent: {}\n{}".format(
                "*" * 15,
                url,
                "*" * 15,
                resp.headers,
                resp.text,
                "*" * (32 + len(url)),
            ))

        if options.json_response:
            return json.loads(resp.text)

        return resp.text

    def _get_request(self, url, data=None, options=None) -> Request:
        """Generate the Request object."""

        url = URLs.get(url)

        headers = {}
        if self.cookie:
            headers["Cookie"] = self.cookie

        if (data is None) or options.get:
            return Request(
                method="GET",
                url=url,
                headers=headers,
                params=data,
            )

        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return Request(
            method="POST",
            url=url,
            data=data,
            headers=headers,
        )

    def _populate_cache(self, response):
        """Gets general information from iRacing service.

        For eg; current tracks, cars, series, etc. Fills in self.cache.
        """

        items = {
            "tracks": "TrackListing",
            "cars": "CarListing",
            "car_class": "CarClassListing",
            "club": "ClubListing",
            "season": "SeasonListing",
            "division": "DivisionListing",
            "year_and_quarter": "YearAndQuarterListing"
        }

        for item, key in items.items():
            try:
                self.cache[item] = utils.get_irservice_var(key, response)
            except Exception as error:
                log.error("Failed to parse %s: %r", item, error)
                raise  # if this happens iRacing is probably down

    def irating_chart(self, customer_id=None, category=Charts.ROAD):
        """Gets the iRating data of a driver using its customer_id.

        This is used to generate the chart in the driver's profile.
        """

        return self._req(
            URLs.STATS_CHART % (customer_id or self.customer_id, category)
        )

    def driver_counts(self):
        """Gets list of connected myracers and notifications."""

        return self._req(URLs.DRIVER_COUNTS)

    def career_stats(self, customer_id=None):
        """Gets career stats (top5, top 10, etc.) of customer_id."""

        return self._req(URLs.CAREER_STATS % (customer_id or self.customer_id))

    def yearly_stats(self, customer_id=None):
        """Gets yearly stats (top5, top 10, etc.) of customer_id."""

        return self._req(URLs.YEARLY_STATS % (customer_id or self.customer_id))

    def cars_driven(self, customer_id=None):
        """Gets list of cars driven by customer_id."""

        return self._req(URLs.CARS_DRIVEN % (customer_id or self.customer_id))

    def personal_best(self, customer_id=None, car_id=0):
        """Personal best times of customer_id in car_id official events."""

        if car_id not in self.cache["cars"]:
            raise ValueError("car_id not known: %d" % car_id)

        return self._req(
            URLs.PERSONAL_BEST % (car_id, customer_id or self.customer_id)
        )

    def driver_data(self, driver_name):
        """Personal data of driver using their name in the request."""

        return self._req(
            URLs.DRIVER_STATUS % (urlencode({"searchTerms": driver_name}))
        )

    def last_race_stats(self, customer_id=None):
        """Gets stats of last races (10 max?) of customer_id."""

        return self._req(
            URLs.LAST_RACE_STATS % (customer_id or self.customer_id)
        )

    def driver_search(self, query=None, page=1):
        """Search for drivers using several search fields.

        Args::

            query: a `drivers.DriverSearch` instantiated object
            page: integer page to receive results from (default: 1)

        Returns:
            tuple of (results, total_pages)
        """

        data = drivers.post_data(self.customer_id, query, page)

        try:
            res = self._req(URLs.DRIVER_STATS, data=data)
            # magic number 29 is customer_id
            if int(res["d"]["r"][0]["29"]) == int(self.customer_id):
                return (
                    utils.format_results(res["d"]["r"][1:], res["m"]),
                    res["d"]["32"]
                )

            return (
                utils.format_results(res["d"]["r"], res["m"]),
                res["d"]["32"]
            )
        except Exception as error:
            log.error("Error fetching driver search data: %r", error)

        return {}, 0

    def results_archive(self, customer_id=None, query=None, page=1):
        """Search race results using various fields.

        Returns a tuple (results, total_results) so if you want all results
        you should request different pages (using page). Each page has 25
        (Pages.NUM_ENTRIES) results max.
        """

        data = search.post_data(query, customer_id or self.customer_id, page)
        res = self._req(URLs.RESULTS_ARCHIVE, data=data)

        if res["d"]:
            return (
                utils.format_results(res["d"]["r"], res["m"]),
                res["d"]["46"]
            )

        return [], 0

    def all_seasons(self):
        """Get all season data available at series stats page."""

        return utils.get_irservice_var(
            "SeasonListing",
            self._req(
                URLs.SEASON_STANDINGS2,
                options=RequestOptions(json_response=False),
            ),
        )

    def season_standings(self, season, season_options, sort_options=None,
                         page=1):
        """Search season standings using various fields.

        Args::

            season: integer season ID
            season_options: an instantiated SeasonOptions object
            sort_options: SortOptions class if desired (optional)
            page: integer page to return (default 1)

        Returns:
            tuple (results, total_pages)
        """

        lower = Pages.NUM_ENTRIES * (page - 1) + 1
        upper = lower + Pages.NUM_ENTRIES - 1

        if sort_options is None:
            sort_options = search.SortOptions(Sorting.POINTS)

        data = {
            "sort": sort_options.sort,
            "order": sort_options.order,
            "seasonid": season,
            "carclassid": season_options.car_class,
            "clubid": season_options.club,
            "raceweek": season_options.race_week,
            "division": season_options.division,
            "start": lower,
            "end": upper,
        }

        res = self._req(URLs.SEASON_STANDINGS, data=data)

        if res["d"]:
            return (
                utils.format_results(res["d"]["r"], res["m"]),
                res["d"]["27"]
            )

        return [], 0

    def hosted_results(self, session_options=None, date_range=None,
                       sort_options=None, page=1):
        """Search hosted races results using various fields.

        Returns a tuple (results, total_results) so if you want all results
        you should request different pages (using page) until you gather all
        total_results. Each page has 25 (Pages.NUM_ENTRIES) results max.
        """

        lower, upper = utils.page_bounds(page)

        session_options = session_options or search.SessionOptions()
        sort_options = sort_options or search.SortOptions()

        data = {
            "sort": sort_options.sort,
            "order": sort_options.order,
            "lowerBound": lower,
            "upperBound": upper,
        }

        if session_options.host is not None:
            data["sessionhost"] = session_options.host
        if session_options.name is not None:
            data["sessionname"] = session_options.name

        if date_range is not None:
            # Date range
            data["starttime_lowerbound"] = utils.as_timestamp(date_range[0])
            data["starttime_upperbound"] = utils.as_timestamp(date_range[1])

        res = self._req(URLs.HOSTED_RESULTS, data=data)
        # doesn't need utils.format_results
        return res["rows"], res["rowcount"]

    def session_times(self, series_season, start, end):
        """Gets current and future sessions of series_season."""

        return self._req(
            URLs.SESSION_TIMES,
            data={"start": start, "end": end, "season": series_season},
            options=RequestOptions(get=True),
        )

    def series_race_results(self, season, race_week):
        """ Gets races results of all races of season in specified raceweek """

        res = self._req(
            URLs.SERIES_RACE_RESULTS,
            data={"seasonid": season, "raceweek": race_week}  # TODO no bounds?
        )
        return utils.format_results(res["d"], res["m"])

    def event_results(self, subsession, sessnum=0):
        """Gets the event results (table of positions, times, etc.).

        The event is identified by a subsession id.
        """

        data = list(csv.reader(
            StringIO(self._req(
                URLs.EVENT_RESULTS % (subsession, sessnum),
                options=RequestOptions(json_response=False),
            )),
            delimiter=",",
            quotechar='"',
        ))

        return (
            dict(list(zip(data[0], data[1]))),
            [dict(list(zip(data[3], x))) for x in data[4:]]
        )

    def league_seasons(self, league_id):
        """Returns the list of seasons in the league."""

        results = self._req(URLs.LEAGUE_SEASONS, data={"leagueID": league_id})
        return utils.format_results(results["d"]["r"], results["m"])

    def league_members(self, league_id, page=1):
        """Returns the member list for a league."""

        # lower, upper = utils.page_bounds(page)
        return self._req(
            URLs.LEAGUE_MEMBERS,
            data={
                "leagueID": league_id,
                # "lowerBound": lower,
                # "upperBound": upper,
            },
        )

    def league_season_standings(self, league_id, season_id):
        """Returns the standings for the given season in the league."""

        return self._req(
            URLs.LEAGUE_SEASON_STANDINGS,
            data={
                "leagueID": league_id,
                "leagueSeasonID": season_id,
            },
        )

    def league_season_team_standings(self, league_id, season_id):
        """Returns the team standings for the season in the league."""

        return self._req(
            URLs.LEAGUE_TEAM_STANDINGS,
            data={
                "leagueID": league_id,
                "leagueSeasonID": season_id,
            },
        )

    def league_season_calendar(self, league_id, season_id):
        """Returns the calendar of events for the league and season."""

        return self._req(
            URLs.LEAGUE_SEASON_CALENDAR,
            data={
                "leagueID": league_id,
                "leagueSeasonID": season_id,
            },
        )
