# views.py — Saptapadi Lingayat Matrimony
# Full backend with email notifications:
#   1. New user registration → welcome email (with password reminder)
#   2. Upgrade plan request → pending notification to user + alert to admin
#   3. Admin approves upgrade → activation email to user

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.generics import RetrieveAPIView
from django.utils import timezone
from django.db.models import Q, Case, When, IntegerField
from datetime import timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from io import BytesIO

from .models import Member, ContactInquiry, SuccessStory, AdminUser, MemberInterest, MemberShortlist, Match, Plan, Branch

from .serializers import (
    MemberRegistrationSerializer, MemberAdminSerializer, AdminUserSerializer,
    ContactInquirySerializer, SuccessStorySerializer, MemberPublicSerializer,
    MemberProfileSerializer, MemberInterestSerializer, MatchSerializer, PlanSerializer, BranchMemberSerializer, BranchSerializer,
)

PLAN_DURATIONS = {'free': 7, 'basic': 30, 'silver': 60, 'gold': 90}
ADMIN_EMAIL    = getattr(settings, 'ADMIN_NOTIFY_EMAIL', settings.DEFAULT_FROM_EMAIL)


# ─────────────────────────────────────────────────────────────────────
# EMAIL HELPERS
# ─────────────────────────────────────────────────────────────────────

def _html_wrap(title, body_html, cta_label=None, cta_url=None):
    """Minimal responsive HTML email wrapper."""
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
        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#741014,#5a0c0f);padding:28px 32px;text-align:center;">
          <p style="margin:0 0 6px;font-size:28px;">🪔</p>
          <h1 style="margin:0;color:#E8C97A;font-size:22px;font-style:italic;font-family:Georgia,serif;">{title}</h1>
          <p style="margin:8px 0 0;color:rgba(255,255,255,0.5);font-size:11px;letter-spacing:0.25em;text-transform:uppercase;">Saptapadi Lingayat Matrimony</p>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:32px 32px 28px;color:#1f2937;font-size:14px;line-height:1.8;">
          {body_html}
          {cta_block}
        </td></tr>
        <!-- Footer -->
        <tr><td style="padding:20px 32px;border-top:1px solid #f0ebe0;text-align:center;color:#9ca3af;font-size:11px;">
          © Saptapadi Lingayat Matrimony · This is an automated notification
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def send_welcome_email(member, plain_password=None):
    """
    Sent to new member on registration.
    Reminds them of their login credentials.
    """
    password_note = f"""
    <div style="margin:20px 0;padding:16px 20px;background:#FDF5E4;border-radius:10px;border-left:4px solid #C5A059;">
      <p style="margin:0 0 6px;font-weight:700;color:#9A6B1A;">🔑 Your Login Credentials</p>
      <p style="margin:0;color:#374151;">Email: <strong>{member.email}</strong></p>
      <p style="margin:4px 0 0;color:#374151;">Password: <strong>{plain_password or "the password you set during registration"}</strong></p>
      <p style="margin:8px 0 0;font-size:12px;color:#9ca3af;">Please keep this safe and do not share it with anyone.</p>
    </div>""" if plain_password else f"""
    <div style="margin:20px 0;padding:16px 20px;background:#FDF5E4;border-radius:10px;border-left:4px solid #C5A059;">
      <p style="margin:0 0 4px;font-weight:700;color:#9A6B1A;">🔑 Login Details</p>
      <p style="margin:0;color:#374151;">Email: <strong>{member.email}</strong></p>
      <p style="margin:4px 0 0;font-size:12px;color:#9ca3af;">Use the password you set during registration.</p>
    </div>"""

    rel = getattr(member, 'profile_for', 'Self')
    
    greeting = f"Namaskara <strong>{member.full_name}</strong> 🙏"
    if rel != 'Self':
        greeting = f"Namaskara, account for <strong>{member.full_name}</strong> ({rel}) has been created 🙏"
    
    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>
    <p>Welcome to <strong>Saptapadi Lingayat Matrimony</strong>! Your registration has been received and is currently <strong>pending admin approval</strong>.</p>
    {password_note}
    <div style="margin:20px 0;padding:16px 20px;background:#E8F5E9;border-radius:10px;">
      <p style="margin:0 0 6px;font-weight:700;color:#2E7D32;">✅ What happens next?</p>
      <p style="margin:0;color:#374151;">1. Our team will review your registration within 24 hours.</p>
      <p style="margin:4px 0 0;color:#374151;">2. You'll receive a confirmation email once your account is activated.</p>
      <p style="margin:4px 0 0;color:#374151;">3. Login and complete your profile to attract the best matches!</p>
    </div>
    <p style="color:#9ca3af;font-size:12px;">If you did not register on our platform, please ignore this email.</p>"""

    subject  = "Welcome to Saptapadi Matrimony — Your Registration is Under Review"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Welcome to Saptapadi Lingayat Matrimony!\n"
        f"Your registration is under review. Login with: {member.email}\n\n"
        f"You'll get another email once approved.\n\nSaptapadi Team"
    )
    html_msg = _html_wrap("Welcome to Saptapadi! 🎉", body_html, "Visit Website", getattr(settings, 'SITE_URL', '#'))
    try:
        msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email])
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Welcome email failed: {e}")


def send_upgrade_request_email(member, plan_key):
    """Sent to user after they submit a plan upgrade request."""
    plan_labels = {'basic':'Basic (₹299)', 'silver':'Silver (₹499)', 'gold':'Gold (₹999)'}
    plan_label  = plan_labels.get(plan_key, plan_key.title())

    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong>,</p>
    <p>We have received your plan upgrade request to <strong>{plan_label}</strong>.</p>
    <div style="margin:20px 0;padding:16px 20px;background:#FDF5E4;border-radius:10px;border-left:4px solid #C5A059;">
      <p style="margin:0 0 6px;font-weight:700;color:#9A6B1A;">⏳ Verification in Progress</p>
      <p style="margin:0;color:#374151;">Our admin team is reviewing your payment screenshot.</p>
      <p style="margin:6px 0 0;color:#374151;">⏱ Typical approval time: <strong>2–6 hours</strong></p>
    </div>
    <p>Once your payment is verified, your account will be upgraded and you'll receive a confirmation email with your new plan benefits.</p>
    <p style="color:#9ca3af;font-size:12px;">If you did not initiate this request, please contact us immediately.</p>"""

    subject  = f"Plan Upgrade Request Received — {plan_label} | Saptapadi"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Your upgrade request to {plan_label} has been received.\n"
        f"Our team will verify your payment within 2-6 hours.\n"
        f"You'll receive a confirmation email once approved.\n\nSaptapadi Team"
    )
    html_msg = _html_wrap("Plan Upgrade Requested 💎", body_html)
    try:
        msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email])
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Upgrade request email failed: {e}")


def send_upgrade_approved_email(member):
    """Sent to user when admin approves their plan upgrade."""
    plan_key   = member.plan
    plan_label = PLANS_META.get(plan_key, {}).get('label', plan_key.title())
    expires    = member.plan_expires_at.strftime("%d %B %Y") if member.plan_expires_at else "N/A"

    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🎉</p>
    <p>Your plan has been successfully upgraded! Welcome to the <strong>{plan_label}</strong> experience.</p>
    <div style="margin:20px 0;padding:20px 24px;background:#E8F5E9;border-radius:12px;border-left:4px solid #4CAF50;">
      <p style="margin:0 0 10px;font-weight:700;color:#2E7D32;font-size:16px;">✅ Plan Activated: {plan_label}</p>
      <p style="margin:0;color:#374151;">Valid until: <strong>{expires}</strong></p>
    </div>
    <div style="margin:20px 0;padding:16px 20px;background:#F9F6F1;border-radius:10px;">
      <p style="margin:0 0 8px;font-weight:700;color:#741014;">🎯 Your New Benefits</p>
      {'<p style="margin:3px 0;color:#374151;">👑 Unlimited profile views</p>' if plan_key == 'gold' else ''}
      {'<p style="margin:3px 0;color:#374151;">💌 Up to 30 interests per day</p>' if plan_key == 'gold' else ''}
      {'<p style="margin:3px 0;color:#374151;">💌 Up to 10 interests per day</p>' if plan_key == 'silver' else ''}
      {'<p style="margin:3px 0;color:#374151;">👁 150 profile views per day</p>' if plan_key == 'silver' else ''}
      <p style="margin:3px 0;color:#374151;">📞 Contact details unlocked after mutual match</p>
      <p style="margin:3px 0;color:#374151;">🔍 Access to all profession profiles</p>
    </div>
    <p>Login now and start connecting with compatible matches!</p>"""

    subject  = f"🎉 Plan Activated — {plan_label} | Saptapadi Matrimony"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Your {plan_label} plan has been activated!\n"
        f"Valid until: {expires}\n\n"
        f"Login now to enjoy your new benefits.\n\nSaptapadi Team"
    )
    html_msg = _html_wrap(f"{plan_label} Plan Activated! 🎉", body_html, "Go to Dashboard", getattr(settings, 'SITE_URL', '#') + '/dashboard')
    try:
        msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email])
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Upgrade approved email failed: {e}")


def send_admin_upgrade_alert(member, plan_key):
    """Notifies admin email when a new upgrade request comes in."""
    plan_label = plan_key.title()
    body_html  = f"""
    <p>A member has submitted a plan upgrade request and is awaiting your approval.</p>
    <div style="margin:20px 0;padding:16px 20px;background:#F9F6F1;border-radius:10px;">
      <p style="margin:0 0 6px;font-weight:700;color:#741014;">Member Details</p>
      <p style="margin:0;color:#374151;">Name: <strong>{member.full_name}</strong></p>
      <p style="margin:4px 0;color:#374151;">Email: <strong>{member.email}</strong></p>
      <p style="margin:4px 0;color:#374151;">Phone: <strong>{member.phone}</strong></p>
      <p style="margin:4px 0;color:#374151;">Requested Plan: <strong>{plan_label}</strong></p>
    </div>
    <p>Please login to the admin panel to review the payment screenshot and approve or reject the request.</p>"""

    subject  = f"[Admin] New Upgrade Request — {member.full_name} → {plan_label}"
    text_msg = f"New upgrade request from {member.full_name} ({member.email}) for {plan_label} plan. Please review in admin panel."
    html_msg = _html_wrap("New Plan Upgrade Request ⚡", body_html, "Open Admin Panel", getattr(settings, 'ADMIN_URL', '#'))
    try:
        msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, [ADMIN_EMAIL])
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Admin alert email failed: {e}")


def send_account_approved_email(member):
    """Sent when admin approves a new registration."""
    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>
    <p>Great news! Your Saptapadi Lingayat Matrimony account has been <strong>approved and activated</strong>.</p>
    <div style="margin:20px 0;padding:16px 20px;background:#E8F5E9;border-radius:10px;">
      <p style="margin:0 0 6px;font-weight:700;color:#2E7D32;">✅ Account Activated</p>
      <p style="margin:0;color:#374151;">You can now login and explore profiles.</p>
      <p style="margin:4px 0 0;color:#374151;">Login Email: <strong>{member.email}</strong></p>
    </div>
    <div style="margin:20px 0;padding:16px 20px;background:#FDF5E4;border-radius:10px;">
      <p style="margin:0 0 6px;font-weight:700;color:#9A6B1A;">💡 Pro Tips</p>
      <p style="margin:0;color:#374151;">• Complete your profile to get 3× more matches</p>
      <p style="margin:4px 0;color:#374151;">• Add a clear profile photo</p>
      <p style="margin:4px 0 0;color:#374151;">• Set your partner preferences</p>
    </div>
    <p>We wish you a blessed journey towards your sacred union! 🪔</p>"""

    subject  = "Your Account is Approved — Welcome to Saptapadi! 🎉"
    text_msg = f"Namaskara {member.full_name},\n\nYour account has been approved!\nLogin with: {member.email}\n\nSaptapadi Team"
    html_msg = _html_wrap("Account Approved! 🎉", body_html, "Login Now", getattr(settings, 'SITE_URL', '#') + '/login')
    try:
        msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email])
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Account approved email failed: {e}")

from django.core.mail import send_mail
from django.conf import settings
from typing import NoReturn


from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_account_rejected_email(member) -> None:
    subject: str = "⚠️ Account Update — Saptapadi Matrimony"

    # ── TEXT VERSION (fallback) ─────────────────────────
    text_msg: str = (
        f"Namaskara {member.full_name},\n\n"
        "We regret to inform you that your account request has been rejected.\n"
        "For assistance, please contact support.\n\n"
        "Saptapadi Team"
    )

    # ── HTML BODY (PREMIUM UI) ─────────────────────────
    body_html: str = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>

    <p>We regret to inform you that your account request has been 
    <strong style="color:#D32F2F;">not approved</strong> at this time.</p>

    <div style="margin:20px 0;padding:18px 22px;background:#FFF4F4;
                border-radius:12px;border-left:4px solid #D32F2F;">
        <p style="margin:0 0 8px;font-weight:700;color:#B71C1C;">
            ⚠️ Application Status
        </p>
        <p style="margin:0;color:#374151;">
            Your registration did not meet our current verification requirements.
        </p>
    </div>

    <div style="margin:20px 0;padding:16px 20px;background:#F9F6F1;
                border-radius:10px;">
        <p style="margin:0 0 8px;font-weight:700;color:#741014;">
            💡 What you can do next
        </p>
        <p style="margin:3px 0;color:#374151;">• Verify your details carefully</p>
        <p style="margin:3px 0;color:#374151;">• Ensure correct information is provided</p>
        <p style="margin:3px 0;color:#374151;">• Contact support if you believe this is an error</p>
    </div>

    <p style="margin-top:16px;">
        If you have any questions, feel free to reach out to our support team.
    </p>

    <p style="color:#9ca3af;font-size:12px;">
        This is an automated message. Please do not reply directly.
    </p>
    """

    # ── WRAP WITH YOUR PREMIUM TEMPLATE ─────────────────
    html_msg: str = _html_wrap(
        "Account Update ⚠️",
        body_html,
        "Contact Support",
        getattr(settings, "SITE_URL", "#") + "/contact"
    )

    # ── SEND EMAIL ─────────────────────────────────────
    try:
        msg = EmailMultiAlternatives(
            subject,
            text_msg,
            settings.DEFAULT_FROM_EMAIL,
            [member.email],
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=False)

    except Exception as e:
        print(f"[EMAIL] Reject email failed: {e}")


# Plan metadata for email helpers
PLANS_META = {
    'free':   {'label': 'Free Trial'},
    'basic':  {'label': 'Basic'},
    'silver': {'label': 'Silver'},
    'gold':   {'label': 'Gold'},
}


# ─────────────────────────────────────────────────────────────────────
# PERMISSIONS
# ─────────────────────────────────────────────────────────────────────

class IsAdminToken(BasePermission):
    def has_permission(self, request, view):
        auth = request.headers.get('Authorization', '').strip()
        if not auth.startswith('Bearer '):
            return False
        raw_token = auth.split(' ', 1)[1].strip()
        if not raw_token or raw_token in ('null', 'undefined', 'None'):
            return False
        try:
            token    = AccessToken(raw_token)
            is_admin = bool(token.get('is_admin'))
            return is_admin
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────
# PUBLIC
# ─────────────────────────────────────────────────────────────────────

def homepage(request):
    return render(request, 'index.html')


class ContactInquiryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactInquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Inquiry received. We'll respond within 24 hours."}, status=201)
        return Response(serializer.errors, status=400)


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class MemberRegisterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        plain_password = request.data.get('password', '')
        
        # mother_tongue is not a model field, remove it to avoid serializer errors
        data = request.data.copy()
        data.pop('mother_tongue', None)

        serializer = MemberRegistrationSerializer(data=data)
        if serializer.is_valid():
            member = serializer.save()
            send_welcome_email(member, plain_password=plain_password)
            return Response({"message": "Registration submitted. Pending admin approval."}, status=201)
        
        # Return detailed errors for debugging
        return Response(serializer.errors, status=400)


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import Any, Dict


class MemberLoginView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        member = (
            Member.objects.filter(email=email).first() or
            Member.objects.filter(member_id__iexact=email).first()
        )

        if not member:
            return Response({"error": "Invalid email or Member ID"}, status=401)

        if not member.check_password(password):
            return Response({"error": "Invalid password"}, status=401)

        if member.status not in ("active", "expired"):
            return Response(
                {"error": f"Account not approved yet. Status: {member.status}"},
                status=403
            )

        # ✅ for_user() sets sub claim correctly so JWTAuthentication resolves request.user
        refresh = RefreshToken.for_user(member)
        refresh["email"] = member.email
        refresh["is_admin"] = False

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "member": {
                "id": member.id,
                "email": member.email,
                "full_name": member.full_name,
                "plan": member.plan,
                "member_id": member.member_id,
                "status": member.status,
            }
        }, status=200)
# ─────────────────────────────────────────────────────────────────────
# ADMIN AUTH
# ─────────────────────────────────────────────────────────────────────

from typing import Any
from django.db import connection


def get_mysql_version() -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        version: Any = cursor.fetchone()
    return version[0]

print("mysql", get_mysql_version())



class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        email    = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({"error": "Email and password required."}, status=400)
        admin = AdminUser.objects.filter(email=email).first()
        if not admin or not admin.check_password(password):
            return Response({"error": "Invalid credentials."}, status=401)
        if not admin.is_active:
            return Response({"error": "Account is disabled."}, status=403)
        refresh = RefreshToken()
        refresh['user_id']   = admin.pk
        refresh['email']     = admin.email
        refresh['full_name'] = admin.full_name
        refresh['role']      = admin.role
        refresh['is_admin']  = True
        return Response({
            "access": str(refresh.access_token), "refresh": str(refresh),
            "admin": {"id": admin.id, "full_name": admin.full_name, "email": admin.email, "role": admin.role},
        })


# ─────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────

class DashboardStatsView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        members = Member.objects.all()
        return Response({
            "total": members.count(), "active": members.filter(status='active').count(),
            "pending": members.filter(status='pending').count(),
            "rejected": members.filter(status='rejected').count(),
            "expired":  members.filter(status='expired').count(),
            "plans": {k: members.filter(plan=k).count() for k in ['free','basic','silver','gold']},
        })


# ─────────────────────────────────────────────────────────────────────
# ADMIN MEMBERS
# ─────────────────────────────────────────────────────────────────────

class MemberListView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        qs = Member.objects.select_related('added_by_branch').all()
        s  = request.query_params.get('status')
        p  = request.query_params.get('plan')
        q  = request.query_params.get('search')
        if s: qs = qs.filter(status=s)
        if p: qs = qs.filter(plan=p)
        if q: qs = qs.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
        return Response(MemberAdminSerializer(qs, many=True).data)


class MemberDetailView(APIView):
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try: return Member.objects.select_related('added_by_branch').get(pk=pk)
        except Member.DoesNotExist: return None

    def get(self, request, pk):
        member = self.get_object(pk)
        if not member: return Response({"error": "Not found."}, status=404)
        return Response(MemberAdminSerializer(member).data)

    def patch(self, request, pk):
        member = self.get_object(pk)
        if not member: return Response({"error": "Not found."}, status=404)
        action = request.data.get('action')

        if action == 'approve':
            is_upgrade = member.status == 'pending' and member.plan != 'free' and member.payment_screenshot
            member.status            = 'active'
            member.is_active         = True
            member.plan_activated_at = timezone.now()
            member.plan_expires_at   = timezone.now() + timedelta(days=PLAN_DURATIONS.get(member.plan, 30))
            member.upgrade_status    = 'approved'
            member.save()
            if is_upgrade:
                send_upgrade_approved_email(member)
            else:
                send_account_approved_email(member)
            return Response({"message": "Approved successfully"})

        elif action == 'reject':
            member.status         = 'rejected'
            member.is_active      = False
            member.upgrade_status = None
            member.save()
            send_account_rejected_email(member)
            return Response({"message": "Rejected successfully"})

        else:
            # ── General field update from admin dashboard edit ──
            INTEGER_FIELDS = {'exp_age_from', 'exp_age_to', 'brothers', 'sisters', 'height'}
            DATE_FIELDS    = {'date_of_birth'}

            EDITABLE_FIELDS = [
                'full_name', 'email', 'phone', 'gender', 'date_of_birth',
                'birth_time', 'birth_place', 'marital_status', 'location',
                'district', 'state', 'pincode', 'address', 'languages', 'bio',
                'religion', 'caste', 'gotra', 'raasi', 'nakshatra', 'house_deity',
                'height', 'complexion', 'blood_group', 'diet',
                'education', 'education_details', 'occupation', 'occupation_details',
                'profession', 'income', 'family_type', 'family_status',
                'father_name', 'father_occupation', 'mother_name', 'mother_occupation',
                'brothers', 'sisters',
                'exp_age_from', 'exp_age_to', 'exp_caste', 'exp_education',
                'exp_occupation', 'exp_income',
                'plan', 'status',
            ]

            for field in EDITABLE_FIELDS:
                if field not in request.data:
                    continue  # only update fields actually sent

                value = request.data[field]

                # Convert empty string → None for integer fields
                if field in INTEGER_FIELDS:
                    if value == '' or value is None:
                        value = None
                    else:
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            value = None

                # Convert empty string → None for date fields
                if field in DATE_FIELDS:
                    if value == '' or value is None:
                        value = None

                setattr(member, field, value)

            # Keep is_active in sync with status
            if 'status' in request.data:
                member.is_active = request.data['status'] == 'active'

            # Seed plan dates if activating for the first time
            if request.data.get('status') == 'active' and not member.plan_activated_at:
                member.plan_activated_at = timezone.now()
                member.plan_expires_at   = timezone.now() + timedelta(days=PLAN_DURATIONS.get(member.plan, 30))

            member.save()
            return Response(MemberAdminSerializer(member).data)

    def delete(self, request, pk):
        member = self.get_object(pk)
        if not member: return Response({"error": "Not found."}, status=404)
        member.delete()
        return Response(status=204)

    def delete(self, request, pk):
        member = self.get_object(pk)
        if not member: return Response({"error": "Not found."}, status=404)
        member.delete()
        return Response(status=204)


# ─────────────────────────────────────────────────────────────────────
# ADMIN INQUIRIES
# ─────────────────────────────────────────────────────────────────────

class ContactInquiryListView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        qs = ContactInquiry.objects.all()
        q  = request.query_params.get('search')
        if q: qs = qs.filter(Q(name__icontains=q) | Q(contact__icontains=q))
        return Response(ContactInquirySerializer(qs, many=True).data)


class ContactInquiryDetailView(APIView):
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try: return ContactInquiry.objects.get(pk=pk)
        except ContactInquiry.DoesNotExist: return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        return Response(ContactInquirySerializer(obj).data)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response(status=204)


# ─────────────────────────────────────────────────────────────────────
# ADMIN SUCCESS STORIES
# ─────────────────────────────────────────────────────────────────────

from rest_framework.parsers import JSONParser

class SuccessStoryListView(APIView):
    permission_classes = [IsAdminToken]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        qs = SuccessStory.objects.all()
        p  = request.query_params.get('plan')
        if p: qs = qs.filter(plan=p.lower())
        return Response(SuccessStorySerializer(qs, many=True).data)

    def post(self, request):
        serializer = SuccessStorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SuccessStoryDetailView(APIView):
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try: return SuccessStory.objects.get(pk=pk)
        except SuccessStory.DoesNotExist: return None

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        serializer = SuccessStorySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response(status=204)


# ─────────────────────────────────────────────────────────────────────
# ADMIN USERS
# ─────────────────────────────────────────────────────────────────────

class AdminUserListView(APIView):
    permission_classes = [IsAdminToken]
    def get(self, request):
        return Response(AdminUserSerializer(AdminUser.objects.all(), many=True).data)


class AdminUserCreateView(APIView):
    permission_classes = [IsAdminToken]
    def post(self, request):
        serializer = AdminUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try: return AdminUser.objects.get(pk=pk)
        except AdminUser.DoesNotExist: return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        return Response(AdminUserSerializer(obj).data)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        serializer = AdminUserSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj: return Response({"error": "Not found."}, status=404)
        obj.delete()
        return Response(status=204)


# ─────────────────────────────────────────────────────────────────────
# PROFILE SYSTEM
# ─────────────────────────────────────────────────────────────────────

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import QuerySet
from typing import Any


class ExploreProfilesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request):
        from .plan_utils import get_effective_plan
        from django.db.models import QuerySet
 
        user         = request.user
        eff_plan     = get_effective_plan(user)
 
        # Plans that can see all professions
        ALL_ACCESS   = ('silver', 'gold')
 
        qs = (
            Member.objects
            .exclude(id=user.id)
            .filter(status="active")
            .only(
                "id", "full_name", "gender", "date_of_birth",
                "profession", "occupation", "location",
                "education", "income", "raasi", "gotra",
                "height", "languages", "family_type",
                "bio", "plan", "profile_photo",
                "caste", "district", "state",
                "religion", "diet", "complexion",
                "marital_status", "nakshatra", "blood_group",
                "brothers", "sisters", "birth_time",
                "occupation_details"
            )
            .order_by("-registered_at")
        )
 
        # ── Gender filter ──────────────────────────────────────────────
        if user.gender:
            gender_map = {"male": "female", "female": "male"}
            target     = gender_map.get(user.gender.lower())
            if target:
                qs = qs.filter(gender__iexact=target)
 
        # ── Plan access filter ─────────────────────────────────────────
        # Free & Basic: only see free/basic profiles (NOT silver/gold)
        if eff_plan not in ALL_ACCESS:
            qs = qs.exclude(plan__in=('silver', 'gold'))
 
        serializer = MemberPublicSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class MyProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]
    parser_classes         = [MultiPartParser, FormParser]

    def get(self, request):
        serializer = MemberProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = MemberProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


# ─────────────────────────────────────────────────────────────────────
# INTEREST SYSTEM
# ─────────────────────────────────────────────────────────────────────

class InterestListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        interests  = MemberInterest.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        serializer = MemberInterestSerializer(interests, many=True, context={'request': request})
        return Response(serializer.data)


class SendInterestView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        receiver_id = request.data.get('receiver')
        if not receiver_id: return Response({"error": "Receiver required"}, status=400)
        try:
            receiver = Member.objects.get(id=receiver_id)
        except Member.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        if receiver == request.user:
            return Response({"error": "Cannot send to yourself"}, status=400)
        obj, created = MemberInterest.objects.get_or_create(sender=request.user, receiver=receiver)
        if not created:
            return Response({"error": "Already sent"}, status=400)
        request.user.interests_sent_today += 1
        request.user.save()
        return Response({"message": "Interest sent"})


class RespondInterestView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def patch(self, request, pk):
        action = request.data.get("action")
        try:
            interest = MemberInterest.objects.get(id=pk, receiver=request.user)
        except MemberInterest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        if action not in ["accepted", "declined"]:
            return Response({"error": "Invalid action"}, status=400)
        interest.status = action
        interest.save()
        return Response({"message": f"Interest {action}"})


# ─────────────────────────────────────────────────────────────────────
# SHORTLIST SYSTEM
# ─────────────────────────────────────────────────────────────────────

class ShortlistView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        shortlisted = MemberShortlist.objects.filter(member=request.user).select_related('target')
        targets     = [s.target for s in shortlisted]
        serializer  = MemberPublicSerializer(targets, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        target_id = request.data.get("target")
        try:
            target = Member.objects.get(id=target_id)
        except Member.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        existing = MemberShortlist.objects.filter(member=request.user, target=target).first()
        if existing:
            existing.delete()
            return Response({"message": "Removed from shortlist"})
        MemberShortlist.objects.create(member=request.user, target=target)
        return Response({"message": "Added to shortlist"})


ToggleShortlistView = ShortlistView


# ─────────────────────────────────────────────────────────────────────
# UPGRADE PLAN — submit request (pending admin approval)
# ─────────────────────────────────────────────────────────────────────

class UpgradePlanView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]
    parser_classes         = [MultiPartParser, FormParser]

    def post(self, request):
        user       = request.user
        plan       = request.data.get("plan")
        screenshot = request.FILES.get("payment_screenshot")

        if plan not in ["basic", "silver", "gold"]:
            return Response({"error": "Invalid plan"}, status=400)
        if not screenshot:
            return Response({"error": "Payment screenshot is required"}, status=400)

        # Store request — keep status pending until admin approves
        user.plan                = plan
        user.payment_screenshot  = screenshot
        user.status              = "pending"
        user.upgrade_status      = "pending"
        user.save()

        # Email user: confirmation of request
        send_upgrade_request_email(user, plan)
        # Email admin: alert to review
        send_admin_upgrade_alert(user, plan)

        return Response({"message": "Upgrade request submitted. Awaiting admin verification."})

    # Legacy PATCH (kept for backward compat, but no email)
    def patch(self, request):
        plan = request.data.get("plan")
        if plan not in PLAN_DURATIONS:
            return Response({"error": "Invalid plan"}, status=400)
        request.user.plan             = plan
        request.user.plan_activated_at = timezone.now()
        request.user.plan_expires_at   = timezone.now() + timedelta(days=PLAN_DURATIONS[plan])
        request.user.save()
        return Response({"message": f"Upgraded to {plan}"})


# ─────────────────────────────────────────────────────────────────────
# PROFILE DETAIL
# ─────────────────────────────────────────────────────────────────────

class ProfileDetailView(RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]
    queryset               = Member.objects.filter(status='active')
    serializer_class       = MemberPublicSerializer
    lookup_field           = "id"

    def get_serializer_context(self):
        return {'request': self.request}


# ─────────────────────────────────────────────────────────────────────
# MATCHES
# ─────────────────────────────────────────────────────────────────────

class MatchListCreateView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        matches = Match.objects.select_related('male', 'female').all().order_by('-created_at')
        return Response(MatchSerializer(matches, many=True).data)

    def post(self, request):
        serializer = MatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class MatchDetailView(APIView):
    permission_classes = [IsAdminToken]

    def patch(self, request, pk):
        match = Match.objects.get(pk=pk)
        serializer = MatchSerializer(match, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        Match.objects.filter(pk=pk).delete()
        return Response(status=204)


# ─────────────────────────────────────────────────────────────────────
# PLANS (Admin)
# ─────────────────────────────────────────────────────────────────────

class PlanListCreateView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        return Response(PlanSerializer(Plan.objects.all(), many=True).data)

    def post(self, request):
        serializer = PlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class PlanDetailView(APIView):
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try: return Plan.objects.get(pk=pk)
        except: return None

    def get(self, request, pk):
        plan = self.get_object(pk)
        if not plan: return Response({"error": "Not found."}, status=404)
        return Response(PlanSerializer(plan).data)

    def patch(self, request, pk):
        plan = self.get_object(pk)
        if not plan: return Response({"error": "Not found."}, status=404)
        serializer = PlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        plan = self.get_object(pk)
        if not plan: return Response({"error": "Not found."}, status=404)
        plan.delete()
        return Response(status=204)


class AdminPlanStatsView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        members = Member.objects.all()
        return Response({k: members.filter(plan=k).count() for k in ['free','basic','silver','gold']})


PlanStatsView = AdminPlanStatsView


class PublicPlansView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(status__iexact='Active').order_by('price')
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)


class PlanStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request):
        from .plan_utils import get_plan_status, get_effective_plan
 
        member = request.user
        ps     = get_plan_status(member)
        eff    = get_effective_plan(member)
 
        # Limits per effective plan
        LIMITS = {
            'free':   {'interests_per_day': 1,  'views_per_day': 20,  'can_see_all': False},
            'basic':  {'interests_per_day': 3,  'views_per_day': 50,  'can_see_all': False},
            'silver': {'interests_per_day': 10, 'views_per_day': 150, 'can_see_all': True},
            'gold':   {'interests_per_day': 30, 'views_per_day': -1,  'can_see_all': True},
        }
        limits = LIMITS.get(eff, LIMITS['free'])
        gender_offer = None
        if member.gender:
            from .models import Plan
            gender = member.gender.lower()
            field = "free_for_female" if gender == "female" else "free_for_male"
            offer_plan = Plan.objects.filter(**{field: True}, status="Active").first()
            if offer_plan:
                gender_offer = {
                    "label": offer_plan.gender_offer_label or f"Free {offer_plan.name} for you!",
                    "plan": offer_plan.name,
                }
 
        return Response({
            # Plan info
            "plan":             member.plan,
            "effective_plan":   eff,           # 'free' if expired
            "plan_label":       ps["plan_label"],
            "expires_at":       ps["expires_at"],
            "days_left":        ps["days_left"],
            "is_expired":       ps["is_expired"],
            "gender_offer": gender_offer,
 
            # Status string: "active" | "warning" | "critical" | "expired"
            "expiry_status":    ps["status"],
 
            # Access limits based on effective (possibly downgraded) plan
            "interests_per_day": limits["interests_per_day"],
            "views_per_day":     limits["views_per_day"],
            "can_see_all":       limits["can_see_all"],
 
            # Upgrade pending?
            "upgrade_status":   member.upgrade_status,
        })


# ─────────────────────────────────────────────────────────────────────
# ADMIN CREATE MEMBER
# ─────────────────────────────────────────────────────────────────────

class AdminCreateMemberView(APIView):
    permission_classes = [IsAdminToken]

    def post(self, request):
        data = request.data
        try:
            member = Member.objects.create(
                email=data.get("email"), full_name=data.get("full_name"), phone=data.get("phone"),
                gender=data.get("gender"), date_of_birth=data.get("date_of_birth"),
                religion=data.get("religion", "Lingayat"), caste=data.get("caste"),
                gotra=data.get("gotra"), raasi=data.get("raasi"), height=data.get("height"),
                education=data.get("education"), profession=data.get("profession"),
                income=data.get("income"), father_name=data.get("father_name"),
                mother_name=data.get("mother_name"), address=data.get("address"),
                plan=data.get("plan", "basic"), status=data.get("status", "pending"),
                location=data.get("location"), state=data.get("state"), pincode=data.get("pincode"),
            )
            if member.plan != 'free':
                member.plan_activated_at = timezone.now()
                member.plan_expires_at   = timezone.now() + timedelta(days=30)
                member.save()
            return Response({"id": member.id, "message": "Member created successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SuccessStory
from .serializers import SuccessStorySerializer


class PublicSuccessStoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        stories = (
            SuccessStory.objects
            .filter(status="Published")   # 🔥 KEY LOGIC
            .order_by("-submitted_on")
        )

        serializer = SuccessStorySerializer(stories, many=True)
        return Response(serializer.data)



## ADD THESE TO YOUR EXISTING views.py
## Also add Branch, BranchSerializer, BranchMemberSerializer to your imports


# ─────────────────────────────────────────────────────────────────────
# BRANCH PERMISSION
# ─────────────────────────────────────────────────────────────────────

class IsBranchToken(BasePermission):
    """Allows access only to authenticated branch operators."""
    def has_permission(self, request, view):
        auth = request.headers.get('Authorization', '').strip()
        if not auth.startswith('Bearer '):
            return False
        raw_token = auth.split(' ', 1)[1].strip()
        if not raw_token or raw_token in ('null', 'undefined', 'None'):
            return False
        try:
            token      = AccessToken(raw_token)
            is_branch  = bool(token.get('is_branch'))
            return is_branch
        except Exception:
            return False


class IsAdminOrBranchToken(BasePermission):
    """Allows admin OR branch token."""
    def has_permission(self, request, view):
        auth = request.headers.get('Authorization', '').strip()
        if not auth.startswith('Bearer '):
            return False
        raw_token = auth.split(' ', 1)[1].strip()
        if not raw_token or raw_token in ('null', 'undefined', 'None'):
            return False
        try:
            token = AccessToken(raw_token)
            return bool(token.get('is_admin')) or bool(token.get('is_branch'))
        except Exception:
            return False


def get_branch_from_token(request):
    """Extract Branch object from JWT token."""
    auth = request.headers.get('Authorization', '').strip()
    raw  = auth.split(' ', 1)[1].strip()
    token = AccessToken(raw)
    branch_id = token.get('branch_id')
    if not branch_id:
        return None
    try:
        return Branch.objects.get(pk=branch_id)
    except Branch.DoesNotExist:
        return None


# ─────────────────────────────────────────────────────────────────────
# BRANCH AUTH — Login
# ─────────────────────────────────────────────────────────────────────

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import AllowAny


class BranchLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email: str = request.data.get("email")
        password: str = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        branch = Branch.objects.filter(email=email).first()

        if not branch:
            return Response({"error": "Invalid email"}, status=401)

        if not branch.check_password(password):
            return Response({"error": "Invalid password"}, status=401)

        if branch.status != "active":
            return Response({"error": "Branch inactive"}, status=403)

        refresh = RefreshToken()
        refresh["branch_id"] = branch.id
        refresh["email"] = branch.email
        refresh["is_branch"] = True

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "branch": {
                "id": branch.id,
                "branch_name": branch.branch_name,
                "email": branch.email,
            }
        })

# ─────────────────────────────────────────────────────────────────────
# ADMIN — Manage Branches (CRUD)
# ─────────────────────────────────────────────────────────────────────

class AdminBranchListView(APIView):
    """Admin: list all branches + create new branch."""
    permission_classes = [IsAdminToken]

    def get(self, request):
        qs = Branch.objects.all()
        q  = request.query_params.get('search')
        s  = request.query_params.get('status')
        if q:
            from django.db.models import Q as DQ
            qs = qs.filter(
                DQ(branch_name__icontains=q) |
                DQ(branch_code__icontains=q) |
                DQ(contact_name__icontains=q) |
                DQ(email__icontains=q) |
                DQ(city__icontains=q)
            )
        if s:
            qs = qs.filter(status=s)
        return Response(BranchSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AdminBranchDetailView(APIView):
    """Admin: get / update / delete a single branch."""
    permission_classes = [IsAdminToken]

    def get_object(self, pk):
        try:
            return Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return None

    def get(self, request, pk):
        branch = self.get_object(pk)
        if not branch:
            return Response({"error": "Not found."}, status=404)
        return Response(BranchSerializer(branch).data)

    def patch(self, request, pk):
        branch = self.get_object(pk)
        if not branch:
            return Response({"error": "Not found."}, status=404)
        serializer = BranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        branch = self.get_object(pk)
        if not branch:
            return Response({"error": "Not found."}, status=404)
        branch.delete()
        return Response(status=204)


class AdminBranchToggleStatusView(APIView):
    """Admin: activate / deactivate a branch."""
    permission_classes = [IsAdminToken]

    def patch(self, request, pk):
        try:
            branch = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        branch.status    = 'inactive' if branch.status == 'active' else 'active'
        branch.is_active = branch.status == 'active'
        branch.save()
        return Response({"status": branch.status, "message": f"Branch {branch.status}"})


class AdminBranchMembersView(APIView):
    """Admin: view all members added by a specific branch."""
    permission_classes = [IsAdminToken]

    def get(self, request, pk):
        try:
            branch = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        members = Member.objects.filter(added_by_branch=branch)
        return Response(BranchMemberSerializer(members, many=True).data)


# ─────────────────────────────────────────────────────────────────────
# BRANCH — Self-service: add / view / edit their own members
# ─────────────────────────────────────────────────────────────────────

## ─────────────────────────────────────────────────────────────────────
## REPLACE the BranchMemberListView class in your views.py with this
## ─────────────────────────────────────────────────────────────────────

class BranchMemberListView(APIView):
    """Branch: list members THEY added + create new member."""
    permission_classes = [IsBranchToken]
    parser_classes     = [MultiPartParser, FormParser]

    def get(self, request):
        branch = get_branch_from_token(request)
        if not branch:
            return Response({"error": "Branch not found."}, status=404)
        qs = Member.objects.filter(added_by_branch=branch)
        q  = request.query_params.get('search')
        s  = request.query_params.get('status')
        p  = request.query_params.get('plan')
        if q:
            from django.db.models import Q as DQ
            qs = qs.filter(DQ(full_name__icontains=q) | DQ(email__icontains=q) | DQ(phone__icontains=q))
        if s:
            qs = qs.filter(status=s)
        if p:
            qs = qs.filter(plan=p)
        return Response(BranchMemberSerializer(qs, many=True).data)

    def post(self, request):
        branch = get_branch_from_token(request)
        if not branch:
            return Response({"error": "Branch not found."}, status=404)

        data = request.data
        try:
            # ── Parse payment fields safely ───────────────────────────────
            raw_amount    = data.get("payment_amount", "") or ""
            raw_confirmed = data.get("payment_confirmed", "false")

            try:
                payment_amount = float(raw_amount) if str(raw_amount).strip() else None
            except (ValueError, TypeError):
                payment_amount = None

            # Accept "true" / "True" / True / 1
            if isinstance(raw_confirmed, bool):
                payment_confirmed = raw_confirmed
            else:
                payment_confirmed = str(raw_confirmed).strip().lower() in ("true", "1", "yes")

            member = Member(
                email               = data.get("email"),
                full_name           = data.get("full_name"),
                phone               = data.get("phone"),
                gender              = data.get("gender", ""),
                date_of_birth       = data.get("date_of_birth") or None,
                religion            = data.get("religion", "Lingayat"),
                caste               = data.get("caste", ""),
                gotra               = data.get("gotra", ""),
                raasi               = data.get("raasi", ""),
                nakshatra           = data.get("nakshatra", ""),
                house_deity         = data.get("house_deity", ""),
                birth_time          = data.get("birth_time", ""),
                birth_place         = data.get("birth_place", ""),
                height              = data.get("height", ""),
                complexion          = data.get("complexion", ""),
                blood_group         = data.get("blood_group", ""),
                diet                = data.get("diet", ""),
                education           = data.get("education", ""),
                education_details   = data.get("education_details", ""),
                profession          = data.get("profession", ""),
                occupation          = data.get("occupation", ""),
                occupation_details  = data.get("occupation_details", ""),
                income              = data.get("income", ""),
                languages           = data.get("languages", ""),
                father_name         = data.get("father_name", ""),
                father_occupation   = data.get("father_occupation", ""),
                mother_name         = data.get("mother_name", ""),
                mother_occupation   = data.get("mother_occupation", ""),
                brothers            = data.get("brothers", ""),
                sisters             = data.get("sisters", ""),
                family_type         = data.get("family_type", ""),
                family_status       = data.get("family_status", ""),
                bio                 = data.get("bio", ""),
                location            = data.get("location", ""),
                district            = data.get("district", ""),
                state               = data.get("state", ""),
                pincode             = data.get("pincode", ""),
                address             = data.get("address", ""),
                marital_status      = data.get("marital_status", ""),
                plan                = data.get("plan", "free"),
                status              = "pending",

                # ── Payment fields ────────────────────────────────────────
                payment_reference   = data.get("payment_reference", "") or "",
                payment_upi_id      = data.get("payment_upi_id", "") or "",
                payment_amount      = payment_amount,
                payment_confirmed   = payment_confirmed,

                added_by_branch     = branch,
            )

            # Handle profile photo
            photo = request.FILES.get("profile_photo")
            if photo:
                member.profile_photo = photo

            # Set password
            raw_pass = data.get("password", "").strip() or "Member@123"
            member.set_password(raw_pass)
            member.save()

            return Response(
                {
                    "id":        member.id,
                    "member_id": member.member_id,
                    "message":   "Member added successfully",
                },
                status=201,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)


## ─────────────────────────────────────────────────────────────────────
## ALSO REPLACE BranchMemberDetailView.patch() — saves payment fields on edit too
## ─────────────────────────────────────────────────────────────────────

class BranchMemberDetailView(APIView):
    """Branch: get / edit a specific member THEY added."""
    permission_classes = [IsBranchToken]
    parser_classes     = [MultiPartParser, FormParser]

    def get_member(self, request, pk):
        branch = get_branch_from_token(request)
        if not branch:
            return None, Response({"error": "Branch not found."}, status=404)
        try:
            member = Member.objects.get(pk=pk, added_by_branch=branch)
            return member, None
        except Member.DoesNotExist:
            return None, Response({"error": "Member not found or not in your branch."}, status=404)

    def get(self, request, pk):
        member, err = self.get_member(request, pk)
        if err:
            return err
        return Response(BranchMemberSerializer(member).data)

    def patch(self, request, pk):
        member, err = self.get_member(request, pk)
        if err:
            return err
        data = request.data

        editable_text = [
            'full_name', 'phone', 'gender', 'date_of_birth', 'religion',
            'caste', 'gotra', 'raasi', 'height', 'education', 'profession',
            'occupation', 'income', 'father_name', 'mother_name', 'address',
            'location', 'district', 'state', 'pincode', 'marital_status', 'nakshatra',
            'bio', 'family_type', 'blood_group', 'diet', 'complexion', 'languages',
            'education_details', 'occupation_details', 'father_occupation',
            'mother_occupation', 'brothers', 'sisters', 'family_status',
            'house_deity', 'birth_time', 'birth_place',
            # payment text fields
            'payment_reference', 'payment_upi_id',
        ]

        for field in editable_text:
            if field in data:
                setattr(member, field, data[field])

        # ── Payment amount ────────────────────────────────────────────────
        if 'payment_amount' in data:
            try:
                member.payment_amount = float(data['payment_amount']) if data['payment_amount'] else None
            except (ValueError, TypeError):
                pass

        # ── Payment confirmed (checkbox → "true"/"false") ─────────────────
        if 'payment_confirmed' in data:
            raw = data['payment_confirmed']
            if isinstance(raw, bool):
                member.payment_confirmed = raw
            else:
                member.payment_confirmed = str(raw).strip().lower() in ("true", "1", "yes")

        # ── Photo ─────────────────────────────────────────────────────────
        photo = request.FILES.get("profile_photo")
        if photo:
            member.profile_photo = photo

        member.save()
        return Response(BranchMemberSerializer(member).data)

class BranchMeView(APIView):
    """Branch: get own profile."""
    permission_classes = [IsBranchToken]

    def get(self, request):
        branch = get_branch_from_token(request)
        if not branch:
            return Response({"error": "Not found."}, status=404)
        return Response(BranchSerializer(branch).data)


# ─────────────────────────────────────────────────────────────────────
# ADMIN — All members with branch info (for BranchPage overview)
# ─────────────────────────────────────────────────────────────────────

class AdminAllBranchMembersView(APIView):
    """Admin: all members across all branches, with branch attribution."""
    permission_classes = [IsAdminToken]

    def get(self, request):
        branch_id = request.query_params.get('branch')
        qs = Member.objects.select_related('added_by_branch').filter(
            added_by_branch__isnull=False
        )
        if branch_id:
            qs = qs.filter(added_by_branch_id=branch_id)
        return Response(BranchMemberSerializer(qs, many=True).data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # or your custom IsAdminToken
from .models import AppSettings
from .serializers import AppSettingsSerializer


class AdminAppSettingsView(APIView):
    permission_classes = [IsAdminToken]  # keep secure

    def get_object(self) -> AppSettings:
        obj, _ = AppSettings.objects.get_or_create(id=1)
        return obj

    def get(self, request):
        settings_obj = self.get_object()
        serializer = AppSettingsSerializer(settings_obj, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        settings_obj = self.get_object()
        serializer = AppSettingsSerializer(settings_obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


from rest_framework.permissions import AllowAny


class PublicAppSettingsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        settings = AppSettings.objects.first()

        if not settings:
            return Response({
                "upi_id": "",
                "qr_code_url": None
            })

        return Response({
            "upi_id": settings.upi_id,
            "qr_code_url": settings.qr_code.url if settings.qr_code else None
        })


# ── ADD THESE TO YOUR EXISTING views.py ──────────────────────────────────────
# 1. Add PasswordResetToken to your model import line:
#    from .models import Member, ..., PasswordResetToken
#
# 2. Paste both classes anywhere in views.py (near MemberLoginView is best)


# ─────────────────────────────────────────────────────────────────────
# FORGOT PASSWORD — Step 1: user submits email → receive reset link
# ─────────────────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()

        if not email:
            return Response({"error": "Email is required."}, status=400)

        # Always return a success-looking message to prevent email enumeration
        GENERIC_OK = {"message": "If this email is registered, you'll receive a reset link shortly."}

        try:
            member = Member.objects.get(email=email)
        except Member.DoesNotExist:
            return Response(GENERIC_OK)  # Don't reveal whether email exists

        if member.status != "active":
            # Silent fail — inactive accounts don't get reset links
            return Response(GENERIC_OK)

        # Invalidate any old unused tokens for this member
        from .models import PasswordResetToken
        PasswordResetToken.objects.filter(member=member, is_used=False).update(is_used=True)

        # Create fresh token
        reset_token = PasswordResetToken.objects.create(member=member)

        # Build reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        reset_url    = f"{frontend_url}/reset-password?token={reset_token.token}"

        # Send email
        _send_password_reset_email(member, reset_url)

        return Response(GENERIC_OK)


# ─────────────────────────────────────────────────────────────────────
# RESET PASSWORD — Step 2: user submits token + new password
# ─────────────────────────────────────────────────────────────────────

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .models import PasswordResetToken

        token_str    = request.data.get("token", "").strip()
        new_password = request.data.get("password", "").strip()
        confirm_pass = request.data.get("confirm_password", "").strip()

        # Validate inputs
        if not token_str:
            return Response({"error": "Reset token is required."}, status=400)
        if not new_password:
            return Response({"error": "New password is required."}, status=400)
        if len(new_password) < 8:
            return Response({"error": "Password must be at least 8 characters."}, status=400)
        if new_password != confirm_pass:
            return Response({"error": "Passwords do not match."}, status=400)

        # Validate token format (must be valid UUID)
        try:
            import uuid
            token_uuid = uuid.UUID(token_str)
        except ValueError:
            return Response({"error": "Invalid or expired reset link."}, status=400)

        # Look up token
        try:
            reset_token = PasswordResetToken.objects.select_related('member').get(token=token_uuid)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Invalid or expired reset link."}, status=400)

        # Check validity
        if not reset_token.is_valid:
            return Response(
                {"error": "This reset link has expired or already been used. Please request a new one."},
                status=400
            )

        # Apply new password
        member = reset_token.member
        member.set_password(new_password)
        member.save()

        # Mark token as used
        reset_token.is_used = True
        reset_token.save()

        # Invalidate all other tokens for this member (security)
        PasswordResetToken.objects.filter(member=member, is_used=False).update(is_used=True)

        # Send confirmation email
        _send_password_changed_email(member)

        return Response({"message": "Password reset successfully. You can now log in."})


# ─────────────────────────────────────────────────────────────────────
# EMAIL HELPERS — Add these alongside your other email functions
# ─────────────────────────────────────────────────────────────────────

def _send_password_reset_email(member, reset_url: str) -> None:
    """Sends the password reset link to the member."""
    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>
    <p>We received a request to reset your password for your Saptapadi account.</p>

    <div style="margin:24px 0;padding:20px 24px;background:#FDF5E4;border-radius:12px;
                border-left:4px solid #C5A059;">
      <p style="margin:0 0 8px;font-weight:700;color:#9A6B1A;">🔑 Password Reset Link</p>
      <p style="margin:0;color:#374151;font-size:13px;">
        Click the button below to set a new password.<br/>
        <strong>This link expires in 15 minutes.</strong>
      </p>
    </div>

    <p style="text-align:center;margin:28px 0;">
      <a href="{reset_url}"
         style="display:inline-block;padding:14px 32px;border-radius:10px;
                background:linear-gradient(135deg,#741014,#D4AF37);
                color:#fff;font-weight:700;font-size:15px;
                text-decoration:none;letter-spacing:0.05em;">
        Reset My Password
      </a>
    </p>

    <p style="color:#6b7280;font-size:13px;">
      Or copy this link into your browser:<br/>
      <span style="color:#741014;word-break:break-all;">{reset_url}</span>
    </p>

    <div style="margin:20px 0;padding:14px 18px;background:#FFF4F4;border-radius:10px;
                border-left:4px solid #D32F2F;">
      <p style="margin:0;font-size:12px;color:#B71C1C;">
        ⚠️ If you did not request a password reset, please ignore this email.
        Your password will remain unchanged.
      </p>
    </div>"""

    subject  = "Reset Your Saptapadi Password 🔑"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Reset your password using the link below (valid 15 minutes):\n{reset_url}\n\n"
        f"If you didn't request this, ignore this email.\n\nSaptapadi Team"
    )
    html_msg = _html_wrap("Password Reset Request", body_html)

    try:
        msg = EmailMultiAlternatives(
            subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Password reset email failed: {e}")


def _send_password_changed_email(member) -> None:
    """Confirmation email after password is successfully changed."""
    body_html = f"""
    <p>Namaskara <strong>{member.full_name}</strong> 🙏</p>
    <p>Your Saptapadi account password has been <strong>successfully changed</strong>.</p>

    <div style="margin:20px 0;padding:16px 20px;background:#E8F5E9;border-radius:10px;
                border-left:4px solid #4CAF50;">
      <p style="margin:0 0 6px;font-weight:700;color:#2E7D32;">✅ Password Updated</p>
      <p style="margin:0;color:#374151;">
        Your new password is now active. You can log in with your email and new password.
      </p>
    </div>

    <div style="margin:20px 0;padding:14px 18px;background:#FFF4F4;border-radius:10px;
                border-left:4px solid #D32F2F;">
      <p style="margin:0;font-size:12px;color:#B71C1C;">
        ⚠️ If you did not make this change, please contact our support team immediately.
      </p>
    </div>"""

    subject  = "Your Saptapadi Password Has Been Changed ✅"
    text_msg = (
        f"Namaskara {member.full_name},\n\n"
        f"Your password has been changed successfully.\n"
        f"If you didn't do this, contact support immediately.\n\nSaptapadi Team"
    )
    html_msg = _html_wrap("Password Changed Successfully ✅", body_html, "Login Now",
                          getattr(settings, 'SITE_URL', 'http://localhost:5173') + '/login')

    try:
        msg = EmailMultiAlternatives(
            subject, text_msg, settings.DEFAULT_FROM_EMAIL, [member.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"[EMAIL] Password changed email failed: {e}")




# views.py
from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Ad
from .serializers import AdSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication

class AdListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminToken()]

    def get(self, request, *args, **kwargs):
        ads = Ad.objects.filter(active=True).order_by("-created_at")
        serializer = AdSerializer(ads, many=True, context={"request": request})
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = AdSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdToggleView(APIView):
    permission_classes = [IsAdminToken]  # ← was: [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def patch(self, request, pk, *args, **kwargs):
        ad = get_object_or_404(Ad, pk=pk)
        ad.active = not ad.active
        ad.save(update_fields=["active"])
        return Response({"id": ad.id, "active": ad.active})


class AdDeleteView(APIView):
    permission_classes = [IsAdminToken]  # ← was: [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def delete(self, request, pk, *args, **kwargs):
        ad = get_object_or_404(Ad, pk=pk)
        ad.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)