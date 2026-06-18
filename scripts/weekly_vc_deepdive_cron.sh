#!/bin/bash
# weekly_vc_deepdive_cron.sh — weekly cron task to fetch VC deals and send to Slack
set -e

# Navigate to project root and load environment variables
cd /home/vreddy1/Desktop/Projects/scripts
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the live deep dive script using venv python
./venv/bin/python vc-deepdive/scratch/run_live_deepdive.py

# Send the generated report to Slack using send_slack.py
./venv/bin/python send_slack.py --webhook-url "https://hooks.slack.com/services/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" --file vc-deepdive/daily_vc_deepdive_report.md
