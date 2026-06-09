#!/bin/bash

# Define services to monitor
SERVICES=(
    "clawdi-serve-hermes.service"
    "clawdi-serve-claude_code.service"
    "clawdi-serve-codex.service"
    "clawdi-serve-antigravity.service"
    "multica-daemon.service"

    "agentmemory-backend.service"
    "agentmemory-ui.service"
    "gbrain-autopilot.service"
    "projects-git-autosync.service"
)

echo "--- Daemon Status Dashboard ---"
printf "%-35s | %-15s | %-10s\n" "Service Name" "Status" "Uptime"
echo "----------------------------------------------------------------------"

for svc in "${SERVICES[@]}"; do
    STATUS=$(systemctl --user is-active "$svc" 2>/dev/null)
    UPTIME=$(systemctl --user show "$svc" -p ActiveEnterTimestamp | cut -d'=' -f2)
    
    if [ "$STATUS" == "active" ]; then
        STATUS_COLOR="\e[32mACTIVE\e[0m"
    else
        STATUS_COLOR="\e[31m$STATUS\e[0m"
    fi
    
    printf "%-35s | %-24b | %-20s\n" "$svc" "$STATUS_COLOR" "${UPTIME:-N/A}"
done

echo ""
echo "--- Process Check (Grep) ---"
ps -ef | grep -E "hermes|multica|agentmemory|gbrain" | grep -v grep | head -n 10
