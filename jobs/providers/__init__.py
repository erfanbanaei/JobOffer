from . import eestekhdam, irantalent, jobinja, jobvision
from .common import IRAN_PROVINCES, JOB_TYPE_OPTIONS, ScrapeError

PROVIDERS = {
    "jobinja": jobinja,
    "jobvision": jobvision,
    "eestekhdam": eestekhdam,
    "irantalent": irantalent,
}

__all__ = ["PROVIDERS", "IRAN_PROVINCES", "JOB_TYPE_OPTIONS", "ScrapeError"]
