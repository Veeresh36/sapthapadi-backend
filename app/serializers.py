from rest_framework import serializers
from .models import ContactInquiry, Member, MemberInterest, MemberShortlist, SuccessStory, AdminUser, Match, Plan


class ContactInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInquiry
        fields = ['id', 'name', 'role', 'contact', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


class MemberRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'phone', 'email', 'gender',
            'profile_for', 'religion', 'caste',
            'plan', 'payment_screenshot', 'password', 'confirm_password',
            'payment_reference', 'payment_upi_id',
            'payment_amount', 'payment_confirmed',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if data.get('plan') not in (None, 'free', ''):
            if data.get('plan') != 'free' and not data.get('payment_reference'):
                pass  # don't require payment_reference for basic registration
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        amount = validated_data.get("payment_amount")
        if amount:
            validated_data["payment_amount"] = float(amount)
        member = Member(**validated_data)
        member.set_password(password)
        member.save()
        return member

class MemberPublicSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    interest_status = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'age', 'gender', 'profession', 'occupation',
            'location', 'education', 'income', 'raasi', 'gotra', 'height',
            'languages', 'family_type', 'bio', 'plan', 'profile_complete',
            'profile_photo_url', 'liked', 'interest_status', 'is_completed',
            'phone', 'caste', 'district', 'state', 'religion', 'diet',
            'complexion', 'marital_status', 'nakshatra', 'blood_group',

            # ✅ CORRECT FIELDS
            'brothers',
            'sisters',
            'birth_time',
            'occupation_details',   # 🔥 THIS WAS MISSING
        ]

    def get_age(self, obj):
        if not obj.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - obj.date_of_birth.year - (
            (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
        )

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return None

    def get_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return MemberShortlist.objects.filter(member=request.user, target=obj).exists()

    def get_interest_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        user = request.user

        qs = MemberInterest.objects.filter(
            sender__in=[user, obj],
            receiver__in=[user, obj]
        )

        sent = next((i for i in qs if i.sender_id == user.id), None)
        received = next((i for i in qs if i.sender_id == obj.id), None)

        # Any accepted interest in either direction = both see matched
        if sent and sent.status == 'accepted':
            return 'accepted'

        if received and received.status == 'accepted':
            return 'accepted'   # ✅ Supriya now sees matched too

        if sent:
            return sent.status  # pending / rejected

        if received:
            return 'received_pending'

        return None


    def get_phone(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None

        user = request.user

        # Any accepted interest in either direction = reveal phone
        is_matched = MemberInterest.objects.filter(
            sender__in=[user, obj],
            receiver__in=[user, obj],
            status='accepted'
        ).exists()

        return obj.phone if is_matched else None


class MemberProfileSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(required=False)
    profile_photo_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'phone', 'email', 'profession', 'age',
            'gender', 'date_of_birth', 'birth_time', 'birth_place', 'marital_status',
            'religion', 'caste', 'gotra', 'raasi', 'nakshatra', 'house_deity',
            'height', 'complexion', 'blood_group', 'diet',
            'education', 'education_details', 'occupation', 'occupation_details', 'income',
            'location', 'district', 'state', 'pincode',
            'languages', 'family_type', 'family_status',
            'father_name', 'father_occupation', 'mother_name', 'mother_occupation',
            'brothers', 'sisters', 'address',
            'bio', 'plan', 'status', 'profile_complete',
            'profile_photo', 'profile_photo_url',
            'registered_at', 'password', 'is_completed', 'interests_sent_today',
            'exp_age_from', 'exp_age_to', 'exp_caste', 'exp_education',
            'exp_occupation', 'exp_income',
        ]
        read_only_fields = [
            'id', 'email', 'plan', 'status', 'profile_complete',
            'registered_at', 'interests_sent_today',
        ]

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return None

    def get_age(self, obj):
        if not obj.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - obj.date_of_birth.year - (
            (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
        )

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        profile_photo = validated_data.pop('profile_photo', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if profile_photo:
            instance.profile_photo = profile_photo
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# serializers.py

class MemberAdminSerializer(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField()
    branch_code = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ['id', 'registered_at']

    def get_branch_name(self, obj):
        return obj.added_by_branch.branch_name if obj.added_by_branch else None

    def get_branch_code(self, obj):
        return obj.added_by_branch.branch_code if obj.added_by_branch else None

    def validate(self, data):
        return data

class MemberInterestSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.full_name', read_only=True)
    sender_photo = serializers.SerializerMethodField()
    receiver_photo = serializers.SerializerMethodField()
    sender_profession = serializers.CharField(source='sender.profession', read_only=True)
    receiver_profession = serializers.CharField(source='receiver.profession', read_only=True)
    sender_location = serializers.CharField(source='sender.location', read_only=True)
    receiver_location = serializers.CharField(source='receiver.location', read_only=True)
    sender_age = serializers.SerializerMethodField()
    receiver_age = serializers.SerializerMethodField()

    class Meta:
        model = MemberInterest
        fields = [
            'id', 'sender', 'receiver', 'status', 'sent_at',
            'sender_name', 'receiver_name', 'sender_photo', 'receiver_photo',
            'sender_profession', 'receiver_profession',
            'sender_location', 'receiver_location',
            'sender_age', 'receiver_age',
        ]
        read_only_fields = ['id', 'sender', 'sent_at']

    def get_sender_photo(self, obj):
        request = self.context.get('request')
        if obj.sender.profile_photo and request:
            return request.build_absolute_uri(obj.sender.profile_photo.url)
        return None

    def get_receiver_photo(self, obj):
        request = self.context.get('request')
        if obj.receiver.profile_photo and request:
            return request.build_absolute_uri(obj.receiver.profile_photo.url)
        return None

    def get_sender_age(self, obj):
        dob = obj.sender.date_of_birth
        if not dob:
            return None
        from datetime import date
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_receiver_age(self, obj):
        dob = obj.receiver.date_of_birth
        if not dob:
            return None
        from datetime import date
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class MemberShortlistSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.full_name', read_only=True)
    target_photo = serializers.SerializerMethodField()

    class Meta:
        model = MemberShortlist
        fields = ['id', 'target', 'saved_at', 'target_name', 'target_photo']
        read_only_fields = ['id', 'saved_at']

    def get_target_photo(self, obj):
        request = self.context.get('request')
        if obj.target.profile_photo and request:
            return request.build_absolute_uri(obj.target.profile_photo.url)
        return None


class SuccessStorySerializer(serializers.ModelSerializer):
    submitted_on_display = serializers.SerializerMethodField()

    class Meta:
        model = SuccessStory
        fields = [
            'id',
            'groom_name',
            'bride_name',
            'groom_id',
            'bride_id',
            'community',
            'city',
            'marriage_date',
            'story',
            'rating',
            'status',
            'plan',
            'featured',
            'avatar_idx',
            'submitted_on',              # ✅ correct
            'submitted_on_display',      # ✅ custom field
        ]
        read_only_fields = ['id', 'submitted_on']

    def get_submitted_on_display(self, obj):
        return obj.submitted_on.strftime("%b %d, %Y")


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = AdminUser
        fields = ['id', 'full_name', 'email', 'phone', 'role', 'is_active', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        return AdminUser.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class MatchSerializer(serializers.ModelSerializer):
    male_name = serializers.CharField(source='male.full_name', read_only=True)
    female_name = serializers.CharField(source='female.full_name', read_only=True)

    class Meta:
        model = Match
        fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    
    def validate(self, data):
        # CREATE (POST)
        if not self.instance:
            if data.get("price") is None:
                raise serializers.ValidationError({"price": "Price required"})
            if not data.get("name"):
                raise serializers.ValidationError({"name": "Name required"})

        # UPDATE (PATCH)
        else:
            if "price" in data and data.get("price") is None:
                raise serializers.ValidationError({"price": "Price cannot be null"})
            if "name" in data and not data.get("name"):
                raise serializers.ValidationError({"name": "Name required"})

        return data

    def validate_features(self, value):
        for f in value:
            if not isinstance(f, dict):
                raise serializers.ValidationError("Each feature must be a dict")
            if not str(f.get("text", "")).strip():
                raise serializers.ValidationError("Feature text required")
        return value

    class Meta:
        model  = Plan
        fields = [
            'id', 'name', 'subtitle', 'category',
            'price', 'billing', 'status',
            'features', 'max_contacts', 'priority', 'highlight',
            'visibility_days', 'interests_per_day', 'views_per_day',
            'profession_tags', 'cta_text',
            'members', 'revenue', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'members', 'revenue']

    def get_members(self, obj):
        return obj.members_count

    def get_revenue(self, obj):
        return obj.revenue



## ADD THESE TO YOUR EXISTING serializers.py

from .models import Branch  # add Branch to your import line


class BranchSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=6, required=False)
    members_added    = serializers.SerializerMethodField()
    active_members   = serializers.SerializerMethodField()
    pending_members  = serializers.SerializerMethodField()

    class Meta:
        model  = Branch
        fields = [
            'id', 'branch_name', 'branch_code', 'contact_name',
            'email', 'phone', 'city', 'state', 'address',
            'role', 'status', 'is_active', 'created_at',
            'password', 'members_added', 'active_members', 'pending_members',
        ]
        read_only_fields = ['id', 'branch_code', 'created_at']

    def get_members_added(self, obj):
        return obj.members_added.count()

    def get_active_members(self, obj):
        return obj.members_added.filter(status='active').count()

    def get_pending_members(self, obj):
        return obj.members_added.filter(status='pending').count()

    def create(self, validated_data):
        password = validated_data.pop('password', 'Branch@123')
        branch   = Branch(**validated_data)
        branch.set_password(password)
        branch.save()
        return branch

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class BranchMemberSerializer(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField()
    branch_code = serializers.SerializerMethodField()
 
    class Meta:
        model  = Member
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender',
            'plan', 'status', 'registered_at', 'profile_complete',
            'caste', 'religion', 'location', 'district', 'state',
            'education', 'profession', 'date_of_birth',
            'profile_photo', 'member_id',
            'branch_name', 'branch_code',
            # ── Payment fields now included ───────────────────────────
            'payment_reference',
            'payment_upi_id',
            'payment_amount',
            'payment_confirmed',
            'payment_screenshot',
        ]
        read_only_fields = ['id', 'registered_at', 'member_id', 'profile_complete']
 
    def get_branch_name(self, obj):
        return obj.added_by_branch.branch_name if obj.added_by_branch else None
 
    def get_branch_code(self, obj):
        return obj.added_by_branch.branch_code if obj.added_by_branch else None
 


from rest_framework import serializers
from .models import AppSettings


class AppSettingsSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = AppSettings
        fields = "__all__"

    def get_qr_code_url(self, obj):
        request = self.context.get("request")
        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)
        return None



# serializers.py
from rest_framework import serializers
from .models import Ad


class AdSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            "id",
            "brand_name",
            "category",
            "location",
            "image",
            "image_url",
            "type",
            "active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_image_url(self, obj: Ad) -> str:
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return ""