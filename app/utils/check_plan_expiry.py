# app/management/commands/check_plan_expiry.py
#
# SETUP:
#   mkdir -p app/management/commands
#   touch app/management/__init__.py
#   touch app/management/commands/__init__.py
#   # then put this file at app/management/commands/check_plan_expiry.py
#
# RUN MANUALLY:
#   python manage.py check_plan_expiry
#
# SCHEDULE (add to crontab — runs every day at 9 AM):
#   0 9 * * * /path/to/venv/bin/python /path/to/manage.py check_plan_expiry >> /var/log/plan_expiry.log 2>&1
#
# Or with Celery beat — add to CELERY_BEAT_SCHEDULE in settings.py:
#   'check-plan-expiry': {
#       'task': 'app.tasks.check_plan_expiry',
#       'schedule': crontab(hour=9, minute=0),
#   }

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Check plan expiry dates and send warning/expired emails to members."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would happen without actually sending emails.',
        )

    def handle(self, *args, **options):
        from app.models import Member
        from app.plan_utils import (
            send_plan_expiry_warning_email,
            send_plan_expired_email,
        )

        dry_run = options['dry_run']
        now     = timezone.now()

        # ── Target windows ─────────────────────────────────────────────
        # We check: expires in exactly 7 days  OR  exactly 3 days  OR  today
        # "exactly" = within a 24-hour window so daily cron doesn't miss it

        day_7_start  = now + timedelta(days=6, hours=23, minutes=59, seconds=59)
        day_7_end    = now + timedelta(days=7, hours=23, minutes=59, seconds=59)

        day_3_start  = now + timedelta(days=2, hours=23, minutes=59, seconds=59)
        day_3_end    = now + timedelta(days=3, hours=23, minutes=59, seconds=59)

        # Expired: plan_expires_at is in the past and status still 'active'
        # (we don't re-notify already-rejected/pending accounts)
        active_members = Member.objects.filter(status='active').exclude(plan='free')

        sent_7   = 0
        sent_3   = 0
        expired  = 0

        for member in active_members:
            exp = member.plan_expires_at
            if not exp:
                continue

            # ── 7-day warning ──────────────────────────────────────────
            if day_7_start <= exp <= day_7_end:
                days_left = (exp - now).days + 1
                self.stdout.write(f"[7-DAY]  {member.email}  expires {exp.date()}  ({days_left} days)")
                if not dry_run:
                    send_plan_expiry_warning_email(member, days_left=7)
                sent_7 += 1

            # ── 3-day warning ──────────────────────────────────────────
            elif day_3_start <= exp <= day_3_end:
                days_left = (exp - now).days + 1
                self.stdout.write(f"[3-DAY]  {member.email}  expires {exp.date()}  ({days_left} days)")
                if not dry_run:
                    send_plan_expiry_warning_email(member, days_left=3)
                sent_3 += 1

            # ── Just expired (within last 24 h) ───────────────────────
            elif exp < now and exp > now - timedelta(hours=24):
                self.stdout.write(f"[EXPIRED] {member.email}  expired {exp.date()}")
                if not dry_run:
                    # Mark member as expired in DB
                    member.status = 'expired'
                    member.is_active = False
                    member.save(update_fields=['status', 'is_active'])
                    send_plan_expired_email(member)
                expired += 1

        summary = (
            f"\n✅ Done {'(DRY RUN) ' if dry_run else ''}"
            f"— 7-day warnings: {sent_7} | 3-day warnings: {sent_3} | expired: {expired}"
        )
        self.stdout.write(self.style.SUCCESS(summary))