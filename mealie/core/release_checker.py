import datetime
from functools import lru_cache

# Fork version - no upstream checking
APP_VERSION_FORK = "3.6.1+ai"


@lru_cache(maxsize=1)
def get_latest_github_release() -> str:
    return APP_VERSION_FORK


def get_latest_version() -> str:
    return APP_VERSION_FORK
