from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from io import BytesIO
from django.core.files import File


# ── Contact Inquiry ───────────────────────────────────────────────────────────

class ContactInquiry(models.Model):
    ROLE_CHOICES = [
        ('member',  'Member / Family'),
        ('broker',  'Broker / Consultant'),
        ('vendor',  'Wedding Vendor'),
        ('other',   'Other Alliance'),
    ]
    name       = models.CharField(max_length=150)
    role       = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    contact    = models.CharField(max_length=200)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role}) — {self.created_at:%d %b %Y}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Contact Inquiries"


# ── Member ────────────────────────────────────────────────────────────────────

def payment_screenshot_path(instance, filename):
    ext      = filename.split('.')[-1].lower()
    new_name = f"{instance.full_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{ext}"
    return f"payments/{new_name}"


def profile_photo_path(instance, filename):
    ext      = filename.split('.')[-1].lower()
    new_name = f"profile_{instance.full_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{ext}"
    return f"profiles/{new_name}"


class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


class Member(AbstractBaseUser, PermissionsMixin):
    PLAN_CHOICES = [('free', 'Free Trial'), ('basic', 'Basic'), ('silver', 'Silver'), ('gold', 'Gold')]
    STATUS_CHOICES = [('pending', 'Pending Approval'), ('active', 'Active'), ('rejected', 'Rejected')]
    
    PROFILE_FOR_CHOICES = [
        ('Self', 'Myself'),
        ('Son', 'Son'),
        ('Daughter', 'Daughter'),
        ('Brother', 'Brother'),
        ('Sister', 'Sister'),
        ('Friend', 'Friend'),
        ('Relative', 'Relative'),
    ]

    # Auth & System Info
    email                = models.EmailField(unique=True)
    profile_for = models.CharField(max_length=20, choices=PROFILE_FOR_CHOICES, default='Self')
    full_name            = models.CharField(max_length=150)
    phone                = models.CharField(max_length=20)
    is_completed         = models.BooleanField(default=False)
    interests_sent_today = models.IntegerField(default=0)
    member_id            = models.CharField(max_length=20, unique=True, blank=True, null=True, default=None)

    # Subscription/Status
    plan               = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')
    status             = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_screenshot = models.ImageField(upload_to=payment_screenshot_path, null=True, blank=True)
    registered_at      = models.DateTimeField(auto_now_add=True)
    upgrade_status     = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved')],
        null=True, blank=True
    )

    # Extended Profile
    profile_photo  = models.ImageField(upload_to=profile_photo_path, null=True, blank=True)
    gender         = models.CharField(max_length=10, blank=True)
    date_of_birth  = models.DateField(null=True, blank=True)
    birth_time     = models.CharField(max_length=50, blank=True)
    birth_place    = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=50, blank=True)

    religion    = models.CharField(max_length=50, default='Lingayat')
    caste       = models.CharField(max_length=100, blank=True)
    gotra       = models.CharField(max_length=100, blank=True)
    raasi       = models.CharField(max_length=100, blank=True)
    nakshatra   = models.CharField(max_length=100, blank=True)
    house_deity = models.CharField(max_length=100, blank=True)

    height      = models.CharField(max_length=20, blank=True)
    complexion  = models.CharField(max_length=50, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    diet        = models.CharField(max_length=50, blank=True)

    education          = models.CharField(max_length=200, blank=True)
    education_details  = models.TextField(blank=True)
    occupation         = models.CharField(max_length=100, blank=True)
    occupation_details = models.TextField(blank=True)
    income             = models.CharField(max_length=50, blank=True)

    location = models.CharField(max_length=150, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state    = models.CharField(max_length=100, blank=True)
    pincode  = models.CharField(max_length=10, blank=True)

    bio              = models.TextField(blank=True)
    profile_complete = models.PositiveIntegerField(default=0)

    plan_activated_at = models.DateTimeField(null=True, blank=True)
    plan_expires_at   = models.DateTimeField(null=True, blank=True)

    profession  = models.CharField(max_length=100, blank=True)
    languages   = models.CharField(max_length=200, blank=True)
    family_type = models.CharField(max_length=50, blank=True)

    # Family
    father_name       = models.CharField(max_length=150, blank=True)
    father_occupation = models.CharField(max_length=150, blank=True)
    mother_name       = models.CharField(max_length=150, blank=True)
    mother_occupation = models.CharField(max_length=150, blank=True)
    brothers          = models.CharField(max_length=10, blank=True)
    sisters           = models.CharField(max_length=10, blank=True)
    family_status     = models.CharField(max_length=50, blank=True)

    # Partner Preferences
    exp_age_from   = models.IntegerField(null=True, blank=True)
    exp_age_to     = models.IntegerField(null=True, blank=True)
    exp_caste      = models.CharField(max_length=100, blank=True)
    exp_education  = models.CharField(max_length=100, blank=True)
    exp_occupation = models.CharField(max_length=100, blank=True)
    exp_income     = models.CharField(max_length=100, blank=True)
    
    # ── Payment Info ─────────────────────────────
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_upi_id = models.CharField(max_length=100, null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_confirmed = models.BooleanField(default=False)

    # Address & Admin
    address  = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)
    
    added_by_branch = models.ForeignKey(
        'Branch', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='members_added'
    )

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone']
    objects         = MemberManager()

    class Meta:
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.full_name} ({self.member_id or self.email})"

    def _generate_member_id(self):
        """Generate next unique member ID like SP001, SP002, ..."""
        last = (
            Member.objects.filter(member_id__startswith="SP")
            .exclude(pk=self.pk)
            .order_by('-member_id')
            .first()
        )
        if last and last.member_id:
            try:
                last_num = int(last.member_id[2:])
                new_num  = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        candidate = f"SP{new_num:03d}"

        # Safety: ensure no collision (edge case with concurrent saves)
        while Member.objects.filter(member_id=candidate).exclude(pk=self.pk).exists():
            new_num += 1
            candidate = f"SP{new_num:03d}"

        return candidate

    def _calculate_profile_complete(self):
        """Return profile completion percentage (0–100)."""
        required_fields = [
            self.profile_for,
            self.full_name,
            self.gender,
            self.date_of_birth,
            self.religion,
            self.gotra,
            self.raasi,
            self.height,
            self.education,
            self.profession,
            self.income,
            self.father_name,
            self.mother_name,
            self.address,
            self.phone,
        ]
        filled = sum(1 for f in required_fields if f and str(f).strip())
        return int((filled / len(required_fields)) * 100)

    def save(self, *args, **kwargs):
        if not self.member_id:
            self.member_id = self._generate_member_id()

        self.profile_complete = self._calculate_profile_complete()
        self.is_completed     = self.profile_complete >= 80

        super().save(*args, **kwargs)


# ── Member Interest (send interest between members) ───────────────────────────

class MemberInterest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    sender    = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='interests_sent')
    receiver  = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='interests_received')
    status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sent_at   = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender.full_name} → {self.receiver.full_name} ({self.status})"


# ── Member Shortlist (like/save a profile) ────────────────────────────────────

class MemberShortlist(models.Model):
    member    = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='shortlisted')
    target    = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='shortlisted_by')
    saved_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('member', 'target')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.member.full_name} saved {self.target.full_name}"


# ── Success Story ─────────────────────────────────────────────────────────────

class SuccessStory(models.Model):
    groom_name   = models.CharField(max_length=150)
    bride_name   = models.CharField(max_length=150)

    groom_id     = models.CharField(max_length=50, blank=True)
    bride_id     = models.CharField(max_length=50, blank=True)

    community    = models.CharField(max_length=100)
    city         = models.CharField(max_length=100, blank=True)

    marriage_date = models.DateField()

    story        = models.TextField()

    rating       = models.IntegerField(default=5)

    status       = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Published', 'Published'), ('Rejected', 'Rejected')],
        default='Pending'
    )

    plan         = models.CharField(
        max_length=10,
        choices=[('Basic', 'Basic'), ('Silver', 'Silver'), ('Gold', 'Gold')],
        default='Basic'
    )

    featured     = models.BooleanField(default=False)
    avatar_idx   = models.IntegerField(default=0)

    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.groom_name} & {self.bride_name}"


# ── Admin User ────────────────────────────────────────────────────────────────

class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',  True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role',      'superadmin')
        return self.create_user(email, password, **extra_fields)


class AdminUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('manager',    'Manager'),
        ('support',    'Support'),
    ]
    full_name  = models.CharField(max_length=150)
    email      = models.EmailField(unique=True)
    phone      = models.CharField(max_length=20, blank=True)
    role       = models.CharField(max_length=15, choices=ROLE_CHOICES, default='support')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects         = AdminUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    class Meta:
        ordering = ['-created_at']


class Match(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    male = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='matches_as_male')
    female = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='matches_as_female')

    score = models.IntegerField(default=70)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



class Plan(models.Model):
    BILLING_CHOICES = [
        ('Monthly',   'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly',    'Yearly'),
    ]
    STATUS_CHOICES = [
        ('Active',   'Active'),
        ('Inactive', 'Inactive'),
        ('Draft',    'Draft'),
    ]

    # Core
    name     = models.CharField(max_length=50, unique=True)
    price    = models.PositiveIntegerField(default=0)
    billing  = models.CharField(max_length=20, choices=BILLING_CHOICES, default='Monthly')
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    # Display / Marketing
    subtitle  = models.CharField(max_length=120, blank=True, default="")
    category  = models.CharField(max_length=80,  blank=True, default="")
    cta_text  = models.CharField(max_length=60,  blank=True, default="")

    # Features — list of {"text": str, "available": bool}
    features      = models.JSONField(default=list)
    profession_tags = models.JSONField(default=list)

    # Limits
    max_contacts      = models.IntegerField(default=0)   # -1 = unlimited
    visibility_days   = models.IntegerField(default=30)
    interests_per_day = models.IntegerField(default=3)
    views_per_day     = models.IntegerField(default=50)  # -1 = unlimited

    # Flags
    priority  = models.BooleanField(default=False)
    highlight = models.BooleanField(default=False)
    
    free_for_female = models.BooleanField(default=False)  # Full access free for females
    free_for_male = models.BooleanField(default=False)    # Full access free for males
    gender_offer_label = models.CharField(max_length=100, blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} — ₹{self.price}/{self.billing}"

    @property
    def members_count(self):
        return Member.objects.filter(
            plan=self.name.lower(),
            status='active'
        ).count()

    @property
    def revenue(self):
        return self.members_count * self.price


class SuccessStory(models.Model):
    STATUS_CHOICES = [
        ('Published', 'Published'),
        ('Pending',   'Pending'),
        ('Rejected',  'Rejected'),
    ]
    PLAN_CHOICES = [
        ('Gold',   'Gold'),
        ('Silver', 'Silver'),
        ('Basic',  'Basic'),
    ]

    groom_name    = models.CharField(max_length=150, default="")
    bride_name    = models.CharField(max_length=150, default="")
    groom_id      = models.CharField(max_length=20, blank=True, default="")
    bride_id      = models.CharField(max_length=20, blank=True, default="")
    community     = models.CharField(max_length=100, default="")
    city          = models.CharField(max_length=100, blank=True, default="")
    marriage_date = models.CharField(max_length=50, default="")
    story         = models.TextField(default="")
    rating        = models.PositiveSmallIntegerField(default=5)
    status        = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    plan          = models.CharField(max_length=10, choices=PLAN_CHOICES,   default='Basic')
    featured      = models.BooleanField(default=False)
    avatar_idx    = models.PositiveSmallIntegerField(default=0)
    submitted_on  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_on']

    def __str__(self):
        return f"{self.groom_name} & {self.bride_name}"





## ADD THESE TO YOUR EXISTING models.py


class BranchManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Branch(AbstractBaseUser):
    """
    A branch operator account.
    Can log in, add members, view/edit ONLY the members they added.
    """
    ROLE_CHOICES = [
        ('branch',  'Branch Operator'),
        ('manager', 'Branch Manager'),
    ]
    STATUS_CHOICES = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
    ]

    # Identity
    branch_name   = models.CharField(max_length=150)          # e.g. "Hubli Branch"
    branch_code   = models.CharField(max_length=20, unique=True, blank=True)  # e.g. "BR001"
    contact_name  = models.CharField(max_length=150)          # operator's name
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=20, blank=True)
    city          = models.CharField(max_length=100, blank=True)
    state         = models.CharField(max_length=100, blank=True)
    address       = models.TextField(blank=True)
    role          = models.CharField(max_length=10, choices=ROLE_CHOICES, default='branch')
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Auth
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='sub_branches'
    )

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['branch_name', 'contact_name']
    objects         = BranchManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.branch_name} ({self.branch_code})"

    def _generate_branch_code(self):
        last = (
            Branch.objects.filter(branch_code__startswith="BR")
            .exclude(pk=self.pk)
            .order_by('-branch_code')
            .first()
        )
        if last and last.branch_code:
            try:
                num = int(last.branch_code[2:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        candidate = f"BR{num:03d}"
        while Branch.objects.filter(branch_code=candidate).exclude(pk=self.pk).exists():
            num += 1
            candidate = f"BR{num:03d}"
        return candidate

    def save(self, *args, **kwargs):
        if not self.branch_code:
            self.branch_code = self._generate_branch_code()
        super().save(*args, **kwargs)

from django.db import models
from typing import Optional
import qrcode

def generate_upi_qr(upi_id: str) -> BytesIO:
    upi_url: str = f"upi://pay?pa={upi_id}&pn=Sapthapadi&cu=INR"
    qr = qrcode.make(upi_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class AppSettings(models.Model):
    site_name: str = models.CharField(max_length=150, default="Sapthapadi")
    
    # Branch control
    enable_branches: bool = models.BooleanField(default=True)

    # Payment
    upi_id: str = models.CharField(max_length=150, blank=True)
    qr_code = models.ImageField(upload_to="qr/", null=True, blank=True)

    # Contact / misc
    support_email: str = models.EmailField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    default_branch = models.ForeignKey(
        'Branch',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    def __str__(self) -> str:
        return "Global Settings"
    
    
    def save(self, *args, **kwargs):
        if self.upi_id:
            qr_buffer = generate_upi_qr(self.upi_id)
            self.qr_code.save("upi_qr.png", File(qr_buffer), save=False)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "App Settings"



# ── ADD THIS TO YOUR EXISTING models.py ──────────────────────────────────────
# Place it at the bottom of models.py (before or after AppSettings)

import uuid
from django.utils import timezone
from datetime import timedelta


class PasswordResetToken(models.Model):
    """
    One-time password reset token for members.
    Auto-expires after 15 minutes.
    """
    member     = models.ForeignKey(
        'Member',
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.member.email} — {'used' if self.is_used else 'active'}"

    @property
    def is_expired(self):
        """Token is valid for 15 minutes."""
        return timezone.now() > self.created_at + timedelta(minutes=15)

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired




# models.py
from django.db import models
from typing import Final


class Ad(models.Model):
    TYPE_VERTICAL: Final[str] = "vertical"
    TYPE_HORIZONTAL: Final[str] = "horizontal"

    TYPE_CHOICES: Final[tuple[tuple[str, str], ...]] = (
        (TYPE_VERTICAL, "Vertical"),
        (TYPE_HORIZONTAL, "Horizontal"),
    )

    brand_name: str = models.CharField(max_length=255)
    category: str = models.CharField(max_length=255)
    location: str = models.CharField(max_length=255, blank=True, null=True)

    image = models.ImageField(upload_to="ads/")

    type: str = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_VERTICAL,
    )

    active: bool = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.brand_name} ({self.type})"


