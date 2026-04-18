# WHOOP Integration for Health OS

Автоматическая синхронизация данных о сне, recovery и тренировках из WHOOP API.

## Setup

### 1. Install Dependencies

```bash
cd /path/to/health
python3 -m venv .venv
.venv/bin/pip install pyyaml requests python-dotenv whoopy
```

### 2. Configure Credentials

Создай `.env` в корне проекта:

```bash
WHOOP_CLIENT_ID=your-client-id
WHOOP_CLIENT_SECRET=your-client-secret
WHOOP_REDIRECT_URI=https://localhost:8000/callback
```

Credentials можно получить в [WHOOP Developer Dashboard](https://developer-dashboard.whoop.com).

### 3. Authenticate (First Time)

Запусти auth.py для OAuth авторизации:

```bash
cd /path/to/health
.venv/bin/python integrations/whoop/auth.py
```

### 4. Test Sync

```bash
# Dry run (preview without writing)
.venv/bin/python integrations/whoop/sync.py --dry-run --days 3

# Actual sync
.venv/bin/python integrations/whoop/sync.py --days 3

# Initial backfill (30 days)
.venv/bin/python integrations/whoop/sync.py --backfill 30
```

### 5. Setup Cron

```bash
# Edit crontab
crontab -e

# Add line (sync every 12 hours)
0 */12 * * * /path/to/health/integrations/whoop/cron_sync.sh
```

## Files

```
integrations/whoop/
├── __init__.py          # Package exports
├── client.py            # WHOOP API client (headless)
├── transform.py         # API data → Health OS format
├── sync.py              # Main sync script
├── auth.py              # OAuth helper (first-time setup)
├── cron_sync.sh         # Cron wrapper
└── requirements.txt     # Dependencies

data/integrations/whoop/
├── config.json          # OAuth tokens (gitignored)
├── whoop_sync.yaml      # Sync metadata
└── sync.log             # Cron logs
```

## Usage in Daily Logs

После синхронизации, ежедневные логи будут содержать:

```yaml
# Sleep section extended with WHOOP
sleep:
  hours: 7.5
  quality: good
  whoop:
    performance_percent: 82
    efficiency_percent: 91
    stages:
      deep_min: 65
      rem_min: 95
      light_min: 180
      awake_min: 25

# New recovery section
recovery:
  whoop:
    score: 72
    hrv_rmssd: 65.3
    resting_hr: 48

# Workout section extended
workout:
  whoop:
    - strain: 12.5
      zone_durations:
        zone2_min: 35
```

## Coach Integration

Coach автоматически учитывает recovery score:

| Score | Zone | Recommendation |
|-------|------|----------------|
| 0-32 | Red | Skip training |
| 33-65 | Yellow | 50% volume |
| 66-100 | Green | Full training |

## Troubleshooting

### Token Expired

```
Error: No refresh token available
```

Запусти `auth.py` или `get_tokens.py` заново для получения новых токенов.

### Rate Limits

WHOOP API limits:
- 100 requests/minute
- 10,000 requests/day

Sync каждые 12 часов использует ~10-20 запросов.

### Missing Data

WHOOP может отложить данные на несколько часов. Sync забирает последние 2 дня для перекрытия.
