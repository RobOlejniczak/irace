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
    --update-db          update the processed content in couchDB
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

    def __init__(self, amount: int = 1) -> None:
        self._queued = amount
        self._processed = 0
        self._to_file = 0
        self._to_db = 0
        self._nulls = 0
        self._duplicates_to_file = 0
        self._duplicates_to_db = 0
        self.log()

    def log(self, level: int = 20) -> None:
        """Log our current state."""

        if self._queued and not self._processed:
            state = "{:,d} [queued]".format(self._queued)
        elif self._processed < self._queued:
            state = "{:,d}/{:,d} [working]".format(
                self._processed,
                self._queued
            )
        elif self._queued:
            state = "{:,d} [finished]".format(self._queued)
        else:
            state = "[ready]"

        s_stats = [x for x in (
            state,
            "[{} files]".format(self._to_file) if self._to_file else "",
            "[{} duplicate files]".format(
                self._duplicates_to_file
            ) if self._duplicates_to_file else "",
            "[{} records]".format(self._to_db) if self._to_db else "",
            "[{} duplicate records]".format(
                self._duplicates_to_db
            ) if self._duplicates_to_db else "",
            "[{} null results]".format(self._nulls) if self._nulls else "",
        ) if x]

        log.log(level, ("%s " * (len(s_stats) - 1)) + "%s", *s_stats)

    def consume(self, other) -> None:
        """Consume stats from another instance."""

        self._processed += other._processed
        self._to_file += other._to_file
        self._to_db += other._to_db
        self._nulls += other._nulls
        self._duplicates_to_file += other._duplicates_to_file
        self._duplicates_to_db += other._duplicates_to_db
        self.log()

    def inc(self, amount: int = 1) -> None:
        """Increment the processed count."""

        self._processed += amount
        self.log()

    def inc_written_to_file(self, amount: int = 1) -> None:
        """Increment the written to file count."""

        self._to_file += amount

    def inc_written_to_db(self, amount: int = 1) -> None:
        """Increment the written to db count."""

        self._to_db += amount

    def inc_nulls(self, amount: int = 1, _processed: bool = True) -> None:
        """Increment the amount of null results processed."""

        self._nulls += amount
        if _processed:
            self.inc(amount)

    def inc_duplicates_to_file(self, amount: int = 1) -> None:
        """Increment the amount of duplicate results processed (to file)."""

        self._duplicates_to_file += amount

    def inc_duplicates_to_db(self, amount: int = 1) -> None:
        """Increment the amount of duplicate results processed (to db)."""

        self._duplicates_to_db += amount

    def add(self, amount: int = 1) -> None:
        """Increase the amount queued."""

        self._queued += amount
        self.log()


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


def _write_content(args: dict, database: Databases, sub_values: tuple,
                   _id: str, content: object, *prefix,
                   stats: Stats = None) -> None:
    """Write the processed content to the database and/or file."""

    if not database.name.startswith("p_"):
        raise ValueError("Refusing to write non-processed content: {}".format(
            database.name
        ))

    if stats is None:
        stats = args["stats"]

    if content:
        _id = "{}.json".format(_id)

        if args.get("--update-db"):
            if _write_to_db(database, sub_values, _id, content):
                stats.inc_written_to_db()
            else:
                stats.inc_duplicates_to_db()

        if args.get("--output"):
            path = os.path.join(
                args["--output"],
                *prefix,
                *[str(x) for x in sub_values],
                _id,
            )
            if _write_json(content, path):
                stats.inc_written_to_file()
            else:
                stats.inc_duplicates_to_file()
    else:
        stats.inc_nulls(_processed=False)

    stats.inc()


def _write_to_db(database: Databases, sub_values: tuple,
                 _id: str, content: object) -> bool:
    """Write the content to couchDB."""

    if not Server.couch:
        Server.connect()

    if Server.couch:
        if Server.write(database, sub_values, _id, content) >= 0:
            log.log(
                5,
                "Updated content in db %s %r %s",
                database.name,
                sub_values,
                _id,
            )
            return True

        log.log(
            5,
            "Indentical content in db %s %r %s",
            database.name,
            sub_values,
            _id,
        )
        return False

    # might as well throw an error, restart the container
    raise RuntimeError("Cannot update content in couchDB, not connected!")


def _write_json(content: object, path: str) -> bool:
    """JSON dump the content and write it to path."""

    as_json = json.dumps(
        content,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    if os.path.isfile(path):
        if as_json == _read_file(path):
            log.log(5, "Identical content, ignoring: %s", path)
            return False

    _make_missing(os.path.dirname(path))

    with io.open(path, "w", encoding="utf-8") as open_file:
        open_file.write(as_json)

    log.log(5, "Wrote: %s", path)
    return True


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


def _write_driver(args: dict, data: dict, driver: dict, stats: Stats) -> None:
    """Write templated driver data to disk."""

    res = driver_results(data, driver)
    if res:
        _write_content(
            args,
            Databases.p_drivers,
            (),
            driver["custID"],
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
            "drivers",
            stats=stats,
        )
    else:
        stats.inc_nulls()


def _write_drivers(args: dict, data: dict, drivers: list) -> None:
    """Write all driver data to disk."""

    # ensure the cache is populated
    Client.login()

    # per thread stats, update global once we're done
    stats = Stats(len(drivers))

    def _write_driver_async(driver):
        _write_driver(args, data, driver, stats)

    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(_write_driver_async, drivers, timeout=30)

    args["stats"].consume(stats)


def _write_seasons(args: dict, seasons: list, league: dict) -> None:
    """Write templated season data to disk."""

    for season in seasons:
        season_races = []
        args["stats"].add(len(season["races"]))
        for race in season["races"]:
            race_obj = Race(race["laps"], race["race"])
            season_races.append(race_obj)
            _write_content(
                args,
                Databases.p_races,
                (league["leagueid"], season["season"]["league_season_id"]),
                race["race"]["subsessionid"],
                Season([race_obj], season["season"], league).race_summary(
                    race_obj.subsessionid
                ),
            )

        _write_content(
            args,
            Databases.p_seasons,
            (league["leagueid"],),
            season["season"]["league_season_id"],
            Season(season_races, season["season"], league).summary(),
        )


def _league_info(leagues: list, league: int) -> dict:
    """Return the basic information dictionary for this league."""

    for info in leagues:
        if info["leagueid"] == league:
            return info
    return {}


def _write_top_level(args: dict, data: dict) -> None:
    """Write top level files."""

    _write_content(
        args,
        Databases.p_leagues,
        (),
        "leagues",
        [League(x, []).info for x in data["leagues"]],
    )


def write_templates(args: dict, data: dict) -> None:
    """Write the data-formatted templates to the output path."""

    stats = Stats()
    args["stats"] = stats
    _write_top_level(args, data)

    all_drivers = []

    for league, _data in data["data"].items():
        stats.add()
        league_info = _league_info(data["leagues"], league)

        if league_info:
            stats.add(len(_data["seasons"]))
            log.info(
                "Generating %d seasons for %s",
                len(_data["seasons"]),
                league_info["leaguename"],
            )
            _write_content(
                args,
                Databases.p_leagues,
                (),
                league_info["leagueid"],
                League(
                    league_info,
                    [x["season"] for x in _data["seasons"]]
                ).summary,
            )

            for member in _data["members"]:
                found = False
                for known in all_drivers:
                    if known["custID"] == member["custID"]:
                        found = True
                        break
                if not found:
                    stats.add()
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
