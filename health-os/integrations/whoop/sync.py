#!/usr/bin/env python3
"""
WHOOP Sync Script for Health OS

Syncs sleep, recovery, and workout data from WHOOP API
and writes to daily logs.

Usage:
    python sync.py                    # Sync last 2 days
    python sync.py --days 7           # Sync last 7 days
    python sync.py --backfill 30      # Initial backfill
    python sync.py --dry-run          # Preview without writing
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.whoop.transform import (
    transform_sleep,
    transform_sleep_basic,
    transform_recovery,
    transform_workout,
    get_date_for_sleep,
    get_date_for_recovery,
    get_date_for_workout,
    recovery_zone,
)

from integrations.whoop.client import WhoopClient


# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = BASE_DIR / "data" / "integrations" / "whoop" / "config.json"
LOGS_DIR = BASE_DIR / "data" / "tactical" / "logs"
SYNC_META_FILE = BASE_DIR / "data" / "integrations" / "whoop" / "whoop_sync.yaml"
# Change to your local timezone (e.g. America/New_York, Europe/London)
DEFAULT_TIMEZONE = "UTC"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_daily_log(date: str) -> Dict[str, Any]:
    """Load existing daily log or create empty structure."""
    log_path = LOGS_DIR / f"{date}.yaml"

    if log_path.exists():
        with open(log_path, 'r') as f:
            return yaml.safe_load(f) or {}

    return {
        "date": date,
        "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A").lower()
    }


def save_daily_log(date: str, data: Dict[str, Any], dry_run: bool = False):
    """Save daily log to file."""
    log_path = LOGS_DIR / f"{date}.yaml"

    if dry_run:
        logger.info(f"[DRY RUN] Would save to {log_path}")
        return

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    logger.info(f"Saved {log_path}")


def merge_whoop_sleep(log: Dict[str, Any], sleep_basic: Dict, sleep_whoop: Dict) -> Dict[str, Any]:
    """Merge WHOOP sleep data into daily log."""
    # Initialize sleep section if needed
    if 'sleep' not in log:
        log['sleep'] = {}

    # Update basic fields only if not already set by user
    sleep = log['sleep']
    for key in ['hours', 'quality', 'bed_time', 'wake_time']:
        if key not in sleep or sleep[key] is None:
            if sleep_basic.get(key) is not None:
                sleep[key] = sleep_basic[key]

    # Always update whoop subsection
    sleep['whoop'] = sleep_whoop

    return log


def merge_whoop_recovery(log: Dict[str, Any], recovery_whoop: Dict) -> Dict[str, Any]:
    """Merge WHOOP recovery data into daily log."""
    # Initialize recovery section
    if 'recovery' not in log:
        log['recovery'] = {}

    log['recovery']['whoop'] = recovery_whoop

    return log


def merge_whoop_workout(log: Dict[str, Any], workout_whoop: Dict) -> Dict[str, Any]:
    """Merge WHOOP workout data into daily log."""
    # Initialize workout section if needed
    if 'workout' not in log:
        log['workout'] = {}

    # Add or update whoop subsection
    if 'whoop' not in log['workout']:
        log['workout']['whoop'] = []

    # Check if this workout is already logged (by workout_id)
    existing_ids = {w.get('workout_id') for w in log['workout'].get('whoop', [])}

    if workout_whoop.get('workout_id') not in existing_ids:
        if isinstance(log['workout']['whoop'], list):
            log['workout']['whoop'].append(workout_whoop)
        else:
            log['workout']['whoop'] = [workout_whoop]

    return log


def save_sync_metadata(
    sync_time: datetime,
    days_synced: int,
    records: Dict[str, int],
    errors: List[str]
):
    """Save sync metadata for monitoring."""
    meta = {
        "last_sync": sync_time.isoformat(),
        "days_synced": days_synced,
        "records_synced": records,
        "errors": errors if errors else None,
    }

    SYNC_META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_META_FILE, 'w') as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)

    logger.info(f"Sync metadata saved to {SYNC_META_FILE}")


def sync_whoop_data(
    days: int = 2,
    dry_run: bool = False,
    timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
    """
    Sync WHOOP data for specified number of days.

    Args:
        days: Number of days to sync (from today backwards)
        dry_run: If True, preview changes without writing
        timezone: Local timezone for date conversion

    Returns:
        Sync summary with counts and any errors
    """
    logger.info(f"Starting WHOOP sync for {days} days (timezone: {timezone})")

    # Calculate date range
    tz = ZoneInfo(timezone)
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=days)

    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")

    # Initialize client (handles token refresh automatically)
    try:
        client = WhoopClient(config_file=str(CONFIG_FILE))
        logger.info("WHOOP client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize WHOOP client: {e}")
        return {"error": str(e)}

    errors = []
    records = {"sleep": 0, "recovery": 0, "workout": 0}

    # Group data by date
    data_by_date: Dict[str, Dict[str, Any]] = {}

    # Fetch sleep data
    try:
        logger.info("Fetching sleep data...")
        sleep_records = client.get_sleep(start_date=start_date, end_date=end_date)
        logger.info(f"Got {len(sleep_records)} sleep records")

        for sleep in sleep_records:
            date = get_date_for_sleep(sleep, timezone)
            if date:
                if date not in data_by_date:
                    data_by_date[date] = {"sleep": [], "recovery": [], "workout": []}
                data_by_date[date]["sleep"].append(sleep)
                records["sleep"] += 1

    except Exception as e:
        logger.error(f"Error fetching sleep: {e}")
        errors.append(f"Sleep: {e}")

    # Fetch recovery data
    try:
        logger.info("Fetching recovery data...")
        recovery_records = client.get_recovery(start_date=start_date, end_date=end_date)
        logger.info(f"Got {len(recovery_records)} recovery records")

        for recovery in recovery_records:
            date = get_date_for_recovery(recovery, timezone)
            if date:
                if date not in data_by_date:
                    data_by_date[date] = {"sleep": [], "recovery": [], "workout": []}
                data_by_date[date]["recovery"].append(recovery)
                records["recovery"] += 1

    except Exception as e:
        logger.error(f"Error fetching recovery: {e}")
        errors.append(f"Recovery: {e}")

    # Fetch workout data
    try:
        logger.info("Fetching workout data...")
        workout_records = client.get_workouts(start_date=start_date, end_date=end_date)
        logger.info(f"Got {len(workout_records)} workout records")

        for workout in workout_records:
            date = get_date_for_workout(workout, timezone)
            if date:
                if date not in data_by_date:
                    data_by_date[date] = {"sleep": [], "recovery": [], "workout": []}
                data_by_date[date]["workout"].append(workout)
                records["workout"] += 1

    except Exception as e:
        logger.error(f"Error fetching workouts: {e}")
        errors.append(f"Workout: {e}")

    # Process each date
    for date in sorted(data_by_date.keys()):
        logger.info(f"\nProcessing {date}...")
        day_data = data_by_date[date]

        # Load existing log
        log = load_daily_log(date)

        # Merge sleep (use most recent)
        if day_data["sleep"]:
            sleep = day_data["sleep"][-1]  # Most recent
            sleep_basic = transform_sleep_basic(sleep, timezone)
            sleep_whoop = transform_sleep(sleep, timezone)
            log = merge_whoop_sleep(log, sleep_basic, sleep_whoop)
            logger.info(f"  Sleep: {sleep_basic.get('hours')}h, quality={sleep_basic.get('quality')}")

        # Merge recovery (use most recent)
        if day_data["recovery"]:
            recovery = day_data["recovery"][-1]  # Most recent
            recovery_whoop = transform_recovery(recovery, timezone)
            log = merge_whoop_recovery(log, recovery_whoop)
            score = recovery_whoop.get('score')
            zone = recovery_zone(score) if score else {}
            logger.info(f"  Recovery: {score} ({zone.get('zone', 'N/A')})")

        # Merge workouts (all of them)
        for workout in day_data["workout"]:
            workout_whoop = transform_workout(workout, timezone)
            log = merge_whoop_workout(log, workout_whoop)
            logger.info(f"  Workout: {workout_whoop.get('sport_name')}, strain={workout_whoop.get('strain')}")

        # Save updated log
        save_daily_log(date, log, dry_run)

    # Save sync metadata
    if not dry_run:
        save_sync_metadata(
            sync_time=datetime.now(tz),
            days_synced=days,
            records=records,
            errors=errors
        )

    # Auto-aggregate after sync
    if not dry_run:
        try:
            from integrations.whoop.aggregate import update_aggregates
            logger.info("\nUpdating aggregates...")
            update_aggregates()
        except Exception as e:
            logger.warning(f"Aggregate update failed: {e}")
            errors.append(f"Aggregate: {e}")

    # Summary
    summary = {
        "dates_processed": len(data_by_date),
        "records": records,
        "errors": errors
    }

    logger.info(f"\nSync complete: {summary}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Sync WHOOP data to Health OS")
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=2,
        help="Number of days to sync (default: 2)"
    )
    parser.add_argument(
        "--backfill",
        type=int,
        help="Initial backfill - sync this many days"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing"
    )
    parser.add_argument(
        "--timezone", "-tz",
        default=DEFAULT_TIMEZONE,
        help=f"Local timezone (default: {DEFAULT_TIMEZONE})"
    )

    args = parser.parse_args()

    days = args.backfill if args.backfill else args.days

    result = sync_whoop_data(
        days=days,
        dry_run=args.dry_run,
        timezone=args.timezone
    )

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
