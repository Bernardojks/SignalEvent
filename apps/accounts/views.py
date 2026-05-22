from django.contrib.auth import login, logout

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.serializers import (
    AuthSessionSerializer,
    CurrentUserSerializer,
    JwtLogoutSerializer,
    LoginSerializer,
    RegisterCompanyAccountSerializer,
)
from apps.accounts.services import (
    authenticate_company_user,
    blacklist_refresh_token,
    generate_auth_tokens,
    register_company_account,
)


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


class RegisterCompanyAccountAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterCompanyAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_company_account(
            organization_name=serializer.validated_data["organization_name"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            full_name=serializer.validated_data.get("full_name", ""),
        )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        response_serializer = AuthSessionSerializer(
            {
                "user": user,
                "tokens": generate_auth_tokens(user),
            }
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate_company_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        response_serializer = AuthSessionSerializer(
            {
                "user": user,
                "tokens": generate_auth_tokens(user),
            }
        )
        return Response(response_serializer.data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.auth is not None:
            serializer = JwtLogoutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            refresh_token = serializer.validated_data["refresh"]
            blacklisted = blacklist_refresh_token(refresh_token)

            if not blacklisted:
                return Response(
                    {"detail": "Invalid or expired refresh token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshTokenAPIView(TokenRefreshView):
    permission_classes = [AllowAny]
