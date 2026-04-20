# from django.urls import path
# from .views import (
#     homepage,
#     # ── Public ──────────────────────────────────────────────────────────────
#     ContactInquiryView,
#     MemberRegisterView,
#     # ── Admin auth ───────────────────────────────────────────────────────────
#     AdminLoginView,
#     # ── Admin dashboard ──────────────────────────────────────────────────────
#     DashboardStatsView,
#     # ── Admin members ────────────────────────────────────────────────────────
#     MemberListView,
#     MemberDetailView,
#     # ── Admin inquiries ──────────────────────────────────────────────────────
#     ContactInquiryListView,
#     ContactInquiryDetailView,
#     # ── Success stories ──────────────────────────────────────────────────────
#     SuccessStoryListView,
#     SuccessStoryDetailView,
#     # ── Admin users ──────────────────────────────────────────────────────────
#     AdminUserListView,
#     AdminUserCreateView,
#     AdminUserDetailView,
#     MemberLoginView,
# )

# urlpatterns = [

#     # ── Public endpoints (no auth) ───────────────────────────────────────────
#     path('register/',   MemberRegisterView.as_view(),  name='member-register'),
#     path('contact/',    ContactInquiryView.as_view(),  name='contact-submit'),
#     path('member/login/', MemberLoginView.as_view(), name='member-login'),
    
    
#     # ── Admin auth ───────────────────────────────────────────────────────────
#     path('admin/login/', AdminLoginView.as_view(),     name='admin-login'),

#     # ── Admin dashboard stats ────────────────────────────────────────────────
#     path('admin/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),

#     # ── Admin members ─────────────────────────────────────────────────────────
#     path('admin/members/',            MemberListView.as_view(),   name='member-list'),
#     path('admin/members/<int:pk>/',   MemberDetailView.as_view(), name='member-detail'),

#     # ── Admin contact inquiries ───────────────────────────────────────────────
#     path('admin/inquiries/',          ContactInquiryListView.as_view(),   name='inquiry-list'),
#     path('admin/inquiries/<int:pk>/', ContactInquiryDetailView.as_view(), name='inquiry-detail'),

#     # ── Success stories ───────────────────────────────────────────────────────
#     path('admin/stories/',            SuccessStoryListView.as_view(),   name='story-list'),
#     path('admin/stories/<int:pk>/',   SuccessStoryDetailView.as_view(), name='story-detail'),

#     # ── Admin user management ─────────────────────────────────────────────────
#     path('admin/users/',              AdminUserListView.as_view(),   name='admin-list'),
#     path('admin/users/create/',       AdminUserCreateView.as_view(), name='admin-create'),
#     path('admin/users/<int:pk>/',     AdminUserDetailView.as_view(), name='admin-detail'),
# ]


from django.urls import path
from .views import (
    homepage,

    # ── Public ───────────────────────────────────────────────
    ContactInquiryView,
    MemberRegisterView,
    MemberLoginView,

    # ── Admin auth ───────────────────────────────────────────
    AdminLoginView,

    # ── Admin dashboard ──────────────────────────────────────
    DashboardStatsView,

    # ── Admin members ────────────────────────────────────────
    MemberListView,
    MemberDetailView,

    # ── Admin inquiries ──────────────────────────────────────
    ContactInquiryListView,
    ContactInquiryDetailView,

    # ── Success stories ──────────────────────────────────────
    SuccessStoryListView,
    SuccessStoryDetailView,

    # ── Admin users ──────────────────────────────────────────
    AdminUserListView,
    AdminUserCreateView,
    AdminUserDetailView,

    # ── NEW PROFILE SYSTEM (IMPORTANT) ───────────────────────
    ExploreProfilesView,
    MyProfileView,
    InterestListView,
    SendInterestView,
    RespondInterestView,
    ToggleShortlistView,
    ForgotPasswordView,
    ResetPasswordView,
)

from django.urls import path
from .views import *

urlpatterns = [
    path('', homepage),

    # PUBLIC
    path('register/', MemberRegisterView.as_view()),
    path('contact/', ContactInquiryView.as_view()),
    path('member/login/', MemberLoginView.as_view()),

    # ADMIN
    path('admin/login/', AdminLoginView.as_view()),
    path('admin/stats/', DashboardStatsView.as_view()),
    path('admin/members/', MemberListView.as_view()),
    path('admin/members/<int:pk>/', MemberDetailView.as_view()),
    path('admin/inquiries/', ContactInquiryListView.as_view()),
    path('admin/inquiries/<int:pk>/', ContactInquiryDetailView.as_view()),
    path('admin/stories/', SuccessStoryListView.as_view()),
    path('admin/stories/<int:pk>/', SuccessStoryDetailView.as_view()),
    path('admin/users/', AdminUserListView.as_view()),
    path('admin/users/create/', AdminUserCreateView.as_view()),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view()),

    # MAIN APP APIs
    path('profiles/explore/', ExploreProfilesView.as_view()),
    path('profiles/me/', MyProfileView.as_view()),
    path('profiles/interests/', InterestListView.as_view()),
    path('profiles/interests/send/', SendInterestView.as_view()),
    path('profiles/interests/<int:pk>/respond/', RespondInterestView.as_view()),
    path('profiles/shortlist/', ShortlistView.as_view()),
    path('profiles/upgrade-plan/', UpgradePlanView.as_view()),
    path('profiles/<int:id>/', ProfileDetailView.as_view()),
    path('matches/', MatchListCreateView.as_view()),
    path('matches/<int:pk>/', MatchDetailView.as_view()),
    path('admin/plans/',          PlanListCreateView.as_view()),
    path('admin/plans/<int:pk>/', PlanDetailView.as_view()),
    
    path('admin/plan-stats/', PlanStatsView.as_view()),
    path('admin/members/create/', AdminCreateMemberView.as_view()),
    path("stories/", PublicSuccessStoryView.as_view()),
    
    
    # Branch Auth
    path('branch/login/',  BranchLoginView.as_view()),
    path('branch/me/',     BranchMeView.as_view()),
    
    # Branch self-service (branch operators use these)
    path('branch/members/',          BranchMemberListView.as_view()),
    path('branch/members/<int:pk>/', BranchMemberDetailView.as_view()),
    
    # Admin managing branches
    path('admin/branches/',                    AdminBranchListView.as_view()),
    path('admin/branches/<int:pk>/',           AdminBranchDetailView.as_view()),
    path('admin/branches/<int:pk>/toggle/',    AdminBranchToggleStatusView.as_view()),
    path('admin/branches/<int:pk>/members/',   AdminBranchMembersView.as_view()),
    path('admin/branches/all-members/',        AdminAllBranchMembersView.as_view()),
    
    # admin
    path('admin/settings/', AdminAppSettingsView.as_view()),
    
    # public
    path("settings/public/", PublicAppSettingsView.as_view()),
    
    path('member/forgot-password/', ForgotPasswordView.as_view()),
    path('member/reset-password/',  ResetPasswordView.as_view()),
    
    path("ads/", AdListCreateView.as_view(), name="ads-list-create"),
    path("ads/<int:pk>/toggle/", AdToggleView.as_view(), name="ads-toggle"),
    path("ads/<int:pk>/delete/", AdDeleteView.as_view(), name="ads-delete"),
    
    
    
    # PUBLIC PLAN API (FIX)
    path('plans/public/', PublicPlansView.as_view()),
]