// PM2 Ecosystem File for WHOOP Sync
//
// Usage:
//   pm2 start ecosystem.config.js
//   pm2 logs whoop-sync
//   pm2 stop whoop-sync
//
// Or run manually:
//   pm2 start ecosystem.config.js --only whoop-sync-manual

const path = require('path');
const PROJECT_DIR = path.resolve(__dirname, '../..');

module.exports = {
  apps: [
    {
      name: 'whoop-sync',
      script: '.venv/bin/python',
      args: 'integrations/whoop/sync.py --days 2',
      cwd: PROJECT_DIR,

      // Cron: every 12 hours (00:00 and 12:00)
      cron_restart: '0 */12 * * *',

      // Don't keep running - just execute and stop
      autorestart: false,

      // Logging
      log_file: 'data/integrations/whoop/sync.log',
      error_file: 'data/integrations/whoop/sync-error.log',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',

      // Environment
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      // Manual trigger (for testing)
      name: 'whoop-sync-manual',
      script: '.venv/bin/python',
      args: 'integrations/whoop/sync.py --days 7',
      cwd: PROJECT_DIR,
      autorestart: false,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
