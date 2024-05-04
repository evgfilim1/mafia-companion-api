import datetime


def get_current_datetime_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)
