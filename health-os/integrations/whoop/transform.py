"""
Transform WHOOP API data to Health OS daily log format.

Handles:
- UTC → local timezone conversion
- Quality derivation from performance scores
- Duration conversion (ms → minutes)
- Zone duration extraction
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo


# Default timezone — change to your local timezone
# Examples: America/New_York, Europe/London, Asia/Tokyo
DEFAULT_TIMEZONE = "UTC"


def get_local_date(iso_timestamp: str, timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Convert ISO timestamp to local date string.

    Args:
        iso_timestamp: ISO 8601 timestamp (e.g., "2026-01-30T06:00:00.000Z")
        timezone: Target timezone (default: UTC)

    Returns:
        Date string in YYYY-MM-DD format
    """
    if not iso_timestamp:
        return None

    # Parse ISO timestamp
    dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))

    # Convert to local timezone
    local_tz = ZoneInfo(timezone)
    local_dt = dt.astimezone(local_tz)

    return local_dt.strftime("%Y-%m-%d")


def get_local_time(iso_timestamp: str, timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Convert ISO timestamp to local time string.

    Args:
        iso_timestamp: ISO 8601 timestamp
        timezone: Target timezone

    Returns:
        Time string in HH:MM format
    """
    if not iso_timestamp:
        return None

    dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
    local_tz = ZoneInfo(timezone)
    local_dt = dt.astimezone(local_tz)

    return local_dt.strftime("%H:%M")


def get_local_datetime(iso_timestamp: str, timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Convert ISO timestamp to local datetime string.

    Args:
        iso_timestamp: ISO 8601 timestamp
        timezone: Target timezone

    Returns:
        ISO datetime string with timezone
    """
    if not iso_timestamp:
        return None

    dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
    local_tz = ZoneInfo(timezone)
    local_dt = dt.astimezone(local_tz)

    return local_dt.isoformat()


def quality_from_performance(performance_percent: Optional[float]) -> str:
    """
    Derive sleep quality from WHOOP performance percentage.

    WHOOP performance:
    - 0-49: Poor sleep
    - 50-69: Fair sleep
    - 70-84: Good sleep
    - 85-100: Excellent sleep

    Args:
        performance_percent: WHOOP sleep performance score (0-100)

    Returns:
        Quality enum: poor, fair, good, excellent
    """
    if performance_percent is None:
        return None

    if performance_percent < 50:
        return "poor"
    elif performance_percent < 70:
        return "fair"
    elif performance_percent < 85:
        return "good"
    else:
        return "excellent"


def recovery_zone(score: int) -> Dict[str, str]:
    """
    Get recovery zone and recommendation.

    Args:
        score: WHOOP recovery score (0-100)

    Returns:
        Dict with zone color and training recommendation
    """
    if score < 33:
        return {
            "zone": "red",
            "action": "skip_training",
            "message": "Recovery низкий. Отдых или легкая прогулка."
        }
    elif score < 66:
        return {
            "zone": "yellow",
            "action": "reduce_volume",
            "modifier": 0.5,
            "message": "Recovery умеренный. Снижаем объем на 50%."
        }
    else:
        return {
            "zone": "green",
            "action": "full_training",
            "message": "Recovery хороший. Тренируемся по плану."
        }


def ms_to_minutes(ms: Optional[int]) -> Optional[int]:
    """Convert milliseconds to minutes (rounded)."""
    if ms is None:
        return None
    return round(ms / 60000)


def transform_sleep(
    sleep_data: Dict[str, Any],
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Transform WHOOP sleep data to Health OS format.

    Args:
        sleep_data: Raw sleep record from WHOOP API
        timezone: Target timezone for time conversion

    Returns:
        Dict matching sleep.whoop schema in daily log
    """
    # Extract nested data
    score = sleep_data.get('score', {})
    stage_summary = score.get('stage_summary', {})

    # Calculate efficiency
    total_in_bed_ms = stage_summary.get('total_in_bed_time_milli', 0)
    total_sleep_ms = (
        stage_summary.get('total_light_sleep_time_milli', 0) +
        stage_summary.get('total_slow_wave_sleep_time_milli', 0) +
        stage_summary.get('total_rem_sleep_time_milli', 0)
    )
    efficiency = round(total_sleep_ms / total_in_bed_ms * 100, 1) if total_in_bed_ms > 0 else None

    # Build transformed data
    return {
        "sleep_id": sleep_data.get('id'),
        "efficiency_percent": efficiency,
        "performance_percent": score.get('sleep_performance_percentage'),
        "stages": {
            "awake_min": ms_to_minutes(stage_summary.get('total_awake_time_milli')),
            "light_min": ms_to_minutes(stage_summary.get('total_light_sleep_time_milli')),
            "rem_min": ms_to_minutes(stage_summary.get('total_rem_sleep_time_milli')),
            "deep_min": ms_to_minutes(stage_summary.get('total_slow_wave_sleep_time_milli')),
        },
        "respiratory_rate": score.get('respiratory_rate'),
        "synced_at": datetime.now(ZoneInfo(timezone)).isoformat()
    }


def transform_sleep_basic(
    sleep_data: Dict[str, Any],
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Transform WHOOP sleep to basic sleep fields (hours, quality, bed/wake time).

    Args:
        sleep_data: Raw sleep record from WHOOP API
        timezone: Target timezone

    Returns:
        Dict with basic sleep fields for daily log
    """
    score = sleep_data.get('score', {})
    stage_summary = score.get('stage_summary', {})

    # Calculate total sleep hours
    total_sleep_ms = (
        stage_summary.get('total_light_sleep_time_milli', 0) +
        stage_summary.get('total_slow_wave_sleep_time_milli', 0) +
        stage_summary.get('total_rem_sleep_time_milli', 0)
    )
    hours = round(total_sleep_ms / 3600000, 1) if total_sleep_ms else None

    return {
        "hours": hours,
        "quality": quality_from_performance(score.get('sleep_performance_percentage')),
        "bed_time": get_local_time(sleep_data.get('start'), timezone),
        "wake_time": get_local_time(sleep_data.get('end'), timezone),
    }


def transform_recovery(
    recovery_data: Dict[str, Any],
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Transform WHOOP recovery data to Health OS format.

    Args:
        recovery_data: Raw recovery record from WHOOP API
        timezone: Target timezone

    Returns:
        Dict matching recovery.whoop schema in daily log
    """
    score = recovery_data.get('score', {})

    return {
        "score": score.get('recovery_score'),
        "hrv_rmssd": score.get('hrv_rmssd_milli'),  # Already in ms
        "resting_hr": score.get('resting_heart_rate'),
        "spo2_percent": score.get('spo2_percentage'),
        "skin_temp_celsius": score.get('skin_temp_celsius'),
        "synced_at": datetime.now(ZoneInfo(timezone)).isoformat()
    }


def transform_workout(
    workout_data: Dict[str, Any],
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Transform WHOOP workout data to Health OS format.

    Args:
        workout_data: Raw workout record from WHOOP API
        timezone: Target timezone

    Returns:
        Dict matching workout.whoop schema in daily log
    """
    score = workout_data.get('score') or {}
    zone_durations = score.get('zone_duration') or {}

    # Extract zone 2 duration (WHOOP zone 2 = HR 60-70% of max)
    # Zone durations are in milliseconds
    zone2_ms = zone_durations.get('zone_two', 0) or 0

    return {
        "workout_id": workout_data.get('id'),
        "sport_id": workout_data.get('sport_id'),
        "sport_name": workout_data.get('sport_name'),
        "strain": score.get('strain'),
        "avg_hr": score.get('average_heart_rate'),
        "max_hr": score.get('max_heart_rate'),
        "calories": score.get('kilojoule'),  # Note: WHOOP returns kilojoules, needs conversion
        "zone_durations": {
            "zone1_min": ms_to_minutes(zone_durations.get('zone_one', 0)),
            "zone2_min": ms_to_minutes(zone2_ms),
            "zone3_min": ms_to_minutes(zone_durations.get('zone_three', 0)),
            "zone4_min": ms_to_minutes(zone_durations.get('zone_four', 0)),
            "zone5_min": ms_to_minutes(zone_durations.get('zone_five', 0)),
        },
        "synced_at": datetime.now(ZoneInfo(timezone)).isoformat()
    }


def get_date_for_sleep(sleep_data: Dict[str, Any], timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Determine which date a sleep record belongs to.

    Sleep records should be assigned to the date the user woke up.

    Args:
        sleep_data: Raw sleep record from WHOOP API
        timezone: Target timezone

    Returns:
        Date string in YYYY-MM-DD format
    """
    # Use end time (wake up) to determine the date
    end_time = sleep_data.get('end')
    if end_time:
        return get_local_date(end_time, timezone)

    # Fallback to start time
    start_time = sleep_data.get('start')
    return get_local_date(start_time, timezone)


def get_date_for_recovery(recovery_data: Dict[str, Any], timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Determine which date a recovery record belongs to.

    Recovery is calculated at wake-up, so use created_at.

    Args:
        recovery_data: Raw recovery record from WHOOP API
        timezone: Target timezone

    Returns:
        Date string in YYYY-MM-DD format
    """
    created_at = recovery_data.get('created_at')
    if created_at:
        return get_local_date(created_at, timezone)

    # Fallback to cycle start
    cycle_start = recovery_data.get('cycle', {}).get('start')
    return get_local_date(cycle_start, timezone)


def get_date_for_workout(workout_data: Dict[str, Any], timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Determine which date a workout record belongs to.

    Args:
        workout_data: Raw workout record from WHOOP API
        timezone: Target timezone

    Returns:
        Date string in YYYY-MM-DD format
    """
    start_time = workout_data.get('start')
    return get_local_date(start_time, timezone)


def aggregate_zone2_minutes(workouts: List[Dict[str, Any]], timezone: str = DEFAULT_TIMEZONE) -> Dict[str, int]:
    """
    Aggregate Zone 2 minutes by date.

    Args:
        workouts: List of transformed workout records
        timezone: Target timezone

    Returns:
        Dict mapping date strings to total Zone 2 minutes
    """
    zone2_by_date: Dict[str, int] = {}

    for workout in workouts:
        date = get_date_for_workout(workout, timezone)
        if date:
            zone2_min = workout.get('zone_durations', {}).get('zone2_min', 0) or 0
            zone2_by_date[date] = zone2_by_date.get(date, 0) + zone2_min

    return zone2_by_date
