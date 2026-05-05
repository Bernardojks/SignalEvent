from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.selectors import get_dashboard_overview
from apps.organizations.models import Organization


class DashboardOverviewAPIView(APIView):
    def get(self, request):
        organization = request.user.organization

        if not organization:
            return Response({"detail": "No organization found."}, status=404)

        data = get_dashboard_overview(organization)
        return Response(data)