"""
WHOOP Integration for Health OS

Automatic sync of sleep, recovery, and workout data from WHOOP.
Runs via cron every 12 hours.
"""

from .client import WhoopClient
from .sync import sync_whoop_data
from .transform import (
    transform_sleep,
    transform_recovery,
    transform_workout,
    quality_from_performance,
)

__all__ = [
    "WhoopClient",
    "sync_whoop_data",
    "transform_sleep",
    "transform_recovery",
    "transform_workout",
    "quality_from_performance",
]
