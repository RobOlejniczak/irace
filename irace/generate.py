"""iRace web JSON generator.

This script will recreate all files in the output directory based on the
JSON files located in the input directory.

Alternatively if you have couchDB environment variables setup this
will prefer to fetch results from there.

Usage:
    irace-generate [options]

Options:
    -h --help            show this message
    --version            display version information
    --output=<path>      output path [default: dist]
    --input=<path>       input path, from irace-populate [default: results]
"""


import io
import os
import json
import shutil
from concurrent.futures import ThreadPoolExecutor

from .stats import Client
from .utils import get_args
from .parse import Laps
from .parse import Race
from .parse import Season
from .parse import League
from .storage import Server
from .storage import Databases
from .stats.logger import log


class Stats:
    """Static stats object to track processing."""

    def __init__(self, amount: int):
        self._queued = amount
        self._processed = 0
        self.log()

    def log(self, level: int = 20) -> None:
        """Log our current state."""

        if self._queued and not self._processed:
            log.log(level, "{:,d} [queued]".format(self._queued))
        elif self._processed < self._queued:
            log.log(level, "{:,d}/{:,d} [working]".format(
                self._processed,
                self._queued,
            ))
        elif self._queued:
            log.log(level, "{:,d} [finished]".format(self._queued))
        else:
            log.log(level, "[ready]")

    def inc(self) -> None:
        """Increment the processed count."""

        self._processed += 1


def _make_missing(path: str) -> None:
    """Creates the directory at path if missing."""

    if os.path.exists(path):
        if not os.path.isdir(path):
            raise SystemExit("Output directory exists as a file, aborting.")
    else:
        os.makedirs(path)


def _read_json() -> dict:
    """Read all JSON data."""

    leagues = Server.read_all(Databases.leagues)

    return {
        "leagues": leagues,
        "data": {league["leagueid"]: {
            "members": Server.read_all(
                Databases.members,
                (league["leagueid"],),
            ),
            "seasons": [{
                "season": season,
                "races": [{
                    "race": race,
                    "laps": [Laps(lap_data) for lap_data in Server.read_all(
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
        } for league in leagues},
    }


def _write_json(content: object, path: str) -> None:
    """JSON dump the content and write it to path."""

    if not content:
        return None

    as_json = json.dumps(
        content,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    if os.path.isfile(path):
        if as_json == _read_file(path):
            log.log(5, "Identical content, ignoring: %s", path)
            return None

    return _write_file(as_json, path)


def _write_file(content: str, path: str) -> None:
    """Write the content to the file at path."""

    with io.open(path, "w", encoding="utf-8") as open_file:
        open_file.write(content)

    log.log(5, "Wrote: %s", path)


def _read_file(path: str) -> str:
    """Read the content of file at path."""

    with io.open(path, "r", encoding="utf-8") as open_file:
        return open_file.read()


def _driver_league_results(data: dict, driver: dict) -> dict:
    """Return all results for this driver from all leagues in data."""

    results = {}

    for league_id, _data in data["data"].items():
        seasons = []
        league_info = _league_info(data["leagues"], league_id)

        for season in _data["seasons"]:
            this_season = {
                "results": [],
                "_races": [],
            }

            for race in season["races"]:
                race = Race(**race)
                this_season["_races"].append(race)

                result = race.driver_summary(driver["custID"], lap_info=False)

                if result and race.winner_id:
                    this_season["results"].append(result)

            if this_season["results"]:
                this_season["season"] = Season(
                    this_season.pop("_races"),
                    season["season"],
                    league_info,
                ).driver_summary(driver["custID"])
                seasons.append(this_season)

        if seasons:
            results[str(league_id)] = seasons

    return results


def driver_results(data: dict, driver: dict) -> dict:
    """Pull all driver results from data and merge with cached."""

    results = _driver_league_results(data, driver)
    from_cache = Server.read(Databases.drivers, (), driver["custID"]) or {}
    from_cache.update(results)
    Server.write(Databases.drivers, (), driver["custID"], from_cache)
    return from_cache


def _write_driver(args: dict, data: dict, driver: dict):
    """Write templated driver data to disk."""

    res = driver_results(data, driver)
    if res:
        _write_json(
            {
                "driver": {
                    "name": driver["displayName"],
                    "id": driver["custID"],
                },
                "results": sorted(
                    [z for x in res.values() for y in x for z in y["results"]],
                    key=lambda x: x["id"],
                ),
                "seasons": sorted(
                    [y["season"] for x in res.values() for y in x],
                    key=lambda x: x["season"]["id"],
                ),
            },
            os.path.join(
                args["--output"],
                "drivers",
                "{}.json".format(driver["custID"]),
            ),
        )


def _write_drivers(args: dict, data: dict, drivers: list) -> None:
    """Write all driver data to disk."""

    _make_missing(os.path.join(args["--output"], "drivers"))

    # ensure the cache is populated
    Client.login()

    stats = Stats(len(drivers))

    log_gap = int(len(drivers) / 20)  # every 5% of drivers complete
    processed = 0

    def _write_driver_async(driver):
        _write_driver(args, data, driver)

    with ThreadPoolExecutor(max_workers=20) as executor:
        for _ in executor.map(_write_driver_async, drivers, timeout=30):
            stats.inc()
            processed += 1
            if processed % log_gap == 0:
                stats.log()

    stats.log()


def _write_seasons(args: dict, seasons: list, league: dict) -> None:
    """Write templated season data to disk."""

    for season in seasons:
        season_races = []
        for race in season["races"]:
            _make_missing(os.path.join(
                args["--output"],
                str(league["leagueid"]),
                str(season["season"]["league_season_id"]),
            ))
            race_obj = Race(race["laps"], race["race"])

            season_races.append(race_obj)

            # write out per race JSON through the Season object
            _write_json(
                Season([race_obj], season["season"], league).race_summary(
                    race_obj.subsessionid
                ),
                os.path.join(
                    args["--output"],
                    str(league["leagueid"]),
                    str(season["season"]["league_season_id"]),
                    "{}.json".format(race["race"]["subsessionid"]),
                ),
            )

        # write out the full season with all race objects
        _write_json(
            Season(season_races, season["season"], league).summary(),
            os.path.join(
                args["--output"],
                str(league["leagueid"]),
                "{}.json".format(season["season"]["league_season_id"]),
            ),
        )


def _league_info(leagues: list, league: int) -> dict:
    """Return the basic information dictionary for this league."""

    for info in leagues:
        if info["leagueid"] == league:
            return info
    return {}


def _write_top_level(args: dict, data: dict) -> None:
    """Write top level files."""

    _make_missing(os.path.join(args["--output"]))

    _write_json(
        [League(x, []).info for x in data["leagues"]],
        os.path.join(args["--output"], "leagues.json"),
    )


def write_templates(args: dict, data: dict) -> None:
    """Write the data-formatted templates to the output path."""

    _write_top_level(args, data)

    all_drivers = []

    for league, _data in data["data"].items():
        league_info = _league_info(data["leagues"], league)
        if league_info:
            _write_json(
                League(
                    league_info,
                    [x["season"] for x in _data["seasons"]]
                ).summary,
                os.path.join(
                    args["--output"],
                    "{}.json".format(league_info["leagueid"]),
                ),
            )

            for member in _data["members"]:
                found = False
                for known in all_drivers:
                    if known["custID"] == member["custID"]:
                        found = True
                        break
                if not found:
                    all_drivers.append(member)

            _write_seasons(
                args,
                _data["seasons"],
                league_info,
            )
        else:
            try:
                os.remove(os.path.join(
                    args["--output"],
                    "{}.json".format(league),
                ))
            except Exception as error:
                log.warning("Failed to remove league json: %r", error)

            try:
                shutil.rmtree(os.path.join(args["--output"], str(league)))
            except Exception as error:
                log.warning("Failed to remove league files: %r", error)

    _write_drivers(args, data, all_drivers)


def main():
    """Command line entry point."""

    args = get_args(__doc__)

    # in case we need to fallback to file storage
    os.environ["IRACE_RESULTS"] = args["--input"]

    write_templates(args, _read_json())


if __name__ == "__main__":
    main()
