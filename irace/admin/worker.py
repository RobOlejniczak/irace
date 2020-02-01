"""iRace admin background worker."""


import gc
import os
import subprocess
from datetime import datetime
from traceback import format_exception
from collections import defaultdict

import gevent

from ..parse import Laps
from ..stats import Client
from ..storage import Server
from ..storage import Databases
from ..generate import write_templates
from ..stats.logger import log


ZERO_TIME = datetime.utcfromtimestamp(0).isoformat()


def utcnow(timestamp: int = -1) -> str:
    """Return the current time as a string."""

    if timestamp < 0:
        dt_obj = datetime.utcnow()
    else:
        dt_obj = datetime.utcfromtimestamp(timestamp)

    return dt_obj.replace(microsecond=0).isoformat()


def _next_update(events: dict) -> str:
    """Return a timestamp of the next update for this list of events."""

    timestamp = None
    currently = int(datetime.utcnow().timestamp())

    if events and events["rowcount"] >= 1:
        for event in events["rows"]:
            race_end = (event["launchat"] / 1000) + (
                (event["timelimit"] + 10) * 60
            )
            if race_end > currently:
                if timestamp is None or race_end < timestamp:
                    timestamp = race_end

    if timestamp is None:
        return ZERO_TIME

    return utcnow(timestamp)


class Worker:
    """Manages child threads per action/request."""

    def __init__(self, socketio):
        self._socketio = socketio

        self._state = defaultdict(dict)

        self._output = {
            "local": os.getenv("IRACE_HTML", "html"),
            "remote": os.getenv("IRACE_HOST"),
            "remote_html": os.getenv("IRACE_HOST_HTML"),
        }

        self.stats = {
            "leagues": [],
            "last_sync": ZERO_TIME,
        }

        self._read_stats()

        self.watcher = gevent.spawn(self.watch)
        self._children = []

    @property
    def alive(self) -> bool:
        """Return a boolean of our child thread state."""

        self.watcher.join(0.0001)
        if self.watcher.dead:
            try:
                log.warning(
                    "worker watcher died: %s",
                    "".join(format_exception(*self.watcher.exc_info)).strip(),
                )
            except Exception:
                log.warning("worker watcher died, restarting")
            self.watcher = gevent.spawn(self.watch)
        elif self.watcher.successful():
            log.warning("restarting worker watcher...")
            self.watcher = gevent.spawn(self.watch)

        return self.watcher.started

    @property
    def state(self) -> list:
        """Return a snapshot of the current state."""

        return [
            {"l": k, "t": t}
            for k, a in self._state.items()
            for t, v in a.items()
            if v
        ]

    def _set_state(self, task: str, league: str = "System",
                   value: bool = True) -> None:
        """Set the internal state variable."""

        key = str(league)
        if self._state[key].get(task) != value:
            self._state[key][task] = value
            self._socketio.emit("state", True)

    def _get_state(self, task: str, league: str = "System") -> bool:
        """Return the current value of the state variable."""

        return self._state.get(str(league), {}).get(task, False)

    @property
    def num_requests(self) -> int:
        """Return the number of requests our client has made."""

        return Client.num_requests

    def known_league_id(self, league_id: int) -> bool:
        """Check if the leauge_id is known."""

        for league in self.stats["leagues"]:
            if league["league_id"] == league_id:
                return True
        return False

    def watch(self) -> None:
        """Forever watch our child threads."""

        while True:
            prune = []
            for child in gevent.iwait(self._children, 1):
                if child.successful():
                    prune.append(child)
                elif child.dead:
                    try:
                        log.warning(
                            "worker child died: %s",
                            "".join(format_exception(*child.exc_info)).strip(),
                        )
                    except Exception:
                        child.join(0.0001)
                        log.warning("worker child died :(")
                    prune.append(child)

            for to_prune in prune:
                self._children.remove(to_prune)

            if self._get_state("stats_write_pending"):
                self._write_stats()
                self._set_state("stats_write_pending", value=False)

            self._do_timed_updates()
            self._regenerate_pending()
            self._push_html()

            gc.collect()
            gevent.sleep(10)

    def _spawn(self, func, *args, **kwargs) -> None:
        """Add a child greenlet."""

        log.info(
            "SPAWN %s(*%r, **%r)",
            func.__name__,
            args,
            kwargs,
        )
        self._children.append(gevent.spawn(func, *args, **kwargs))

    def _write_stats(self) -> None:
        """Write our stats out to the admin JSON."""

        self._update_league_stats()
        Server.write(Databases.admin, (), "stats", self.stats)

    def _read_stats(self) -> None:
        """Read our stats from the admin JSON."""

        leagues = [{
            "league_id": league["leagueid"],
            "league_name": league["leaguename"],
            "members_count": Server.count(
                Databases.members,
                (league["leagueid"],),
            ),
            "members_last_updated": ZERO_TIME,
            "seasons": [{
                "season_id": season["league_season_id"],
                "season_name": season["league_season_name"],
                "next_update_time": _next_update({
                    "rowcount": 1 if season["nextrace"] else 0,
                    "rows": [season["nextrace"]],
                }),
                "last_update_time": ZERO_TIME,
                "last_update_reason": "Unknown",
            } for season in Server.read_all(
                Databases.seasons,
                (league["leagueid"],),
            )],
            "seasons_last_update_reason": "Unknown",
            "seasons_last_update": ZERO_TIME,
            "seasons_next_update": ZERO_TIME,
        } for league in Server.read_all(Databases.leagues)]

        if not Server.exists(Databases.admin, (), "stats"):
            self.stats["leagues"] = leagues
            self._write_stats()
            return

        stored_stats = Server.read(Databases.admin, (), "stats")

        for league in leagues:
            found = False
            for known in stored_stats["leagues"]:
                if known["league_id"] == league["league_id"]:
                    found = True
                    break
            if not found:
                stored_stats["leagues"].append(league)

        for key, value in stored_stats.items():
            if self.stats[key] != value:
                self.stats[key] = value
                self._set_state("stats_write_pending")

    def _update_stat(self, key: str, value: object) -> None:
        """Update the stat value."""

        if key not in self.stats:
            raise KeyError("Unknown stat: {}".format(key))
        self.stats[key] = value
        self._set_state("stats_write_pending")

    def _update_stats(self, league_id: int, season_id: int = -1, **kwargs):
        """Update attributes of the league in stats."""

        if season_id < 0:
            for league in self.stats["leagues"]:
                if league["league_id"] == league_id:
                    league.update(kwargs)
                    self._set_state("stats_write_pending")
                    return
            kwargs["league_id"] = league_id
            self.stats["leagues"].append(kwargs)
            self._set_state("stats_write_pending")
            return

        for league in self.stats["leagues"]:
            if league["league_id"] == league_id:
                for season in league["seasons"]:
                    if season["season_id"] == season_id:
                        season.update(kwargs)
                        self._set_state("stats_write_pending")
                        return
                kwargs["season_id"] = season_id
                league["seasons"].append(kwargs)
                self._set_state("stats_write_pending")
                return
        log.warning("unable to record stats of unknown season!")

    def _update_league_stats(self) -> None:
        """For each league stats tracked, sum the top level attributes."""

        for league in self.stats["leagues"]:
            last_update = None
            last_update_reason = None
            next_update = None
            for season in league["seasons"]:
                this_last_time = datetime.fromisoformat(
                    season["last_update_time"]
                )

                if last_update is None or this_last_time > last_update:
                    last_update = this_last_time
                    last_update_reason = season["last_update_reason"]

                if season["next_update_time"] == ZERO_TIME:
                    continue

                this_next_time = datetime.fromisoformat(
                    season["next_update_time"]
                )

                if this_next_time.timestamp() > 0 and (
                        next_update is None or this_next_time < next_update):
                    next_update = this_next_time

            league["seasons_last_update_reason"] = last_update_reason
            league["seasons_last_update"] = last_update.isoformat()
            if next_update is None:
                league["seasons_next_update"] = ZERO_TIME
            else:
                league["seasons_next_update"] = next_update.isoformat()

    def add_league(self, league_id: int) -> None:
        """Non-blocking call to signal to collect all info for a league."""

        if self._get_state("add_league", league_id):
            return

        self._set_state("add_league", league_id)
        self._spawn(self._add_league, league_id)

    def _add_league(self, league_id: int) -> None:
        """Blocking call to add a league to tracking."""

        league = Client.league_info(league_id)
        if league:
            Server.write(Databases.leagues, (), league_id, league)
            self._read_stats()
            self.update_members(league_id)
            self.update_seasons(league_id)
        self._set_state("add_league", league_id, value=False)

    def delete_league(self, league_id: int) -> None:
        """Non-blocking call to signal to delete a league."""

        if self._get_state("delete_league", league_id):
            return

        self._set_state("delete_league", league_id)
        self._spawn(self._delete_league, league_id)

    def _delete_league(self, league_id: int) -> None:
        """Blocking call to delete a league from tracking."""

        Server.delete_all(Databases.calendars, (league_id,))
        Server.delete_all(Databases.laps, (league_id,))
        Server.delete(Databases.leagues, (), league_id)
        Server.delete_all(Databases.members, (league_id,))
        Server.delete_all(Databases.races, (league_id,))
        Server.delete_all(Databases.seasons, (league_id,))

        self.stats["leagues"] = list(filter(
            lambda x: int(x["league_id"]) != int(league_id),
            self.stats["leagues"],
        ))

        self._set_state("stats_write_pending")
        self._set_state("pending_regeneration", league_id)
        self._set_state("delete_league", league_id, value=False)

    def update_members(self, league_id: int) -> None:
        """Non-blocking call to signal for an update to members in a league."""

        if self._get_state("members", league_id):
            return

        self._set_state("members", league_id)
        self._spawn(self._update_members, league_id)

    def _update_members(self, league_id: int) -> None:
        """Blocking call to update the member list for a league."""

        members = 0
        for member in Client.league_members(league_id):
            if member:
                self._set_state("pending_regeneration", league_id)
                Server.write(
                    Databases.members,
                    (league_id,),
                    member["custID"],
                    member,
                )
                members += 1

        self._update_stats(
            league_id,
            member_count=members,
            members_last_updated=utcnow(),
        )
        self._set_state("members", league_id, value=False)

    def update_seasons(self, league_id: int) -> None:
        """Non-blocking call to signal for an update to seasons in a league."""

        if self._get_state("seasons", league_id):
            return

        self._set_state("seasons", league_id)
        self._spawn(self._update_seasons, league_id)

    def _update_seasons(self, league_id: int) -> None:
        """Blocking call to start updates for all seasons in a league."""

        for season in Client.league_seasons(league_id=league_id):
            if season:
                self._set_state("pending_regeneration", league_id)
                Server.write(
                    Databases.seasons,
                    (league_id,),
                    season["league_season_id"],
                    season,
                )
                self.update_season(league_id, season["league_season_id"], True)

        self._set_state("seasons", league_id, value=False)

    def update_season(self, league_id: int, season_id: int,
                      _bypass: bool = False, _reason: str = "Manual") -> None:
        """Non-blocking call to update any missing races in a season."""

        if self._get_state("seasons", league_id) and not _bypass:
            return  # all seasons has been requested in another thread

        key = "season_{}".format(season_id)
        if self._get_state(key, league_id):
            return  # this season has been requested in another thread

        self._set_state(key, league_id)
        self._spawn(self._update_season, league_id, season_id, _reason)

    def _update_season(self, league_id: int, season_id: int,
                       _reason: str) -> None:
        """Blocking call to update unknown races in a season."""

        events = Client.league_season_calendar(league_id, season_id)
        # XXX not currently writing html for calendars, otherwise uncomment:
        # self._set_state("pending_regeneration", league_id)
        Server.write(Databases.calendars, (league_id,), season_id, events)
        currently = int(datetime.utcnow().timestamp())

        future_events = {"rowcount": 0, "rows": []}

        if events and events["rowcount"] >= 1:
            for event in events["rows"]:
                _id = event["subsessionid"]
                sub_values = (league_id, season_id)

                if Server.exists(Databases.races, sub_values, _id):
                    continue

                race_end = (event["launchat"] / 1000) + (
                    (event["timelimit"] + 5) * 60
                )
                if race_end < currently:
                    race = Client.session_results(_id)
                    if race:
                        self._set_state("pending_regeneration", league_id)
                        Server.write(Databases.races, sub_values, _id, race)
                        self._fetch_laps(league_id, season_id, race)
                else:
                    future_events["rowcount"] += 1
                    future_events["rows"].append(event)

        self._set_state("season_{}".format(season_id), league_id, value=False)
        self._update_stats(
            league_id,
            season_id,
            next_update_time=_next_update(future_events),
            last_update_time=utcnow(),
            last_update_reason=_reason,
        )

    def _fetch_laps(self, league_id: int, season_id: int, race: dict) -> None:
        """Fetch laps for all drivers in the session."""

        _id = race["subsessionid"]
        found = []
        for driver in race["rows"]:
            if driver["groupid"] in found:
                continue
            found.append(driver["groupid"])

            laps = Client.session_laps(_id, driver["groupid"])
            if laps:
                self._set_state("pending_regeneration", league_id)
                Server.write(
                    Databases.laps,
                    (league_id, season_id, _id),
                    driver["custid"],
                    laps,
                )

    def _do_timed_updates(self) -> None:
        """Check all seasons for completed races."""

        now = datetime.utcnow()

        for league in self.stats["leagues"]:
            for season in league["seasons"]:
                if season["next_update_time"] == ZERO_TIME:
                    continue

                if datetime.fromisoformat(season["next_update_time"]) < now:
                    log.info(
                        "Auto-updating league %d season %d",
                        league["league_id"],
                        season["season_id"],
                    )
                    self.update_season(
                        league["league_id"],
                        season["season_id"],
                        _reason="Auto",
                    )

    def regenerate_all_html(self) -> None:
        """Put all leagues into a pending html regeneration state."""

        if self._get_state("rsync_pending") or self._get_state("rsync"):
            return

        for league in self.stats["leagues"]:
            league_id = league["league_id"]
            if not self._get_state("pending_regeneration", league_id) and not \
                    self._get_state("regenerate_html", league_id):
                self._set_state("pending_regeneration", league_id)

    def _regenerate_pending(self) -> None:
        """Regenerate any leagues in a pending state and no other activity."""

        for league_id, activity in self._state.items():
            if activity.get("pending_regeneration") and not any(
                    v for k, v in activity.items()
                    if k != "pending_regeneration"):

                self._set_state("regenerate_html", league_id)
                self._set_state("pending_regeneration", league_id, value=False)
                self._spawn(self._regenerate_html, league_id)

    def _regenerate_html(self, league_id: str) -> None:
        """Blocking call to regenerate all HTML relative to the league."""

        write_templates(
            {
                "--output": self._output["local"],
                "--write-json": True,
                "--write-html": False,
            },
            {
                "leagues": Server.read_all(Databases.leagues),
                "data": {
                    int(league_id): {
                        "members": Server.read_all(
                            Databases.members,
                            (league_id,),
                        ),
                        "seasons": [{
                            "season": season,
                            "races": [{
                                "race": race,
                                "laps": [Laps(l) for l in Server.read_all(
                                    Databases.laps,
                                    (
                                        league_id,
                                        season["league_season_id"],
                                        race["subsessionid"],
                                    ),
                                )],
                            } for race in Server.read_all(
                                Databases.races,
                                (league_id, season["league_season_id"]),
                            )],
                        } for season in Server.read_all(
                            Databases.seasons,
                            (league_id,),
                        )],
                    },
                },
            },
        )
        self._set_state("regenerate_html", league_id, value=False)
        self._set_state("rsync_pending")

    def _push_html(self) -> None:
        """Determine if we should push generated html to the webhost."""

        if self._get_state("rsync") or \
                not self._get_state("rsync_pending") or \
                not self._output["remote"] or \
                not self._output["remote_html"]:
            return

        if any([v for league, activity in self._state.items()
                if league != "System" for k, v in activity.items()]):
            log.info("Delaying push due to ongoing activity")
            return

        self._set_state("rsync")
        self._set_state("rsync_pending", value=False)
        self._spawn(self._rsync_html)

    def _rsync_html(self) -> None:
        """Use rsync to sync the generated html with the webhost."""

        subprocess.run(
            "rsync -az {} \"{}:{}\" --delete".format(
                self._output["local"],
                self._output["remote"],
                self._output["remote_html"],
            ),
            shell=True,
            check=True,
        )

        self._set_state("rsync", value=False)
        now = utcnow()
        self._update_stat("last_sync", now)
        self._socketio.emit("sync", now)
