"""iRacing league results fetching and parsing."""


import pkg_resources


try:
    import sentry_sdk
except ImportError:
    pass
else:
    import os
    if "IRACE_SENTRY" in os.environ:
        sentry_sdk.init(os.environ["IRACE_SENTRY"])


__version__ = pkg_resources.get_distribution("irace").version
