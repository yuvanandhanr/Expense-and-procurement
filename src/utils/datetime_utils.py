from datetime import datetime, timezone

def utc_now() -> datetime:
    """
    Returns a timezone-aware UTC datetime.
    """
    return datetime.utcnow()
