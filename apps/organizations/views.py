from django.shortcuts import get_object_or_404

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSecuritySettingsSerializer


class OrganizationSecuritySettingsAPIView(RetrieveUpdateAPIView):
    serializer_class = OrganizationSecuritySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(
            Organization,
            id=self.request.user.organization_id,
        )
