from datetime import datetime
import pytz


def current_utc_timestamp():
    return datetime.now(pytz.utc).isoformat()