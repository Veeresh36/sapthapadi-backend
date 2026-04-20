# ─────────────────────────────────────────────────────────────────────
# plan_utils.py  — Drop this file in your app/ directory
# Then import in views.py:
#   from .plan_utils import get_plan_status, send_plan_expiry_warning_email
# ─────────────────────────────────────────────────────────────────────

from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from typing import Dict


PLAN_DURATIONS = {'free': 7, 'basic': 30, 'silver': 60, 'gold': 90}

# ── Re-use the same HTML wrapper from views.py ────────────────────────
def _html_wrap(title, body_html, cta_label=None, cta_url=None):
    cta_block = ""
    if cta_label and cta_url:
        cta_block = f"""
        <p style="text-align:center;margin:28px 0 0;">
          <a href="{cta_url}" style="display:inline-block;padding:12px 28px;border-radius:8px;
             background:#741014;color:#fff;font-weight:700;font-size:15px;text-decoration:none;">
            {cta_label}
          </a>
        </p>"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F0E8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr><td style="background:linear-gradient(135deg,#741014,#5a0c0f);padding:28px 32px;text-align:center;">
          <p style="margin:0 0 6px;font-size:28px;">🪔</p>
          <h1 style="margin:0;color:#E8C97A;font-size:22px;font-style:italic;font-family:Georgia,serif;">{title}</h1>
          <p style="margin:8px 0 0;color:rgba(255,255,255,0.5);font-size:11px;letter-spacing:0.25em;text-transform:uppercase;">Saptapadi Lingayat Matrimony</p>
        </td></tr>
        <tr><td style="padding:32px 32px 28px;color:#1f2937;font-size:14px;line-height:1.8;">
          {body_html}
          {cta_block}
        </td></tr>
        <tr><td style="padding:20px 32px;border-top:1px solid #f0ebe0;text-align:center;color:#9ca3af;font-size:11px;">
          © Saptapadi Lingayat Matrimony · This is an automated notification
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


# ─────────────────────────────────────────────────────────────────────
# PLAN STATUS UTILITY
# ─────────────────────────────────────────────────────────────────────

def get_plan_status(user) -> Dict:
    """
    Returns plan status dict for a Member instance.

    Keys:
      is_expired  : bool
      days_left   : int  (0 if expired)
      status      : "active" | "warning" | "critical" | "expired"
      plan        : str  (the plan key)
      plan_label  : str  (human label)
      expires_at  : datetime | None
    """
    from .models import Member  # local import to avoid circular

    PLAN_LABELS = {
        'free':   'Free Trial',
        'basic':  'Basic',
        'silver': 'Silver',
        'gold':   'Gold',
    }

    plan_key   = user.plan or 'free'
    plan_label = PLAN_LABELS.get(plan_key, plan_key.title())
    now        = timezone.now()

    # ── Brand-new user: no expiry set yet → treat as active free trial ──
    if not user.plan_expires_at:
        return {
            "is_expired":  False,
            "days_left":   PLAN_DURATIONS.get(plan_key, 7),
            "status":      "active",
            "plan":        plan_key,
            "plan_label":  plan_label,
            "expires_at":  None,
        }

    delta     = user.plan_expires_at - now
    days_left = max(delta.days, 0)

    if days_left <= 0:
        status_str = "expired"
    elif days_left <= 3:
        status_str = "critical"
    elif days_left <= 7:
        status_str = "warning"
    else:
        status_str = "active"

    return {
        "is_expired":  days_left <= 0,
        "days_left":   days_left,
        "status":      status_str,
        "plan":        plan_key,
        "plan_label":  plan_label,
        "expires_at":  user.plan_expires_at,
    }


# ─────────────────────────────────────────────────────────────────────
# PLAN ACCESS GATE
# Returns effective plan key — downgrades to 'free' if expired
# ─────────────────────────────────────────────────────────────────────

def get_effective_plan(user) -> str:
    from .models import Plan

    gender = (user.gender or "").lower()

    if gender == "female":
        gender_plan = Plan.objects.filter(free_for_female=True, status="Active").first()
        if gender_plan:
            return gender_plan.name.lower()

    if gender == "male":
        gender_plan = Plan.objects.filter(free_for_male=True, status="Active").first()
        if gender_plan:
            return gender_plan.name.lower()

    status = get_plan_status(user)
    if status["is_expired"] and user.plan != "free":
        return "free"
    return user.plan or "free"


# ─────────────────────────────────────────────────────────────────────
# EXPIRY WARNING EMAIL  (7-day + 3-day)
# ─────────────────────────────────────────────────────────────────────

def send_plan_expiry_warning_email(member, days_left: int) -> None:
    """
    Sends a plan-expiry warning email.
    days_left should be 7 or 3 (or whatever milestone triggered this).
    """
    plan_key   = member.plan
    plan_label = get_plan_status(member)["plan_label"]
    expires_on = member.plan_expires_at.strftime("%d %B %Y") if member.plan_expires_at else "soon"

    urgency_color = "#D32F2F" if days_left <= 3 else "#C5A059"
    urgency_icon  = "🚨" if days_left <= 3 else "⚠️"
    urgency_word  = "URGENT" if days_left <= 3 else "Reminder"

    renew_url = getattr(settings, 'SITE_URL', '#') + '/dashboard'

    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>

    <div style="margin:20px 0;padding:20px 24px;background:#FFF4F4;border-radius:14px;
                border-left:5px solid {urgency_color};text-align:center;">
      <p style="margin:0 0 6px;font-size:28px;">{urgency_icon}</p>
      <p style="margin:0 0 4px;font-weight:900;font-size:18px;color:{urgency_color};">
        {urgency_word}: Your {plan_label} Plan Expires in {days_left} Day{'s' if days_left != 1 else ''}!
      </p>
      <p style="margin:0;font-size:13px;color:#6b7280;">Expiry date: <strong>{expires_on}</strong></p>
    </div>

    <p>Your <strong>{plan_label}</strong> plan is about to expire. Once it expires, your account will
    revert to the <strong>Free Trial</strong> plan with limited access.</p>

    <div style="margin:20px 0;padding:16px 20px;background:#FDF5E4;border-radius:12px;">
      <p style="margin:0 0 10px;font-weight:700;color:#9A6B1A;">🔒 What you'll lose after expiry:</p>
      {'<p style="margin:3px 0;color:#374151;">👑 Unlimited profile views</p>' if plan_key == 'gold' else ''}
      {'<p style="margin:3px 0;color:#374151;">💌 30 interests per day</p>' if plan_key == 'gold' else ''}
      {'<p style="margin:3px 0;color:#374151;">💌 10 interests per day</p>' if plan_key == 'silver' else ''}
      {'<p style="margin:3px 0;color:#374151;">👁 150 profile views per day</p>' if plan_key == 'silver' else ''}
      {'<p style="margin:3px 0;color:#374151;">💌 3 interests per day</p>' if plan_key == 'basic' else ''}
      <p style="margin:3px 0;color:#374151;">📞 Contact details access</p>
      <p style="margin:3px 0;color:#374151;">🔍 Premium profile visibility</p>
    </div>

    <div style="margin:20px 0;padding:16px 20px;background:#E8F5E9;border-radius:12px;">
      <p style="margin:0 0 8px;font-weight:700;color:#2E7D32;">✅ Renew now and keep your benefits:</p>
      <p style="margin:3px 0;color:#374151;">• Same plan at the same price</p>
      <p style="margin:3px 0;color:#374151;">• No interruption to your matches</p>
      <p style="margin:4px 0 0;color:#374151;">• Your interests & shortlists are preserved</p>
    </div>

    <p style="color:#9ca3af;font-size:12px;">
      To renew, visit the Plans section in your dashboard, pay via UPI and upload the screenshot.
      Admin will activate within 2–6 hours.
    </p>"""

    subject  = f"{urgency_icon} Your {plan_label} Plan Expires in {days_left} Day{'s' if days_left != 1 else ''} — Renew Now"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Your {plan_label} plan expires in {days_left} day(s) on {expires_on}.\n"
        f"Please renew to keep your premium access.\n\n"
        f"Login: {getattr(settings, 'SITE_URL', '')}/dashboard\n\nSaptapadi Team"
    )
    html_msg = _html_wrap(
        f"Plan Expiring in {days_left} Day{'s' if days_left != 1 else ''} {urgency_icon}",
        body_html,
        "Renew My Plan →",
        renew_url,
    )

    try:
        msg = EmailMultiAlternatives(
            subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
        print(f"[EXPIRY EMAIL] Sent {days_left}-day warning to {member.email}")
    except Exception as e:
        print(f"[EXPIRY EMAIL] Failed for {member.email}: {e}")


def send_plan_expired_email(member) -> None:
    """Sent when a plan has just expired (triggered by the daily cron)."""
    plan_label = get_plan_status(member)["plan_label"]
    renew_url  = getattr(settings, 'SITE_URL', '#') + '/dashboard'

    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>

    <div style="margin:20px 0;padding:20px 24px;background:#FFF4F4;border-radius:14px;
                border-left:5px solid #D32F2F;text-align:center;">
      <p style="margin:0 0 4px;font-size:26px;">😔</p>
      <p style="margin:0;font-weight:900;font-size:17px;color:#D32F2F;">
        Your {plan_label} Plan Has Expired
      </p>
    </div>

    <p>Your account has been moved to the <strong>Free Trial</strong> plan.
    You still have access to basic features, but premium benefits are paused.</p>

    <div style="margin:20px 0;padding:16px 20px;background:#F9F6F1;border-radius:12px;">
      <p style="margin:0 0 8px;font-weight:700;color:#741014;">💡 Renew to restore full access:</p>
      <p style="margin:3px 0;color:#374151;">• Basic — ₹299 / 30 days</p>
      <p style="margin:3px 0;color:#374151;">• Silver — ₹499 / 60 days</p>
      <p style="margin:3px 0;color:#374151;">• Gold — ₹999 / 90 days</p>
    </div>

    <p>Your shortlisted profiles and interest history are safe and will be
    fully accessible once you renew.</p>"""

    subject  = f"Your {plan_label} Plan Has Expired — Renew to Continue | Saptapadi"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Your {plan_label} plan has expired. Renew at: {renew_url}\n\nSaptapadi Team"
    )
    html_msg = _html_wrap("Plan Expired 😔", body_html, "Renew Now →", renew_url)

    try:
        msg = EmailMultiAlternatives(
            subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
        print(f"[EXPIRY EMAIL] Expired notice sent to {member.email}")
    except Exception as e:
        print(f"[EXPIRY EMAIL] Expired notice failed for {member.email}: {e}")