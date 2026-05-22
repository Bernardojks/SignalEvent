from rest_framework import serializers

from apps.accounts.models import User
from apps.organizations.models import Organization


class OrganizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
        ]


class CurrentUserSerializer(serializers.ModelSerializer):
    organization = OrganizationSummarySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "organization",
        ]


class AuthTokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AuthSessionSerializer(serializers.Serializer):
    user = CurrentUserSerializer(read_only=True)
    tokens = AuthTokensSerializer(read_only=True)


class RegisterCompanyAccountSerializer(serializers.Serializer):
    organization_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class JwtLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
