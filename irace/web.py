"""iRace development web server.

This script will start a very expensive development server to generate
templated files live. Possibly less expensive than irace-generate though,
useful when working on the HTML templates, css, js, etc.

Usage:
    irace-web [options]

Options:
    -h --help            show this message
    --version            display version information
    --no-debug           disable debug output
    --input=<path>       input path, if using  [default: results]
    --port=<port>        run the server on a non-standard port
    --exposed            run the server on 0.0.0.0 instead of 127.0.0.1
    --drop-drivers       if we should drop all driver data on startup
"""


import os

try:
    from flask import abort
except ImportError:
    raise SystemExit(
        "irace-web requires the admin extras. "
        "Use `pip install .[admin]` to install them."
    )

from flask import Flask
from flask import jsonify
# from flask import redirect
from flask import render_template

from .stats import Client
from .parse import Race
from .parse import Laps
from .parse import Season
from .parse import League
from .utils import get_args
from .storage import Server
from .storage import Databases
from .generate import driver_results
from .parse.utils import random_color
from .parse.utils import time_string
from .parse.utils import time_string_raw
from .stats.logger import log


app = Flask(  # pylint: disable=invalid-name
    __name__,
    static_url_path="/js",
    static_folder=os.path.join("..", "static"),
)


@app.context_processor
def inject_irace_host():
    """Inject our static runtime variables to the jinja2 environment."""

    return dict(
        time_string=time_string,
        time_string_raw=time_string_raw,
        random_color=random_color,
    )


class Cache:
    """Simple cache."""

    _items = {}

    @staticmethod
    def get(*args, **kwargs) -> None:
        """Call Server.read_all with args and kwargs for any missing values."""

        try:
            db_name = args[0].name
        except (IndexError, AttributeError):
            raise ValueError("Expected Databases member")

        try:
            db_args = args[1]
        except IndexError:
            key = db_name
        else:
            key = "{}-{}".format("-".join(str(x) for x in db_args), db_name)

        return Cache.get_func(key, Server.read_all, *args, **kwargs)

    @staticmethod
    def get_one(*args, **kwargs) -> None:
        """Call Server.read with args and kwargs for any missing values."""

        try:
            db_name = args[0].name
        except (IndexError, AttributeError):
            raise ValueError("Expected Databases member")

        try:
            sub_values = args[1]
        except IndexError:
            raise ValueError("Expected sub values")

        try:
            _id = args[2]
        except IndexError:
            raise ValueError("Excepted item id")

        key = "{}{}{}-{}".format(
            _id,
            "-" if sub_values else "",
            "-".join(str(x) for x in sub_values),
            db_name,
        )

        return Cache.get_func(key, Server.read, *args, **kwargs)

    @staticmethod
    def get_func(key: str, func: callable, *args, **kwargs) -> None:
        """Return the value for key, or call func, set and return."""

        if key in Cache._items:
            return Cache._items[key]

        fresh = func(*args, **kwargs)
        Cache._items[key] = fresh
        return fresh


def _get_league(league_id: int) -> dict:
    """Return details for the league."""

    for league in Cache.get(Databases.leagues):
        if league["leagueid"] == league_id:
            return league
    return None


def _get_season(league: dict, season_id: int) -> Season:
    """Build a parsed Season object."""

    seasons = Cache.get(Databases.seasons, (league["leagueid"],))
    for season in seasons:
        if season["league_season_id"] == season_id:
            return Season([Race(
                [Laps(lap_data) for lap_data in Cache.get(
                    Databases.laps,
                    (league["leagueid"], season_id, race["subsessionid"]),
                )],
                race,
            ) for race in Cache.get(
                Databases.races,
                (league["leagueid"], season_id),
            )], season, league)
    return None


@app.route("/style.css", methods=["GET"])
def style_get():
    """Return the stylesheet."""

    return render_template("style.css.j2"), 200, {
        "Content-Type": "text/css; charset=utf-8"
    }


@app.route("/", methods=["GET"])
def main_redirect():
    """Top level static HTML return."""

    return app.send_static_file("index.html")


# @app.route("/index.html", methods=["GET"])
# def all_leagues():
#     """Return top level details for all tracked leagues."""
#
#     return app.send_static_file("index.html")
#
#
# @app.route("/race.html")
# def race_html():
#     """Return the static race results HTML."""
#
#     return app.send_static_file("race.html")
#
#
# @app.route("/season.html")
# def season_html():
#     """Return the static season HTML."""
#
#     return app.send_static_file("season.html")
#
#
# @app.route("/seasons.html")
# def seasons_html():
#     """Return the static seasons HTML."""
#
#     return app.send_static_file("seasons.html")
#
#
# @app.route("/driver.html")
# def driver_html():
#     """Return the static driver overview HTML."""
#
#     return app.send_static_file("driver.html")


@app.route(
    "/<int:league_id>/<int:season_id>/<int:race_id>.json",
    methods=["GET"],
)
def race_json(league_id: int, season_id: int, race_id: int):
    """League race JSON results."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    season = _get_season(league, season_id)
    if season is None:
        return abort(404)

    summary = season.race_summary(race_id)
    if summary:
        return jsonify(summary)

    return abort(404)


@app.route("/<int:league_id>/<int:season_id>.json", methods=["GET"])
def season_json(league_id: int, season_id: int):
    """League season JSON results."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    season = _get_season(league, season_id)
    if season is None:
        return abort(404)

    summary = season.summary()
    if summary:
        return jsonify(summary)

    return abort(404)


@app.route("/<int:league_id>.json", methods=["GET"])
def league_json(league_id: int):
    """Return top level league details."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    seasons = Cache.get(Databases.seasons, (league["leagueid"],))

    league_obj = League(league, seasons)
    return jsonify(league_obj.summary)


@app.route("/leagues.json", methods=["GET"])
def all_leagues_json():
    """Return a list of all leagues."""

    return jsonify([League(x, []).info for x in Cache.get(Databases.leagues)])


def merge_league_season_info(results: list, seasons: list) -> None:
    """Merge the league and season info from seasons into each result."""

    def _pull_info(key: str, _id: int) -> dict:
        for season in seasons:
            if season[key]["id"] == _id:
                return season[key]
        return {"id": _id, "name": "N/A"}

    for result in results:
        result["league"] = _pull_info("league", result["league"])
        result["season"] = _pull_info("season", result["season"])


@app.route("/drivers/<int:driver_id>.json", methods=["GET"])
def driver_json(driver_id: int):
    """Return JSON for the driver details page."""

    driver, leagues, results = get_or_generate(driver_id)

    log.info("driver_id: %d results: %r", driver_id, results)

    if results:
        flat_results = sorted(
            [z for x in results.values() for y in x for z in y["results"]],
            key=lambda x: x["id"],
        )
        flat_seasons = sorted(
            [y["season"] for x in results.values() for y in x],
            key=lambda x: x["season"]["id"],
        )

        return jsonify({
            "driver": {
                "name": driver["displayName"],
                "id": driver["custID"],
            },
            "results": flat_results,
            "seasons": flat_seasons,
        })

    return abort(404)


def get_driver_results(driver: dict, leagues: list) -> dict:
    """Return a list of driver results from all leagues."""

    Client.login()
    data = {league["leagueid"]: {
        "members": Server.read_all(
            Databases.members,
            (league["leagueid"],),
        ),
        "seasons": [{
            "season": season,
            "races": [{
                "race": race,
                "laps": [Laps(l) for l in Server.read_all(
                    Databases.laps,
                    (
                        league["leagueid"],
                        season["league_season_id"],
                        race["subsessionid"],
                    ),
                )],
            } for race in Server.read_all(
                Databases.races,
                (league["leagueid"], season["league_season_id"]),
            )],
        } for season in Server.read_all(
            Databases.seasons,
            (league["leagueid"],),
        )],
    } for league in leagues}

    return driver_results({"leagues": leagues, "data": data}, driver)


def get_or_generate(driver_id: int) -> tuple:
    """Return the cached driver stats or generate new ones."""

    cached_results = Server.read(Databases.drivers, (), driver_id)

    driver = {}
    leagues = {}

    for league in Cache.get(Databases.leagues):
        league_driver = Cache.get_one(
            Databases.members,
            (league["leagueid"],),
            driver_id,
        )
        if league_driver:
            leagues[league["leagueid"]] = league
            driver = league_driver

    if leagues:
        if cached_results:
            log.info("returning cached results")
            return driver, leagues, cached_results
        log.info("Getting new results")
        return driver, leagues, get_driver_results(
            driver,
            list(leagues.values()),
        )

    log.warn("driver %d is not a member of any league", driver_id)
    return {}, {}, {}


def main():
    """Command line entry point."""

    args = get_args(__doc__)

    if args["--drop-drivers"]:
        log.warning("Dropping all drivers (expensive!)")
        Server.delete_all(Databases.drivers, ())

    app.run(
        host="0.0.0.0" if bool(int(
            args["--exposed"] or os.getenv("IRACE_EXPOSED") or 0
        )) else None,
        port=int(args["--port"] or os.getenv("IRACE_PORT") or 8000),
        debug=not args["--no-debug"],
    )


if __name__ == "__main__":
    main()
