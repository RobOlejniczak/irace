"""iRace web HTML generator.

This script will recreate all files in the output directory based on the
JSON files located in the input directory.

Usage:
    irace-generate [options]

Options:
    -h --help            show this message
    --version            display version information
    --output=<path>      output path [default: html]
    --input=<path>       input path, from irace-populate [default: results]
    --preserve           preserve contents in output path
"""


import io
import os
import json
import shutil
from glob import glob

import jinja2

from .utils import get_args
from .parse import Laps
from .parse import Race
from .parse import Season
from .parse.utils import time_string
from .parse.utils import time_string_raw


def _has_depth(path: str, depth: int) -> bool:
    """Check if the path has some files in the required depth."""

    return glob(os.path.join(path, *["*"] * depth)) != []


def _depth(path: str) -> int:
    """Returns the depth of path."""

    depth = 0
    path_split = os.path.split(path)
    while path_split[1] != path:
        depth += 1
        path = path_split[0]
        path_split = os.path.split(path)
    return depth


def _make_missing(path: str) -> None:
    """Creates the directory at path if missing."""

    if os.path.exists(path):
        if not os.path.isdir(path):
            raise SystemExit("Output directory exists as a file, aborting.")
    else:
        os.makedirs(path)


def _ensure_paths(args: dict) -> None:
    """Ensure the input and output paths exist and are valid."""

    input_path = args["--input"]
    if not os.path.exists(input_path) or not os.path.isdir(input_path):
        raise SystemExit("Input path does not exist or is a file")

    path_depths = {
        "leagues": (os.path.join(input_path, "leagues"), 1),
        "members": (os.path.join(input_path, "members"), 2),
        "seasons": (os.path.join(input_path, "seasons"), 2),
        "races": (os.path.join(input_path, "races"), 3),
        "laps": (os.path.join(input_path, "laps"), 4),
    }

    all_leagues = []
    for key, depths in path_depths.items():
        if not os.path.isdir(depths[0]) or not _has_depth(*depths):
            raise SystemExit("Missing {} results".format(key))

        if key == "leagues":
            continue

        leagues_found = []
        for league_path in glob(os.path.join(depths[0], "*")):
            try:
                leagues_found.append(int(os.path.split(league_path)[1]))
            except ValueError:
                raise SystemExit("Invalid path found in results, aborting")

        if all_leagues == []:
            all_leagues = leagues_found
        elif all_leagues != leagues_found:
            raise SystemExit("Incomplete result data, aborting")

    output_path = args["--output"]

    if not args["--preserve"] and os.path.exists(output_path):
        shutil.rmtree(output_path)

    _make_missing(output_path)

    args["leagues"] = all_leagues
    args["paths"] = {key: value[0] for key, value in path_depths.items()}
    args["paths"]["output"] = output_path

    args.pop("--input")
    args.pop("--output")


def _read_data(args: dict, data_type: str, *sub: str) -> list:
    """Read all JSON data at path."""

    data = []
    path = os.path.join(args["paths"][data_type], *[str(x) for x in sub], "*")
    for json_path in glob(path):
        try:
            with io.open(json_path, "r", encoding="utf-8") as open_data:
                data.append(json.load(open_data))
        except Exception as err:
            raise SystemExit("Failed to read {}: {!r}".format(data_type, err))
    return data


def _read_json(args: dict) -> dict:
    """Read all JSON data."""

    return {
        "leagues": _read_data(args, "leagues"),
        "data": {league: {
            "members": _read_data(args, "members", league),
            "seasons": [{
                "season": season,
                "races": [{
                    "race": race,
                    "laps": [Laps(lap_data) for lap_data in _read_data(
                        args,
                        "laps",
                        league,
                        season["league_season_id"],
                        race["subsessionid"],
                    )],
                } for race in _read_data(
                    args,
                    "races",
                    league,
                    season["league_season_id"],
                )],
            } for season in _read_data(args, "seasons", league)],
        } for league in args["leagues"]},
    }


def _get_templates() -> dict:
    """Load the jinja2 templates."""

    env = jinja2.Environment(
        loader=jinja2.PackageLoader("irace", "templates"),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )

    # jinja2 helpers
    env.globals["time_string"] = time_string
    env.globals["time_string_raw"] = time_string_raw

    return {
        os.path.splitext(t)[0]: env.get_template(t)
        for t in env.list_templates()
    }


def _write_file(content: str, path: str) -> None:
    """Write the content to the file at path."""

    with io.open(path, "w", encoding="utf-8") as open_file:
        open_file.write(content)


def _write_members(templates: dict, base_path: str, members: list,
                   league_info: dict) -> None:
    """Write templated member data to disk."""

    _make_missing(os.path.join(base_path, "members"))
    for member in members:
        _write_file(
            templates["member.html"].render(
                member=member,
                league=league_info,
            ),
            os.path.join(
                base_path,
                "members",
                "{}.html".format(member["custID"]),
            ),
        )

    _write_file(
        templates["members.html"].render(
            members=members,
            league=league_info,
        ),
        os.path.join(base_path, "members.html"),
    )


def _write_seasons(templates: dict, base_path: str, seasons: list,
                   league_info: dict) -> None:
    """Write templated season data to disk."""

    _make_missing(os.path.join(base_path, "seasons"))
    for season in seasons:
        season_races = []
        for race in season["races"]:
            _make_missing(os.path.join(
                base_path,
                "seasons",
                str(season["season"]["league_season_id"]),
                str(race["race"]["subsessionid"]),
            ))
            race_obj = Race(race["laps"], race["race"])
            season_races.append(race_obj)
            _write_file(
                templates["race.html"].render(
                    season=season["season"],
                    race=race_obj,
                    league=league_info,
                ),
                os.path.join(
                    base_path,
                    "seasons",
                    str(season["season"]["league_season_id"]),
                    "{}.html".format(race["race"]["subsessionid"]),
                )
            )

        _write_file(
            templates["season.html"].render(
                season=Season(season_races, season["season"]),
                league=league_info,
                races=[x["race"] for x in season["races"]],
            ),
            os.path.join(
                base_path,
                "seasons",
                "{}.html".format(season["season"]["league_season_id"]),
            )
        )


def _league_info(leagues: list, league: int) -> dict:
    """Return the basic information dictionary for this league."""

    for info in leagues:
        if info["leagueid"] == league:
            return info
    return {}


def _write_templates(args: dict, data: dict) -> None:
    """Write the data-formatted templates to the output path."""

    templates = _get_templates()
    _write_file(
        templates["style.css"].render(),
        os.path.join(args["paths"]["output"], "style.css"),
    )
    _write_file(
        templates["index.html"].render(leagues=data["leagues"]),
        os.path.join(args["paths"]["output"], "index.html"),
    )

    for league, _data in data["data"].items():
        base_path = os.path.join(args["paths"]["output"], str(league))
        league_info = _league_info(data["leagues"], league)
        _write_file(
            templates["league.html"].render(
                league=league_info,
                seasons=[x["season"] for x in _data["seasons"]],
            ),
            os.path.join(
                args["paths"]["output"],
                "{}.html".format(league_info["leagueid"]),
            ),
        )
        _write_members(templates, base_path, _data["members"], league_info)
        _write_seasons(templates, base_path, _data["seasons"], league_info)


def main():
    """Command line entry point."""

    args = get_args(__doc__)
    _ensure_paths(args)
    _write_templates(args, _read_json(args))


if __name__ == "__main__":
    main()
