import datetime

import pytz

from arch import app


def log_and_return_error(error, *args, exception=False):
    result = {"success": "false"}
    if exception:
        app.logger.exception(error, *args)
    else:
        app.logger.error(error, *args)
    result['error'] = error % tuple(*args)
    return str(result)


def get_time_in_utc(form):
    date = form.date.data if form.date.data else datetime.date.today()
    tz = pytz.timezone("America/Los_Angeles")
    start_time_utc = None
    end_time_utc = None

    if form.start_time.data:
        start_time = datetime.datetime.combine(date, form.start_time.data)
    else:
        start_time = datetime.datetime.combine(date, datetime.datetime.now().time())

    if form.end_time.data:
        end_time = datetime.datetime.combine(date, form.end_time.data)
    else:
        end_time = None

    if start_time:
        start_time_utc = tz.localize(start_time).astimezone(pytz.utc)
    if end_time:
        end_time_utc = tz.localize(end_time).astimezone(pytz.utc)

    return start_time_utc, end_time_utc


def get_tod():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:  # 6am - 12pm
        return "morning"
    elif hour < 17:     # 12pm - 5pm
        return "afternoon"
    elif hour < 20:     # 5pm - 8pm
        return "evening"
    else:               # 8pm - 6am
        return "night"
