import datetime


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