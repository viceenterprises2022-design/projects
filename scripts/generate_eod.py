#!/usr/bin/env python3
import json
import subprocess
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running cmd: {cmd}\nStderr: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def fetch_all_issues():
    all_issues = []
    offset = 0
    limit = 100
    while True:
        print(f"Fetching issues offset {offset}...")
        raw = run_cmd(f"multica issue list --limit {limit} --offset {offset} --output json")
        if not raw:
            break
        try:
            data = json.loads(raw)
        except Exception as e:
            print(f"JSON decode error for issues at offset {offset}: {e}", file=sys.stderr)
            break
        issues = data.get("issues", [])
        if not issues:
            break
        all_issues.extend(issues)
        if len(issues) < limit:
            break
        offset += len(issues)
    return all_issues

def main():
    # Allow overriding the date via command line argument
    if len(sys.argv) > 1:
        today_str = sys.argv[1]
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Generating EOD Report for date: {today_str}")

    print("Fetching projects from Multica...")
    projects_raw = run_cmd("multica project list --output json")
    if not projects_raw:
        sys.exit("Failed to fetch projects")
    projects = json.loads(projects_raw)

    print("Fetching all issues from Multica...")
    issues = fetch_all_issues()
    print(f"Fetched {len(issues)} issues in total.")

    print("Fetching agents from Multica...")
    agents_raw = run_cmd("multica agent list --output json")
    if not agents_raw:
        sys.exit("Failed to fetch agents")
    agents = json.loads(agents_raw)

    # Maps
    project_map = {p["id"]: p for p in projects}
    agent_map = {a["id"]: a for a in agents}

    # 1. Projects and tasks summary
    project_summaries = []
    for p in projects:
        project_summaries.append(
            f"• *{p['title']}* (Status: {p['status']}) — {p['done_count']}/{p['issue_count']} issues completed"
        )
    
    # 2. Tasks completed today (either done or in_review)
    completed_today = []
    for i in issues:
        if i["status"] in ["done", "in_review"]:
            if i["identifier"] == "ALP-759":
                continue
            updated_at = i.get("updated_at", "")
            # We check if updated_at matches today's date
            if updated_at.startswith(today_str):
                completed_today.append(i)

    completed_details = []
    for i in completed_today:
        proj_id = i.get("project_id")
        proj_title = project_map.get(proj_id, {}).get("title") if proj_id else "None"
        assignee_id = i.get("assignee_id")
        assignee_name = agent_map.get(assignee_id, {}).get("name") if assignee_id else "Unassigned"
        
        # Get details from latest comment if possible
        comments_raw = run_cmd(f"multica issue comment list {i['id']} --output json")
        summary_text = "No detail comment found."
        if comments_raw:
            try:
                comments = json.loads(comments_raw)
                if comments:
                    # Get the latest comment
                    latest_comment = comments[-1].get("content", "")
                    
                    # Clean up active memories boilerplate
                    active_memories_phrases = [
                        "modes/memories are active",
                        "Caveman Ultra Mode",
                        "Graphify",
                        "Mempalace",
                        "Wozcode",
                        "RTK",
                        "###"
                    ]
                    
                    # Clean up or extract key info
                    lines = latest_comment.split("\n")
                    summary_lines = []
                    for line in lines:
                        if any(phrase in line for phrase in active_memories_phrases):
                            continue
                        if line.strip().startswith(("-", "*", "|", "#", "•", "1.", "2.", "3.", "4.", "5.")):
                            summary_lines.append(line.strip())
                        elif any(k in line for k in ["Spot Price", "Overall Signal", "LTP", "Price (USD)", "Asset", "Spot LTP"]):
                            summary_lines.append(line.strip())
                    if summary_lines:
                        summary_text = "\n    ".join(summary_lines[:8]) + ("\n    ..." if len(summary_lines) > 8 else "")
                    else:
                        summary_text = latest_comment[:300] + ("..." if len(latest_comment) > 300 else "")
            except Exception as e:
                print(f"Error parsing comments for issue {i['id']}: {e}", file=sys.stderr)

        completed_details.append(
            f"• *{i.get('identifier')}*: {i['title']}\n"
            f"  - *Executed by*: {assignee_name}\n"
            f"  - *Project*: {proj_title}\n"
            f"  - *Key Output*:\n    {summary_text}"
        )

    # 3. New tasks logged today in backlog
    backlog_today = []
    for i in issues:
        if i["status"] == "backlog":
            created_at = i.get("created_at", "")
            if created_at.startswith(today_str):
                backlog_today.append(i)
    
    backlog_summaries = []
    if backlog_today:
        for i in backlog_today:
            proj_id = i.get("project_id")
            proj_title = project_map.get(proj_id, {}).get("title") if proj_id else "None"
            backlog_summaries.append(f"• *{i.get('identifier')}*: {i['title']} (Project: {proj_title})")
    else:
        backlog_summaries.append("• _No new backlog tasks created today._")

    # 4. In review / in progress
    in_review = []
    in_progress = []
    for i in issues:
        if i["status"] == "in_review":
            in_review.append(i)
        elif i["status"] == "in_progress":
            in_progress.append(i)

    in_review_summaries = []
    for i in in_review:
        assignee_id = i.get("assignee_id")
        assignee_name = agent_map.get(assignee_id, {}).get("name") if assignee_id else "Unassigned"
        in_review_summaries.append(f"• *{i.get('identifier')}*: {i['title']} (Assignee: {assignee_name})")

    in_progress_summaries = []
    for i in in_progress:
        assignee_id = i.get("assignee_id")
        assignee_name = agent_map.get(assignee_id, {}).get("name") if assignee_id else "Unassigned"
        in_progress_summaries.append(f"• *{i.get('identifier')}*: {i['title']} (Assignee: {assignee_name})")

    # Agent Statuses
    working_agents = [a['name'] for a in agents if a['status'] == 'working']
    idle_agents = [a['name'] for a in agents if a['status'] == 'idle']

    # Compile report
    report = []
    report.append("*1. Projects and Tasks Summary*")
    report.extend(project_summaries)
    report.append("")
    report.append("*2. Tasks Completed Today*")
    if completed_details:
        report.extend(completed_details)
    else:
        report.append("• _No tasks completed today._")
    report.append("")
    report.append("*3. New Tasks Logged Today (Backlog)*")
    report.extend(backlog_summaries)
    report.append("")
    report.append("*4. Value-Add Workspace Insights*")
    report.append(f"• *Active In-Review Tasks* ({len(in_review)}):")
    if in_review_summaries:
        report.extend(["  " + s for s in in_review_summaries])
    else:
        report.append("  _None_")
    report.append(f"• *Active In-Progress Tasks* ({len(in_progress)}):")
    if in_progress_summaries:
        report.extend(["  " + s for s in in_progress_summaries])
    else:
        report.append("  _None_")
    report.append(f"• *Agent Operations Status*:")
    report.append(f"  - *Active Working*: {', '.join(working_agents) if working_agents else 'None'}")
    report.append(f"  - *Idle/Standby*: {len(idle_agents)} agents (including daily-news-crawl, crypto-realtime-price, knowledge-agent, Deep Researcher Agent)")

    report_text = "\n".join(report)
    
    # Save report
    with open("eod_report.txt", "w") as f:
        f.write(report_text)
    
    print("\nGenerated report:")
    print(report_text)
    print("\nSending to Slack...")
    
    # Run send_slack.py
    slack_cmd = f"{sys.executable} send_slack.py --header \"AlphaEdge - EOD Report to Management\" --color info --file eod_report.txt"
    slack_res = run_cmd(slack_cmd)
    print("Slack script output:")
    print(slack_res)

if __name__ == "__main__":
    main()
