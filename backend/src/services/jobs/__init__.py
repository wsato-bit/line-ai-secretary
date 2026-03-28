"""Scheduled job definitions for Cloud Scheduler / Cloud Tasks.

Jobs are triggered by HTTP POST requests from Cloud Scheduler.
Each job endpoint is protected by a shared secret or service account auth.

Job Registry:
    - morning-summary:    Runs daily, per-user configured time (default 07:00 JST)
    - event-reminders:    Runs every 5 minutes, checks upcoming events
    - unreplied-reminders: Runs daily (e.g. 09:00 JST), checks overdue unreplied items

Cloud Scheduler cron expressions (Asia/Tokyo):
    morning-summary:     */5 6-9 * * *    (every 5min during 06:00-09:59)
    event-reminders:     */5 * * * *       (every 5 minutes)
    unreplied-reminders: 0 9 * * *         (daily at 09:00)
"""

JOB_REGISTRY = {
    "morning-summary": {
        "description": "Send morning summary to users at their configured time",
        "cron": "*/5 6-9 * * *",
        "timezone": "Asia/Tokyo",
    },
    "event-reminders": {
        "description": "Check upcoming events and send reminders",
        "cron": "*/5 * * * *",
        "timezone": "Asia/Tokyo",
    },
    "unreplied-reminders": {
        "description": "Send reminders for overdue unreplied items",
        "cron": "0 9 * * *",
        "timezone": "Asia/Tokyo",
    },
}
