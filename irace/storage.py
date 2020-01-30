"""iRace JSON storage utility.

Usage:
    irace-storage [options]

Options:
    -h --help            show this message
    --version            display version information
    --to-couch           migrate JSON files to couchDB
    --to-files           migrate couchDB to JSON files
    --files=<PATH>       path to JSON files storage location [default: results]
    --drop-db            use to drop all couchDB data prior to import
    --overwrite          use to overwrite files when exporting from couchDB

Note the following environment variables are used to connect to couchDB:

    COUCHDB_HOST         name or IP of couchDB host [default: localhost]
    COUCHDB_PORT         port couchDB is exposed on [default: 5984]
    COUCHDB_SSL          boolean if couchDB is exposed with ssl [default: 0]
    COUCHDB_USER         username to write results with [default: ""]
    COUCHDB_PASSWORD     password to write results with [default: ""]
"""


import io
import os
import json
from enum import Enum
from glob import glob
from collections import namedtuple

import couchdb

from .utils import get_args
from .utils import read_json
from .stats.logger import log


Database = namedtuple("Database", ("name", "sub_keys", "final_key"))


class Databases(Enum):
    """All stored databases of JSON results."""

    calendars = Database("calendars", ("league",), "season")
    laps = Database("laps", ("league", "season", "race"), "driver")
    leagues = Database("leagues", (), "league")
    members = Database("members", ("league",), "member")
    races = Database("races", ("league", "season"), "race")
    seasons = Database("seasons", ("league",), "season")
    admin = Database("admin", (), "system")
    drivers = Database("drivers", (), "driver")


def get_server() -> couchdb.Server:
    """Return the couchDB server connection."""

    host = os.getenv("COUCHDB_HOST") or "127.0.0.1"
    port = int(os.getenv("COUCHDB_PORT") or 5984)
    user = os.getenv("COUCHDB_USER")

    if user:
        con_str = "http{}://{}:{}@{}:{}/".format(
            "s" * int(bool(int(os.getenv("COUCHDB_SSL") or 0))),
            user,
            os.getenv("COUCHDB_PASSWORD"),
            host,
            port,
        )
    else:
        con_str = "http://{}:{}/".format(host, port)

    return couchdb.Server(con_str)


def _db(database: Database) -> Database:
    """Wrapper to allow enum members to be passed as their values."""

    if isinstance(database, Database):
        return database
    if isinstance(database, Databases):
        return database.value
    raise TypeError(
        "database argument must be a Database namedtuple or a "
        "member of the Databases enum"
    )


class IServer:
    """Interface layer for couchDB and static file implmentations."""

    def write(self, database: Database, sub_values: tuple, _id: str,
              data: dict) -> None:
        """Write results."""

        raise NotImplementedError

    def read(self, database: Database, sub_values: tuple, _id: str) -> dict:
        """Read results."""

        raise NotImplementedError

    def read_all(self, database: Database, sub_values: tuple) -> list:
        """Read all results under the given sub values."""

        raise NotImplementedError

    def exists(self, database: Database, sub_values: tuple, _id: str) -> bool:
        """Return a boolean of if we have any stored data."""

        raise NotImplementedError

    def count(self, database: Database, sub_values: tuple) -> int:
        """Return a count of stored items for the given sub values."""

        raise NotImplementedError

    def delete(self, database: Database, sub_values: tuple, _id: str) -> None:
        """Delete a result."""

        raise NotImplementedError

    def delete_all(self, database: Database, sub_values: tuple) -> None:
        """Delete all results under the given sub values."""

        raise NotImplementedError


class Server:
    """Static object to interface both couchDB and static files."""

    @staticmethod
    def _impl() -> IServer:
        """Returns the implementation in use."""

        if hasattr(Server, "__impl"):
            return Server.__impl

        server = get_server()
        try:
            server.version()
        except Exception:
            Server.__impl = FileServer(os.getenv("IRACE_RESULTS") or "results")
        else:
            Server.__impl = CouchServer(server)
        return Server.__impl

    @staticmethod
    def write(database: Database, sub_values: tuple, _id: str,
              data: dict) -> None:
        """Write results."""

        return Server._impl().write(_db(database), sub_values, _id, data)

    @staticmethod
    def read(database: Database, sub_values: tuple, _id: str) -> dict:
        """Read results."""

        return Server._impl().read(_db(database), sub_values, _id)

    @staticmethod
    def read_all(database: Database, sub_values: tuple = None) -> list:
        """Read all results under the given sub values."""

        if sub_values is None:
            sub_values = tuple()
        return Server._impl().read_all(_db(database), sub_values)

    @staticmethod
    def exists(database: Database, sub_values: tuple, _id: str) -> bool:
        """Return a boolean of if we have any stored data."""

        return Server._impl().exists(_db(database), sub_values, _id)

    @staticmethod
    def count(database: Database, sub_values: tuple) -> int:
        """Return a count of stored items for the given sub values."""

        return Server._impl().count(_db(database), sub_values)

    @staticmethod
    def delete(database: Database, sub_values: tuple, _id: str) -> None:
        """Delete a result."""

        return Server._impl().delete(_db(database), sub_values, _id)

    @staticmethod
    def delete_all(database: Database, sub_values: tuple) -> None:
        """Delete all results under the given sub values."""

        return Server._impl().delete_all(_db(database), sub_values)


class CouchServer(IServer):
    """CouchDB implementation specifics."""

    def __init__(self, server: couchdb.Server):
        self.server = server
        create_missing_dbs(self.server)

    @staticmethod
    def _payload(database: Database, sub_values: tuple, _id: str) -> dict:
        """Generate a basic payload dictionary."""

        payload = dict(zip(
            database.sub_keys,
            [int(x) for x in sub_values],
        ))
        try:
            payload[database.final_key] = int(_id)
        except ValueError:
            payload[database.final_key] = _id
        payload["_id"] = "{}{}{}".format(
            "/".join(str(x) for x in sub_values),
            "/" if sub_values else "",
            _id,
        )
        return payload

    def _find_all(self, database: Database, sub_values: tuple) -> list:
        """Extract all results given the sub values."""

        all_results = []
        page_size = 100

        couch = self.server[database.name]
        mango = {
            "selector": dict(zip(
                database.sub_keys,
                [int(x) for x in sub_values],
            )),
            "fields": ["data", "_id"],
            "limit": page_size,
        }

        while True:
            this_page_size = 0
            for result in couch.find(mango):
                this_page_size += 1
                all_results.append(result)

            if this_page_size >= page_size:
                mango["skip"] = mango.get("skip", 0) + this_page_size
            else:
                break

        return all_results

    def write(self, database: Database, sub_values: tuple, _id: str,
              data: dict) -> None:
        """Write results."""

        payload = CouchServer._payload(database, sub_values, _id)
        payload["data"] = data

        key = payload["_id"]
        couch = self.server[database.name]

        if key in couch:
            value = couch[key]
            if value["data"] != payload["data"]:
                payload["_rev"] = value["_rev"]
                couch[key] = payload
                log.info("Updated %s data for %s", database.name, key)
        else:
            couch[key] = payload
            log.info("Saved %s data for %s", database.name, key)

    def read(self, database: Database, sub_values: tuple, _id: str) -> dict:
        """Read results."""

        payload = CouchServer._payload(database, sub_values, _id)
        couch = self.server[database.name]

        if payload["_id"] in couch:
            return couch[payload["_id"]]["data"]

        return {}

    def read_all(self, database: Database, sub_values: tuple) -> list:
        """Read all results under the given sub values."""

        return [x["data"] for x in self._find_all(database, sub_values)]

    def exists(self, database: Database, sub_values: tuple, _id: str) -> bool:
        """Return a boolean of if we have any stored data."""

        payload = CouchServer._payload(database, sub_values, _id)
        return payload["_id"] in self.server[database.name]

    def count(self, database: Database, sub_values: tuple) -> int:
        """Return a count of stored items for the given sub values."""

        return len(self._find_all(database, sub_values))

    def delete(self, database: Database, sub_values: tuple, _id: str) -> None:
        """Delete a result."""

        payload = CouchServer._payload(database, sub_values, _id)
        couch = self.server[database.name]
        if payload["_id"] in couch:
            del couch[payload["_id"]]
        else:
            log.warning(
                "Failed to delete %s id: %s",
                database.name,
                payload["_id"],
            )

    def delete_all(self, database: Database, sub_values: tuple) -> None:
        """Delete all results under the given sub values."""

        couch = self.server[database.name]
        for doc in self._find_all(database, sub_values):
            del couch[doc["_id"]]


class FileServer(IServer):
    """File implementation specifics."""

    def __init__(self, path: str):
        self.path = path

    def _list(self, database: Database, sub_values: tuple) -> list:
        """Return a list of files under the given sub_values."""

        return glob(os.path.join(
            self.path,
            database.name,
            *[str(x) for x in sub_values],
            "*.json",
        ))

    def _path(self, database: Database, sub_values: tuple, _id: str) -> str:
        """Return the path the the specific file."""

        return os.path.join(
            self.path,
            database.name,
            *[str(x) for x in sub_values],
            "{}.json".format(_id),
        )

    def _delete(self, file_path: str) -> None:  # pylint: disable=no-self-use
        """Attempt to delete a file."""

        try:
            os.remove(file_path)
        except Exception as error:
            log.warning("Failed to delete %s: %r", file_path, error)

    def write(self, database: Database, sub_values: tuple, _id: str,
              data: dict) -> None:
        """Write results."""

        path = os.path.join(
            self.path,
            database.name,
            *[str(x) for x in sub_values],
        )

        if os.path.exists(path):
            if not os.path.isdir(path):
                log.error("Output path (%s) is a file, aborting!", path)
                return
        else:
            os.makedirs(path)

        path = os.path.join(path, "{}.json".format(_id))
        try:
            with io.open(path, "w", encoding="utf-8") as open_file:
                open_file.write(json.dumps(
                    data,
                    sort_keys=True,
                    indent=4,
                    ensure_ascii=False,
                ))
        except Exception as error:
            log.error("Failed to write %s: %r", path, error)

    def read(self, database: Database, sub_values: tuple, _id: str) -> dict:
        """Read results."""

        path = self._path(database, sub_values, _id)
        try:
            with io.open(path, "r", encoding="utf-8") as open_data:
                return json.load(open_data)
        except Exception as error:
            log.error("Failed to read %s: %r", path, error)
            return {}

    def read_all(self, database: Database, sub_values: tuple) -> list:
        """Read all results under the given sub values."""

        results = []
        for path in self._list(database, sub_values):
            try:
                with io.open(path, "r", encoding="utf-8") as open_data:
                    results.append(json.load(open_data))
            except Exception as error:
                log.error("Failed to read %s: %r", path, error)
        return results

    def exists(self, database: Database, sub_values: tuple, _id: str) -> bool:
        """Return a boolean of if we have any stored data."""

        path = self._path(database, sub_values, _id)
        return os.path.isfile(path) and os.path.getsize(path) > 0

    def count(self, database: Database, sub_values: tuple) -> int:
        """Return a count of stored items for the given sub values."""

        return len(self._list(database, sub_values))

    def delete(self, database: Database, sub_values: tuple, _id: str) -> None:
        """Delete a result."""

        self._delete(self._path(database, sub_values, _id))

    def delete_all(self, database: Database, sub_values: tuple) -> None:
        """Delete all results under the given sub values."""

        for path in self._list(database, sub_values):
            self._delete(path)


def couch_connection_check() -> couchdb.Server:
    """Check if we can connect to the couchDB."""

    server = get_server()
    try:
        print("Connected to couchDB! Server version: {}".format(
            server.version()
        ))
    except Exception as error:
        raise SystemExit("Failed to connect to couchDB: {!r}".format(error))

    return server


def create_missing_dbs(server: couchdb.Server, args: dict = None) -> None:
    """Ensure any missing dbs are created in couchDB."""

    if args is None:
        args = {}

    found = []
    for db_name in server:
        if args.get("--drop-db", False):
            del server[db_name]
            if args:
                print("Deleted DB: {}".format(db_name))
        else:
            found.append(db_name)

    for database in Databases:
        if database.name not in found:
            server.create(database.name)
            if args:
                print("Created DB: {}".format(database.name))


def _to_couch(args: dict, server: couchdb.Server, database: Database) -> None:
    """Import a database of JSON to couchDB."""

    couch = server[database.name]
    updates = []

    paths = glob(os.path.join(
        args["--files"],
        database.name,
        *["*"] * len(database.sub_keys),
        "*.json",
    ))

    if paths:
        print("Parsing {} JSON files for {}".format(
            len(paths),
            database.name,
        ))

    for path in paths:
        rem, filename = os.path.split(path)
        key_parts = []
        for _ in database.sub_keys:
            rem, part = os.path.split(rem)
            key_parts.append(part)

        key_parts.reverse()
        payload = dict(zip(
            database.sub_keys,
            [int(x) for x in key_parts],
        ))

        final_value = os.path.splitext(filename)[0]
        key_parts.append(final_value)
        payload[database.final_key] = int(final_value)

        key = "/".join(key_parts)
        payload["_id"] = key
        payload["data"] = read_json(path)

        if key in couch:
            if couch[key]["data"] != payload["data"]:
                updates.append(payload)
                print("Update to {} data for {}".format(database.name, key))
        else:
            updates.append(payload)

    if updates:
        couch.update(updates)
        print("Sent {} updates to couchDB for {}".format(
            len(updates),
            database.name,
        ))


def _to_files(args: dict, server: couchdb.Server, database: Database) -> None:
    """Write all JSON files stored in the couchDB."""

    couch = server[database.name]
    written = 0

    for doc in couch.view("_all_docs"):
        data = couch[doc.key]
        path = os.path.join(
            args["--files"],
            database.name,
            *[str(data[x]) for x in database.sub_keys]
        )

        if os.path.exists(path):
            if not os.path.isdir(path):
                raise SystemExit("Output directory exists as a file!")
        else:
            os.makedirs(path)

        fname = os.path.join(path, "{}.json".format(data[database.final_key]))

        if os.path.isfile(fname) and not args["--overwrite"]:
            print("Output file found: {}, refusing to overwrite".format(fname))
            continue

        with io.open(fname, "w", encoding="utf-8") as open_file:
            open_file.write(json.dumps(
                data["data"],
                sort_keys=True,
                indent=4,
                ensure_ascii=False,
            ))
            written += 1

    if written:
        print("Exported {} JSON files from couchDB for {}".format(
            written,
            database.name,
        ))


def transition_to_couch(args: dict) -> None:
    """Import JSON results to the couchDB."""

    server = couch_connection_check()
    create_missing_dbs(server, args)
    for database in Databases:
        _to_couch(args, server, database.value)


def transition_to_files(args: dict) -> None:
    """Extract all JSON files from the couchDB."""

    server = couch_connection_check()
    for database in Databases:
        _to_files(args, server, database.value)


def main():
    """Command line entry point."""

    args = get_args(__doc__)
    if args["--to-couch"]:
        transition_to_couch(args)
    elif args["--to-files"]:
        transition_to_files(args)
    else:
        couch_connection_check()


if __name__ == "__main__":
    main()
