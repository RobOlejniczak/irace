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
from flask import redirect
from flask import render_template

from .stats import Client
from .parse import Race
from .parse import Laps
from .parse import Season
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
            )], season)
    return None


@app.route("/style.css", methods=["GET"])
def style_get():
    """Return the stylesheet."""

    return render_template("style.css.j2"), 200, {
        "Content-Type": "text/css; charset=utf-8"
    }


@app.route("/", methods=["GET"])
def main_redirect():
    """Top level redirect."""

    return redirect("/index.html")


@app.route("/index.html", methods=["GET"])
def all_leagues():
    """Return top level details for all tracked leagues."""

    return render_template(
        "index.html.j2",
        leagues=Cache.get(Databases.leagues),
    )


@app.route("/<int:league_id>.html", methods=["GET"])
def league_details(league_id: int):
    """Return top level details for a tracked league."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    return render_template(
        "league.html.j2",
        league=league,
        seasons=Cache.get(Databases.seasons, (league["leagueid"],)),
    )


@app.route("/<int:league_id>/<int:season_id>.html", methods=["GET"])
def league_season(league_id: int, season_id: int):
    """Return details for a season in a league."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    season = _get_season(league, season_id)
    if season is None:
        return abort(404)

    return render_template("season.html.j2", league=league, season=season)


@app.route(
    "/<int:league_id>/<int:season_id>/<int:race_id>.html",
    methods=["GET"],
)
def league_race(league_id: int, season_id: int, race_id: int):
    """Return details for a race in a season in a league."""

    league = _get_league(league_id)
    if league is None:
        return abort(404)

    season = _get_season(league, season_id)
    if season is None:
        return abort(404)

    for race in season.races:
        if race.race["subsessionid"] == race_id:
            return render_template(
                "race.html.j2",
                league=league,
                season=season.season,
                race=race,
            )

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

    return driver_results(data, driver)


def get_or_generate(driver_id: int) -> tuple:
    """Return the cached driver stats or generate new ones."""

    cached_results = Server.read(Databases.drivers, (), driver_id)

    driver = {}
    leagues = {}

    for league in Cache.get(Databases.leagues):
        driver = Cache.get_one(
            Databases.members,
            (league["leagueid"],),
            driver_id,
        )
        if driver:
            leagues[league["leagueid"]] = league

    if driver:
        if cached_results:
            log.info("returning cached results")
            return driver, leagues, cached_results
        log.info("Getting new results")
        return driver, leagues, get_driver_results(
            driver,
            list(leagues.values()),
        )

    # driver has not raced in any league
    return {}, {}, {}


@app.route("/drivers/<int:driver_id>.html", methods=["GET"])
def get_driver(driver_id: int):
    """Return details about a specific driver."""

    driver, leagues, results = get_or_generate(driver_id)

    log.info("driver_id: %d results: %r", driver_id, results)

    if results:
        flat_results = sorted(
            [z for x in results.values() for y in x for z in y["results"]],
            key=lambda x: x["race_id"],
        )
        flat_seasons = sorted(
            [y["season"] for x in results.values() for y in x],
            key=lambda x: x["season_id"],
        )
        return render_template(
            "driver.html.j2",
            driver=driver,
            results=flat_results,
            multiclass=any([x.get("class_drivers") for x in flat_results]),
            seasons=flat_seasons,
            leagues=leagues,
        )

    return abort(404)


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
