"""Generic parsing utilities."""


from datetime import timedelta


def as_timedelta(timestamp: float) -> timedelta:
    """Convert whatever timestamps iRacing is using into standard."""

    # NB: not microseconds nor milliseconds, unfortunately
    return timedelta(seconds=timestamp / 10000.0)


def time_string(timestamp) -> str:
    """Convert the timestamp to a decent looking time string."""

    if isinstance(timestamp, timedelta):
        return _format_seconds(timestamp.total_seconds())
    return _format_seconds(timedelta(seconds=timestamp).total_seconds())


def time_string_raw(timestamp) -> str:
    """Convert iRacing timestamp to string."""

    return time_string(timestamp / 10000.0)


def _format_seconds(seconds: float) -> str:
    """Format the total number of seconds into a time string."""

    if seconds <= 0:
        return "--:--"

    hours, remaining = divmod(seconds, 3600)
    minutes, remaining = divmod(remaining, 60)
    seconds, microseconds = divmod(remaining, 1)

    timestr = "{:02}:{:02}.{:04}".format(
        int(minutes),
        int(seconds),
        int(microseconds * 10000)
    )

    if hours:
        return "{:02}:{}".format(int(hours), timestr)

    return timestr


def suffix(number: int) -> str:
    """Return the english suffix for the number."""

    if number != 11 and number % 10 == 1:
        return "st"
    if number != 12 and number % 10 == 2:
        return "nd"
    if number != 13 and number % 10 == 3:
        return "rd"
    return "th"
