#!/usr/bin/env python3
"""
WHOOP Analytics ETL - Aggregation Script

Generates weekly, monthly, and rolling analytics from daily WHOOP data.

Usage:
    python aggregate.py                  # Update rolling + current week/month
    python aggregate.py --week 2026-W04  # Regenerate specific week
    python aggregate.py --month 2026-01  # Regenerate specific month
    python aggregate.py --full           # Regenerate all history
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from zoneinfo import ZoneInfo
from collections import defaultdict

import yaml

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = BASE_DIR / "data" / "tactical" / "logs"
ANALYTICS_DIR = BASE_DIR / "data" / "tactical" / "analytics" / "whoop"
DIRECTIVES_FILE = BASE_DIR / "data" / "strategic" / "directives.yaml"
PROFILE_FILE = BASE_DIR / "data" / "tactical" / "user_profile.yaml"
# Change to your local timezone (e.g. America/New_York, Europe/London)
DEFAULT_TIMEZONE = "UTC"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file, return empty dict if not exists."""
    if path.exists():
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml(path: Path, data: Dict[str, Any]):
    """Save data to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_directives() -> Dict[str, Any]:
    """Load strategic directives for target values."""
    return load_yaml(DIRECTIVES_FILE)


def load_user_profile() -> Dict[str, Any]:
    """Load user profile for max HR calculation."""
    return load_yaml(PROFILE_FILE)


def calculate_max_hr(profile: Dict[str, Any]) -> int:
    """Calculate max HR from age (220 - age formula)."""
    age = profile.get('personal', {}).get('age', 30)
    return 220 - age


def is_zone2_hr(avg_hr: int, max_hr: int) -> bool:
    """
    Check if avg HR is in Zone 2 range (60-70% of max HR).

    Workaround for WHOOP API returning 0 for zone_durations.
    """
    if not avg_hr or not max_hr:
        return False
    hr_percent = (avg_hr / max_hr) * 100
    return 60 <= hr_percent <= 70


def estimate_zone2_minutes(workout: Dict[str, Any], max_hr: int) -> int:
    """
    Estimate Zone 2 minutes from workout.

    If zone_durations has data, use it. Otherwise, estimate based on avg_hr.
    """
    zone_durations = workout.get('zone_durations', {})
    zone2_min = zone_durations.get('zone2_min', 0) or 0

    # If WHOOP provides zone2, use it
    if zone2_min > 0:
        return zone2_min

    # Workaround: if avg_hr is in Zone 2 range, estimate duration
    # We don't have duration directly, but can estimate from strain
    avg_hr = workout.get('avg_hr', 0)
    strain = workout.get('strain', 0) or 0

    if is_zone2_hr(avg_hr, max_hr) and strain > 0:
        # Rough estimate: 1 strain point ≈ 5-10 min of Zone 2
        # Conservative estimate for Zone 2 activities
        estimated_min = int(strain * 6)
        return min(estimated_min, 90)  # Cap at 90 min

    return 0


def load_daily_logs(start_date: date, end_date: date) -> Dict[str, Dict[str, Any]]:
    """Load all daily logs in date range."""
    logs = {}
    current = start_date

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        log_path = LOGS_DIR / f"{date_str}.yaml"

        if log_path.exists():
            log = load_yaml(log_path)
            if log:
                logs[date_str] = log

        current += timedelta(days=1)

    return logs


def get_week_dates(year: int, week: int) -> Tuple[date, date]:
    """Get start (Monday) and end (Sunday) dates for ISO week."""
    # ISO week starts on Monday
    jan4 = date(year, 1, 4)  # Jan 4 is always in week 1
    start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=week-1)
    end = start + timedelta(days=6)
    return start, end


def get_month_dates(year: int, month: int) -> Tuple[date, date]:
    """Get start and end dates for month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def aggregate_sleep(logs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate sleep data from daily logs."""
    sleep_data = []

    for date_str, log in logs.items():
        sleep = log.get('sleep', {})
        whoop = sleep.get('whoop', {})

        if whoop:
            sleep_data.append({
                'date': date_str,
                'hours': sleep.get('hours'),
                'performance': whoop.get('performance_percent'),
                'efficiency': whoop.get('efficiency_percent'),
                'stages': whoop.get('stages', {})
            })

    if not sleep_data:
        return {}

    # Calculate averages
    valid_hours = [s['hours'] for s in sleep_data if s['hours']]
    valid_perf = [s['performance'] for s in sleep_data if s['performance']]
    valid_eff = [s['efficiency'] for s in sleep_data if s['efficiency']]

    # Stages
    deep_mins = [s['stages'].get('deep_min', 0) for s in sleep_data if s['stages']]
    rem_mins = [s['stages'].get('rem_min', 0) for s in sleep_data if s['stages']]

    return {
        'days_with_data': len(sleep_data),
        'avg_hours': round(sum(valid_hours) / len(valid_hours), 1) if valid_hours else None,
        'avg_performance': round(sum(valid_perf) / len(valid_perf), 1) if valid_perf else None,
        'avg_efficiency': round(sum(valid_eff) / len(valid_eff), 1) if valid_eff else None,
        'stages': {
            'avg_deep_min': round(sum(deep_mins) / len(deep_mins)) if deep_mins else None,
            'avg_rem_min': round(sum(rem_mins) / len(rem_mins)) if rem_mins else None,
        }
    }


def aggregate_recovery(logs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate recovery data from daily logs."""
    recovery_data = []

    for date_str, log in logs.items():
        recovery = log.get('recovery', {})
        whoop = recovery.get('whoop', {})

        if whoop and whoop.get('score') is not None:
            recovery_data.append({
                'date': date_str,
                'score': whoop.get('score'),
                'hrv': whoop.get('hrv_rmssd'),
                'resting_hr': whoop.get('resting_hr')
            })

    if not recovery_data:
        return {}

    scores = [r['score'] for r in recovery_data if r['score'] is not None]
    hrvs = [r['hrv'] for r in recovery_data if r['hrv']]
    hrs = [r['resting_hr'] for r in recovery_data if r['resting_hr']]

    # Count zones
    red = sum(1 for s in scores if s < 33)
    yellow = sum(1 for s in scores if 33 <= s < 66)
    green = sum(1 for s in scores if s >= 66)

    return {
        'days_with_data': len(recovery_data),
        'avg_score': round(sum(scores) / len(scores), 1) if scores else None,
        'avg_hrv': round(sum(hrvs) / len(hrvs), 1) if hrvs else None,
        'avg_resting_hr': round(sum(hrs) / len(hrs)) if hrs else None,
        'zone_distribution': {
            'red': red,
            'yellow': yellow,
            'green': green
        }
    }


def aggregate_workout(
    logs: Dict[str, Dict[str, Any]],
    max_hr: int,
    directives: Dict[str, Any]
) -> Dict[str, Any]:
    """Aggregate workout data from daily logs."""
    workouts = []
    walks = []  # Track walks separately
    by_sport = defaultdict(lambda: {'sessions': 0, 'strain': 0.0})
    total_zone2 = 0
    merged_ids = set()  # Track merged workout IDs

    for date_str, log in logs.items():
        workout = log.get('workout', {})
        whoop_workouts = workout.get('whoop', [])

        if isinstance(whoop_workouts, list):
            # First pass: collect merged IDs
            for w in whoop_workouts:
                if w.get('merged_with'):
                    merged_ids.add(w.get('merged_with'))

            for w in whoop_workouts:
                workout_id = w.get('workout_id')

                # Skip walks (type_override: walk)
                if w.get('type_override') == 'walk':
                    walks.append({
                        'date': date_str,
                        'strain': w.get('strain', 0) or 0,
                        'calories': w.get('calories', 0) or 0
                    })
                    continue

                # Skip if this workout is merged into another (avoid double counting)
                if workout_id in merged_ids:
                    # Still count zone2 and strain, but not as separate session
                    total_zone2 += estimate_zone2_minutes(w, max_hr)
                    continue

                workouts.append({
                    'date': date_str,
                    'sport': w.get('sport_name', 'unknown'),
                    'strain': w.get('strain', 0) or 0,
                    'avg_hr': w.get('avg_hr'),
                    'zone_durations': w.get('zone_durations', {}),
                    'is_merged': bool(w.get('merged_with'))  # Has another workout merged into it
                })

                # Aggregate by sport
                sport = w.get('sport_name', 'unknown')
                by_sport[sport]['sessions'] += 1
                by_sport[sport]['strain'] += w.get('strain', 0) or 0

                # Zone 2 with workaround
                total_zone2 += estimate_zone2_minutes(w, max_hr)

    if not workouts:
        return {}

    # Get target from directives
    constraints = directives.get('constraints', {}).get('training', {})
    zone2_target = constraints.get('min_zone2_minutes_week', 90)

    # Calculate compliance
    zone2_compliance = round((total_zone2 / zone2_target) * 100) if zone2_target > 0 else 0

    # Format by_sport
    by_sport_formatted = {
        sport: {
            'sessions': data['sessions'],
            'strain': round(data['strain'], 1)
        }
        for sport, data in by_sport.items()
    }

    result = {
        'total_sessions': len(workouts),
        'total_strain': round(sum(w['strain'] for w in workouts), 1),
        'by_sport': by_sport_formatted,
        'zone2': {
            'total_min': total_zone2,
            'target_min': zone2_target,
            'compliance_percent': min(zone2_compliance, 100)
        }
    }

    # Add walks info if any
    if walks:
        result['walks'] = {
            'count': len(walks),
            'total_strain': round(sum(w['strain'] for w in walks), 1)
        }

    return result


def calculate_compliance(
    sleep_agg: Dict[str, Any],
    workout_agg: Dict[str, Any],
    directives: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate compliance with directives."""
    constraints = directives.get('constraints', {})
    training = constraints.get('training', {})
    sleep = constraints.get('sleep', {})

    compliance = {}

    # Zone 2 compliance
    zone2_data = workout_agg.get('zone2', {})
    zone2_compliance = zone2_data.get('compliance_percent', 0)
    compliance['zone2_met'] = zone2_compliance >= 100

    # Strength sessions (approximate from weightlifting sessions)
    min_strength = training.get('min_strength_sessions_week', 2)
    by_sport = workout_agg.get('by_sport', {})
    strength_sessions = by_sport.get('weightlifting_msk', {}).get('sessions', 0)
    strength_sessions += by_sport.get('functional_fitness', {}).get('sessions', 0)
    compliance['strength_sessions_met'] = strength_sessions >= min_strength

    # Sleep target
    target_hours = sleep.get('target_hours_min', 7)
    avg_hours = sleep_agg.get('avg_hours', 0) or 0
    compliance['sleep_target_met'] = avg_hours >= target_hours

    return compliance


def generate_weekly(year: int, week: int, directives: Dict[str, Any], max_hr: int) -> Dict[str, Any]:
    """Generate weekly aggregate report."""
    start_date, end_date = get_week_dates(year, week)
    logs = load_daily_logs(start_date, end_date)

    if not logs:
        logger.warning(f"No logs found for {year}-W{week:02d}")
        return {}

    # Aggregate data
    sleep_agg = aggregate_sleep(logs)
    recovery_agg = aggregate_recovery(logs)
    workout_agg = aggregate_workout(logs, max_hr, directives)
    compliance = calculate_compliance(sleep_agg, workout_agg, directives)

    return {
        'week': f"{year}-W{week:02d}",
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'days_with_data': len(logs),
        'sleep': sleep_agg,
        'recovery': recovery_agg,
        'workout': workout_agg,
        'compliance': compliance,
        'generated_at': datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat()
    }


def generate_monthly(year: int, month: int, directives: Dict[str, Any], max_hr: int) -> Dict[str, Any]:
    """Generate monthly aggregate report."""
    start_date, end_date = get_month_dates(year, month)
    logs = load_daily_logs(start_date, end_date)

    if not logs:
        logger.warning(f"No logs found for {year}-{month:02d}")
        return {}

    # Aggregate data
    sleep_agg = aggregate_sleep(logs)
    recovery_agg = aggregate_recovery(logs)
    workout_agg = aggregate_workout(logs, max_hr, directives)

    return {
        'month': f"{year}-{month:02d}",
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'days_with_data': len(logs),
        'sleep': sleep_agg,
        'recovery': recovery_agg,
        'workout': workout_agg,
        'generated_at': datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat()
    }


def generate_rolling(directives: Dict[str, Any], max_hr: int) -> Dict[str, Any]:
    """Generate rolling averages (7d, 14d, 30d)."""
    tz = ZoneInfo(DEFAULT_TIMEZONE)
    today = datetime.now(tz).date()

    rolling = {
        'as_of': today.isoformat()
    }

    for period_days, period_name in [(7, '7d'), (14, '14d'), (30, '30d')]:
        start_date = today - timedelta(days=period_days - 1)
        logs = load_daily_logs(start_date, today)

        if logs:
            sleep_agg = aggregate_sleep(logs)
            workout_agg = aggregate_workout(logs, max_hr, directives)
            recovery_agg = aggregate_recovery(logs)

            # Zone 2 weekly rate (extrapolate to 7 days)
            zone2_data = workout_agg.get('zone2', {})
            zone2_total = zone2_data.get('total_min', 0)
            zone2_target = zone2_data.get('target_min', 90)
            # Scale to weekly
            zone2_weekly = int(zone2_total * 7 / period_days) if period_days > 0 else 0
            zone2_compliance = round((zone2_weekly / zone2_target) * 100) if zone2_target > 0 else 0

            rolling[f'rolling_{period_name}'] = {
                'sleep': {
                    'avg_hours': sleep_agg.get('avg_hours'),
                    'avg_performance': sleep_agg.get('avg_performance')
                },
                'recovery': {
                    'avg_score': recovery_agg.get('avg_score'),
                    'avg_hrv': recovery_agg.get('avg_hrv')
                },
                'workout': {
                    'sessions': workout_agg.get('total_sessions', 0),
                    'zone2_min': zone2_total,
                    'zone2_weekly_rate': zone2_weekly,
                    'zone2_compliance_percent': min(zone2_compliance, 100)
                }
            }

    # Determine trends
    rolling['trends'] = calculate_trends(rolling)

    # Generate alerts
    rolling['alerts'] = generate_alerts(rolling, directives)

    rolling['last_updated'] = datetime.now(tz).isoformat()

    return rolling


def calculate_trends(rolling: Dict[str, Any]) -> Dict[str, str]:
    """Calculate trends comparing 7d vs 14d averages."""
    trends = {}

    r7 = rolling.get('rolling_7d', {})
    r14 = rolling.get('rolling_14d', {})

    # Sleep performance trend
    perf_7 = r7.get('sleep', {}).get('avg_performance')
    perf_14 = r14.get('sleep', {}).get('avg_performance')
    if perf_7 is not None and perf_14 is not None:
        if perf_7 > perf_14 + 3:
            trends['sleep_performance'] = 'improving'
        elif perf_7 < perf_14 - 3:
            trends['sleep_performance'] = 'declining'
        else:
            trends['sleep_performance'] = 'stable'

    # Recovery trend
    rec_7 = r7.get('recovery', {}).get('avg_score')
    rec_14 = r14.get('recovery', {}).get('avg_score')
    if rec_7 is not None and rec_14 is not None:
        if rec_7 > rec_14 + 5:
            trends['recovery'] = 'improving'
        elif rec_7 < rec_14 - 5:
            trends['recovery'] = 'declining'
        else:
            trends['recovery'] = 'stable'

    # Zone 2 compliance trend
    z2_7 = r7.get('workout', {}).get('zone2_compliance_percent', 0)
    z2_14 = r14.get('workout', {}).get('zone2_compliance_percent', 0)
    if z2_7 > z2_14 + 10:
        trends['zone2_compliance'] = 'improving'
    elif z2_7 < z2_14 - 10:
        trends['zone2_compliance'] = 'declining'
    else:
        trends['zone2_compliance'] = 'stable'

    return trends


def generate_alerts(rolling: Dict[str, Any], directives: Dict[str, Any]) -> List[str]:
    """Generate alerts based on rolling data and directives."""
    alerts = []

    r7 = rolling.get('rolling_7d', {})

    # Zone 2 alert
    zone2_compliance = r7.get('workout', {}).get('zone2_compliance_percent', 0)
    if zone2_compliance < 50:
        alerts.append(f"Zone 2 critically below target ({zone2_compliance}%)")
    elif zone2_compliance < 80:
        alerts.append(f"Zone 2 below target ({zone2_compliance}%)")

    # Sleep alert
    sleep_hours = r7.get('sleep', {}).get('avg_hours')
    target_hours = directives.get('constraints', {}).get('sleep', {}).get('target_hours_min', 7)
    if sleep_hours is not None and sleep_hours < target_hours:
        alerts.append(f"Sleep below target ({sleep_hours:.1f}h vs {target_hours}h)")

    # Recovery alert
    recovery = r7.get('recovery', {}).get('avg_score')
    if recovery is not None and recovery < 50:
        alerts.append(f"Recovery low ({recovery:.0f}% avg)")

    return alerts


def update_aggregates():
    """Update rolling and current week/month aggregates."""
    logger.info("Updating aggregates...")

    directives = load_directives()
    profile = load_user_profile()
    max_hr = calculate_max_hr(profile)

    tz = ZoneInfo(DEFAULT_TIMEZONE)
    today = datetime.now(tz).date()
    year, week, _ = today.isocalendar()
    month = today.month

    # Rolling
    rolling = generate_rolling(directives, max_hr)
    rolling_path = ANALYTICS_DIR / "rolling.yaml"
    save_yaml(rolling_path, rolling)
    logger.info(f"Saved {rolling_path}")

    # Current week
    weekly = generate_weekly(year, week, directives, max_hr)
    if weekly:
        weekly_path = ANALYTICS_DIR / "weekly" / f"{year}-W{week:02d}.yaml"
        save_yaml(weekly_path, weekly)
        logger.info(f"Saved {weekly_path}")

    # Current month
    monthly = generate_monthly(today.year, month, directives, max_hr)
    if monthly:
        monthly_path = ANALYTICS_DIR / "monthly" / f"{today.year}-{month:02d}.yaml"
        save_yaml(monthly_path, monthly)
        logger.info(f"Saved {monthly_path}")

    return {
        'rolling': rolling_path,
        'weekly': weekly_path if weekly else None,
        'monthly': monthly_path if monthly else None
    }


def full_aggregation():
    """Regenerate all historical aggregates."""
    logger.info("Running full aggregation...")

    directives = load_directives()
    profile = load_user_profile()
    max_hr = calculate_max_hr(profile)

    # Find date range from logs
    log_files = sorted(LOGS_DIR.glob("*.yaml"))
    if not log_files:
        logger.warning("No log files found")
        return

    first_date = datetime.strptime(log_files[0].stem, "%Y-%m-%d").date()
    last_date = datetime.strptime(log_files[-1].stem, "%Y-%m-%d").date()

    logger.info(f"Processing logs from {first_date} to {last_date}")

    # Generate all weeks
    current = first_date
    weeks_generated = 0
    while current <= last_date:
        year, week, _ = current.isocalendar()
        weekly = generate_weekly(year, week, directives, max_hr)
        if weekly:
            weekly_path = ANALYTICS_DIR / "weekly" / f"{year}-W{week:02d}.yaml"
            save_yaml(weekly_path, weekly)
            weeks_generated += 1
        current += timedelta(weeks=1)

    logger.info(f"Generated {weeks_generated} weekly reports")

    # Generate all months
    months_generated = 0
    current = date(first_date.year, first_date.month, 1)
    while current <= last_date:
        monthly = generate_monthly(current.year, current.month, directives, max_hr)
        if monthly:
            monthly_path = ANALYTICS_DIR / "monthly" / f"{current.year}-{current.month:02d}.yaml"
            save_yaml(monthly_path, monthly)
            months_generated += 1

        # Move to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    logger.info(f"Generated {months_generated} monthly reports")

    # Update rolling
    rolling = generate_rolling(directives, max_hr)
    rolling_path = ANALYTICS_DIR / "rolling.yaml"
    save_yaml(rolling_path, rolling)
    logger.info(f"Saved {rolling_path}")

    logger.info("Full aggregation complete")


def main():
    parser = argparse.ArgumentParser(description="WHOOP Analytics Aggregation")
    parser.add_argument(
        "--week",
        help="Generate specific week (e.g., 2026-W04)"
    )
    parser.add_argument(
        "--month",
        help="Generate specific month (e.g., 2026-01)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Regenerate all history"
    )

    args = parser.parse_args()

    directives = load_directives()
    profile = load_user_profile()
    max_hr = calculate_max_hr(profile)

    if args.full:
        full_aggregation()
    elif args.week:
        # Parse week string (2026-W04)
        year, week_str = args.week.split('-W')
        year = int(year)
        week = int(week_str)

        weekly = generate_weekly(year, week, directives, max_hr)
        if weekly:
            weekly_path = ANALYTICS_DIR / "weekly" / f"{year}-W{week:02d}.yaml"
            save_yaml(weekly_path, weekly)
            logger.info(f"Generated {weekly_path}")
        else:
            logger.warning(f"No data for {args.week}")
    elif args.month:
        # Parse month string (2026-01)
        year, month = args.month.split('-')
        year = int(year)
        month = int(month)

        monthly = generate_monthly(year, month, directives, max_hr)
        if monthly:
            monthly_path = ANALYTICS_DIR / "monthly" / f"{year}-{month:02d}.yaml"
            save_yaml(monthly_path, monthly)
            logger.info(f"Generated {monthly_path}")
        else:
            logger.warning(f"No data for {args.month}")
    else:
        # Default: update current
        update_aggregates()


if __name__ == "__main__":
    main()
