from . import eestekhdam, jobinja, jobvision
from .common import IRAN_PROVINCES, JOB_TYPE_OPTIONS, ScrapeError

PROVIDERS = {
    "jobinja": jobinja,
    "jobvision": jobvision,
    "eestekhdam": eestekhdam,
}

__all__ = ["PROVIDERS", "IRAN_PROVINCES", "JOB_TYPE_OPTIONS", "ScrapeError"]
