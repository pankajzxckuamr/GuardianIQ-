from datetime import datetime, timedelta
from croniter import croniter
import pytz

def calculate_next_run(schedule) -> datetime | None:
    tz = pytz.timezone(schedule.timezone)
    now = datetime.now(tz)
    if schedule.schedule_type == 'MANUAL': return None
    if schedule.schedule_type == 'ONE_TIME': return None  # already ran
    if schedule.schedule_type == 'DAILY': return (now + timedelta(days=1)).replace(hour=schedule.start_at.hour, minute=schedule.start_at.minute, second=0, microsecond=0)
    if schedule.schedule_type == 'WEEKLY': return now + timedelta(weeks=1)
    if schedule.schedule_type == 'MONTHLY': return now.replace(month=now.month % 12 + 1)
    if schedule.schedule_type == 'CRON':
        return croniter(schedule.cron_expression, now).get_next(datetime).replace(tzinfo=tz)
    if schedule.schedule_type == 'INTERVAL':
        interval_secs = schedule.metadata_json.get('interval_seconds', 3600) if schedule.metadata_json else 3600
        return now + timedelta(seconds=interval_secs)
