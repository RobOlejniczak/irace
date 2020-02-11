"""iRacing league results fetching and parsing."""


import os
import io
import pkg_resources


__version__ = pkg_resources.get_distribution("irace").version


def read_environment_file() -> None:
    """Injects environment variables from the IRACE_ENV file."""

    env_file = os.environ.get("IRACE_ENV", ".env")

    if os.path.exists(env_file) and os.path.isfile(env_file):
        with io.open(env_file, "r", encoding="utf-8") as open_conf:
            for line in open_conf.readlines():
                if not line or line.startswith("#"):
                    continue
                try:
                    key, value = line.split("=", 1)
                except ValueError:
                    pass
                else:
                    os.environ[key] = value.strip()


read_environment_file()
