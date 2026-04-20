# mysite/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

jwt_urlpatterns = [
    path('token/',         TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),
    path('token/verify/',  TokenVerifyView.as_view(),     name='token_verify'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('auth/', include(jwt_urlpatterns)),
        path('', include('app.urls')),        # fixed: 'app.url' → 'app.urls'
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)