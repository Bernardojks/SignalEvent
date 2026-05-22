from django.urls import path

from apps.accounts.views import (
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
    RegisterCompanyAccountAPIView,
)

urlpatterns = [
    path(
        "auth/register/",
        RegisterCompanyAccountAPIView.as_view(),
        name="auth-register",
    ),
    path(
        "auth/login/",
        LoginAPIView.as_view(),
        name="auth-login",
    ),
    path(
        "auth/logout/",
        LogoutAPIView.as_view(),
        name="auth-logout",
    ),
    path(
        "auth/token/refresh/",
        RefreshTokenAPIView.as_view(),
        name="auth-token-refresh",
    ),
    path(
        "account/me/",
        CurrentUserAPIView.as_view(),
        name="account-me",
    ),
]
