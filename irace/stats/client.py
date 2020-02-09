"""Stats client."""


import os
import json
import time
import atexit
from urllib.parse import urlencode

from requests import Session
from requests import Request
from requests import Response
from requests_throttler import throttler

from . import utils
from . import search
from . import drivers
from .logger import log
from .logger import set_log_level
from .constants import Pages
from .constants import Charts
from .constants import Sorting
from .constants import URLs


class ParsingOptions:
    """Options for parsing individual requests."""

    def __init__(self, get=False, login=False, json_response=True):
        self.get = get
        self.login = login
        self.json_response = json_response


class RequestOptions:
    """Options for individual requests."""

    def __init__(self, parsing: ParsingOptions = None, headers: dict = None,
                 cookies: dict = None):
        self.parsing = parsing or ParsingOptions()
        self.headers = headers or {}
        self.cookies = cookies or {}

    def merge_headers(self, headers: dict) -> None:
        """Merge our headers and cookies into the request headers."""

        for key, value in self.headers.items():
            headers[key] = value

        cookie = headers.get("cookie", "")
        for key, value in self.cookies.items():
            if cookie:
                cookie += "; {}={}".format(key, value)
            else:
                cookie = "{}={}".format(key, value)

        headers["cookie"] = cookie


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

    def __init__(self):
        """Create a new stats client."""

        self.num_requests = 0

        self._debug = False
        self.set_debug(bool(int(os.getenv("IRACE_DEBUG") or 0)))

        self.cache = {
            "tracks": {},
            "cars": {},
            "division": {},
            "car_class": {},
            "club": {},
            "season": None,
            "year_and_quarter": (None, None),
        }

        self.__auth = {
            "last": 0,  # timestamp of last succesful login
            "min": 7200,  # minimum seconds to keep cookie for (2hr)
            "max": 21600,  # maximum seconds to keep cookie for (6hr)
            "cookie": "",
            "custid": int(os.getenv("IRACING_CUSTID") or 0),
            "url": os.getenv("IRACING_LOGIN") or URLs.LOGIN,
            "data": {
                "username": os.getenv("IRACING_USERNAME"),
                "password": os.getenv("IRACING_PASSWORD"),
                "utcoffset": 300,
                "todaysdate": "",
            },
        }

    def set_debug(self, debug: bool) -> None:
        """Set the logging level."""

        self._debug = debug
        set_log_level(debug)

    def set_credentials(self, username: str = "", password: str = "") -> None:
        """Update the auth credentials."""

        if username:
            self.__auth["data"]["username"] = username

        if password:
            self.__auth["data"]["password"] = password

    def login(self, username: str = "", password: str = "",
              force: bool = False) -> None:
        """Perform the login procedure."""

        self.set_credentials(username, password)

        if force or (self.__auth["last"] < (time.time() - self.__auth["min"])):
            log.info("Performing login")
            self._req(
                self.__auth["url"],
                data=self.__auth["data"],
                options=RequestOptions(
                    ParsingOptions(login=True, json_response=False),
                ),
            )
            self.__auth["last"] = time.time()

        self._populate_cache(force)

    def _populate_cache(self, force: bool = False):
        """Gets general information from iRacing service.

        For eg; current tracks, cars, series, etc. Fills in self.cache.
        """

        if self.cache.get("__populated") and not force:
            return

        log.info("Populating cache")

        resp = self._req(
            URLs.CACHE,
            options=RequestOptions(ParsingOptions(json_response=False)),
        )

        try:
            self.__auth["custid"] = int([
                x for x in resp.splitlines()
                if x.lstrip().startswith("custid:")
            ][0].split(":")[1].split(",")[0])
        except Exception as error:
            log.warning("Unable to extract custID: %r", error)
            return

        items = {
            "tracks": "TrackListing",
            "cars": "CarListing",
            "car_class": "CarClassListing",
            # "club": "ClubListing",  # broken
            "season": "SeasonListing",
            "division": "DivisionListing",
            "year_and_quarter": "YearAndQuarterListing"
        }

        errored = False
        for item, key in items.items():
            try:
                self.cache[item] = utils.get_irservice_var(key, resp)
            except Exception as error:
                log.warning("Failed to parse %s: %r", item, error)
                errored = True

        if not errored:
            self.cache["__populated"] = True

    def __del__(self):
        """Standard destructor method."""

        _Client.app_exit()
        del self

    def _req(self, url, data: dict = None, options: RequestOptions = None):
        """Create and send an HTTP request to iRacing."""

        if options is None:
            options = RequestOptions()

        if not options.parsing.login and (
                not self.__auth["last"] or self.__auth["last"] < (
                    time.time() - self.__auth["max"])):
            self.login()

        resp = _Client.send_request(
            self._get_request(url, data=data, options=options)
        )

        self.num_requests += 1

        resp.raise_for_status()

        if options.parsing.login and "Set-Cookie" in resp.headers:
            self.__auth["cookie"] = resp.headers["Set-Cookie"]
            # Must get irsso_members from another header. wtf...
            if "cookie" in resp.request.headers:
                # holy moly...
                self.__auth["cookie"] += ";" + resp.request.headers["cookie"]

        if not options.parsing.login:
            header = " ".join((
                "*" * 15,
                resp.request.method,
                url,
                str(resp.status_code),
                "*" * 15,
            ))
            log.log(
                5,
                "\n%s\nreq data: %r\nreq headers: %r\n"
                "resp headers: %r\nresp data: %r\n%s",
                header,
                data,
                resp.request.headers,
                resp.headers,
                resp.text,
                "*" * len(header),
            )

        if options.parsing.json_response:
            return json.loads(resp.text)

        return resp.text

    def _get_request(self, url: str, data: dict,
                     options: RequestOptions) -> Request:
        """Generate the Request object."""

        url = URLs.get(url)

        headers = {}
        if self.__auth["cookie"] and not options.parsing.login:
            headers["cookie"] = self.__auth["cookie"]

        options.merge_headers(headers)

        if (data is None) or options.parsing.get:
            return Request(
                method="GET",
                url=url,
                headers=headers,
                params=data,
            )

        return Request(
            method="POST",
            url=url,
            data=data,
            headers=headers,
        )

    @utils.untested
    def irating_chart(self, customer_id=None, category=Charts.ROAD):
        """Gets the iRating data of a driver using its customer_id.

        This is used to generate the chart in the driver's profile.
        """

        return self._req(
            URLs.STATS_CHART % (customer_id or self.__auth["custid"], category)
        )

    @utils.untested
    def driver_counts(self):
        """Gets list of connected myracers and notifications."""

        return self._req(URLs.DRIVER_COUNTS)

    @utils.untested
    def career_stats(self, customer_id=None):
        """Gets career stats (top5, top 10, etc.) of customer_id."""

        return self._req(
            URLs.CAREER_STATS % (customer_id or self.__auth["custid"])
        )

    @utils.untested
    def yearly_stats(self, customer_id=None):
        """Gets yearly stats (top5, top 10, etc.) of customer_id."""

        return self._req(
            URLs.YEARLY_STATS % (customer_id or self.__auth["custid"])
        )

    @utils.untested
    def cars_driven(self, customer_id=None):
        """Gets list of cars driven by customer_id."""

        return self._req(
            URLs.CARS_DRIVEN % (customer_id or self.__auth["custid"])
        )

    @utils.untested
    def personal_best(self, customer_id=None, car_id=0):
        """Personal best times of customer_id in car_id official events."""

        if car_id not in self.cache["cars"]:
            raise ValueError("car_id not known: %d" % car_id)

        return self._req(
            URLs.PERSONAL_BEST % (car_id, customer_id or self.__auth["custid"])
        )

    @utils.untested
    def driver_data(self, driver_name):
        """Personal data of driver using their name in the request."""

        return self._req(
            URLs.DRIVER_STATUS % (urlencode({"searchTerms": driver_name}))
        )

    @utils.untested
    def last_race_stats(self, customer_id=None):
        """Gets stats of last races (10 max?) of customer_id."""

        return self._req(
            URLs.LAST_RACE_STATS % (customer_id or self.__auth["custid"])
        )

    @utils.untested
    def driver_search(self, query=None, page=1):
        """Search for drivers using several search fields.

        Args::

            query: a `drivers.DriverSearch` instantiated object
            page: integer page to receive results from (default: 1)

        Returns:
            tuple of (results, total_pages)
        """

        data = drivers.post_data(self.__auth["custid"], query, page)

        try:
            res = self._req(URLs.DRIVER_STATS, data=data)
            # magic number 29 is customer_id
            if int(res["d"]["r"][0]["29"]) == int(self.__auth["custid"]):
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

    @utils.untested
    def results_archive(self, customer_id=None, query=None, page=1):
        """Search race results using various fields.

        Returns a tuple (results, total_results) so if you want all results
        you should request different pages (using page). Each page has 25
        (Pages.NUM_ENTRIES) results max.
        """

        data = search.post_data(
            query,
            customer_id or self.__auth["custid"],
            page
        )
        res = self._req(URLs.RESULTS_ARCHIVE, data=data)

        if res["d"]:
            return (
                utils.format_results(res["d"]["r"], res["m"]),
                res["d"]["46"]
            )

        return [], 0

    @utils.untested
    def all_seasons(self):
        """Get all season data available at series stats page."""

        return utils.get_irservice_var(
            "SeasonListing",
            self._req(
                URLs.SEASON_STANDINGS2,
                options=RequestOptions(ParsingOptions(json_response=False)),
            ),
        )

    @utils.untested
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

        lower, upper = utils.page_bounds(page)

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

    @utils.untested
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

    @utils.untested
    def session_times(self, series_season, start, end):
        """Gets current and future sessions of series_season."""

        return self._req(
            URLs.SESSION_TIMES,
            data={"start": start, "end": end, "season": series_season},
            options=RequestOptions(ParsingOptions(get=True)),
        )

    @utils.untested
    def series_race_results(self, season, race_week):
        """Gets races results of all races of season in specified raceweek."""

        res = self._req(
            URLs.SERIES_RACE_RESULTS,
            data={"seasonid": season, "raceweek": race_week}  # TODO no bounds?
        )
        return utils.format_results(res["d"], res["m"])

    def session_results(self, sub_session_id: int) -> dict:
        """Get the session (race) results."""

        results = self._req(
            URLs.SESSION_RESULTS,
            data={
                "subsessionID": sub_session_id,
                "custid": self.__auth["custid"],
            },
        )

        if results:
            utils.format_strings(results)

        return results

    def session_laps(self, sub_session_id, group_id):
        """Return the laps for the given group_id (driver)."""

        results = self._req(
            URLs.SESSION_LAPS,
            data={
                "subsessionid": sub_session_id,
                "groupid": group_id,
            },
        )

        if results:
            utils.format_strings(results)

        return results

    def league_seasons(self, league_id):
        """Returns the list of seasons in the league."""

        results = self._req(URLs.LEAGUE_SEASONS, data={"leagueID": league_id})
        seasons = utils.format_results(
            results["d"]["r"],
            results["m"],
        )
        utils.format_strings(seasons)

        for season in seasons:
            season["custom_points_json"] = json.loads(
                season["custom_points_json"]
            )

            for previous_race in season.get("previousrace", []):
                if previous_race:
                    utils.format_season_race(previous_race)

            if season["nextrace"]:
                utils.format_season_race(season["nextrace"])

        return seasons

    def league_members(self, league_id):
        """Returns all members in a league (will paginate)."""

        all_results = []
        page = 1

        while True:
            results = self._league_members(league_id, page=page)
            all_results.extend(results)
            page += 1
            if len(results) < Pages.NUM_ENTRIES:
                break

        return all_results

    def _league_members(self, league_id, page=1):
        """Returns the member list for a league."""

        lower, upper = utils.page_bounds(page)
        members = self._req(
            URLs.LEAGUE_MEMBERS,
            data={
                "leagueid": league_id,
                "lowerBound": lower,
                "upperBound": upper,
            },
        )

        utils.format_strings(members)
        return members

    @utils.untested
    def league_season_standings(self, league_id, season_id):
        """Returns the standings for the given season in the league."""

        return self._req(
            URLs.LEAGUE_SEASON_STANDINGS,
            data={
                "leagueID": league_id,
                "leagueSeasonID": season_id,
            },
        )

    @utils.untested
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

        res = self._req(
            URLs.LEAGUE_SEASON_CALENDAR,
            data={
                "leagueID": league_id,
                "leagueSeasonID": season_id,
            },
        )
        utils.format_strings(res)
        return res

    def _league_search(self, term):
        """Requests the league directory with the search parameter."""

        raw = self._req(
            URLs.LEAGUE_SEARCH,
            data={
                "search": term,
                "restrictToMember": 0,
                "lowerbound": 1,
                "upperbound": 33,
            },
        )
        if raw and raw.get("d"):
            res = utils.format_results(raw["d"]["r"], raw["m"])
            utils.format_strings(res)
            return res
        return []

    def league_search(self, phrase):
        """Returns basic info about the league (by name)."""

        for result in self._league_search(phrase):
            # XXX not sure if iRacing leagues are actually case-insensitive
            if result["leaguename"].lower() == phrase.lower():
                return result
        return None

    def league_info(self, league_id):
        """Returns basic info about the league by ID."""

        for result in self._league_search(league_id):
            if result["leagueid"] == league_id:
                return result
        return None


Client = Stats()  # pylint: disable=invalid-name
