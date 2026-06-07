#!/bin/bash

# Slack Alert Script for Systemd
# Usage: slack_alert.sh "ServiceName"

SERVICE_NAME=$1
WEBHOOK_URL=$(grep "^SLACK_WEBHOOK_SYSTEM_ALERTS=" /home/vreddy1/Desktop/Projects/scripts/.env | cut -d'=' -f2-)
if [ -z "$WEBHOOK_URL" ]; then
    WEBHOOK_URL=$(grep "^SLACK_WEBHOOK_URL=" /home/vreddy1/Desktop/Projects/scripts/.env | cut -d'=' -f2-)
fi

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service_name>"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: SLACK_WEBHOOK_URL not found in scripts/.env"
    exit 1
fi

# Gather failure details
STATUS=$(systemctl --user status "$SERVICE_NAME")
LOGS=$(journalctl --user -u "$SERVICE_NAME" -n 20 --no-pager)
HOSTNAME=$(hostname)
DATE=$(date)

# Build JSON payload
PAYLOAD=$(cat <<EOF
{
  "text": "🔴 *Systemd Service Failure Alert*",
  "attachments": [
    {
      "color": "#ff0000",
      "fields": [
        { "title": "Service", "value": "$SERVICE_NAME", "short": true },
        { "title": "Host", "value": "$HOSTNAME", "short": true },
        { "title": "Time", "value": "$DATE", "short": false }
      ],
      "text": "*Last 20 log lines:*\n\`\`\`$LOGS\`\`\`"
    }
  ]
}
EOF
)

# Send to Slack
curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$WEBHOOK_URL" > /dev/null
